#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from doc_web_import import (
    build_runtime_paths,
    fetch_doc_web_contract,
    load_runtime_manifest,
    run_doc_web,
    validate_bundle_contract,
)
from process_supplemental_scans import DOCUMENTS, processed_dir


ROOT = Path(__file__).resolve().parents[1]
RECIPE_PATH = ROOT / "configs" / "doc-web" / "recipe-companion-document-images-html-mvp.yaml"
ACCEPTED_ROOT = ROOT / "input" / "doc-web-html" / "companion-documents"
MANIFEST_PATH = ACCEPTED_ROOT / "manifest.json"
SCHEMA_VERSION = "alain_lessard_companion_doc_web_bundles_v1"
RUN_ID_PREFIX = "alain-companion"
RUN_ID_SUFFIX = "doc-web-r1"


def rel(path: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def accepted_bundle_dir(slug: str) -> Path:
    return ACCEPTED_ROOT / slug


def run_all(*, force: bool) -> int:
    runtime_paths = build_runtime_paths(load_runtime_manifest())
    contract = fetch_doc_web_contract(runtime_paths)
    ACCEPTED_ROOT.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    for document in DOCUMENTS:
        source_pages = processed_dir(document)
        if not source_pages.exists():
            raise SystemExit(f"Missing processed pages for {document.slug}: {source_pages}")

        run_id = f"{RUN_ID_PREFIX}-{document.slug}-{RUN_ID_SUFFIX}"
        bundle_root = run_doc_web(
            runtime_paths,
            run_id=run_id,
            recipe_path=RECIPE_PATH,
            input_images_path=source_pages,
            force=force,
        )
        summary = validate_bundle_contract(bundle_root)

        destination = accepted_bundle_dir(document.slug)
        if destination.exists():
            if not force:
                raise SystemExit(f"Accepted companion bundle already exists: {destination}. Use --force to replace it.")
            shutil.rmtree(destination)
        shutil.copytree(bundle_root, destination)

        imported_at = datetime.now().astimezone().isoformat(timespec="seconds")
        metadata = {
            "schemaVersion": "alain_companion_doc_web_import_v1",
            "slug": document.slug,
            "title": document.title,
            "importedAt": imported_at,
            "source": {
                "docWebRoot": rel(runtime_paths.source_root),
                "runId": run_id,
                "bundleRoot": rel(bundle_root),
                "recipePath": rel(RECIPE_PATH),
                "inputImages": rel(source_pages),
                "contract": contract,
            },
            "bundle": {
                **asdict(summary),
                "acceptedBundleRoot": rel(destination),
                "manifestPath": rel(destination / "manifest.json"),
                "provenancePath": rel(destination / "provenance" / "blocks.jsonl"),
            },
        }
        write_json(destination / "_alain-companion-import-metadata.json", metadata)

        records.append(
            {
                "slug": document.slug,
                "title": document.title,
                "description": document.description,
                "run_id": run_id,
                "bundle_root": rel(destination),
                "manifest": rel(destination / "manifest.json"),
                "provenance": rel(destination / "provenance" / "blocks.jsonl"),
                "entry_count": summary.entry_count,
                "provenance_row_count": summary.provenance_row_count,
                "image_count": summary.image_count,
                "reading_order": summary.reading_order,
            }
        )
        print(f"{document.slug}: imported doc-web bundle with {summary.entry_count} entries")

    write_json(
        MANIFEST_PATH,
        {
            "schema_version": SCHEMA_VERSION,
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "recipe": rel(RECIPE_PATH),
            "document_count": len(records),
            "documents": records,
        },
    )
    print(f"companion doc-web manifest: {rel(MANIFEST_PATH)}")
    return 0


def validate() -> int:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"Missing companion doc-web manifest: {MANIFEST_PATH}")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version is {manifest.get('schema_version')!r}, expected {SCHEMA_VERSION!r}")
    records = manifest.get("documents")
    if not isinstance(records, list):
        errors.append("documents must be a list")
        records = []
    if len(records) != len(DOCUMENTS):
        errors.append(f"document_count is {len(records)}, expected {len(DOCUMENTS)}")

    expected_slugs = {document.slug for document in DOCUMENTS}
    seen_slugs: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            errors.append("document manifest row must be an object")
            continue
        slug = str(record.get("slug") or "")
        seen_slugs.add(slug)
        if slug not in expected_slugs:
            errors.append(f"unexpected companion doc-web slug: {slug}")
        bundle_root = ROOT / str(record.get("bundle_root") or "")
        try:
            summary = validate_bundle_contract(bundle_root)
        except Exception as exc:  # noqa: BLE001 - validation should show the exact bundle problem.
            errors.append(f"{slug} bundle failed validation: {exc}")
            continue
        if summary.entry_count < 1:
            errors.append(f"{slug} bundle has no HTML entries")
        if not summary.reading_order:
            errors.append(f"{slug} bundle has empty reading order")

    missing = expected_slugs - seen_slugs
    for slug in sorted(missing):
        errors.append(f"missing companion doc-web slug: {slug}")

    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"companion doc-web bundles: {len(records)}")
    for record in records:
        print(f"{record['slug']}: {record['entry_count']} entries")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run and accept doc-web bundles for Alain companion documents.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--force", action="store_true")
    subparsers.add_parser("validate")
    args = parser.parse_args()

    if args.command == "run":
        return run_all(force=bool(args.force))
    if args.command == "validate":
        return validate()
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
