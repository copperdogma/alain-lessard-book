---
name: triage-stories
description: Evaluate the story backlog and recommend what to work on next
user-invocable: true
---

# /triage-stories [story-number]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md` and relevant decision records in `docs/decisions/`. If this work touches a known compromise in `docs/spec.md`, respect its limitation type and evolution path. If none apply, say so explicitly.

Canonical story-backlog triage leaf skill. Direct invocation is allowed, and
`/triage stories` routes here.

## What This Skill Produces

A short advisory report:
- ranked problem-line recommendations
- bottlenecks / concerns
- one recommended next command

This skill is read-only.

## Steps

1. **Read project state**
   Load `docs/methodology/graph.json` (and the generated `docs/stories.md` if
   helpful) and identify all stories by status:
   - In Progress
   - Pending
   - Draft
   - Blocked
   - Done

   Candidate work lines are not just backlog shells. Read:
   - active `In Progress` stories with unresolved work
   - `Pending` stories with met dependencies
   - `Draft` stories that appear detailed enough to be promoted soon
   - `Blocked` stories only when unblocking them may be the highest-leverage move

   For `Blocked` stories, do not stop at the status label. Read the blocker
   summary, blocker evidence, and unblock condition. A blocked story only stays
   in the candidate set when the current pass has fresh evidence that the
   unblock condition is now met or is immediately satisfiable by the proposed
   next action. Otherwise treat it as a health flag, not as a ranked next move.

   Draft/Pending existence alone does not make a story high priority.
   A story can still be high priority when it is mostly manual site refinement
   or editorial grunt work on the current surfaced website. Do not downrank
   that line just because it creates little new code or schema.

2. **Read the Ideal**
   Load `docs/ideal.md` and score against what the system should become, not
   just what is locally convenient.

3. **Read candidate stories and graph/state context**
   For every candidate with met dependencies or strong continuity relevance,
   read the actual story file. Do not rank by title alone. When multiple recent
   stories touch the same subsystem, validation boundary, and success surface,
   treat them as one problem line first and ask whether the honest next move is
   to continue, reopen, expand, or consolidate that line instead of treating
   each story shell as a separate vote.

   If the current problem line is `Blocked`, verify whether the blocker still
   stands. A stale implementation plan inside the story does not override newer
   blocker evidence or an unmet unblock condition.

   For each candidate, also read the matching graph/state category and note:
   - **Substrate status** (`exists`/`partial`/`missing`) — a story whose
     category substrate is `missing` should not be recommended unless the story
     itself creates that substrate
   - **Phase** (`climb`/`hold`/`converge`) — this determines what kind of work
     is highest leverage
   - **Coverage matrix** state when the story touches inputs, filetypes,
     artifacts, or channels
   - **UI-scout freshness** when the candidate is about the current website
     experience and `state.ui_scout` exists
   If a candidate depends on upstream architecture, schema, runtime, or
   artifact substrate, inspect the repo to verify that substrate exists in code
   and is not just asserted in story text.
   If a candidate is manual refinement of the current site, verify that the
   surfaced website really exists in repo code/docs and is not just implied by
   old story prose.

4. **Score and rank**
   Evaluate each candidate on:
   - Ideal alignment
   - real problem pressure
   - dependency readiness
   - blocking power
   - stage leverage
   - simplification leverage
   - **substrate readiness** — read the graph/state category's substrate status;
     don't recommend stories when substrate is `missing` unless the story creates it.
     For architecture-dependent stories, prefer code-verified substrate over
     paper status alone
   - **phase coherence** — read the category's phase from methodology state:
     - `climb`: recommend quality-improvement work
     - `hold`: recommend efficiency/simplification work
     - `converge`: recommend deletion work
     - Work that fights the phase is lower priority
   - **blocked-state honesty** — a blocked line with an unmet unblock condition
     should lose to an actionable line even if continuity and problem pressure
     are high
   - **surfaced-product quality / ship-readiness leverage** — when the repo
     already has a real website surface, stories that make it materially more
     readable, trustworthy, and shippable are legitimate high-value work
   - **manual-refinement legitimacy** — do not penalize a story just because
     the work is mostly hand cleanup or editorial shaping rather than new
     deterministic tooling
   - momentum
   - continuity for active unresolved work lines
   - convergence value
   - complexity vs payoff
   - user impact
   - existing story-shell presence only as packaging / tie-break context

5. **Flag concerns**
   Surface issues such as:
   - same-surface work accidentally split across multiple stories that should
     likely stay one line
   - stories marked Draft/Pending that are actually blocked
   - blocked stories with weak or missing blocker evidence / unblock conditions
   - blocked stories whose older plan text or stale assumptions still imply a
     ready next move even though the current blocker says not to reopen yet
   - stories whose documented prerequisites exist in decision docs or older planning notes
     but not yet in code, schemas, runtime wiring, tests, or artifacts
   - stale or superseded stories
   - claimed scope that disagrees with the compiled graph/state reality
   - bottlenecked dependency chains

6. **Return the report**

   Use this format:

   ```markdown
   ## Triage Stories

   ### Ranked Problem Lines
   - Story NNN — {title} ({Status}) — recommended action: {continue|reopen|expand|consolidate|create} — {why}

   ### Bottlenecks / Concerns
   - {issue}

   ### Recommended Action
   - {one next story action}
   ```

7. **User decides**
   Wait for the user to pick a story or ask for more detail. Do not start
   building; that's `/build-story`.

## Arguments

If the user passes a story ID, evaluate only that story's readiness instead of
doing a full backlog scan. Report:
- dependency status
- blocking power
- build readiness
- verified substrate readiness where relevant
- concerns / missing prerequisites

## Guardrails

- Read-only and advisory — never modify files
- Always read the actual story files, not just the index titles
- If the backlog is empty or everything is blocked, say so clearly
- Do not recommend stories that depend on unfinished work unless the dependency
  is trivially close to done
- Do not recommend a new story when continuing, reopening, expanding, or
  consolidating the current problem line is the more honest move
- Do not recommend architecture-dependent stories as build-ready on story text
  alone when the critical substrate has not been verified in the repo
- Do not assume schema-first or tooling-first stories beat manual website
  refinement once a real surfaced site exists
- Treat `Blocked` stories as candidates only when the unblock path is itself the
  highest-leverage next move
- Do not recommend reopening a blocked story when the current pass only repeats
  previously failed evidence or when the story's own unblock condition is still
  unmet
- Keep the report compact enough for `/triage` to synthesize with other leaf reports
