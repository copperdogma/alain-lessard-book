---
name: you-pick
description: Autonomously pick the most impactful next task and start working on it
user-invocable: true
---

# You Pick Next Task (doc-forge)

Think about what we need to do to progress doc-forge.

When you've picked the most impactful next task, start working on it.

## Context
- Pipeline modules: OCR, clean, portionize, consensus/resolve, enrichment (future), validators, image cropper.
- Config/outputs: `docs/requirements.md`, `snapshot.md`, run outputs in `output/runs/<run_id>/`.
- Priorities typically: correctness/coverage of portionization, enrichment/validators, performance/cost, documentation/automation.

## Decision Framework
1. **Dependencies**: What must be true before other work can proceed (e.g., clean text before portionize, resolve overlaps before enrichment)?
2. **User Impact**: What unlocks value (structured data, validation, layout, images)?
3. **Risk/Cost**: Expensive LLM steps? Try smallest slices/overlaps first.
4. **Reproducibility**: Do we have configs/run_id/state captured?
5. **Docs**: Does README/requirements need updating for new behavior?

## Starting points
- Improve portionization (coarse+fine windows, continuation merge, priors).
- Build enrichment (choices/combat/items/endings) and validators (turn-to checks).
- Add image cropping/mapping pipeline.
- Add AI planner to assemble module config from user goals.
- Automate run manifest and config snapshots per run.

Pick one, then execute with small, testable steps.
