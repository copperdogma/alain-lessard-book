# Runbook: Setup Methodology

> Canonical prose front door for this repo's methodology package.
> Use this runbook together with `/setup-methodology`.

## Why This Exists

This repo is new, but it still needs an honest operating surface for AI and
human collaboration. The methodology package installs or refreshes:

- the ideal/spec/state canon
- a compiled methodology graph
- a generated stories index
- a working setup checklist
- eval-surface docs
- AGENTS wiring
- cross-CLI skill sync

## Core Hierarchy

1. **Ideal** - `docs/ideal.md`
2. **Spec** - `docs/spec.md`
3. **Methodology State** - `docs/methodology/state.yaml`
4. **Coverage Matrix** - `tests/fixtures/formats/_coverage-matrix.json`
5. **Compiled Graph** - `docs/methodology/graph.json`
6. **Stories** - `docs/stories.md` and `docs/stories/`
7. **Evals** - `docs/evals/registry.yaml`

Operating rule: planning starts from state, graph, and coverage. Implementation
starts from the active story plus the relevant spec context.

## Public Surface

### Bootstrap / Refresh

- `/setup-methodology` - canonical setup or refresh entrypoint

Modes:

- `greenfield`
- `retrofit`
- `adr-021-migration`
- `refresh`

### Recurring Work

- `/triage`
- `/align`
- the normal story / validate / close-out flow

## Greenfield Guidance

For this repo, greenfield setup means:

1. define the ideal for the scan/PDF/website project
2. define the first category-aligned spec and state surfaces
3. establish the source inventory for raw scans and companion materials
4. install the setup/eval/story methodology package
5. keep current repo reality honest while the site stack is still undecided

## Checklist Rule

Every `/setup-methodology` run should work from `docs/setup-checklist.md`.
