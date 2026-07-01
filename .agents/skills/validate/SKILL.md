---
name: validate
description: Validate work against requirements using git diff analysis and graded scoring
user-invocable: true
---

> Decision check: If this validation raises an architectural, workflow, schema, or cross-cutting project question, read the relevant decision record(s) in `docs/decisions/` before choosing an approach. If none apply, say so explicitly.

# Validate Work Against Requirements

Thoroughly analyze what was done and how it compares to the original instructions using git diff and file analysis.

## Analysis Process

1. **Review Changes**
  Please review ALL local changes, including untracked files.
  Use these commands and include them in your analysis:

  git status --short
  git diff --stat
  git diff
  git ls-files --others --exclude-standard

  For any untracked files, open them and include them in the review. Treat untracked files as part of the change set.

2. **Examine Modified Files**
   - Open each changed file to understand what was implemented
   - Compare against original requirements/story/documentation
   - Check for completeness, quality, and adherence to specifications
   - Treat every positive status claim as provisional until it is backed by
     fresh commands, artifact inspection, or both from this validation pass

2.5 **If there is a known story/ticket, validate against it**
   - **When a story is "known"**: the user provided a story path/ID/title, or a single story file is clearly in-scope (e.g., `docs/stories/story-*.md`) for the work being validated.
   - Open the story/ticket doc and extract:
     - `## Success Criteria` / `## Acceptance Criteria` / `## Requirements` (as applicable)
     - `## Tasks` checklist items (look for `- [ ]` / `- [x]`)
     - `## Workflow Gates` when present
   - Separate **implementation completeness** from **close-out bookkeeping**.
   - Missing close-out items owned by `/mark-story-done` or `/finish-and-push` do **not** count against the story by themselves. This includes items such as:
     - story/status/index flips
     - `CHANGELOG.md`
     - `Story marked done via /mark-story-done`
     - commit/push/PR or other landing hygiene
   - If implementation is complete and only those close-out items remain, treat the story as implementation-complete and recommend **`Close now`** rather than calling the story incomplete.
   - In the report, include a **Story Validation** section that:
     - Lists each story requirement/checklist item as **Met / Partial / Unmet** with evidence.
     - Reports the current workflow-gate state when the story has gates
       (`Build complete`, `Validation complete or explicitly skipped by user`,
       `Story marked done via /mark-story-done`).
     - Explicitly calls out **all Unmet** (and Partial) implementation items as "Remaining Story Gaps" with concrete next steps.
     - Separately notes close-out bookkeeping that belongs to `/mark-story-done` or `/finish-and-push` without scoring it as an implementation failure.
     - Suggests which story checkboxes appear ready to check off, and asks the user if they want the AI to apply those edits.
     - If the delivered slice is coherent but the remaining gaps have clearly been split into other stories, explicitly say whether the current story should be:
       - **Rescoped then closed**
       - **Kept open**
       - **Marked blocked**
       - Same subsystem + same validation boundary + same success surface
         should normally stay **`Keep open`** even if follow-up story shells
         already exist
     - Do not end in an ambiguous "not done" state without a firm recommendation.

2.75 **Read decision context when relevant**
   - If a known story/ticket affects architecture, workflows, schemas, or cross-cutting project behavior, read `docs/ideal.md`, the story's `Spec Refs`, and any ADRs or decision docs in `Decision Refs`.
   - If the story appears to touch those areas and cites no ADRs, search `docs/decisions/` before assuming none exist.
   - Call out missing ADR / decision alignment explicitly in the report when relevant.

3. **Score Each Requirement**
   - **A**: Fully implemented, high quality, exceeds expectations
   - **B**: Implemented well, minor improvements possible
   - **C**: Implemented but has notable issues or missing elements
   - **D**: Partially implemented or significant problems
   - **F**: Not implemented or completely incorrect

## Project Validation Checklist

### Architecture & Design
- [ ] Clear boundaries and responsibilities between modules/services
- [ ] Data contracts and interfaces documented and followed
- [ ] Error handling strategy consistent across layers
- [ ] Observability in place (logging/metrics/tracing) for critical paths

### Code Quality
- [ ] Code is readable, idiomatic, and follows project style conventions
- [ ] Dependencies are pinned/approved and minimal
- [ ] Memory/resource usage reasonable; no obvious leaks
- [ ] Security practices observed (input validation, secrets handling, authz)

### Functionality & UX
- [ ] Core requirements implemented as specified
- [ ] User interactions are clear, accessible, and responsive where applicable
- [ ] Integration between components/services is verified
- [ ] Edge/error cases handled gracefully with actionable errors

### Performance & Reliability
- [ ] Latency/throughput meets expectations or budgeted limits
- [ ] Concurrency/race conditions considered; retries/backoff where needed
- [ ] Start-up/shutdown, migrations, and rollbacks validated

### Testing & Validation
- [ ] Unit/integration/e2e tests cover happy path and key edge cases
- [ ] CI workflows are green; flaky tests identified or quarantined
- [ ] Manual validation notes captured where automation lacks coverage
- [ ] Docs updated for touched behavior/contracts (README, ADRs, API docs, runbooks, contracts as applicable). Do not score repo close-out bookkeeping like `CHANGELOG.md` or story-status/index updates here; note them separately as follow-up owned by close-out skills.

