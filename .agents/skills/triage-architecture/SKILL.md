---
name: triage-architecture
description: Audit a bounded architecture domain for cleanup pressure and record the next structural move
user-invocable: true
---

# /triage-architecture [domain-id]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology/state.yaml`, and relevant decision records in `docs/decisions/`. If this work touches a known compromise in `docs/spec.md`, respect its limitation type and evolution path. If none apply, say so explicitly.

Canonical architecture-audit leaf skill. Direct invocation is allowed, and
`/triage architecture` routes here.

## What This Skill Produces

A short advisory report:

- domain health
- structural cleanup signal
- one recommended next action

This skill is read-only unless the user explicitly asks to update the audit
state.

## Read First

1. `docs/ideal.md`
2. `docs/spec.md`
3. `docs/methodology/state.yaml`
4. `docs/methodology/graph.json`
5. `docs/runbooks/triage-architecture.md`
6. relevant ADRs and recent story files for the chosen domain

## Steps

1. Resolve the domain
   - if no domain is supplied, inspect `architecture_audits` in
     `docs/methodology/state.yaml` and pick the most due domain
   - if a domain is supplied, verify it exists in state

2. Read the domain state
   - last audit date
   - recent story refs
   - open findings
   - manual priority
   - notes

3. Inspect recent evidence
   - story files in `recent_story_refs`
   - recent validation or work-log drift signals
   - relevant ADR/spec slices

4. Judge whether an audit is due
   - high manual priority
   - open findings
   - overdue cadence
   - obvious repeated drift

5. Decide one output
   - no action
   - fold into existing story
   - create follow-up story
   - escalate to ADR/discussion

## Report Format

```markdown
## Triage Architecture

### Domain
- `{domain-id}` — {short summary}

### Due Signals
- {signal or "None"}

### Findings
- {bounded structural issue or "No actionable drift found"}

### Recommended Action
- {one next architecture action}
```

## Guardrails

- Read-only by default
- Keep audits bounded to one domain unless the evidence clearly spans two
- Prefer delete / merge / re-home over new abstraction
- If no action is the honest answer, say so explicitly
