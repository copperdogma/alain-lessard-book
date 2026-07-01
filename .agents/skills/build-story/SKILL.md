---
name: build-story
description: Execute a story from planning through implementation with work-log discipline
user-invocable: true
---

# /build-story [story-number]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, and relevant decision records in `docs/decisions/`. If this work touches a known compromise in `docs/spec.md`, respect its limitation type and evolution path. If none apply, say so explicitly.

Execute a development story through implementation handoff.

## Phase 1 — Explore (story-file edits allowed, code changes forbidden)

1. **Resolve story** — Read `docs/stories/story-{NNN}-*.md` (or resolve from `docs/methodology/graph.json`). Verify status is Draft, Pending, In Progress, or Blocked.
   - If status is **Draft**, do not stop yet. Continue through the required-section and substrate checks first.
   - If the Draft story is still skeletal or unverified after those checks, STOP and recommend keeping it `Draft`.
   - If the Draft story is already detailed enough and substrate-verified, record that it should be promoted and continue.
   - If status is **Blocked**, read `Blocker Summary`, `Blocker Evidence`,
     `Unblock Condition`, the latest work log, and `## Plan` first. STOP
     unless the user explicitly asked to reassess the blocker.
   - When reassessing a blocked story, continue only if there is fresh evidence
     that the unblock condition is now met. If it is still unmet, rewrite any
     stale plan text that still reads as "proceed" or "build now" so the story
     matches blocker truth, then stop and report the line as a health flag.

2. **Verify required sections** — Ensure the story has:
   - Goal
   - Acceptance Criteria
   - Tasks (checkbox items)
   - Workflow Gates
   - Work Log
   If tasks are missing, add actionable items without discarding existing intent.

3. **Read context** — Read `docs/ideal.md` first, then:
   - all `Spec Refs`
   - the relevant categories in `docs/methodology/graph.json` and `docs/methodology/state.yaml`
   - any dependency stories
   - referenced ADRs / decision docs
   If the story touches inputs, formats, or artifacts, also read the relevant
   rows in `tests/fixtures/formats/_coverage-matrix.json`. If the story
   does not cite an ADR and the work affects architecture, workflow, schemas,
   or cross-cutting project behavior, search `docs/decisions/` before assuming
   none exist.

4. **Ideal Alignment Gate** — Before exploring code:
   - Does this story close an Ideal gap? → proceed
   - Does it move AWAY from the Ideal? → STOP, tell user to re-evaluate
   - Does it optimize a compromise without closing a gap? → flag as potentially low-value
   - If introducing a new AI compromise: note whether a detection eval exists or should be created

5. **Explore the codebase actively** — Don't just read what's listed. Trace the code:
   - Follow call graphs from every entry point the story touches
   - Find every file that will change and every file that could break
   - Identify existing patterns and conventions to match
   - Identify existing helpers, modules, or docs this change could reuse or make redundant
  - Verify that any claimed upstream substrate actually exists in code, tests,
    schemas, artifacts, or wiring, not just in stories or stale planning prose
   - Note schema, config, or migration concerns

6. **Substrate reality check** — If the story depends on upstream architecture,
   schemas, or runtime seams:
   - If the substrate exists and is sufficient, continue
   - If it exists only partially, decide whether the missing slice is a small
     tightly coupled delta or a real prerequisite
   - If the substrate is missing such that the story cannot honestly satisfy
     its acceptance criteria, STOP treating the story as build-ready. Record
     the evidence, update the story with the blocker or new dependency, mark it
     `Blocked` when the blocker is real and named, and bring that
     recommendation back to the user before implementation planning
   - When a story becomes `Blocked`, clear or rewrite any stale `## Plan` text
     that still implies immediate implementation. The visible next move should
     be the unblock condition, not the invalidated build plan.

7. **Identify scope deltas** — If exploration reveals important work that is missing from the story but is necessary to actually solve the story's goal:
   - **Small, coherent delta** → expand the story automatically. Update the story's tasks, acceptance criteria, and work log so the real scope is visible.
   - **Large delta** → do not silently absorb or silently split it out. Add it to the plan as a recommended scope expansion for user approval.
   - Prefer expanding the current story when the new work is tightly coupled, in the same subsystem, and reasonably achievable in the same implementation pass.
   - Prefer a follow-up story only when the new work is materially distinct, changes the story's goal, adds major blast radius, or would make validation unclear.
   - Do not optimize for human sprint sizing. Optimize for a coherent slice that an AI can implement and validate end-to-end.

8. **Record exploration findings** — Write a brief exploration entry in the work log:
   - Files that will change
   - Files at risk
   - ADRs / decision docs consulted
   - Relevant graph/state category and current substrate/phase
   - Relevant coverage-matrix rows when applicable
   - Critical substrate verified versus missing, with file evidence
   - Patterns to follow
   - Potential redundant code or docs to remove
   - Surprises found

## Phase 2 — Plan (produces a written artifact)

