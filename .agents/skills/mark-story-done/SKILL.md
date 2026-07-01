---
name: mark-story-done
description: Validate a story is complete and update statuses safely
user-invocable: true
---

# /mark-story-done [story-number]

> ADR check: If this task raises an architectural, workflow, schema, or cross-cutting project question, read the relevant decision record(s) in `docs/decisions/` before choosing an approach. If none apply, say so explicitly.

Close a completed story after validation.

## Inputs

- Story id, title, or path (optional if inferable from context)

## Validation Steps

1. **Resolve story file** — Read `docs/stories/story-{NNN}-*.md`.

2. **Check workflow gates first:**
   - [ ] `Build complete` is checked
   - [ ] `Validation complete or explicitly skipped by user` is checked, or the
     user explicitly instructed you to skip validation in this close-out request
   - [ ] `Story marked done via /mark-story-done` is still unchecked
   - If the story predates `Workflow Gates`, add the section and backfill
     equivalent state before continuing

3. **Validate completeness:**
   - [ ] All task checkboxes checked
   - [ ] All acceptance criteria met (with fresh current-state evidence)
   - [ ] Work log is current (no dangling "Next Steps" without resolution)
   - [ ] Dependencies addressed (if depends on other stories, are they done?)
   - [ ] If `Decision Refs` cite ADRs or ADR open items: check the parent ADR `Remaining Work` and note whether this story resolves any item enough for that ADR to move toward `ACCEPTED`
   - [ ] Central Tenet verification checkboxes checked
   - [ ] Doc update checkbox checked
   - [ ] Project checks pass:
     - `python -m pytest tests/`
     - `python -m ruff check modules/ tests/`
   - [ ] If pipeline modules changed: tested through `driver.py` with artifacts inspected
   - [ ] If evals were run: mismatches classified, `docs/evals/registry.yaml` updated with verified scores

4. **Produce completion report:**

   **Story: [ID] - [Title]**
   - Tasks: [X/Y] complete
   - Acceptance Criteria: [X/Y] met
   - Tenets Verified: [Yes/No]
   - Evals Updated: [Yes/No/N/A]
   - Outstanding: [List items if any]
   - Closure Recommendation: [`Close now` / `Rescope then close` / `Keep open` / `Mark blocked`]

## If Story Is Not Complete

Do **not** stop at raw blockers only. Classify the unmet items and make a firm recommendation:

1. **Still belongs to this story** because it remains in the same subsystem,
   validation boundary, and success surface → recommend **`Keep open`**
2. **Waiting on an external dependency/decision** → recommend **`Mark blocked`**
3. **Moved to explicit follow-up story/stories** and the remaining work is
   genuinely separate from the shipped slice → recommend **`Rescope then close`**

Default preference:
- If the remaining work is still same-surface, prefer **`Keep open`** even if
  follow-up stories were already created by mistake.
- Use **`Rescope then close`** only when the remaining work is genuinely
  separate and validation will stay clear after narrowing the story.

If recommending **`Rescope then close`**, propose these edits explicitly:
1. Narrow the title/goal/acceptance criteria/tasks to the shipped slice
2. Add a work-log note explaining which remaining gaps were split into which follow-up stories
3. Re-run this `/mark-story-done` validation against the revised story
4. Only then apply `Done` status + index/changelog updates

Never silently weaken requirements or hide newly discovered defects.

## Apply Completion

If complete (or user approves remaining gaps):

1. Set story file status to `Done`.
2. Check `Story marked done via /mark-story-done`.
3. If validation was explicitly skipped by the user, record that decision in
   the work log and check `Validation complete or explicitly skipped by user`.
4. Regenerate generated `docs/stories.md` and compiled
   `docs/methodology/graph.json` so the generated story index and graph reflect `Done`.
5. Append completion note to story work log with date and evidence. End the
   note with the recommended next step: `/check-in-diff`.
6. Update CHANGELOG.md:
   - Search CHANGELOG.md for the story number (e.g., `Story 001`)
   - If an entry already exists, skip — do not duplicate
   - If no entry exists, prepend a new entry:

     ```
     ## [YYYY-MM-DD-NN] - Short summary (Story NNN)

     ### Added
     - ...

     ### Changed
     - ...

     ### Fixed
     - ...
     ```

   - **CalVer**: `YYYY-MM-DD-NN` where `NN` is sequence for the day. Check previous entry to increment.
   - Only include subsections that apply.

If not complete and the user has **not** approved a closure recommendation, stop after reporting:
- what is incomplete
- the **single recommended story disposition**
- the exact edits or next steps required

## Guardrails

- Never hide gaps — always report unmet criteria explicitly
- Never treat old notes or stale passing logs as proof for the current story
  state; if something was not re-verified now, say it is not freshly verified
- Never describe the story as complete, ready, or validated without fresh
  close-out evidence or an explicitly cited prior validation result
- Ask for confirmation when unresolved items remain
- Do not duplicate CHANGELOG.md entries — always check before writing
- Never mark Done without running the full check suite
- Never mark a Draft story as Done — it must be promoted to Pending and built via `/build-story` first
- Never treat the existence of a follow-up story by itself as a reason to close
  the current one
- If evals were run during the story: verified scores must be recorded in `docs/evals/registry.yaml` before closing
- Never commit or push without explicit user request
- When incomplete, never end with "can't mark done" alone. Always include a firm recommendation: **`Rescope then close`**, **`Keep open`**, or **`Mark blocked`**.
