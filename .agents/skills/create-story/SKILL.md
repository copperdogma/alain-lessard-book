---
name: create-story
description: Create a new story when warranted and regenerate the generated views
user-invocable: true
---

# /create-story [title]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, and relevant decision records in `docs/decisions/`. If this work touches a known compromise in `docs/spec.md`, respect its limitation type and evolution path. If none apply, say so explicitly.

Create a new story in `docs/stories/` with consistent format when a new story is
actually warranted. If the honest move is to expand or reopen an existing story
on the same problem line, do that instead of minting a new ID.

## Inputs

- `title`: human-readable story title
- `slug`: kebab-case slug (derived from title if not provided)
- `priority`: High / Medium / Low (default: Medium)
- `ideal_refs`: ideal.md requirements this story serves
- `spec_refs`: relevant spec.md sections or compromise numbers
- `decision_refs`: relevant ADRs, runbooks, scout docs, notes, or other decision docs (or `None found after search`)
- `depends_on`: story IDs this depends on (if any)
- `status`: optional override; prefer inferring the honest initial state from repo reality
  - **Draft** — worth preserving, but still incomplete, underspecified, or not yet substrate-verified enough to claim build-readiness
  - **Pending** — fully detailed ACs, tasks, workflow gates, files to modify, and honestly buildable now
  - **Blocked** — concrete enough to preserve, but cannot proceed because of a named blocker with explicit evidence and an unblock condition

## Steps

1. **Check whether this should be a new story at all**
   - Read `docs/methodology/graph.json`, `docs/methodology/state.yaml`, and any
     recent stories in the same subsystem or category before creating a new ID
   - If the requested work remains in the same subsystem, validation boundary,
     and success surface as a recent active or just-finished story, default to
     expanding or reopening that story instead of creating a new one
   - If expansion or reopen is the honest move, STOP here. Do not run the
     bootstrap script. Return the existing story to continue, or update that
     story directly when the user explicitly asked to flesh out that same line.
   - Only continue to bootstrap a new story after you have explicitly concluded
     that a new ID is honest for this work
   - If you still create a new story on that same line, record explicit
     justification in the story notes for why expansion/reopen was not honest

2. **Run the bootstrap script:**

   ```bash
   .agents/skills/create-story/scripts/start-story.sh <slug> [priority]
   ```

   This creates `docs/stories/story-NNN-<slug>.md` from the template with the next available number.

3. **Fill in the story file** — Replace all placeholder text (`{...}`) with real content:
   - Title (replace the slug with human-readable title)
   - Goal, acceptance criteria, out of scope, tasks, files to modify
   - Ideal refs, spec refs, decision refs, and dependencies
   - Graph/state context: relevant category, current substrate, current phase,
     and any relevant coverage-matrix rows if the story touches formats or artifacts
   - Approach evaluation: candidate approaches, repo constraints, existing patterns to reuse, and what eval distinguishes them
   - Workflow Gates
   - Blocker Summary / Blocker Evidence / Unblock Condition when the story is
     or may become `Blocked`
   - Redundancy or removal targets
   - Architectural Fit notes
   - For architecture-dependent work, inspect the relevant code, schema,
     runtime, or artifact substrate and record what was verified versus assumed.
     If the critical substrate is missing, either add the prerequisite explicitly
     or keep the story in `Draft` / mark it `Blocked` instead of promoting it
     to `Pending`
   - If the functionality is meant to be user-facing and needs a UI to be used
     or inspected honestly, include that UI slice in the goal, acceptance
     criteria, and tasks. Backend-only scope is acceptable only when the story
     explicitly records why the UI is intentionally deferred or owned elsewhere.

4. **Ideal alignment check** — Before writing the story, read `docs/ideal.md`:
   - Does this story close an Ideal gap? → proceed
   - Does it move AWAY from the Ideal? → STOP, push back, recommend alternative
   - Does it only optimize a compromise without closing a gap? → flag as low-value, confirm with user
   - If introducing a new AI compromise: note whether a detection eval exists