9. **Eval-first approach gate** — Before planning implementation:
   - **What eval?** Identify or create a test that measures success. Even a minimal fixture + assertion counts.
   - **What's the baseline?** Run the eval against current code. Document the number.
   - **Candidate approaches?** For tasks involving reasoning/language/understanding: enumerate AI-only, hybrid, and pure code. If the story pre-decided an approach without evidence, challenge it.
   - **Test the simplest first.** Often a single LLM call. If it works, don't build code.
   - For pure orchestration/plumbing: code is obviously simpler — no comparison needed.

10. **Write the implementation plan** — Add a `## Plan` section to the story with:
   - For each task: which files change, what changes, in what order
   - Impact analysis: what tests are affected, what could break
   - Relevant graph/state context and any coverage-matrix movement expected
   - Structural health notes (file sizes, schema-boundary risks, redundancy plan)
   - Human-approval blockers (new dependencies, schema changes)
   - Any recommended scope adjustments discovered during exploration
   - If giving effort guidance, use relative effort only (`XS`, `S`, `M`, `L`, `XL` or equivalent), not hours/days
   - What "done" looks like for each task

11. **Human gate** — Present the plan to the user. Surface ambiguities and risks.
    - Small scope expansions already folded into the story should be called out explicitly.
    - Large scope expansions should be presented as a recommendation with rationale and relative effort.
    - **Do not write implementation code until approved.**

## Phase 3 — Implement

12. **Implement** — Work through tasks in order:
    - If the story status is `Draft` and the exploration proved it honestly buildable, first promote it to `Pending` and regenerate the graph/index so the status matches reality
    - If the story status is `Pending`, set it to `In Progress` in the story file and regenerate the graph/index before implementation starts
    - Mark task in progress in story file
    - Do the work
    - Run relevant checks after meaningful changes
    - Mark task complete with brief evidence
    - If implementation or deeper exploration proves a real blocker instead, record it, set the story to `Blocked`, regenerate the graph/index, and stop

13. **Verification** — Run the project's validation:
    - `make test`
    - `make lint`
    - If agent tooling changed: `make skills-check`
    - If pipeline behavior changed: clear stale `*.pyc`, run the narrowest real `driver.py` or `docs/RUNBOOK.md` path that proves the change, and inspect artifacts
    - If evals or goldens changed: run `/improve-eval` and update `docs/evals/registry.yaml`
    - Review each acceptance criterion — is it met?

14. **Update docs** — Search all docs and update anything related to what was touched.
    - If the story changed documented format coverage or graduation readiness,
      update `tests/fixtures/formats/_coverage-matrix.json` and any relevant
      methodology state in the same slice and keep the truth surfaces honest
      about current reality

15. **Verify Central Tenets** — Check each tenet in the story:
    - T0 — Traceability: every output traces to source page, OCR engine, confidence, processing step?
    - T1 — AI-First: didn't write code for a problem AI solves better?
    - T2 — Eval Before Build: measured SOTA before building complex logic?
    - T3 — Fidelity: source content preserved faithfully?
    - T4 — Modular: new recipe not new code; no hardcoded book assumptions?
    - T5 — Inspect Artifacts: visually verified outputs?

16. **Update work log** — Add dated entry: what was done, decisions, evidence, blockers.

17. **Implementation handoff** — Do not close the story here:
    - Check the `Build complete` workflow gate
    - Leave `Validation complete or explicitly skipped by user` unchecked
    - Leave `Story marked done via /mark-story-done` unchecked
    - Leave the story status as `In Progress`
    - Give the user a concise implementation summary, highlight residual risks,
      recommend `/validate` as the next step, and include a short `Where to verify`
      note whenever there is a concrete path for the user to inspect the result
    - Do not describe anything as fixed, passing, or done unless that claim is
      backed by fresh checks or artifact inspection from the current pass. If
      something was not re-run, label it as not freshly verified

## Work Log Format

```
YYYYMMDD-HHMM — action: result, evidence, next step
```

Entries should be verbose. Capture decisions, failures, solutions, and learnings. These are build artifacts — any future AI session should be able to pick up context from the log.

## Guardrails

- **Never write implementation code before the human gate (step 11)**
- Never treat `Pending` as proof that the critical substrate already exists
- Never let a stale `Draft` label block obviously buildable work when the story
  is already detailed enough and substrate-verified; promote it explicitly
- When important adjacent work is required to actually satisfy the story, default to expanding the current story modestly instead of pretending it is out of scope
- For larger expansions, recommend the scope change explicitly before implementing
- Use relative effort estimates only; never present hours/days unless the user explicitly asks for calendar-style estimates
- Never skip acceptance criteria verification
- Never claim something is fixed, passing, or done without fresh current-pass evidence
- Never continue planning or implementation if the critical substrate reality check shows the story is not honestly buildable yet
- Never trust or preserve stale blocked-story plan text that contradicts the
  current blocker evidence
- Never mark Done if any check fails
- Never mark a story `Done` from `/build-story`
- Never mark Done without inspecting produced artifacts (not just checking logs)
- If evals were run: classify mismatches as **model-wrong**, **golden-wrong**, or **ambiguous**
- Never commit without explicit user request
- Always update the work log, even for partial progress
- If blocked, record the blocker and stop — don't guess
