---
name: align
description: Check alignment of the methodology graph after a change — Ideal, ADRs, Spec, State, Graph, Stories, Coverage, Evals — and propose corrections
user-invocable: true
---

# /align [what-changed | ADR-NNN]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md` and relevant decision records in `docs/decisions/`. If this work touches a known compromise in `docs/spec.md`, respect its limitation type and evolution path. If none apply, say so explicitly.

Check the methodology graph for misalignment after a change. This is read-only
and advisory.

## When To Use

Use this after changes that may ripple across core project guidance:

- an ADR is accepted or materially redirected
- `docs/ideal.md`, `docs/spec.md`, or `docs/requirements.md` changes
- `docs/methodology/state.yaml` or `docs/methodology/graph.json` changes
- an eval newly passes and may delete a compromise
- a story reveals a new repo-level lesson
- a new model, tool, or external constraint may invalidate current guidance

## Read First

1. `docs/ideal.md`
2. `docs/spec.md`
3. `docs/methodology/state.yaml`
4. `docs/methodology/graph.json`
5. `tests/fixtures/formats/_coverage-matrix.json`
6. `docs/requirements.md`
7. generated `docs/stories.md` plus directly affected story files
8. relevant ADRs under `docs/decisions/`
9. `docs/evals/registry.yaml`
10. `AGENTS.md` if workflow or guardrails may be affected

## What To Check

### Ideal
- did this reveal a new product ideal that is not explicit yet?
- did this reveal an execution ideal gap (build process limitation)?
- did it sharpen an existing central tenet or requirement?

### Spec / Requirements
- does this add, remove, or change a compromise?
- does it change a detection mechanism or evolution path?
- should any existing compromise now be re-evaluated?
- are `spec:N.N` constraint blocks consistent with the change?
- do build-process compromises (spec:8, spec:9) need updating?

### State / Graph / Coverage
- does this change category scope, dependency order, or compromise progress?
- does a category's substrate status need to change (`exists`/`partial`/`missing`)?
- does a category's phase need to change (`climb`/`hold`/`converge`)?
- does coverage truth, graduation tracking, or known-gap prioritization need to move?

### Stories
- are any Draft, Pending, or In Progress stories affected?
- did any Done stories become stale or mis-scoped?
- should a new story likely exist? Flag it; do not create it.

### Evals
- should any evals be rerun, added, or retired?
- does a compromise now lack a meaningful deletion signal?

### ADRs / Runbooks / Guardrails
- does this contradict an ADR?
- should an existing ADR or runbook be updated?
- does `AGENTS.md` need stronger or different guidance?

## Report Format

```markdown
## Align — {what changed}

### Ideal
- {impact or "Aligned"}

### Spec / Requirements
- {impact or "Aligned"}

### State / Graph / Coverage
- {impact or "Aligned"}

### Stories
- {story IDs and why}

### Evals
- {rerun / add / remove guidance}

### ADRs / Runbooks / AGENTS
- {affected guidance or "Aligned"}

### Recommended Actions
- [ ] {specific action in priority order}
```

## Guardrails

- Read the actual docs; do not reason from memory.
- Keep the report short and actionable.
- If there is no meaningful downstream impact, say so explicitly.
- Do not silently create stories, ADRs, or evals while using this skill.
