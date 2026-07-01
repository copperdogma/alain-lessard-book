---
name: setup-methodology
description: Install or refresh the repo's methodology package — docs, checklist, eval surface, and AGENTS wiring
user-invocable: true
---

# /setup-methodology [greenfield|retrofit|adr-021-migration|refresh]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology/state.yaml`, and relevant decision records in `docs/decisions/`. If this work touches a known compromise in `docs/spec.md`, respect its limitation type and evolution path. If none apply, say so explicitly.

Use this skill as the canonical bootstrap or refresh entrypoint for the repo's
Ideal-first methodology package.

## What This Skill Owns

- `docs/ideal.md` / `docs/spec.md` / `docs/methodology/state.yaml` alignment
- `docs/methodology/graph.json` compilation
- `docs/methodology-ideal-spec-compromise.md` as the methodology reference
- `docs/setup-checklist.md` working-copy generation from the bundled template
- eval-surface bootstrap docs under `docs/evals/`
- `AGENTS.md` methodology wiring and graph/state operating rules
- cross-CLI skill sync via `scripts/sync-agent-skills.sh`

Use the bundled checklist template at
`.agents/skills/setup-methodology/templates/setup-checklist.md` and the mode
reference at `.agents/skills/setup-methodology/references/modes.md`.

## Modes

### `greenfield`

For a new repo or project skeleton. Install the methodology package from
scratch.

### `retrofit`

For an existing repo that needs the methodology package applied or re-applied.
Read the repo thoroughly, preserve provenance, and normalize the docs and skill
surface onto the canonical package.

### `adr-021-migration`

For repos that already use Ideal-first but still need the graph+state physical
artifact model around the authored canon.

### `refresh`

For repos that already have the package but need it re-synced: update AGENTS,
runbook, checklist structure, eval-surface docs, and public-surface guidance
without redoing the whole bootstrap conversation.

## Working Rules

1. **Create or refresh the checklist first.** Copy the bundled template to
   `docs/setup-checklist.md` if it is missing or if the existing file is stale.
   Work from that file and check items off as the run proceeds.
2. **Graph/state operating rule:** planning and triage start from
   `docs/methodology/state.yaml`, `docs/methodology/graph.json`, and the
   coverage matrix. Implementation starts from the active story, but must read
   the relevant category/state slice and linked `spec:N` sections first.
3. **Baseline evidence surfaces are part of setup.** Setup is incomplete until
   the repo has documented eval conventions, registry protocol, and benchmark /
   golden guidance.
4. **Keep recurring work separate.** This skill installs the package; ongoing
   work uses `/improve-eval`, `/align`, `/triage`, and the normal
   story/build/validate flow.
5. **Canonical public surface only.** AGENTS and runbooks should advertise
   `/setup-methodology` as the canonical setup / refresh entrypoint.

## Steps

1. **Determine mode from repo reality** — new repo, retrofit, ADR-021
   migration, or refresh. If the user supplied a mode, verify it matches what
   the repo actually looks like.

2. **Read the canonical references**:
   - `docs/runbooks/setup-methodology.md`
   - `docs/methodology-ideal-spec-compromise.md`
   - `docs/methodology/state.yaml` if it exists
   - relevant ADRs in `docs/decisions/`
   - `AGENTS.md`
   - `docs/evals/README.md`
   - existing setup / story / eval / runbook docs if present

3. **Create or refresh `docs/setup-checklist.md`** from the bundled template.
   Replace placeholders and check items off as work is completed. Never treat
   the checklist as optional.

4. **Install or refresh the methodology package**:
   - `docs/methodology-ideal-spec-compromise.md`
   - `docs/methodology/state.yaml`
   - `docs/methodology/graph.json` via compiler
   - `docs/runbooks/setup-methodology.md`
   - `docs/setup-checklist.md`
   - `docs/evals/README.md`
   - `docs/evals/attempt-template.md`
   - `AGENTS.md`

5. **Audit baseline evidence surfaces**:
   - ensure the benchmark / golden workspace guidance is current
   - ensure `docs/evals/registry.yaml` is still the source of truth
   - ensure `docs/RUNBOOK.md`, `docs/runbooks/golden-build.md`, and the AGENTS
     benchmark guidance still match reality
   - ensure the recurring eval-improvement path is documented honestly

6. **Normalize the planning surface**:
   - planning skills and templates point to the graph/state package
   - story drafting and story building treat substrate verification as required
   - workflow guidance distinguishes implementation handoff from validation and close-out
   - `docs/stories.md` is generated, not hand-maintained

7. **Normalize the public skill surface**:
   - `/setup-methodology` is discoverable in `AGENTS.md`
   - run `scripts/sync-agent-skills.sh`
   - validate with `scripts/sync-agent-skills.sh --check`

8. **Audit and summarize**:
   - reference audit for stale setup-language drift
   - eval-surface audit
   - methodology-graph alignment sweep across Ideal / Spec / State / Graph / Stories / Evals / ADRs / AGENTS

## Outputs

- Canonical setup skill surface installed
- Working `docs/setup-checklist.md`
- Methodology reference + runbook aligned to the same package
- `docs/methodology/graph.json` compiled and checked
- Eval-surface docs aligned to current repo reality
- Cross-CLI wrappers regenerated and checked

## Guardrails

- Do not advertise commands this repo does not actually have.
- Do not create a second competing setup model in AGENTS or runbooks.
- Do not treat benchmark / eval conventions as optional tribal knowledge.
- Do not copy wording blindly where this repo's runtime, eval, or pipeline
  surfaces differ.
