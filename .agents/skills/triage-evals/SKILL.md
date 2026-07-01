---
name: triage-evals
description: Evaluate eval health, deletion gates, and rerun candidates
user-invocable: true
---

# /triage-evals [eval-id]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md` and relevant decision records in `docs/decisions/`. If this work touches a known compromise in `docs/spec.md`, respect its limitation type and evolution path. If none apply, say so explicitly.

Canonical eval-health triage leaf skill. Direct invocation is allowed, and
`/triage evals` routes here.

## Scope

- no argument: scan the full eval surface
- eval ID argument: assess one eval's health, staleness, and next action

This skill is read-only and advisory. It never runs evals automatically.

## Read First

1. `docs/evals/registry.yaml`
2. `docs/spec.md`
3. `docs/methodology/state.yaml`
4. `docs/methodology/graph.json`
5. relevant ADRs under `docs/decisions/`
6. recent `git log --oneline -20`

If a recommendation depends on model availability, pricing, or a newly released
provider capability, verify it with current official docs or a fresh web search
before claiming the trigger is met.

## What To Evaluate

### 1. Eval class

Derive the triage class from registry context:

- **quality-runtime** — quality evals where latency or cost is part of the decision
- **quality-capability** — output-fidelity or behavior-quality gates
- **compromise-detection** — deletion gates for spec compromises

### 2. Rerun triggers

Check whether recorded `retry_when` conditions are now actionable:

- `new-worker-model`
- `new-subject-model`
- `cheaper-subject-model`
- `faster-subject-model`
- `new-approach`
- `golden-fix`
- `architecture-change`
- `dependency-available`

Use recent git history, current stories, current docs, and verified model
availability to judge whether the trigger is actually met. If the same trigger
was already exercised in the latest attempt and failed without changing the
decision surface, do not recommend the same rerun again until there is another
material trigger.

### 3. Phase-aware assessment

Read the methodology-state phase for each eval's compromise category:
- `climb` → focus on quality (better prompts, better golden fixtures)
- `hold` → focus on efficiency (cheaper, faster, simpler)
- `converge` → recommend deleting the compromise

### 4. Deletion-gate health

For compromise-detection evals:

- is the last score close to the threshold?
- did it already pass while the compromise still lingers in docs?
- is a compromise missing an eval entirely?
- does `docs/methodology/state.yaml` still match the registry?
- does the compiled graph's category/compromise linkage match the eval's target?

### 5. General eval hygiene

Look for:

- active systems whose quality evals are stale after meaningful prompt/pipeline changes
- stale compromise-detection scores
- duplicate or confusing eval coverage
- missing evals for active compromises

## Report Format

```markdown
## Triage Evals

### Rerun Candidates
- {eval-id} — {why now}

### Deletion Candidates
- {compromise / eval-id} — {why the compromise may now be deletable}

### Missing / Weak Coverage
- {gap}

### Recommended Action
- {one next eval action}

### Health Flags
- {stale score / missing eval / docs-registry drift}
```

## Follow-Through Guidance

Recommend the smallest correct next step:

- `/improve-eval <id>` when an eval should be investigated or rerun
- current model-availability research when the trigger depends on new releases
- `/create-story` when the issue is an implementation gap, not just eval staleness
- update `docs/methodology/state.yaml`, `tests/fixtures/formats/_coverage-matrix.json`, or `docs/spec.md` when the truth surfaces drift from a passing gate

Do not auto-run expensive evals. Present cost/time implications and let the
user decide.

## Guardrails

- Read-only and advisory
- Be explicit when a recommendation depends on verified current model availability
- Do not confuse runtime benchmarks with capability gates or deletion gates
- Do not recommend the same retry trigger repeatedly when the latest recorded
  attempt already exercised it and no new model, approach, golden, or
  architecture change has appeared since
- If no eval action is justified, say so clearly
- Keep the report compact enough for `/triage` to synthesize with other leaf reports
