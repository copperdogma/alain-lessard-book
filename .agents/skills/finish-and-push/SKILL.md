---
name: finish-and-push
description: Close a completed story, fix minor close-out issues inline, then run the full check-in and push-to-main flow
user-invocable: true
---

# /finish-and-push [story-number] [--cleanup]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md` and relevant decision records in `docs/decisions/`. If this work touches a known compromise in `docs/spec.md`, respect its limitation type and evolution path. If none apply, say so explicitly.

`/finish-and-push` is an orchestrator. It does not define a second close-out or
landing workflow. It wraps the existing leaf skills in order:

1. `/mark-story-done`
2. `/check-in-diff`

Use it when the user wants the story closed, checked in, and landed on `main`
in one pass.

## Inputs

- Story id, title, or path (optional if inferable from context)
- `--cleanup` to request the optional branch/worktree cleanup step after landing

## Bundled Permission

Invocation counts as explicit approval to:

- run `/mark-story-done`
- make narrowly scoped fixes needed to complete close-out safely
- commit intended files
- push the execution branch
- sync with latest `origin/main`
- re-run required validation
- fast-forward `main`
- push `main`

Do not ask again for those actions unless a real blocker, risk, or ambiguity
appears.

## Flow

1. **Resolve the target**
   - Read the target story and current git context.
   - Confirm the worktree actually contains the intended story changes.
   - If the story cannot be resolved unambiguously, stop and ask.

2. **Run `/mark-story-done` first**
   - Reuse that skill's workflow gates, validation requirements, generated `docs/stories.md`
     update, and `CHANGELOG.md` behavior.
   - Do not skip it and jump straight to git check-in.

3. **Triage issues from close-out**
   - If the leaf skill surfaces only minor issues, fix them immediately, rerun
     the required checks, update the story work log, and continue.
   - If it surfaces major gaps, stop before any commit/push, investigate, and
     give the user a recommendation.

4. **Run `/check-in-diff` in full landing mode**
   - Reuse that skill's branch selection, staging discipline, changelog audit,
     sync-with-main, validation, and fast-forward-only landing rules.
   - Treat this invocation as explicit approval for the full landing flow, not
     audit-only mode.
   - Pass through `--cleanup` only if the user explicitly requested it.

5. **Triage issues from check-in**
   - Fix minor mechanical issues inline and continue.
   - Stop on major check-in or integration issues and report the safest next
     action instead of forcing the landing.

6. **Report the outcome**
   - If successful: summarize story closure, commit/landing path, validation
     results, and whether `main` was pushed and cleanup was performed.
   - If stopped: list blockers, what you already checked or fixed, and the
     recommended next step.

## Minor vs Major

Treat these as **minor** unless they reveal a larger underlying problem:

- missing workflow-gate checkbox or stale story status row
- missing or incomplete `CHANGELOG.md` entry
- generated skill wrapper drift fixed by `scripts/sync-agent-skills.sh`
- small doc or metadata mismatch caused by the current work
- narrow lint/test failure with an obvious, low-risk local fix
- missing re-run of a required check after a small patch

Treat these as **major** and stop before commit/push:

- unmet acceptance criteria or unchecked substantive tasks
- missing eval classification / registry updates required by the story scope
- failing tests or lint with unclear root cause or broad blast radius
- unrelated, risky, or suspicious git changes in the landing set
- secrets, credentials, large artifacts, or accidental generated output
- integration conflicts that are not purely mechanical
- anything that requires architecture changes, scope renegotiation, or user
  judgment about what should land

## Guardrails

- Never bypass `/mark-story-done`
- Never push partial work just because only a small issue remains
- After every inline fix, rerun the minimum required validation before continuing
- Never weaken the guardrails from `/mark-story-done` or `/check-in-diff`
- Never land onto `main` without the fast-forward-only rule
- If you stop, explain whether the issue is minor-but-blocked or major and why
