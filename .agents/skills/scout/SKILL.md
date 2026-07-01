---
name: scout
description: Research a source (repo, URL, article) for ideas to adopt, recommend changes, implement approved items, and self-verify.
user-invocable: true
---

# /scout [source]

> Decision check: If this task affects architecture, workflow, schemas, or cross-cutting agent behavior, read relevant docs in `docs/runbooks/`, `docs/scout/`, `docs/notes/`, and any future decision-doc directories before choosing an approach. If none apply, say so explicitly.

Research external sources for patterns, ideas, and approaches worth adopting. Produces a persistent scout document tracking what was found, what was adopted, and the verification evidence.

When a finding is a concrete reusable pattern worth porting, treat it as a
**gene transfusion**: capture the source exemplar, the invariant worth
preserving, the local adaptation, and the proof target. Do not force this for
every finding. Use it only when there is a real pattern transfer, not just an
inspiration or a skip.

## Inputs

- **source** (required): One of:
  - Local repo path
  - GitHub URL
  - Article or web URL
  - File path to docs or papers
- **scope** (optional): Time range, branch, specific area to focus on

## Phase 0 — Resolve Sources and Bootstrap

### Resolve ambiguous source references

Before doing anything else, read `docs/scout.md` and the scout doc for each previous expedition to build a source registry. Users often give shorthand names instead of full paths or URLs.
Treat previous scout findings as historical baselines, not as current-state
proof, unless you re-verify the relevant claims in this pass.

When the input does not look like a path, URL, or file:
1. Search scout history for previous expeditions matching the name
2. If found, reuse that source path or URL and treat the task as a re-scout scoped to changes since the last scout date
3. If multiple matches exist, ask the user which one
4. If nothing matches, ask the user for the full path or URL

### Bootstrap the expedition

```bash
.agents/skills/scout/scripts/start-scouting.sh <topic-slug>
```

This creates the expedition file under `docs/scout/` and prints the path.

## Phase 1 — Research

1. **Check history** — If this is a re-scout, default the scope to "changes since YYYY-MM-DD" using the last expedition date.

2. **Explore the source** based on type:
   - Local repo: read recent history, inspect changed files, AGENTS, docs, and skill surfaces
   - GitHub URL: clone shallow or inspect via API
   - Article or docs: extract patterns, tradeoffs, and concrete ideas
   - File or paper: read the source directly and extract actionable findings

3. **Compare against our project** — For each finding, assess:
   - What the source does
   - Whether we already have it
   - Whether it moves us toward `docs/ideal.md`
   - Whether it simplifies or removes a compromise in `docs/spec.md`
   - Value: HIGH, MEDIUM, or LOW
   - Effort: inline or story-sized
   - If it is a real pattern-transfer candidate, add a short gene-transfusion
     note:
     - **Exemplar** — the concrete source pattern being copied
     - **Invariant** — the behavior or principle that must survive locally
     - **Adaptation** — what changes in doc-forge because the local context differs
     - **Proof target** — what will show the transfusion actually worked

4. **Fill in the scout document** created in Phase 0 with the findings.

5. **Present findings** as a numbered list with value and effort estimates.

6. **Recommend** with a clear approval prompt:
   - Inline items ready now
   - Story-sized items to defer
   - Low-value items to skip

## Phase 2 — Approval

Wait for the user to approve specific items.

An explicit instruction such as "port everything relevant" counts as approval for inline items you recommend, but you should still record what was adopted, adapted, and skipped.

## Phase 3 — Implementation

1. Create a task list from approved items.
2. Implement each inline item.
3. For large items, create a story instead of forcing inline implementation.
4. Update the scout doc's `Approved` section as items land.

## Phase 4 — Verification

After implementation:

1. Re-read every modified file
2. Fill in evidence for each approved item in the scout doc
   - For gene-transfusion items, explicitly confirm whether the proof target
     was met and where that evidence lives
3. Run the relevant checks
4. Update the scout doc's final status
5. Update `docs/scout.md` with the new expedition row
6. Report a concise summary to the user

## Guardrails

- Never implement without explicit user approval
- Always create the scout document before implementation
- Never skip the verification phase
- When in doubt about size, suggest a story rather than inline implementation
- Record skipped items and why they were skipped
- Don't commit or push unless the user explicitly requests it
