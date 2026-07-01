# The Ideal-First Methodology

## TLDR

This repo starts from two authored north stars:

- the **Product Ideal** in `docs/ideal.md`
- the **Execution Ideal** in `docs/ideal.md`

`docs/spec.md` records the active compromises between that ideal and current
project reality. Mutable planning state lives in
`docs/methodology/state.yaml`, the machine-readable source inventory lives in
`tests/fixtures/formats/_coverage-matrix.json`, and
`docs/methodology/graph.json` compiles those surfaces into one inspectable
view.

The goal is not to preserve process forever. The goal is to make every layer of
extra machinery easy to delete once the corresponding limitation stops being
real.

## What It Produces

1. **Ideal** - `docs/ideal.md`
2. **Spec** - `docs/spec.md`
3. **Structured Methodology State** - `docs/methodology/state.yaml`
4. **Coverage Matrix** - `tests/fixtures/formats/_coverage-matrix.json`
5. **Compiled Graph** - `docs/methodology/graph.json`
6. **Generated Views** - `docs/stories.md`
7. **Decision Records** - `docs/decisions/`
8. **Stories** - `docs/stories/`
9. **Evals** - `docs/evals/registry.yaml`

## Core Idea

The method is simple:

1. describe what the project should look like without current limitations
2. describe what reality forces us to do instead
3. keep that workaround explicitly tied to a named limitation
4. delete or shrink the workaround when the limitation changes

For this repo, common early examples include:

- keeping raw scans immutable while generated outputs live under `output/`
- using deterministic crop rules because raw scans include scanner-platen bands
- keeping OCR validation artifacts because text quality cannot be assumed
- delaying website runtime choices until the source PDF and inventory are real

## Product Constraints vs Execution Constraints

**Product constraints** affect what the book/PDF/site can do.

Examples here:

- supplemental scans are not all present yet
- OCR quality needs sampled evidence
- the website content model is not yet defined

**Execution constraints** affect how the project has to be built right now.

Examples here:

- keeping an explicit methodology state and compiled graph
- keeping an eval registry before a website runtime exists
- documenting local `input/` assumptions instead of relying on memory

## Phase Governance

Each compromise carries a phase in `docs/methodology/state.yaml`:

- `climb` - improve or establish the missing substrate
- `hold` - protect an honest working floor without adding sprawl
- `converge` - simplify or delete the workaround

## Operating Rule

Planning starts from:

- `docs/methodology/state.yaml`
- `docs/methodology/graph.json`
- `tests/fixtures/formats/_coverage-matrix.json`

Implementation starts from the active story, but the story still needs the
relevant `spec:N` context.

## Why The Graph Exists

The compiled graph is a lightweight join surface. It keeps the authored canon,
mutable planning state, and source inventory aligned for AI and human readers.

If the graph, checklist, or eval surfaces stop paying for themselves, they
should be simplified. They are scaffolding, not a ritual.
