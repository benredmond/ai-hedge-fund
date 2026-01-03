---
id: kLHQqUaIwmXKRannXQvCv
identifier: vixy-prompt-overemphasis
title: Investigate VIXY overemphasis in strategy prompting
created: 2026-01-03T04:25:20Z
updated: 2026-01-03T04:30:36Z
phase: research
status: active
---

# Investigate VIXY overemphasis in strategy prompting

<research>
<metadata>
  <timestamp>2026-01-03T04:30:36Z</timestamp>
  <agents-deployed>5</agents-deployed>
  <files-analyzed>10</files-analyzed>
  <confidence>7.4</confidence>
  <adequacy-score>0.78</adequacy-score>
  <ambiguities-resolved>0</ambiguities-resolved>
</metadata>

<context-pack-refs>
  ctx.patterns = apex-patterns section
  ctx.impl = codebase-patterns section
  ctx.web = web-research section
  ctx.history = git-history section
  ctx.docs = documentation section (from documentation-researcher)
  ctx.risks = risks section
  ctx.exec = recommendations.winner section
</context-pack-refs>

<executive-summary>
The live candidate generation path loads `candidate_generation_single.md` and `system/candidate_generation_single_system.md` (see `src/agent/stages/candidate_generator.py:336-338`). Both prompts repeatedly showcase VIX/VIXY as the canonical conditional logic trigger, and the single worked example in `candidate_generation_single.md` is a VIX tactical rotation that uses VIXY in the logic_tree. That means every candidate (across five parallel personas) is trained on the same VIXY-heavy scaffold. The generator itself also embeds VIX in the logic_tree schema example and in fix prompts, compounding the bias toward VIX-based triggers even when the archetype is not volatility-focused.

Project docs already diagnose a "one example → one implementation" pattern: a single concrete VIX example yields 100% conditional-logic adoption for VIX and 0% for other archetypes, despite dynamic claims (see `docs/prompt_engineering_analysis_nov2024.md:20-27,64-70` and `docs/prompt_engineering_architecture_plan.md:251-306`). Recent generated outputs reflect this: the testing batch contains multiple strategies and charter sections keyed off VIXY (`data/cohorts/testing-batch-kimi/strategies.json:7,14,93,123`). Composer constraints correctly require an ETF proxy, but the prompts overfit to that proxy as the default conditional trigger.

There are also internal inconsistencies that reinforce VIX/VIXY anchoring: `candidate_generation_single.md` forbids absolute VIXY_price thresholds as "syntax error" while the system prompt uses `VIXY_price > 25` and the generator fix prompt shows `VIX > 22` (not VIXY) as the schema example. These contradictions make VIX/VIXY the safest, most explicit "known-good" pattern for the model to copy.

enhanced_prompt:
  intent: "Identify prompt or validation sources that bias strategy generation toward VIXY triggers and outline prompt-level and/or validation-level adjustments to diversify conditional logic."
  scope:
    in: ["candidate generation prompts and system prompts", "candidate generator validation/fix prompts", "documented prompt engineering analyses", "recent generated strategy artifacts"]
    out: ["model provider changes", "market data correctness", "live trading logic"]
  acceptance_criteria:
    - "Locate exact prompt/validation sections that explicitly recommend or exemplify VIXY usage."
    - "Confirm which prompt files are actually loaded in the generation path."
    - "Cite evidence from recent outputs showing VIXY triggers."
    - "Produce 2-3 solution approaches with tradeoffs."
  success_metrics:
    - "Clear root-cause mapping from prompt examples to output patterns."
  related_patterns: []
</executive-summary>

<web-research>
  <official-docs>Network access restricted; no external docs fetched.</official-docs>
  <best-practices>Use multiple, archetype-specific worked examples to avoid single-template anchoring; align all prompt examples with validation rules to reduce contradictions.</best-practices>
  <security-concerns>None identified.</security-concerns>
  <gap-analysis>Current prompts emphasize VIX/VIXY as the only concrete conditional example; validation and system prompts contain conflicting threshold guidance (absolute vs relative).</gap-analysis>
