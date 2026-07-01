# `/setup-methodology` Mode Map

## `greenfield`

Use when the repo is new or only lightly scaffolded.

- Create the methodology docs from scratch
- Create the working checklist
- Install canonical eval-surface docs
- Normalize AGENTS and skill sync

## `retrofit`

Use when the repo already has meaningful docs, code, stories, or ADRs.

- Read the repo before editing methodology artifacts
- Preserve provenance while normalizing the package
- Keep what is already true; replace only stale methodology packaging

## `adr-021-migration`

Use when the repo already uses Ideal-first but not the dual-ideal,
category-aligned, graph+state structure.

- Add execution ideal
- Reshape spec plus methodology state/graph around shared categories
- Normalize the public setup surface around `/setup-methodology`

## `refresh`

Use when the repo already has the package but it has drifted.

- Refresh AGENTS, runbook, checklist, and eval-surface docs
- Refresh skill wrappers
- Audit for stale setup language and degraded planning guidance