5. **Graph/state reality check and honest status selection**
   - Read the relevant category in `docs/methodology/graph.json` and
     `docs/methodology/state.yaml`
   - If the story touches formats or artifacts, read the relevant rows in
     `tests/fixtures/formats/_coverage-matrix.json`
   - Confirm whether the substrate the story depends on actually exists in the repo
   - Set the initial status from the research result:
     - `Draft` when the story is still rough, incomplete, or missing verified substrate
     - `Pending` when the story is concrete and honestly buildable now
     - `Blocked` when the story is concrete enough to preserve but already
       proven blocked, with blocker summary, blocker evidence, and unblock
       condition filled in
   - If the substrate is unverified or missing, keep the story as `Draft` or
     mark it `Blocked` instead of treating paper readiness as real readiness

6. **Regenerate generated views** — After the story file is ready, run
   `make methodology-compile` so generated `docs/stories.md` and
   `docs/methodology/graph.json` reflect the new story.

7. **Verify** — Confirm the file exists, the new story ID is unique and uses
   the next available number (`max + 1`), and the generated graph/index include
   the new story.

## Story Statuses

- **Draft** — Worth preserving, but still incomplete, underspecified, or not yet substrate-verified enough to claim build-readiness
- **Pending** — Fully detailed and honestly buildable now
- **In Progress** — Being built
- **Done** — Validated and closed
- **Blocked** — Concrete enough to preserve, but cannot proceed because of a named blocker with explicit evidence and an unblock condition

## Conventions

- Every story must trace to an Ideal requirement or spec compromise. Stories without lineage are untraceable scope.
- Acceptance criteria must be testable and concrete.
- Always include the Approach Evaluation section — list candidates without pre-deciding. Approach selection happens during `/build-story`.
- `Pending` means buildable in implemented reality, not just plausible on paper.
  If critical substrate is unverified or missing, use `Draft` or `Blocked`
  instead of pretending the story is ready.
- Stories are execution packaging, not priority signals. Do not create a new
  story when the honest move is to expand or reopen the same problem line.
- Same subsystem + same validation boundary + same success surface stays in one
  story by default. Split only when the work becomes materially distinct,
  crosses a new runtime / ownership seam, or would make validation unclear.
- If a story is `Blocked`, fill the canonical `Blocker Summary`,
  `Blocker Evidence`, and `Unblock Condition` sections with repo-backed truth.
- If a story starts `Blocked`, the visible `## Plan` should describe the
  unblock path or blocker reassessment work, not stale implementation steps
  that assume the story can proceed immediately.
- If a feature needs a UI to be honestly usable or inspectable, include that UI
  slice in the story unless the story explicitly records why the UI is deferred
  or owned elsewhere.
- **Simplification baseline gate**: Every story involving new logic must answer: "Can a single LLM call already do this?" If untested, first task = measure the baseline.
- Search `docs/methodology/state.yaml`, `docs/methodology/graph.json`, `tests/fixtures/formats/_coverage-matrix.json`, `docs/decisions/`, `docs/runbooks/`, `docs/scout/`, and `docs/notes/` for prior decisions or constraints while drafting. If none apply, say so explicitly.
- If the story raises a new unresolved architecture, workflow, or schema question, either cite the missing ADR need explicitly or recommend creating one before implementation starts.
- If the story touches input formats, format families, or output artifacts, use
  the current coverage-matrix truth when writing the goal, acceptance criteria,
  tasks, and notes.
- Filetype-aware stories should usually include:
  - the current coverage row or gap they address
  - the target change in coverage or graduation readiness
  - a task to update `tests/fixtures/formats/_coverage-matrix.json` and any
    relevant methodology state if shipped behavior changes the documented reality
- If the story changes pipeline, module, driver, schema, or recipe behavior, include a task for real `driver.py` verification and artifact inspection in `output/runs/`.
- If the story changes agent tooling or project instructions, include `make skills-check` in the task list.
- If the story will run evals, include a task to run `/improve-eval` and update `docs/evals/registry.yaml`.
- Always include the Workflow Gates section. These gates enforce the handoff chain: `/build-story` → `/validate` → `/mark-story-done`.
- If the story supersedes existing code or docs, name likely removal targets up front instead of silently accumulating parallel paths.
- "Files to Modify" is gold for AI agents — fill it in when known.
- Story IDs are identifiers, not sequence numbers. New stories get max+1. Never use letter suffixes.

## Work Log Entry Format

```
YYYYMMDD-HHMM — action: result, evidence, next step
```

## Guardrails

- Never overwrite an existing story file — the script will error
- Never commit or push without explicit user request
- Story IDs are identifiers, not sequence numbers. Gaps are expected; use the
  next available id (`max + 1`), verify there are no duplicates, and never use
  letter suffixes
