---
name: triage
description: Orchestrate the triage leaf skills and synthesize the highest-value next action
user-invocable: true
---

# /triage [stories|inbox|evals|architecture] [sub-arg]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md` and relevant decision records in `docs/decisions/`. If this work touches a known compromise in `docs/spec.md`, respect its limitation type and evolution path. If none apply, say so explicitly.

`/triage` is the meta-skill. It does not own the backlog, inbox, or eval logic
itself. It routes to the leaf skills and, in full-sweep mode, synthesizes one
recommended next action.

When this repo already has a real surfaced website, manual editorial
refinement, accessibility cleanup, navigation fixes, and other site-shaping
grunt work are first-class progress. Do not default to inventing a deeper
deterministic layer unless it clearly removes repeated grunt work, prevents
content loss, or unblocks shipping the real site.

## Routing

| Invocation | Behavior |
|---|---|
| `/triage` | Full-sweep orchestrator mode |
| `/triage stories` | Delegate to `/triage-stories` |
| `/triage stories 145` | Delegate to `/triage-stories 145` |
| `/triage inbox` | Delegate to `/triage-inbox` (processing mode) |
| `/triage inbox scan` | Delegate to `/triage-inbox scan` (read-only mode) |
| `/triage evals` | Delegate to `/triage-evals` |
| `/triage evals image-crop-extraction` | Delegate to `/triage-evals image-crop-extraction` |
| `/triage architecture` | Delegate to `/triage-architecture` |
| `/triage architecture methodology_tooling` | Delegate to `/triage-architecture methodology_tooling` |

When a scope is provided, hand off completely to the leaf skill. Do not
maintain duplicate logic here.

## Leaf Skills

- `/triage-stories` — backlog prioritization, readiness, dependency bottlenecks
- `/triage-inbox` — inbox scan or processing
- `/triage-evals` — eval health, rerun candidates, compromise deletion signals
- `/triage-architecture` — bounded structural simplification / cleanup lane

## Full-Sweep Mode

When invoked with no scope:

1. **Read the shared frame**
   - `docs/ideal.md`
   - `docs/spec.md`
   - `docs/methodology/state.yaml`
   - `docs/methodology/graph.json`
   - `tests/fixtures/formats/_coverage-matrix.json`
   - relevant ADRs under `docs/decisions/`
   - recent `git log --oneline -20`

2. **Run leaf sweeps in parallel**
   - `/triage-stories`
   - `/triage-inbox scan`
   - `/triage-evals`
   - `/triage-architecture`

3. **Collect leaf reports**
   Each report should return:
   - one top recommendation
   - 1-3 supporting reasons
   - health flags / bottlenecks
   - whether the recommendation is read-only or action-taking

4. **Synthesize one cross-domain recommendation**
   Rank the problem first, then choose the vehicle that best advances it
   (continue an active story, expand/reopen a story, create a story, run a UI
   scout, run an eval, do architecture work, or no-op).

   Choose the next action with the strongest combined signal across:
   - movement toward the Ideal
   - real problem pressure
   - blocking power / dependency leverage
   - compromise-elimination leverage
   - phase coherence (climb/hold/converge alignment across categories)
   - substrate readiness
   - continuity from active or recently advanced unresolved work lines
   - urgency / staleness
   - operator cost
   - surfaced-product quality / ship-readiness pressure on the current website
   - UI product-truth freshness when `state.ui_scout` exists
   - existing story shells only as packaging / tie-break context, not as value by themselves

   If `docs/methodology/state.yaml` includes `ui_scout` and the lane is
   `never`, stale, `issues_found`, or `recheck_due`, inspect `docs/ui-scout.md`
   and the latest relevant report under `docs/ui-scout/` before outranking that
   line with unrelated abstraction or architecture work.

   If the strongest problem line is explicitly `Blocked`, verify whether its
   unblock condition is actually met in the current pass. If not, surface that
   line as a health flag and recommend a different actionable move or an honest
   `no-op`; do not turn blocked continuity into a reopen recommendation.

   If the repo already has a real reading surface and the strongest live gap is
   that the site still does not feel ready to ship, prefer UI scouting,
   follow-up manual refinement, or a focused site-quality story over
   schema-first work that does not directly improve the actual website.

   The recommended action must be phrased so it can be executed directly on the
   next turn. A bare `yes` from the user should be enough to authorize that one
   action without needing a follow-up clarification.

5. **Return the compact report**

```markdown
## Triage

### Recommended Action
- {one next action}

### Why
- {2-3 strongest reasons}

### Runner-Ups
- {alternate action}
- {alternate action}

### Domain Notes
- Stories: {summary}
- Inbox: {summary}
- Evals: {summary}
- UI Scout: {freshness / latest report summary or "not configured"}

### Health Flags
- {blocked story / stale inbox / stale eval / pending ADR}

### Decision
- Reply `yes` to proceed with: {repeat the one recommended action verbatim}
```

## Guardrails

- Scoped invocations delegate; do not duplicate leaf logic here.
- Full-sweep mode is read-only.
- Use parallel leaf sweeps when feasible.
- Return one recommendation, not a vague list.
- End with a clear acceptance prompt that the user can approve with `yes`.
- Respect leaf-skill boundaries: `/triage inbox` may modify files; unscoped
  `/triage` may not.
- Do not overweight `Draft` / `Pending` story presence. Story shells are
  packaging, not priority signals.
- Preserve continuity for active unresolved work lines when leverage is
  otherwise comparable.
- Do not assume deeper deterministic abstraction is automatically higher value
  than manual refinement once a real surfaced website exists.
- Do not recommend reopening a blocked line unless the current pass can point
  to fresh evidence that satisfies the story's unblock condition.
