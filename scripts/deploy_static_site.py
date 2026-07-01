#!/usr/bin/env python3
"""Deploy a static bundle to DreamHost shared hosting over SFTP.

This repo intentionally keeps deployment thin: upload the contents of a local
static bundle into the verified DreamHost site directory using credentials from
the local gitignored `.env`.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import tempfile
from pathlib import Path, PurePosixPath

try:
    import pexpect
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing Python dependency `pexpect`. Install it with "
        "`python -m pip install -r requirements-deploy.txt`."
    ) from exc


REQUIRED_ENV_KEYS = [
    "DREAMHOST_SFTP_HOST",
    "DREAMHOST_SFTP_USERNAME",
    "DREAMHOST_SFTP_PASSWORD",
    "DREAMHOST_SITE_PATH",
]
IGNORED_NAMES = {".DS_Store", ".deploy-manifest.json", "_internal"}
MANIFEST_NAME = ".deploy-manifest.json"
DEFAULT_SFTP_TIMEOUT_SECONDS = 1800


def parse_dotenv(dotenv_path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not dotenv_path.exists():
        return env
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip("'").strip('"')
    return env


def load_env(repo_root: Path) -> dict[str, str]:
    merged = parse_dotenv(repo_root / ".env")
    for key in REQUIRED_ENV_KEYS + ["DREAMHOST_DEPLOY_SOURCE_DIR"]:
        if os.environ.get(key):
            merged[key] = os.environ[key]
    missing = [key for key in REQUIRED_ENV_KEYS if not merged.get(key)]
    if missing:
        raise SystemExit(
            "Missing required deploy config: "
            + ", ".join(missing)
            + ". Populate them in the local .env or shell env."
        )
    return merged


def rel_depth(rel_path: str) -> tuple[int, str]:
    return (rel_path.count("/"), rel_path)


def to_posix(rel_path: Path) -> str:
    return PurePosixPath(*rel_path.parts).as_posix()


def iter_parent_paths(rel_path: str) -> list[str]:
    current = PurePosixPath(rel_path)
    return [parent.as_posix() for parent in current.parents if parent.as_posix() != "."]


def collect_source_state(source_dir: Path) -> dict[str, list[str]]:
    top_level = sorted(
        child
        for child in source_dir.iterdir()
        if child.name not in IGNORED_NAMES
    )
    if not top_level:
        raise SystemExit(f"Source directory is empty: {source_dir}")

    files: set[str] = set()
    dirs: set[str] = set()

    for path in sorted(source_dir.rglob("*")):
        rel = path.relative_to(source_dir)
        if any(part in IGNORED_NAMES for part in rel.parts):
            continue
        rel_str = to_posix(rel)
        if path.is_dir():
            dirs.add(rel_str)
            continue
        if path.is_file():
            files.add(rel_str)
            dirs.update(iter_parent_paths(rel_str))

    return {
        "files": sorted(files),
        "dirs": sorted(dirs, key=rel_depth),
        "top_level": [child.name for child in top_level],
    }


def fetch_remote_manifest(remote_path: str, host: str, username: str, password: str) -> dict | None:
    with tempfile.TemporaryDirectory() as tmpdir:
        local_manifest = Path(tmpdir) / MANIFEST_NAME
        batch_text = "\n".join(
            [
                f"cd {shlex.quote(remote_path)}",
                f"-get {MANIFEST_NAME} {shlex.quote(str(local_manifest))}",
            ]
        ) + "\n"
        run_sftp(
            batch_text=batch_text,
            host=host,
            username=username,
            password=password,
        )
        if not local_manifest.exists():
            return None
        return json.loads(local_manifest.read_text(encoding="utf-8"))


def build_sync_plan(previous: dict | None, current: dict[str, list[str]]) -> dict[str, list[str]]:
    old_files = set((previous or {}).get("files", []))
    old_dirs = set((previous or {}).get("dirs", []))
    new_files = set(current["files"])
    new_dirs = set(current["dirs"])

    pre_delete_files = set(old_files & new_dirs)
    pre_delete_dirs: set[str] = set()

    for old_file in old_files:
        if any(parent in new_files for parent in iter_parent_paths(old_file)):
            pre_delete_files.add(old_file)

    for old_dir in old_dirs:
        if old_dir in new_files or any(parent in new_files for parent in iter_parent_paths(old_dir)):
            pre_delete_dirs.add(old_dir)

    stale_files = {path for path in (old_files - new_files) if path not in pre_delete_files}
    stale_dirs = {path for path in (old_dirs - new_dirs) if path not in pre_delete_dirs}

    return {
        "pre_delete_files": sorted(pre_delete_files, key=rel_depth, reverse=True),
        "pre_delete_dirs": sorted(pre_delete_dirs, key=rel_depth, reverse=True),
        "stale_files": sorted(stale_files, key=rel_depth, reverse=True),
        "stale_dirs": sorted(stale_dirs, key=rel_depth, reverse=True),
    }


def write_manifest_file(source_dir: Path, current: dict[str, list[str]]) -> Path:
    payload = {
        "source_dir": str(source_dir),
        "files": current["files"],
        "dirs": current["dirs"],
    }
    handle = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
    with handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return Path(handle.name)


def build_batch(
    source_dir: Path,
    remote_path: str,
    current: dict[str, list[str]],
    plan: dict[str, list[str]],
    manifest_path: Path,
) -> str:
    commands = [
        f"cd {shlex.quote(remote_path)}",
        f"lcd {shlex.quote(str(source_dir))}",
    ]

    for rel_path in plan["pre_delete_files"]:
        commands.append(f"-rm {shlex.quote(rel_path)}")
    for rel_path in plan["pre_delete_dirs"]:
        commands.append(f"-rmdir {shlex.quote(rel_path)}")

    for child_name in current["top_level"]:
        name = shlex.quote(child_name)
        child = source_dir / child_name
        if child.is_dir():
            commands.append(f"put -r {name}")
        else:
            commands.append(f"put {name}")

    for rel_path in plan["stale_files"]:
        commands.append(f"-rm {shlex.quote(rel_path)}")
    for rel_path in plan["stale_dirs"]:
        commands.append(f"-rmdir {shlex.quote(rel_path)}")

    commands.append(f"put {shlex.quote(str(manifest_path))} {MANIFEST_NAME}")
    commands.extend(
        [
            "ls index.html",
            "ls chapter-001.html",
            "ls images",
            f"ls {MANIFEST_NAME}",
        ]
    )
    return "\n".join(commands) + "\n"


def run_sftp(batch_text: str, host: str, username: str, password: str) -> str:
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
        handle.write(batch_text)
        batch_path = handle.name

    command = [
        "sftp",
        "-oBatchMode=no",
        "-oStrictHostKeyChecking=accept-new",
        "-b",
        batch_path,
        f"{username}@{host}",
    ]

    try:
        child = pexpect.spawn(
            command[0],
            command[1:],
            encoding="utf-8",
            timeout=int(os.environ.get("DREAMHOST_SFTP_TIMEOUT_SECONDS", DEFAULT_SFTP_TIMEOUT_SECONDS)),
        )
        transcript_parts: list[str] = []

        while True:
            index = child.expect(
                [
                    r"Are you sure you want to continue connecting \(yes/no/\[fingerprint\]\)\?",
                    r"[Pp]assword:",
                    pexpect.EOF,
                    pexpect.TIMEOUT,
                ]
            )
            transcript_parts.append(child.before)

            if index == 0:
                child.sendline("yes")
                continue
            if index == 1:
                child.sendline(password)
                continue
            if index == 2:
                break
            raise SystemExit(
                "Timed out while waiting for SFTP to finish. "
                "Set DREAMHOST_SFTP_TIMEOUT_SECONDS to a larger value if this bundle is unusually large."
            )

        tail = child.after if isinstance(child.after, str) else ""
        transcript = "".join(transcript_parts) + tail
        if child.exitstatus not in (0, None) and child.exitstatus != 0:
            raise SystemExit(f"SFTP exited with status {child.exitstatus}.\n{transcript}")
        return transcript
    finally:
        try:
            os.unlink(batch_path)
        except FileNotFoundError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        help="Path to the local static bundle directory to upload. Defaults to DREAMHOST_DEPLOY_SOURCE_DIR from .env.",
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repo root containing the local .env (default: current repo root).",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    env = load_env(repo_root)

    source_dir = Path(args.source or env.get("DREAMHOST_DEPLOY_SOURCE_DIR", "")).expanduser()
    if not str(source_dir):
        raise SystemExit(
            "No deploy source provided. Pass --source or set DREAMHOST_DEPLOY_SOURCE_DIR in the local .env."
        )
    source_dir = source_dir.resolve()
    if not source_dir.is_dir():
        raise SystemExit(f"Deploy source directory does not exist: {source_dir}")
    if not (source_dir / "index.html").exists():
        raise SystemExit(f"Deploy source is missing index.html: {source_dir}")

    current = collect_source_state(source_dir)
    previous = fetch_remote_manifest(
        remote_path=env["DREAMHOST_SITE_PATH"],
        host=env["DREAMHOST_SFTP_HOST"],
        username=env["DREAMHOST_SFTP_USERNAME"],
        password=env["DREAMHOST_SFTP_PASSWORD"],
    )
    plan = build_sync_plan(previous=previous, current=current)
    manifest_path = write_manifest_file(source_dir=source_dir, current=current)

    try:
        batch_text = build_batch(
            source_dir=source_dir,
            remote_path=env["DREAMHOST_SITE_PATH"],
            current=current,
            plan=plan,
            manifest_path=manifest_path,
        )
        print(
            f"Deploying {source_dir} to "
            f"{env['DREAMHOST_SFTP_USERNAME']}@{env['DREAMHOST_SFTP_HOST']}:{env['DREAMHOST_SITE_PATH']}"
        )
        print(
            "Sync plan:",
            json.dumps(
                {
                    "previous_manifest_found": previous is not None,
                    **plan,
                },
                indent=2,
                sort_keys=True,
            ),
        )
        transcript = run_sftp(
            batch_text=batch_text,
            host=env["DREAMHOST_SFTP_HOST"],
            username=env["DREAMHOST_SFTP_USERNAME"],
            password=env["DREAMHOST_SFTP_PASSWORD"],
        )
        print("SFTP transcript:")
        print(transcript.strip())
        return 0
    finally:
        try:
            manifest_path.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    sys.exit(main())
