# Validation Flow (Strategy Creation)

This document summarizes where validation happens in the strategy creation workflow and what each check covers. Task-specific investigations and audit plans live in `.apex/tasks/`.

## Stages & Validation Points

1. **Candidate Generation**
   - **Validation:** Structural + semantic checks per candidate.
   - **Behavior:** Errors trigger targeted retry prompts; validated candidates proceed.

2. **Edge Scoring**
   - **Validation:** None (pure evaluation). Produces scorecards only.

3. **Backtesting (Optional)**
   - **Validation:** None (single tool call per candidate). Results are recorded for selection.

4. **Winner Selection**
   - **Validation:** None (composite ranking + reasoning).

5. **Charter Generation**
   - **Validation:** Optional **Symphony Logic Audit** (non-blocking warnings).

6. **Deployment (Composer)**
   - **Validation:** Final schema/build checks before API call (blocking on errors).

## Candidate Generation Checks

- **Syntax:** Weights sum to ~1.0; logic_tree shape is valid when present; assets exist.
- **Concentration:** Single-asset and sector caps; minimum asset count unless high conviction.
- **Leverage Justification:** 2x/3x ETFs must be justified in the thesis.
- **Archetype ↔ Logic Coherence:** Strategy type must match structure.
- **Thesis ↔ Logic Thresholds:** Numeric claims align with logic_tree conditions (tolerance allowed).
- **Weight Derivation:** Weights reflect stated rationale, not arbitrary rounding.

## Symphony Logic Audit (If Enabled)

For strategies with a `logic_tree`, a lightweight audit can flag:
- Condition validity (syntax and realistic thresholds)
- Branch completeness (assets + weights present)
- Asset consistency (branch assets match scenario)
- Regime applicability (condition likely to trigger under current regime)
- Charter alignment (failure modes cover logic branches)

This audit should be **non-blocking** during charter generation, with a **blocking** schema validation at deployment.

## References

- `docs/VALIDATION_PATTERNS.yaml` for common validation errors and messaging patterns.
- Implementation lives in `src/agent/stages/` (candidate generator, scorer, selector, charter, deployer).