## Grading Criteria

### Grade A (90-100%)
- **Implementation**: Complete, exceeds requirements
- **Quality**: Excellent code quality, follows best practices
- **Testing**: Thoroughly tested, handles edge cases
- **Documentation**: Clear, comprehensive documentation
- **Innovation**: Shows creative problem-solving

### Grade B (80-89%)
- **Implementation**: Complete, meets all requirements
- **Quality**: Good code quality, minor improvements possible
- **Testing**: Well tested, some edge cases could be better
- **Documentation**: Good documentation, could be more detailed
- **Innovation**: Solid implementation, some creative elements

### Grade C (70-79%)
- **Implementation**: Mostly complete, minor gaps
- **Quality**: Adequate code quality, some areas need improvement
- **Testing**: Basic testing, some issues not covered
- **Documentation**: Basic documentation, could be clearer
- **Innovation**: Standard implementation, limited creativity

### Grade D (60-69%)
- **Implementation**: Partially complete, significant gaps
- **Quality**: Poor code quality, needs major improvements
- **Testing**: Limited testing, many issues not addressed
- **Documentation**: Minimal documentation, unclear
- **Innovation**: Basic implementation, no creative elements

### Grade F (Below 60%)
- **Implementation**: Incomplete or incorrect
- **Quality**: Very poor code quality, major problems
- **Testing**: No testing or completely inadequate
- **Documentation**: No documentation or completely unclear
- **Innovation**: No evidence of problem-solving

## Detailed Analysis Template

For each requirement, provide:

### Requirement: [Description]
- **Status**: [Implemented/Partially Implemented/Not Implemented]
- **Grade**: [A/B/C/D/F]
- **Evidence**: [Specific code/files that demonstrate implementation]
- **Quality Assessment**: [Code quality, error handling, performance]
- **Improvement Suggestions**: [If not A grade, specific recommendations]

### Example Analysis

#### Requirement: User authentication and session management
- **Status**: Implemented
- **Grade**: B
- **Evidence**: `services/auth/service.ts` session issuance and renewal; `web/routes/login.ts` form handling
- **Quality Assessment**: Follows project patterns; session expiry tested, but no CSRF protection on form POST
- **Improvement Suggestions**:
  - Add CSRF token validation for form submissions
  - Add rate limiting for login endpoint
  - Expand tests to cover password reset and simultaneous session revocation

## Final Scorecard

### Overall Grade: [A/B/C/D/F]

### Summary
- **Requirements Met**: X of Y requirements fully implemented
- **If a story/ticket was validated**: include a 1–2 line summary of whether the story implementation is **Done / Not Done**, and name any remaining implementation gaps separately from close-out follow-up.
- **If a story/ticket was validated**: include a one-line **Closure Recommendation**:
  - `Close now`
  - `Rescope then close`
  - `Keep open`
  - `Mark blocked`
- **Quality Score**: [High/Medium/Low] code quality
- **Testing Coverage**: [Comprehensive/Partial/Minimal]
- **Documentation**: [Excellent/Good/Adequate/Poor]

### Critical Issues (if any)
1. [Issue 1]: [Description and impact]
2. [Issue 2]: [Description and impact]

**Note:** If a story/ticket was validated, treat **Unmet** (and important **Partial**) story requirements as critical issues unless explicitly deferred. Critical issues should summarize "where we are", why the story is not done, and include the concrete next step(s) required to close each gap.
Do **not** treat close-out bookkeeping owned by `/mark-story-done` or `/finish-and-push` as a critical issue by itself.

### Recommendations for Improvement
1. [Priority 1]: [Specific actionable improvement]
2. [Priority 2]: [Specific actionable improvement]
3. [Priority 3]: [Specific actionable improvement]

### Next Steps
- End with a single numbered plan the user can approve.
- When a story is not ready to close, the plan must start with the **recommended disposition** of the story:
  1) `Rescope then close`, `Keep open`, or `Mark blocked`
  2) Concrete edits needed to support that recommendation
  3) Remaining implementation work, if any
  4) Run tests/smoke and inspect outputs
  5) Re-validate or close

Ask one direct question:
- If recommending closure: `"Do you want me to apply that recommendation?"`
- If recommending more implementation first: `"Do you want me to proceed with these next steps?"`

Default behavior:
- If implementation is complete and the only remaining work is close-out bookkeeping owned by `/mark-story-done` or `/finish-and-push`, prefer **`Close now`**.
- If the remaining work still belongs to the same subsystem, validation
  boundary, and success surface, prefer **`Keep open`** even if follow-up
  stories were already created.
- If the implemented slice is coherent and the remaining gaps are genuinely
  separate and explicitly moved to follow-up stories, prefer
  **`Rescope then close`**.
- If the story cannot honestly proceed because of a dependency or decision,
  prefer **`Mark blocked`**.
- Never silently weaken requirements. The report must say exactly what would be rescoped and why.

Fresh-verification rule:
- Do not say something is fixed, passing, or done unless that claim is backed
  by commands, artifact reads, or both from this validation pass
- If something was not re-run or re-opened now, label it explicitly as not
  freshly verified instead of implying current confidence


## ADDITIONAL NOTES FROM USER
(there may be none)

$ARGUMENTS
