---
id: odJkbRHYwThOs83GRZMdK
identifier: strategy-grade-2026-01-05
title: Grade AI Factor-ETF Strategy and Ship Recommendation
created: 2026-01-05T17:12:19Z
updated: 2026-01-05T17:14:50Z
phase: research
status: active
---

# Grade AI Factor-ETF Strategy and Ship Recommendation

<research>
<metadata>
  <timestamp>2026-01-05T17:14:50Z</timestamp>
  <agents-deployed>5</agents-deployed>
  <files-analyzed>3</files-analyzed>
  <confidence>6</confidence>
  <adequacy-score>0.7</adequacy-score>
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
The internal evaluation rubrics emphasize explicit edge articulation, falsifiable failure modes, regime alignment, and coherence between thesis, weights, and rebalancing. The provided strategy maps cleanly to the multi-factor guidance, but the current implementation details create a few avoidable penalties: the "risk-off" sleeve is small relative to the defensive claim and the weights in the else-branch sum to 102%, which will be rejected or silently normalized by tooling.

Using the edge-scoring prompt as the grading backbone, this strategy likely passes but with mid-range scores in edge economics and coherence. It is framed around factor premia in a low-vol, disinflationary regime, but the timing signal is a single relative-strength threshold without hysteresis or corroborating regime filter, which increases whipsaw risk and weakens the causal story.

Recommendation: do not ship completely unchanged. Apply minimal fixes that preserve the thesis: (1) correct the weight math; (2) add simple hysteresis or a confirmatory regime filter; (3) align the defensive sleeve size with the claimed "weaker markets" behavior. These are small edits that improve rubric alignment without changing the core thesis.
</executive-summary>

<web-research>
  <official-docs>Not performed (network restricted). Internal rubrics and prompts serve as the authoritative source for scoring.</official-docs>
  <best-practices>Use internal edge-scoring rubric and investing guidelines for evaluation consistency.</best-practices>
  <security-concerns>Not applicable.</security-concerns>
  <gap-analysis>External market data not verified; any time-sensitive claims should be re-validated against the context pack before shipment.</gap-analysis>
</web-research>

<codebase-patterns>
  <primary-pattern location="src/agent/prompts/edge_scoring.md:7">
    Strategy grading is a 5-dimension rubric with pass/fail if any score is below 3. Use explicit evidence and do not "fill in gaps." 
  </primary-pattern>
  <primary-pattern location="plan/INVESTING_STRATEGY_GUIDELINES.md:13">
    Edge articulation is mandatory; the strategy must name a structural inefficiency, explain why it exists, and why now.
  </primary-pattern>
  <primary-pattern location="plan/INVESTING_STRATEGY_GUIDELINES.md:141">
    Portfolio construction must justify concentration, correlation, position sizing, and rebalancing frequency based on edge timescale.
  </primary-pattern>
  <primary-pattern location="plan/COHORT_SCORING_RUBRIC.md:20">
    Charter quality scoring prioritizes edge articulation, falsifiability, regime awareness, and internal coherence.
  </primary-pattern>
  <conventions>Use numeric thresholds for failure modes; match rebalancing frequency to signal timescale; align "why now" with specific regime evidence.</conventions>
  <reusable-snippets>Use the edge scoring rubric and charter quality rubric as the grading template; include per-dimension scores and concrete evidence citations.</reusable-snippets>
  <testing-patterns>Not applicable for this evaluation-only task.</testing-patterns>
  <inconsistencies>Edge scoring (5-dimension) and cohort rubric (4 charter dimensions) are complementary but not identical; state which rubric you use to avoid confusion.</inconsistencies>
</codebase-patterns>

<apex-patterns>
  <anti-patterns>No relevant APEX patterns returned for this task.</anti-patterns>
</apex-patterns>

<documentation>
  <architecture-context>Strategy evaluation uses internal scoring rubrics and emphasizes process quality over raw returns (plan/COHORT_SCORING_RUBRIC.md:1-116).</architecture-context>
  <past-decisions>Edge scoring upgraded to institutional-grade rubric (commit d9598e1).</past-decisions>
  <historical-learnings>Guidelines emphasize edge articulation and regime alignment to prevent generic factor tilts (plan/INVESTING_STRATEGY_GUIDELINES.md:13-116).</historical-learnings>
  <docs-to-update>None.</docs-to-update>
</documentation>

<git-history>
  <similar-changes>Recent scoring rubric updates include commit d9598e1 and a VIX proxy wording alignment in 1f389d3.</similar-changes>
  <evolution>Evaluation guidance has become more explicit around edge economics and regime fit.</evolution>
</git-history>

<risks>
  <risk probability="H" impact="M">Weight math error (else branch totals 102%) could cause Composer normalization or rejection; fix before shipping.</risk>
  <risk probability="M" impact="M">Binary IWM vs SPY trigger without hysteresis may whipsaw in choppy markets; add confirmation or buffer.</risk>
  <risk probability="M" impact="M">Defensive sleeve (10% AGG) may be too small versus stated "risk-off" intent, weakening coherence scores.</risk>
</risks>

<recommendations>
  <solution id="A" name="Ship As-Is (Minimal Intervention)">
    <philosophy>Accept current thesis and rely on factor premia continuity; avoid scope creep.</philosophy>
    <path>Only fix CPI mismatch already addressed; proceed to deployment.</path>
    <pros>Fast; maintains continuity with original analysis.</pros>
    <cons>Leaves weight-math error and coherence gaps; increases evaluation risk.</cons>
    <risk-level>Medium</risk-level>
  </solution>
  <solution id="B" name="Light Fixes, Same Thesis (Recommended)">
    <philosophy>Preserve core factor-premia thesis while improving rubric alignment and execution safety.</philosophy>
    <path>Fix weight totals; add hysteresis/confirmation to IWM vs SPY trigger; increase AGG sleeve in weak regime to match defensive claim.</path>
    <pros>Improves coherence and risk framework without changing strategy identity.</pros>
    <cons>Minor strategy changes require updated charter text.</cons>
    <risk-level>Low</risk-level>
  </solution>
  <solution id="C" name="Add Regime Filter (Higher Effort)">
    <philosophy>Gate factor exposure with explicit regime filter (trend/volatility) to reduce whipsaw.</philosophy>
    <path>Add VIX or trend filter; scale factor weights based on regime; update thesis and failure modes.</path>
    <pros>Stronger causal chain and regime alignment; improved robustness.</pros>
    <cons>Higher complexity; may drift from original thesis.</cons>
    <risk-level>Medium</risk-level>
  </solution>
  <winner id="B" reasoning="Provides the best risk-adjusted improvement with minimal change to the thesis and avoids rubric penalties."/>
</recommendations>

<next-steps>
Run `/apex:plan strategy-grade-2026-01-05` to create architecture from these findings.
</next-steps>
</research>

<plan>
<!-- Populated by /apex:plan -->
</plan>

<implementation>
<!-- Populated by /apex:implement -->
</implementation>

<ship>
<!-- Populated by /apex:ship -->
</ship>