</web-research>

<codebase-patterns>
  <primary-pattern location="src/agent/stages/candidate_generator.py:336">Candidate generation loads `candidate_generation_single.md` and `system/candidate_generation_single_system.md`, so the VIX/VIXY-heavy worked example and dynamic allocation snippets in those files directly shape all candidates.</primary-pattern>
  <conventions>Conditional logic uses tradeable assets; prompts explicitly translate VIX to VIXY proxies (see `src/agent/prompts/candidate_generation_single.md:107-176`, `src/agent/prompts/system/candidate_generation_single_system.md:124-131`, and `src/agent/prompts/tools/composer.md:171-182`).</conventions>
  <reusable-snippets>Logic tree schema examples embed VIX thresholds (e.g., `src/agent/stages/candidate_generator.py:616-626` and `src/agent/prompts/candidate_generation_single.md:174-190`).</reusable-snippets>
  <testing-patterns>`tests/agent/test_threshold_hygiene.py` validates VIXY thresholds as allowed zero-bounded checks and rejects absolute VIXY_price thresholds, which should stay aligned with prompt examples.</testing-patterns>
  <inconsistencies>Prompt guidance forbids absolute VIXY_price thresholds (`src/agent/prompts/candidate_generation_single.md:119-133`) while the system prompt and generator fix prompt show absolute VIX/VIXY thresholds (`src/agent/prompts/system/candidate_generation_single_system.md:124-128`, `src/agent/stages/candidate_generator.py:1761-1769`). The generator schema example uses `VIX > 22` despite other prompts requiring VIXY proxy.</inconsistencies>
</codebase-patterns>

<apex-patterns>
  <pattern id="APEX.SYSTEM:PAT:EMPTY" trust="★☆☆☆☆" uses="0" success="0%">No relevant APEX patterns returned for prompt bias reduction.</pattern>
  <anti-patterns>None identified.</anti-patterns>
</apex-patterns>

<documentation>
  <architecture-context>`docs/prompt_engineering_analysis_nov2024.md` documents the VIX-only worked example and resulting conditional-logic skew; `docs/prompt_engineering_architecture_plan.md` reinforces that only one concrete example exists and biases implementation.</architecture-context>
  <past-decisions>Commit history and docs note a deliberate addition of a VIX worked example to prove conditional logic capability (see `docs/prompt_engineering_analysis_nov2024.md:64-70`).</past-decisions>
  <historical-learnings>"One example → one implementation" confirmed: only the VIX archetype reliably uses conditional logic without additional examples.</historical-learnings>
  <docs-to-update>If prompt examples change, update `docs/prompt_engineering_analysis_nov2024.md` and `docs/prompt_engineering_architecture_plan.md` to reflect new archetype-specific examples and any diversity constraints.</docs-to-update>
</documentation>

<git-history>
  <similar-changes>e088815 (add Composer condition validation + VIXY proxy), 45cfdde (add VIX worked example), bb4c883 (tool guidance + abstract examples).</similar-changes>
  <evolution>VIX/VIXY examples introduced to enforce conditional logic and Composer compatibility; over time, these examples became the dominant concrete template across prompts.</evolution>
</git-history>

<risks>
  <risk probability="M" impact="M">Reducing VIX examples without adding alternative concrete templates may degrade conditional-logic quality or increase invalid conditions.</risk>
  <risk probability="M" impact="L">Enforcing a hard cap on VIXY usage could block legitimate volatility strategies unless exception logic is precise.</risk>
  <risk probability="L" impact="M">New non-VIX trigger examples must remain Composer-compatible to avoid deployment failures.</risk>
</risks>

