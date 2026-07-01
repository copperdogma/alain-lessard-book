---
name: advice-for-past-self
description: Write advice to your past self with everything critical learned before resetting context
user-invocable: true
---

# Advice for Past Self

I'm going to reset this chat which will destroy all context and revert all code.

I want you to write advice to your past self with everything critical that you've learned so you can try again.

Write out very succinctly:

- Start with a succinct description of what feature you were attempting to build or test you were attempting to run that failed.
- What you attempted to do to fix the issue and why it failed. Should we continue down that path? Why or why not?
- Any critical wisdom you gained about the system that would be useful context for solving this issue.
- Any promising ideas of what to try next to solve this issue.

IMPORTANT: If you feel there you added critical net good code that should be kept, explain what code should be kept and why. If so, be clear about what code should be kept and what should be reverted.

## Doc-Forge Context

When writing advice, consider:
- Pipeline stages and artifacts (pages_raw/clean, hypotheses, resolved portions, manifests).
- Model/config choices (LLM model, window/stride, confidence thresholds).
- Reproducibility and state (run_id locations, overlap strategy, priors).
- Performance/cost trade-offs (batch sizes, coarse vs. fine passes).
