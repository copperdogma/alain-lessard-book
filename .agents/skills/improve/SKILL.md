---
name: improve
description: Perform deep evidence-based analysis and propose ranked improvements to the codebase
user-invocable: true
---

# Improve Solution

  You are the engineering AI responsible for improving this codebase/feature. Before coding, perform a deep, evidence-based analysis:

  1) Observe current behavior: run or inspect small, real samples (outputs, logs, UI, data dumps—whatever is available) and note concrete findings,
  not assumptions.
  2) Identify failure modes and risks across correctness, robustness, performance/cost, UX, debuggability/observability, and maintainability.
  3) Propose 5–10 actionable improvements, ranked by ROI. For each, state:
     - What to change (brief)
     - Why it helps (expected benefit)
     - Cost/complexity and any risks/side effects
     - How to validate success
     Favor generic, structural fixes over case-specific tweaks.
  4) Call out missing telemetry/forensics that would make issues obvious (e.g., per-stage metrics, source histograms, sanity checks).
  5) If a cheaper/simpler path exists to reach the goal, surface it and ask before proceeding.

  Output: concise observations + the ranked recommendation list. Keep it practical and testable.