<recommendations>
  <solution id="A" name="Prompt diversification + VIX scoping">
    <philosophy>Keep VIXY guidance for volatility archetypes but remove it as the default template for every candidate.</philosophy>
    <path>Replace the single VIX worked example with 3-4 archetype-specific conditional logic examples (e.g., SPY MA regime, cross-sector momentum, factor premium shift). Add an explicit rule: “VIXY only when archetype = volatility/tactical or tail-risk persona.” Align all schema examples to VIXY proxies and threshold hygiene rules.</path>
    <pros>Directly addresses anchoring; minimal code changes; preserves Composer compatibility.</pros>
    <cons>Prompt length increases; requires careful curation of new examples.</cons>
    <risk-level>Medium</risk-level>
  </solution>
  <solution id="B" name="Validation guardrail for trigger diversity">
    <philosophy>Enforce diversity by limiting VIXY-trigger usage across the 5 candidates.</philosophy>
    <path>Add a validation pass to detect VIXY conditions and fail/regen if more than one candidate uses VIXY (unless persona = tail_risk/volatility). Provide retry guidance with alternative trigger templates.</path>
    <pros>Guarantees diversified triggers; measurable enforcement.</pros>
    <cons>Additional retries increase runtime; needs careful exception handling.</cons>
    <risk-level>Medium</risk-level>
  </solution>
  <solution id="C" name="Context pack threshold scaffolding">
    <philosophy>Make non-VIX conditional logic easier by providing explicit thresholds for other regime signals.</philosophy>
    <path>Augment context pack with threshold guidance (e.g., SPY vs MA delta bands, breadth thresholds, sector dispersion bands) and cite them in prompts so models can construct non-VIX logic_tree conditions confidently.</path>
    <pros>Reduces uncertainty about non-VIX triggers; improves regime-fit specificity.</pros>
    <cons>Requires market_context schema changes and downstream validation updates.</cons>
    <risk-level>Medium</risk-level>
  </solution>
  <winner id="A" reasoning="The bias is primarily prompt-driven; diversifying examples and scoping VIXY to volatility/tail-risk keeps Composer compliance while breaking the one-template anchoring without additional code paths."/>
</recommendations>

<next-steps>
Run `/apex:plan vixy-prompt-overemphasis` to create architecture from these findings.
</next-steps>
</research>

<plan>
<metadata>
  <timestamp>2026-01-03T05:05:24Z</timestamp>
  <approach>Concrete non-VIX template + VIXY thesis validator + retry guidance</approach>
  <estimated-files>4</estimated-files>
  <estimated-changes>~190 lines modified</estimated-changes>
</metadata>

## Architecture: Concrete Example + Enforcement

### Problem Statement

The current prompts anchor on the VIX worked example, causing widespread VIXY trigger usage across non-volatility personas. Prompt-only "AUTO-REJECT" language does not enforce thesis-trigger alignment, so VIXY conditions appear even when volatility is not central to the thesis.

### Design Principles

1. **Keep a concrete worked example** to preserve conditional-logic quality, but make it non-VIX.
2. **Provide pattern variety** with a syntax reference table (no additional full templates).
3. **Enforce VIXY usage** with code-level validation tied to thesis/rationale content.
4. **Avoid invalid constraints** (do not require trigger asset in the allocation asset list).
5. **Remove retry anchoring** by replacing VIX examples in fix prompts.

### Architecture Overview

```
CURRENT
- Concrete VIX example anchors VIXY usage across personas
- Prompt-only constraints => no enforcement

NEW
- Concrete SPY-vs-MA example (non-VIX template)
- Syntax reference table for pattern variety
- Validator enforces VIXY usage only when thesis is volatility-focused
```

### Detailed Changes

#### 1. candidate_generation_single.md - Replace VIX Example + Add Pattern Table

**Current**: VIX Tactical Rotation worked example (full Strategy object).

**Proposed**:
- Replace with a concrete SPY-vs-200d MA trend-regime example (full Strategy object).
- Add a syntax reference table listing multiple valid pattern types.
- Remove any rule that the trigger asset must appear in the allocation asset list.

**Example anchor** (non-VIX):
```python
logic_tree = {
  "condition": "SPY_price > SPY_200d_MA",
  "if_true": {...},
  "if_false": {...}
}
```

