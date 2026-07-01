#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IDEAL_PATH = ROOT / "docs/ideal.md"
SPEC_PATH = ROOT / "docs/spec.md"
STATE_PATH = ROOT / "docs/methodology/state.yaml"
GRAPH_PATH = ROOT / "docs/methodology/graph.json"
STORIES_DIR = ROOT / "docs/stories"
STORIES_INDEX_PATH = ROOT / "docs/stories.md"
EVALS_PATH = ROOT / "docs/evals/registry.yaml"
COVERAGE_PATH = ROOT / "tests/fixtures/formats/_coverage-matrix.json"

SPEC_CATEGORY_RE = re.compile(r"^##\s+(spec:\d+(?:\.\d+)*)\s+(.+)$")
COMPROMISE_RE = re.compile(r"\b(?:C|B)\d+\b")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_json_document(path: Path) -> object:
    return json.loads(read_text(path))


def parse_title(path: Path) -> str:
    for line in read_text(path).splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    raise ValueError(f"Missing markdown title in {path.relative_to(ROOT)}")


def summarize_body(lines: list[str]) -> str:
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        if line.startswith("#"):
            continue
        stripped = line.strip()
        if not stripped:
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
            continue
        current.append(stripped)
    if current:
        paragraphs.append(" ".join(current).strip())
    return paragraphs[0] if paragraphs else ""


def parse_spec_categories() -> list[dict[str, object]]:
    lines = read_text(SPEC_PATH).splitlines()
    categories: list[dict[str, object]] = []
    current_id: str | None = None
    current_title = ""
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_id, current_title, current_lines
        if not current_id:
            return
        categories.append(
            {
                "id": current_id,
                "title": current_title,
                "summary": summarize_body(current_lines),
                "compromise_refs": sorted(set(COMPROMISE_RE.findall("\n".join(current_lines)))),
            }
        )
        current_id = None
        current_title = ""
        current_lines = []

    for line in lines:
        match = SPEC_CATEGORY_RE.match(line)
        if match and "." not in match.group(1):
            flush()
            current_id = match.group(1)
            current_title = match.group(2).strip()
            current_lines = []
            continue
        if current_id:
            current_lines.append(line)

    flush()
    return categories


def parse_story_file(path: Path) -> dict[str, str]:
    text = read_text(path)
    title = ""
    status = "Draft"

    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            frontmatter = text[4:end].splitlines()
            for line in frontmatter:
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"')
                if line.startswith("status:"):
                    status = line.split(":", 1)[1].strip().strip('"')

    if not title:
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break

    if not title:
        title = path.stem

    return {
        "path": path.relative_to(ROOT).as_posix(),
        "title": title,
        "status": status,
    }


def parse_stories() -> list[dict[str, str]]:
    if not STORIES_DIR.exists():
        return []
    stories = []
    for path in sorted(STORIES_DIR.glob("*.md")):
        if path.name == ".gitkeep":
            continue
        stories.append(parse_story_file(path))
    return stories


def build_graph_object() -> dict[str, object]:
    state = read_json_document(STATE_PATH)
    evals = read_json_document(EVALS_PATH)
    coverage = read_json_document(COVERAGE_PATH)
    categories = parse_spec_categories()
    category_state = state.get("categories", {})

    for category in categories:
        state_slice = category_state.get(category["id"], {})
        category["substrate"] = state_slice.get("substrate", "unknown")
        category["last_reviewed"] = state_slice.get("last_reviewed")

    stories = parse_stories()
    status_counts: dict[str, int] = {}
    for story in stories:
        status_counts[story["status"]] = status_counts.get(story["status"], 0) + 1

    return {
        "version": 1,
        "documents": {
            "ideal": "docs/ideal.md",
            "spec": "docs/spec.md",
            "state": "docs/methodology/state.yaml",
            "graph": "docs/methodology/graph.json",
            "stories_index": "docs/stories.md",
            "coverage_matrix": "tests/fixtures/formats/_coverage-matrix.json",
            "evals_registry": "docs/evals/registry.yaml",
        },
        "ideal": {
            "path": "docs/ideal.md",
            "title": parse_title(IDEAL_PATH),
        },
        "spec": {
            "path": "docs/spec.md",
            "title": parse_title(SPEC_PATH),
            "categories": categories,
        },
        "state": state,
        "coverage_matrix": coverage,
        "evals": evals.get("evals", []),
        "stories": {
            "items": stories,
            "counts_by_status": status_counts,
        },
    }


def render_graph(graph: dict[str, object]) -> str:
    return json.dumps(graph, indent=2, ensure_ascii=True) + "\n"


def render_stories_index(graph: dict[str, object]) -> str:
    state = graph["state"]
    stories = graph["stories"]["items"]
    lines = [
        "# Stories",
        "",
        "> Generated by `python scripts/methodology_graph.py build`. Do not edit manually.",
        "",
    ]

    sections = state.get("stories_index", {}).get("sections", [])
    for section in sections:
        lines.append(f"## {section['title']}")
        lines.append("")
        markdown = section.get("markdown", "").rstrip()
        if markdown:
            lines.extend(markdown.splitlines())
            lines.append("")

    lines.append("## Current Stories")
    lines.append("")
    if not stories:
        lines.append(
            "_No story files exist yet. The next story should package the first end-to-end slice of import, canonical data shaping, and site presentation._"
        )
        lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    for story in stories:
        lines.append(f"- **{story['status']}** — `{story['path']}` — {story['title']}")
    lines.append("")
    return "\n".join(lines)


def build() -> int:
    graph = build_graph_object()
    write_text(GRAPH_PATH, render_graph(graph))
    write_text(STORIES_INDEX_PATH, render_stories_index(graph))
    print("methodology-compile: OK")
    return 0


def check() -> int:
    graph = build_graph_object()
    expected_graph = render_graph(graph)
    expected_stories = render_stories_index(graph)

    actual_graph = read_text(GRAPH_PATH) if GRAPH_PATH.exists() else ""
    actual_stories = read_text(STORIES_INDEX_PATH) if STORIES_INDEX_PATH.exists() else ""

    errors: list[str] = []
    if actual_graph != expected_graph:
        errors.append("docs/methodology/graph.json is stale; run `make methodology-compile`")
    if actual_stories != expected_stories:
        errors.append("docs/stories.md is stale; run `make methodology-compile`")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("methodology-check: OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile or check methodology artifacts.")
    parser.add_argument("command", choices=("build", "check"))
    args = parser.parse_args()
    if args.command == "build":
        return build()
    return check()


if __name__ == "__main__":
    raise SystemExit(main())

