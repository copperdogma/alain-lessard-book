#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_MANIFEST = REPO_ROOT / "doc-web-runtime.json"
MANIFEST_SCHEMA_VERSION = "doc_web_bundle_manifest_v1"
PROVENANCE_SCHEMA_VERSION = "doc_web_provenance_block_v1"
ACTIVE_BUNDLE_FILENAME = "active-bundle.json"


class DocWebImportError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeManifest:
    source_path: str
    python_executable: str
    default_recipe: str
    default_input_images: str | None
    default_input_pdf: str | None
    source_runs_root: str
    snapshot_root: str
    accepted_bundle_root: str


@dataclass(frozen=True)
class RuntimePaths:
    source_root: Path
    python_executable: str
    default_recipe_path: Path
    default_input_images_path: Path | None
    default_input_pdf_path: Path | None
    source_runs_root: Path
    snapshot_root: Path
    accepted_bundle_root: Path
    active_bundle_path: Path


@dataclass(frozen=True)
class BundleSummary:
    document_id: str
    title: str
    entry_count: int
    provenance_row_count: int
    image_count: int
    reading_order: list[str]


@dataclass(frozen=True)
class ImportedBundle:
    snapshot_id: str
    runtime_metadata_path: Path
    runtime_bundle_root: Path
    accepted_bundle_root: Path
    active_bundle_path: Path


class _BundleHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.dom_ids: set[str] = set()
        self.image_paths: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {name.lower(): value for name, value in attrs}
        element_id = attrs_map.get("id")
        if element_id:
            self.dom_ids.add(element_id)
        if tag.lower() == "img":
            src = attrs_map.get("src")
            if src:
                self.image_paths.append(src)


def load_runtime_manifest() -> RuntimeManifest:
    payload = _load_json_object(RUNTIME_MANIFEST, label="runtime manifest")
    return RuntimeManifest(
        source_path=_required_string(payload, "sourcePath"),
        python_executable=str(payload.get("pythonExecutable") or "python"),
        default_recipe=_required_string(payload, "defaultRecipe"),
        default_input_images=_optional_string(payload, "defaultInputImages"),
        default_input_pdf=_optional_string(payload, "defaultInputPdf"),
        source_runs_root=str(payload.get("sourceRunsRoot") or "output/runs"),
        snapshot_root=str(payload.get("snapshotRoot") or ".runtime/doc-web-imports"),
        accepted_bundle_root=str(payload.get("acceptedBundleRoot") or "input/doc-web-html"),
    )


def build_runtime_paths(manifest: RuntimeManifest) -> RuntimePaths:
    source_root = _resolve_repo_path(manifest.source_path)
    default_recipe_path = _resolve_recipe_path(source_root, manifest.default_recipe)
    default_input_images_path = (
        _resolve_repo_path(manifest.default_input_images)
        if manifest.default_input_images
        else None
    )
    default_input_pdf_path = (
        _resolve_repo_path(manifest.default_input_pdf)
        if manifest.default_input_pdf
        else None
    )
    snapshot_root = _resolve_repo_path(manifest.snapshot_root)
    accepted_bundle_root = _resolve_repo_path(manifest.accepted_bundle_root)
    source_runs_root = _resolve_source_path(source_root, manifest.source_runs_root)
    return RuntimePaths(
        source_root=source_root,
        python_executable=manifest.python_executable,
        default_recipe_path=default_recipe_path,
        default_input_images_path=default_input_images_path,
        default_input_pdf_path=default_input_pdf_path,
        source_runs_root=source_runs_root,
        snapshot_root=snapshot_root,
        accepted_bundle_root=accepted_bundle_root,
        active_bundle_path=accepted_bundle_root / ACTIVE_BUNDLE_FILENAME,
    )