**Syntax reference table** (variety without full templates):
- Price vs MA (trend)
- Return direction (momentum)
- Cross-asset comparison (factor rotation)
- RSI threshold (overbought/oversold)
- VIXY cumulative return (vol regime only, with note)

#### 2. candidate_generation_single_system.md - Non-VIX Dynamic Allocation Example

**Current**: `VIXY_price > 25` dynamic allocation example.

**Proposed**:
- Swap to SPY vs 200d MA as the concrete example.
- Add a short note: VIXY conditions allowed only when thesis is volatility-focused.

#### 3. candidate_generator.py - VIXY Thesis Alignment Validator + Fix Prompt

Add `_validate_vixy_thesis_alignment`:
- Use `_extract_all_conditions` to collect conditions.
- Count occurrences of `VIXY` in conditions.
- If count > 0 and combined text (thesis + rebalancing_rationale) lacks volatility keywords, emit an error.
- Keyword match should be case-insensitive with word boundaries; include `vix`, `vixy`, `volatility`, `vol regime`, `volatility regime`, `vol spike`.
- Include the VIXY count in the error message for testability.

Wire this validator into `_validate_semantics` before quality scoring.

Fix prompt anchoring:
- Replace all `VIX > 22` schema examples in `create_fix_prompt()` with a non-VIX example:
  `SPY_price > SPY_200d_MA`.

Retry guidance:
- If the VIXY validator fails, append fix guidance:
  1) Remove VIXY condition and use a thesis-appropriate trigger, OR
  2) Add volatility justification to thesis_document/rebalancing_rationale.

#### 4. Tests - VIXY Trigger Coherence

Add tests to confirm:
- VIXY conditions fail when thesis lacks volatility keywords (error includes count).
- VIXY conditions pass when thesis includes volatility/VIX terms.
- VIXY conditions still fail when thesis mentions unrelated words like "volume" (word-boundary check).

Target file: `tests/agent/test_threshold_hygiene.py` (new test class or section).

### Validation Criteria

1. **VIXY enforcement**: Validator rejects VIXY conditions without volatility-focused thesis/rationale.
2. **Example quality preserved**: Concrete example remains, but is non-VIX.
3. **Retry prompt de-anchored**: Fix prompt examples no longer use VIX.
4. **Prompt accuracy**: No rule requires trigger asset to be in the allocation asset list.

### Expected Outcomes

- VIXY usage constrained to volatility-focused theses/rationales.
- Non-VIX triggers increase due to SPY-vs-MA template and pattern table.
- Syntax quality preserved by keeping a concrete worked example.
- Retry guidance reduces VIX anchoring during validation fixes.

### File Change Summary

| File | Lines Modified | Change Type |
|------|----------------|-------------|
| `src/agent/prompts/candidate_generation_single.md` | ~80 lines | Replace VIX example with SPY-vs-MA; add syntax reference table |
| `src/agent/prompts/system/candidate_generation_single_system.md` | ~15 lines | Replace VIXY example with SPY-vs-MA; add VIXY note |
| `src/agent/stages/candidate_generator.py` | ~55 lines | Add VIXY thesis-alignment validator + fix prompt updates + retry guidance |
| `tests/agent/test_threshold_hygiene.py` | ~30 lines | Add VIXY coherence tests |

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Model anchors on SPY-vs-MA example | Pattern table provides alternatives; validator does not enforce SPY |
| VIXY validator too strict | Keep keyword list broad and explicit; allow "VIX" or "VIXY" mentions; include rationale text |
| False positives from partial word matches | Use word-boundary matching and avoid "vol" alone |

### Testing Strategy

1. Run `pytest tests/agent/test_threshold_hygiene.py -v` (avoid TestPhase5EndToEnd).
2. Optionally generate a sample batch and inspect VIXY usage manually.

### Next Steps

Run `/apex:implement vixy-prompt-overemphasis` to execute this architecture.
</plan>

<implementation>
<!-- Populated by /apex:implement -->
</implementation>

<ship>
<!-- Populated by /apex:ship -->
</ship>
