---
title: "TITLE"
status: "Draft"
priority: "PRIORITY"
ideal_refs:
  - "{ideal.md requirements}"
spec_refs:
  - "{spec.md sections or compromises}"
adr_refs: []
depends_on: []
category_refs:
  - "{spec:N category}"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "{bounded architecture domain}"
roadmap_tags: []
legacy_system: ""
---

# Story NNN — TITLE

**Priority**: PRIORITY
**Status**: Draft
**Decision Refs**: {ADRs, runbooks, scout docs, notes, or "None found after search"}
**Depends On**: {story IDs}

> If this story is `Blocked`, replace `N/A` in `Blocker Summary`, `Blocker
> Evidence`, and `Unblock Condition` with repo-backed truth, and make the
> visible `## Plan` describe the unblock path or blocker reassessment work
> instead of stale "proceed now" steps. Leave those sections as `N/A`
> otherwise.

## Goal

{One paragraph describing what this story accomplishes and why it matters.}

## Acceptance Criteria

- [ ] {Testable criterion 1}
- [ ] {Testable criterion 2}
- [ ] {Testable criterion 3}

## Out of Scope

- {Explicitly list what this story does NOT do}

## Approach Evaluation

{List candidate approaches — do NOT pre-decide. build-story's eval-first gate selects the winner with evidence.}

- **Simplification baseline**: {Can a single LLM call already do this? Evidence?}
- **AI-only**: {Could an LLM call handle this? Cost per run?}
- **Hybrid**: {Cheap detection + AI judgment? Where's the split?}
- **Pure code**: {Only if strictly orchestration/plumbing with no reasoning.}
- **Repo constraints / prior decisions**: {What existing ADRs, runbooks, scout findings, notes, or patterns constrain the choice?}
- **Existing patterns to reuse**: {Which helpers, modules, or prior stories should this extend instead of duplicating?}
- **Eval**: {What test distinguishes the approaches? Does it exist yet?}

## Tasks

- [ ] {Implementation task 1}
- [ ] {Implementation task 2}
- [ ] {Implementation task 3}
- [ ] If this story changes documented format coverage or graduation reality: update `tests/fixtures/formats/_coverage-matrix.json` and any relevant methodology state honestly
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [ ] Run required checks for touched scope:
  - [ ] Default Python checks: `make test`
  - [ ] Default Python lint: `make lint`
  - [ ] If pipeline behavior changed: clear stale `*.pyc`, run through `driver.py` or `make smoke`, verify artifacts in `output/runs/`, and manually inspect sample JSON/JSONL data
  - [ ] If agent tooling changed: `make skills-check`
- [ ] If evals or goldens changed: run `/improve-eval` and update `docs/evals/registry.yaml`
- [ ] Search all docs and update any related to what we touched
- [ ] Verify Central Tenets:
  - [ ] T0 — Traceability: every output traces to source page, OCR engine, confidence, processing step
  - [ ] T1 — AI-First: didn't write code for a problem AI solves better
  - [ ] T2 — Eval Before Build: measured SOTA before building complex logic
  - [ ] T3 — Fidelity: source content preserved faithfully, no silent losses
  - [ ] T4 — Modular: new recipe not new code; no hardcoded book assumptions
  - [ ] T5 — Inspect Artifacts: visually verified outputs, not just checked logs

## Workflow Gates

- [ ] Build complete: implementation finished, required checks run, and summary shared
- [ ] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning module / area**: {Which stage, module, script, or doc area should own this?}
- **Methodology reality**: {Which graph/state category owns this? What are the current substrate and phase? Which coverage-matrix row(s) are relevant?}
- **Substrate evidence**: {Which files, schemas, modules, artifacts, or tests prove the dependency exists? If it is missing or partial, say so explicitly.}
- **Data contracts / schemas**: {What schemas or artifact definitions change? If new fields cross artifact boundaries, they must be added to `schemas.py` first.}
- **File sizes**: {Current line count of each file to be modified. Run `make check-size` when relevant. Flag any file >500 lines.}
- **Decision context**: {Which ADRs, runbooks, scout docs, notes, or other decision docs were reviewed? If none apply, say why.}

## Files to Modify

- {path/to/file} — {what changes} ({current line count})

## Redundancy / Removal Targets

- {old path, helper, abstraction, or docs likely to become redundant if this lands}

## Notes

{Design notes, open questions, references}

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, repo-fit evidence, approval blockers. If the story is currently `Blocked`, replace stale "proceed now" language with blocker truth and the unblock path instead.}

## Work Log

{Entries added during implementation — YYYYMMDD-HHMM — action: result, evidence, next step}