def fetch_doc_web_contract(paths: RuntimePaths, *, python_executable: str | None = None) -> dict[str, Any]:
    command = [
        python_executable or paths.python_executable,
        "-c",
        "from doc_web.cli import main; main()",
        "contract",
        "--json",
    ]
    result = subprocess.run(
        command,
        cwd=paths.source_root,
        check=True,
        text=True,
        capture_output=True,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise DocWebImportError(f"doc-web contract did not return JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise DocWebImportError("doc-web contract response must be a JSON object")
    return payload


def run_doc_web(
    paths: RuntimePaths,
    *,
    run_id: str,
    recipe_path: Path | None = None,
    input_images_path: Path | None = None,
    input_pdf_path: Path | None = None,
    python_executable: str | None = None,
    force: bool = False,
    allow_run_id_reuse: bool = False,
    start_from: str | None = None,
    end_at: str | None = None,
    dry_run: bool = False,
    extra_args: list[str] | None = None,
) -> Path:
    recipe = (recipe_path or paths.default_recipe_path).resolve()
    input_images = (input_images_path or paths.default_input_images_path)
    input_pdf = (input_pdf_path or paths.default_input_pdf_path)
    python_bin = python_executable or paths.python_executable

    if not recipe.exists():
        raise DocWebImportError(f"Recipe not found: {recipe}")
    if input_images and not input_images.exists():
        raise DocWebImportError(f"Input images directory not found: {input_images}")
    if input_pdf and not input_pdf.exists():
        raise DocWebImportError(f"Input PDF not found: {input_pdf}")
    if bool(input_images) == bool(input_pdf):
        raise DocWebImportError("Exactly one of input images or input PDF must be configured")

    command = [
        python_bin,
        "driver.py",
        "--recipe",
        str(recipe),
        "--run-id",
        run_id,
        "--output-dir",
        str(paths.source_runs_root),
    ]
    if input_images:
        command.extend(["--input-images", str(input_images.resolve())])
    if input_pdf:
        command.extend(["--input-pdf", str(input_pdf.resolve())])
    if force:
        command.append("--force")
    if allow_run_id_reuse:
        command.append("--allow-run-id-reuse")
    if start_from:
        command.extend(["--start-from", start_from])
    if end_at:
        command.extend(["--end-at", end_at])
    if dry_run:
        command.append("--dry-run")
    if extra_args:
        command.extend(extra_args)

    run_command(command, cwd=paths.source_root)
    return paths.source_runs_root / run_id / "output" / "html"


def import_run_bundle(
    paths: RuntimePaths,
    *,
    run_id: str,
    snapshot_id: str | None = None,
    recipe_path: Path | None = None,
    python_executable: str | None = None,
    force: bool = False,
) -> ImportedBundle:
    bundle_root = paths.source_runs_root / run_id / "output" / "html"
    if not bundle_root.exists():
        raise DocWebImportError(f"Bundle output not found for run '{run_id}': {bundle_root}")
    source_payload = {
        "runId": run_id,
        "recipePath": _rel_or_abs(recipe_path or paths.default_recipe_path),
    }
    return import_bundle(
        paths,
        bundle_root=bundle_root,
        snapshot_id=snapshot_id or run_id,
        python_executable=python_executable,
        force=force,
        source_payload=source_payload,
    )


def import_bundle(
    paths: RuntimePaths,
    *,
    bundle_root: Path,
    snapshot_id: str,
    python_executable: str | None = None,
    force: bool = False,
    source_payload: dict[str, Any] | None = None,
) -> ImportedBundle:
    bundle_root = bundle_root.resolve()
    if not bundle_root.exists():
        raise DocWebImportError(f"Bundle root not found: {bundle_root}")

    summary = validate_bundle_contract(bundle_root)
    contract_payload = fetch_doc_web_contract(paths, python_executable=python_executable)

    runtime_snapshot_dir = (paths.snapshot_root / snapshot_id).resolve()
    runtime_bundle_root = runtime_snapshot_dir / "bundle"
    accepted_bundle_root = (paths.accepted_bundle_root / snapshot_id).resolve()
    runtime_metadata_path = runtime_snapshot_dir / "import-metadata.json"
    accepted_metadata_path = accepted_bundle_root / "_alain-import-metadata.json"

    for target in (runtime_snapshot_dir, accepted_bundle_root):
        if target.exists():
            if not force:
                raise DocWebImportError(f"Target already exists: {target}. Use --force to replace it.")
            shutil.rmtree(target)

    runtime_bundle_root.parent.mkdir(parents=True, exist_ok=True)
    paths.accepted_bundle_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(bundle_root, runtime_bundle_root)
    shutil.copytree(bundle_root, accepted_bundle_root)

    imported_at = _iso_now()
    metadata = {
        "schemaVersion": "alain_doc_web_import_v1",
        "snapshotId": snapshot_id,
        "importedAt": imported_at,
        "source": {
            "docWebRoot": _rel_or_abs(paths.source_root),
            "bundleRoot": _rel_or_abs(bundle_root),
            "contract": contract_payload,
        },
        "bundle": {
            **asdict(summary),
            "runtimeBundleRoot": _rel_or_abs(runtime_bundle_root),
            "acceptedBundleRoot": _rel_or_abs(accepted_bundle_root),
            "manifestPath": _rel_or_abs(accepted_bundle_root / "manifest.json"),
            "provenancePath": _rel_or_abs(accepted_bundle_root / "provenance" / "blocks.jsonl"),
        },
    }
    if source_payload:
        metadata["source"].update(source_payload)

    write_json(runtime_metadata_path, metadata)
    write_json(accepted_metadata_path, metadata)
    write_json(
        paths.active_bundle_path,
        {
            "schemaVersion": "alain_doc_web_active_bundle_v1",
            "updatedAt": imported_at,
            "snapshotId": snapshot_id,
            "bundleRoot": _rel_or_abs(accepted_bundle_root),
            "manifestPath": _rel_or_abs(accepted_bundle_root / "manifest.json"),
            "provenancePath": _rel_or_abs(accepted_bundle_root / "provenance" / "blocks.jsonl"),
        },
    )

    return ImportedBundle(
        snapshot_id=snapshot_id,
        runtime_metadata_path=runtime_metadata_path,
        runtime_bundle_root=runtime_bundle_root,
        accepted_bundle_root=accepted_bundle_root,
        active_bundle_path=paths.active_bundle_path,
    )


def validate_bundle_contract(bundle_root: Path) -> BundleSummary:
    bundle_root = bundle_root.resolve()
    manifest = _load_json_object(bundle_root / "manifest.json", label="bundle manifest")
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise DocWebImportError(
            f"Bundle manifest schema_version must be {MANIFEST_SCHEMA_VERSION}, got {manifest.get('schema_version')!r}"
        )

    required_top_level = {
        "document_id": str,
        "title": str,
        "source_artifact": str,
        "index_path": str,
        "entries": list,
        "reading_order": list,
        "provenance_path": str,
    }
    for field_name, expected_type in required_top_level.items():
        value = manifest.get(field_name)
        if not isinstance(value, expected_type):
            raise DocWebImportError(f"Bundle manifest field '{field_name}' must be {expected_type.__name__}")

    _resolve_bundle_member(bundle_root, manifest["index_path"], "index_path")
    provenance_path = _resolve_bundle_member(bundle_root, manifest["provenance_path"], "provenance_path")

    entry_map: dict[str, dict[str, Any]] = {}
    for entry in manifest["entries"]:
        if not isinstance(entry, dict):
            raise DocWebImportError("Every manifest entry must be an object")
        entry_id = _required_string(entry, "entry_id")
        if entry_id in entry_map:
            raise DocWebImportError(f"Duplicate manifest entry_id: {entry_id}")
        for field_name in ("kind", "title", "path"):
            _required_string(entry, field_name)
        if not isinstance(entry.get("order"), int):
            raise DocWebImportError(f"Entry '{entry_id}' field 'order' must be int")
        html_path = _resolve_bundle_member(bundle_root, entry["path"], f"entry:{entry_id}")
        if html_path.suffix.lower() != ".html":
            raise DocWebImportError(f"Entry '{entry_id}' path must point to HTML")
        entry_map[entry_id] = entry

    reading_order = manifest["reading_order"]
    if sorted(reading_order) != sorted(entry_map):
        raise DocWebImportError("reading_order must list every manifest entry exactly once")

    provenance_by_entry = _load_provenance_rows(provenance_path, entry_map)
    image_paths: set[str] = set()
    for entry_id, entry in entry_map.items():
        html_path = _resolve_bundle_member(bundle_root, entry["path"], f"entry:{entry_id}")
        parser = _BundleHtmlParser()
        parser.feed(html_path.read_text(encoding="utf-8"))
        parser.close()
        for block_id in provenance_by_entry.get(entry_id, []):
            if block_id not in parser.dom_ids:
                raise DocWebImportError(f"Provenance block '{block_id}' is missing from {entry['path']}")
        for image_path in parser.image_paths:
            _resolve_bundle_member(bundle_root, image_path, f"image:{image_path}")
            image_paths.add(image_path)

    return BundleSummary(
        document_id=manifest["document_id"],
        title=manifest["title"],
        entry_count=len(entry_map),
        provenance_row_count=sum(len(rows) for rows in provenance_by_entry.values()),
        image_count=len(image_paths),
        reading_order=list(reading_order),
    )


def _load_provenance_rows(provenance_path: Path, entry_map: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    rows_by_entry: dict[str, list[str]] = {entry_id: [] for entry_id in entry_map}
    for line_number, raw_line in enumerate(provenance_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            payload = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise DocWebImportError(f"Provenance row {line_number} is not valid JSON: {exc}") from exc
        if payload.get("schema_version") != PROVENANCE_SCHEMA_VERSION:
            raise DocWebImportError(
                f"Provenance row {line_number} schema_version must be {PROVENANCE_SCHEMA_VERSION}"
            )
        entry_id = payload.get("entry_id")
        block_id = payload.get("block_id")
        if not isinstance(entry_id, str) or entry_id not in entry_map:
            raise DocWebImportError(f"Provenance row {line_number} references unknown entry_id {entry_id!r}")
        if not isinstance(block_id, str):
            raise DocWebImportError(f"Provenance row {line_number} block_id must be a string")
        rows_by_entry[entry_id].append(block_id)
    return rows_by_entry


def run_command(command: list[str], *, cwd: Path) -> None:
    print("+ " + " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def _resolve_repo_path(value: str | None) -> Path:
    if not value:
        raise DocWebImportError("Missing required path value")
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (REPO_ROOT / path).resolve()


def _resolve_source_path(source_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (source_root / path).resolve()


def _resolve_recipe_path(source_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    repo_candidate = (REPO_ROOT / path).resolve()
    if repo_candidate.exists():
        return repo_candidate
    return (source_root / path).resolve()


def _resolve_bundle_member(bundle_root: Path, relative_path: str, label: str) -> Path:
    candidate = (bundle_root / PurePosixPath(relative_path)).resolve()
    if not candidate.is_relative_to(bundle_root):
        raise DocWebImportError(f"{label} escapes bundle root: {relative_path}")
    if not candidate.exists():
        raise DocWebImportError(f"{label} not found: {relative_path}")
    return candidate


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    if not path.exists():
        raise DocWebImportError(f"Missing {label}: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DocWebImportError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise DocWebImportError(f"{label} must be a JSON object")
    return payload


def _required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise DocWebImportError(f"Field '{field_name}' must be a non-empty string")
    return value.strip()


def _optional_string(payload: dict[str, Any], field_name: str) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise DocWebImportError(f"Field '{field_name}' must be a string when present")
    normalized = value.strip()
    return normalized or None


def _iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _rel_or_abs(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _print_json(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run and import doc-web bundles for the Alain Lessard book.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    contract_parser = subparsers.add_parser("contract", help="Emit the local doc-web contract payload.")
    contract_parser.add_argument("--python", help="Override the Python executable used for doc-web commands.")

    run_parser = subparsers.add_parser("run", help="Run the configured doc-web recipe.")
    run_parser.add_argument("--run-id", required=True, help="Run id to use in the sibling doc-web checkout.")
    run_parser.add_argument("--recipe", help="Override the recipe path.")
    run_parser.add_argument("--input-images", help="Override the cleaned image directory path.")
    run_parser.add_argument("--input-pdf", help="Override the input PDF path.")
    run_parser.add_argument("--python", help="Override the Python executable used for doc-web commands.")
    run_parser.add_argument("--force", action="store_true", help="Pass --force to doc-web driver.py.")
    run_parser.add_argument("--allow-run-id-reuse", action="store_true", help="Pass --allow-run-id-reuse to doc-web driver.py.")
    run_parser.add_argument("--start-from", help="Resume from a specific stage id.")
    run_parser.add_argument("--end-at", help="Stop after a specific stage id.")
    run_parser.add_argument("--dry-run", action="store_true", help="Validate the recipe graph without executing it.")
    run_parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Additional args to pass to doc-web driver.py after '--'.")

    import_run_parser = subparsers.add_parser("import-run", help="Import output/html from a doc-web run id.")
    import_run_parser.add_argument("--run-id", required=True, help="Source doc-web run id.")
    import_run_parser.add_argument("--snapshot-id", help="Accepted snapshot id; defaults to the run id.")
    import_run_parser.add_argument("--recipe", help="Override the recipe path recorded in metadata.")
    import_run_parser.add_argument("--python", help="Override the Python executable used for doc-web commands.")
    import_run_parser.add_argument("--force", action="store_true", help="Replace existing snapshot targets.")

    import_bundle_parser = subparsers.add_parser("import-bundle", help="Import an existing bundle directory.")
    import_bundle_parser.add_argument("--bundle-path", required=True, help="Bundle root containing manifest.json.")
    import_bundle_parser.add_argument("--snapshot-id", required=True, help="Accepted snapshot id.")
    import_bundle_parser.add_argument("--python", help="Override the Python executable used for doc-web commands.")
    import_bundle_parser.add_argument("--force", action="store_true", help="Replace existing snapshot targets.")

    validate_parser = subparsers.add_parser("validate-bundle", help="Validate an existing bundle directory.")
    validate_parser.add_argument("--bundle-path", required=True, help="Bundle root containing manifest.json.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = build_runtime_paths(load_runtime_manifest())

    if args.command == "contract":
        _print_json(fetch_doc_web_contract(paths, python_executable=args.python))
        return 0

    if args.command == "run":
        extra_args = list(args.extra_args or [])
        if extra_args and extra_args[0] == "--":
            extra_args = extra_args[1:]
        bundle_root = run_doc_web(
            paths,
            run_id=args.run_id,
            recipe_path=_resolve_recipe_path(paths.source_root, args.recipe) if args.recipe else None,
            input_images_path=_resolve_repo_path(args.input_images) if args.input_images else None,
            input_pdf_path=_resolve_repo_path(args.input_pdf) if args.input_pdf else None,
            python_executable=args.python,
            force=args.force,
            allow_run_id_reuse=args.allow_run_id_reuse,
            start_from=args.start_from,
            end_at=args.end_at,
            dry_run=args.dry_run,
            extra_args=extra_args,
        )
        _print_json(
            {
                "schemaVersion": "alain_doc_web_run_v1",
                "runId": args.run_id,
                "bundleRoot": _rel_or_abs(bundle_root),
                "dryRun": args.dry_run,
            }
        )
        return 0

    if args.command == "import-run":
        snapshot = import_run_bundle(
            paths,
            run_id=args.run_id,
            snapshot_id=args.snapshot_id,
            recipe_path=_resolve_recipe_path(paths.source_root, args.recipe) if args.recipe else None,
            python_executable=args.python,
            force=args.force,
        )
        _print_json(import_result_payload(snapshot))
        return 0

    if args.command == "import-bundle":
        snapshot = import_bundle(
            paths,
            bundle_root=_resolve_repo_path(args.bundle_path),
            snapshot_id=args.snapshot_id,
            python_executable=args.python,
            force=args.force,
        )
        _print_json(import_result_payload(snapshot))
        return 0

    if args.command == "validate-bundle":
        summary = validate_bundle_contract(_resolve_repo_path(args.bundle_path))
        _print_json({"schemaVersion": "alain_doc_web_validate_bundle_v1", **asdict(summary)})
        return 0

    parser.error(f"Unhandled command: {args.command}")
    return 2


def import_result_payload(snapshot: ImportedBundle) -> dict[str, str]:
    return {
        "schemaVersion": "alain_doc_web_import_result_v1",
        "snapshotId": snapshot.snapshot_id,
        "runtimeMetadataPath": _rel_or_abs(snapshot.runtime_metadata_path),
        "runtimeBundleRoot": _rel_or_abs(snapshot.runtime_bundle_root),
        "acceptedBundleRoot": _rel_or_abs(snapshot.accepted_bundle_root),
        "activeBundlePath": _rel_or_abs(snapshot.active_bundle_path),
    }


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DocWebImportError as exc:
        raise SystemExit(f"error: {exc}") from exc
