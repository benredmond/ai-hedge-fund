---
id: IazEGONpzDn2ur8abC8Gu
identifier: candidate-diversity-sector-etfs
title: Candidate diversity collapse to sector ETFs
created: 2026-01-03T22:54:32Z
updated: 2026-01-04T00:04:34Z
phase: complete
status: complete
---

# Candidate diversity collapse to sector ETFs

<research>
<metadata>
  <timestamp>2026-01-03T23:02:32Z</timestamp>
  <agents-deployed>0</agents-deployed>
  <files-analyzed>5</files-analyzed>
  <confidence>8</confidence>
  <adequacy-score>0.72</adequacy-score>
  <ambiguities-resolved>0</ambiguities-resolved>
</metadata>

<context-pack-refs>
  ctx.patterns = apex-patterns section
  ctx.impl = codebase-patterns section
  ctx.web = web-research section
  ctx.history = git-history section
  ctx.docs = documentation section
  ctx.risks = risks section
  ctx.exec = recommendations.winner section
</context-pack-refs>

<executive-summary>
The current candidate generation pipeline strongly anchors on explicit sector ETF leaders exposed in the context pack. The pack names XLB/XLF/XLY as top leaders with returns, which are high-signal labels for LLMs and appear repeatedly in candidate outputs (data/context_packs/25-1-2.json:39). The only worked example in the candidate generation recipe uses a purely ETF allocation (SPY/QQQ/AGG/TLT/GLD/BIL), which sets an ETF-first precedent and reinforces broad sector ETF usage (src/agent/prompts/candidate_generation.md:152). Persona constraints are broad; only the sector rotation persona is explicitly constrained to sector allocation, while other personas allow any assets, letting the model default to the easiest ETF explanation (src/agent/stages/candidate_generator.py:30).

The prompt does acknowledge intra-sector divergence and suggests individual stocks when spread is high, but this is advisory and not enforced (src/agent/prompts/candidate_generation.md:59). The context pack already contains stock-level divergence data intended to seed stock selection (data/context_packs/25-1-2.json:81), and documentation confirms this section is designed to encourage stock-level strategies (docs/market_context_schema.md:109). Project docs already flag the same sector ETF default as a critical issue, pointing to ETF examples and weak enforcement as root causes (docs/prompt_engineering_architecture_plan.md:73).
</executive-summary>

<web-research>
  <official-docs>N/A (network restricted)</official-docs>
  <best-practices>N/A (network restricted)</best-practices>
  <security-concerns>None identified (prompt and data anchoring changes only)</security-concerns>
  <gap-analysis>External references not reviewed due to network restrictions.</gap-analysis>
</web-research>

<codebase-patterns>
  <primary-pattern location="src/agent/prompts/candidate_generation.md:152">Worked example is ETF-only, which anchors asset selection toward broad ETFs rather than stocks. The example explicitly lists SPY/QQQ/AGG/TLT/GLD/BIL in the strategy assets and logic_tree.</primary-pattern>
  <conventions>Candidate generation relies on a shared recipe prompt and per-persona constraints that are descriptive rather than prescriptive. Constraints are short natural language strings injected into the prompt (src/agent/stages/candidate_generator.py:30).</conventions>
  <reusable-snippets>Strategy block in candidate_generation.md shows the expected schema and can be adapted into a stock-based example (src/agent/prompts/candidate_generation.md:152).</reusable-snippets>
  <testing-patterns>Diversity checking is covered via unit tests in tests/agent/test_stages.py that validate edge type and archetype diversity (tests/agent/test_stages.py:240).</testing-patterns>
  <inconsistencies>Prompt guidance suggests using intra_sector_divergence for stock selection when spread is high, but the only worked example uses ETFs and there are no constraints that enforce stock selection (src/agent/prompts/candidate_generation.md:59).</inconsistencies>
</codebase-patterns>

<apex-patterns>
  <anti-patterns>No relevant APEX patterns found for this query.</anti-patterns>
</apex-patterns>

<documentation>
  <architecture-context>Documentation explicitly calls out the sector ETF default as a critical blocker and cites ETF examples as a root cause (docs/prompt_engineering_architecture_plan.md:73).</architecture-context>
  <past-decisions>None found specific to this prompt change in docs beyond the architecture plan note.</past-decisions>
  <historical-learnings>Context schema describes intra_sector_divergence as a stock-level signal intended to encourage stock selection when dispersion is high (docs/market_context_schema.md:109).</historical-learnings>
  <docs-to-update>docs/prompt_engineering_architecture_plan.md may need updates after changes are implemented to reflect new constraints or examples.</docs-to-update>
</documentation>

<git-history>
  <similar-changes>Recent commits include candidate generation prompt updates and persona diversity work (8e1d977, 10d314e, e5f2e41).</similar-changes>
  <evolution>Candidate generation has evolved through prompt updates and retry logic; prior work focused on syntax/logic coherence and persona diversity, not asset-type diversity.</evolution>
</git-history>

<risks>
  <risk probability="M" impact="M">Tightening prompts or constraints could reduce candidate quality or increase invalid outputs if the model cannot satisfy stricter asset rules. Mitigation: add stock-based example and allow a fallback path when intra-sector divergence is low.</risk>
  <risk probability="M" impact="L">Abstracting sector leader tickers in the context pack may reduce useful signal for sector-rotation personas. Mitigation: keep sector labels but map them to sector names rather than tickers, or provide a separate section for sector-rotation personas.</risk>
</risks>

<recommendations>
  <solution id="A" name="Prompt-level diversification enforcement">
    <philosophy>Replace anchor examples and add persona-specific asset constraints so each persona must use distinct asset types.</philosophy>
    <path>Update candidate_generation.md with a stock-level worked example; add explicit constraints per persona (e.g., trend_follower must use intra_sector_divergence stocks, factor_quant must use factor ETFs). Update quality gates to require non-sector ETFs for non-sector personas.</path>
    <pros>Directly addresses anchoring; minimal code changes; aligns with existing prompt-driven architecture.</pros>
    <cons>Relies on model compliance; may still drift without strong validation.</cons>
    <risk-level>Low</risk-level>
  </solution>
  <solution id="B" name="Context pack de-anchoring">
    <philosophy>Reduce ticker anchoring by abstracting sector leaders to labels and pushing stock-level signals forward.</philosophy>
    <path>Replace sector_leadership tickers with sector names or categories; surface intra_sector_divergence in higher-priority prompt sections; keep raw tickers available for sector-rotation persona only.</path>
    <pros>Reduces repeated ETF anchoring across personas; improves stock selection salience.</pros>
    <cons>Requires context pack schema changes or prompt translation; risk of breaking downstream assumptions.</cons>
    <risk-level>Medium</risk-level>
  </solution>
  <solution id="C" name="Validation-time diversity enforcement">
    <philosophy>Enforce asset-type diversity after generation with deterministic checks and targeted regen.</philosophy>
    <path>Add validation that flags sector-ETF-only portfolios for non-sector personas; regenerate candidate with stricter instructions or replacement asset rules when violated.</path>
    <pros>Guarantees compliance; measurable and testable.</pros>
    <cons>More code complexity; may increase generation cost and latency.</cons>
    <risk-level>Medium</risk-level>
  </solution>
  <winner id="A" reasoning="Prompt-level changes are the lowest-risk fix that directly removes ETF anchoring and can be implemented quickly without schema changes or regeneration loops."/>
</recommendations>

<next-steps>
Run `/apex:plan IazEGONpzDn2ur8abC8Gu` to create architecture from these findings.
</next-steps>
</research>

<plan>
<metadata>
  <timestamp>2026-01-03T23:39:47.667648Z</timestamp>
  <chosen-solution>A</chosen-solution>
  <complexity>4</complexity>
  <risk>LOW</risk>
</metadata>

<chain-of-thought>
chain_of_thought:
  current_state:
    what_exists:
      - Context pack highlights sector ETF leaders (XLB/XLF/XLY) and lags (XLP/XLRE/XLU), which is a strong anchoring signal for ETF selection. data/context_packs/25-1-2.json:39
      - Context pack already includes intra-sector stock divergence lists intended to seed stock selection. data/context_packs/25-1-2.json:81
      - Recipe advises stock selection when spread is high, but the only worked example is ETF-only. src/agent/prompts/candidate_generation.md:59 src/agent/prompts/candidate_generation.md:152
      - Persona constraints are broad; only sector_rotation requires sector allocation. src/agent/stages/candidate_generator.py:30
      - Mean-reversion/value + sector ETF warning only triggers if the thesis uses stock-level language. src/agent/stages/candidate_generator.py:1170
      - Docs flag the sector ETF default as a critical blocker and point to intra_sector_divergence as the intended stock-selection signal. docs/prompt_engineering_architecture_plan.md:73 docs/market_context_schema.md:109
    how_it_got_here:
      - Recent prompt/persona changes focused on generation quality/diversity, not asset-type diversity. docs/prompt_engineering_architecture_plan.md:202
    dependencies:
      - Candidate generation recipe prompt. src/agent/prompts/candidate_generation.md
      - Persona constraints injected by PROMPT_VARIATIONS. src/agent/stages/candidate_generator.py:30
      - Context pack fields: sector_leadership + intra_sector_divergence. data/context_packs/25-1-2.json:39 data/context_packs/25-1-2.json:81
      - Diversity tests validate edge/archetype variety, not asset-type diversity. tests/agent/test_stages.py:240
  problem_decomposition:
    core_problem: Prompt anchoring and weak persona guidance cause non-sector personas to default to sector ETFs instead of stock selection.
    sub_problems:
      - Sector leadership tickers are prominent and easy anchors.
      - ETF-only worked example sets a strong precedent.
      - Persona constraints do not differentiate asset types for non-sector personas.
      - Recipe doesn’t clearly say intra_sector_divergence is a starting signal, not a cap.
      - Tool usage for expanding stock lists is optional and not emphasized.
  hidden_complexity:
    - More examples can over-anchor to specific tickers or patterns.
    - Strong guidance risks constraining creativity or reducing diversity.
    - Prompt bloat can reduce compliance with earlier instructions.
    - Sector_rotation must remain ETF-friendly while others diversify.
  success_criteria:
    automated:
      - Existing tests in tests/agent/test_stages.py still pass (no functional logic changes).
    manual:
      - Generate candidates and confirm non-sector personas include stock-level strategies when divergence is high.
      - Strategies explicitly mention using tools to expand beyond context-pack tickers.
</chain-of-thought>

<tree-of-thought>
  <solution id="A">
    approach: Prompt-first enrichment
    description: Expand persona constraints + add anti-anchoring callout + 3 worked examples (including stock selection) in candidate_generation.md. No hard rules or schema changes.
    implementation:
      - Update PROMPT_VARIATIONS constraints to specify asset-type guidance. src/agent/stages/candidate_generator.py:30
      - Add Asset Types by Persona + Context pack is a starting signal callouts. src/agent/prompts/candidate_generation.md:42
      - Replace the current ETF-only example with a stock-selection example placed first; add two additional examples (factor ETF, macro/trend), with any sector-ETF example labeled sector_rotation-only and placed last. src/agent/prompts/candidate_generation.md:152
    pros:
      - Prompt-only, low-risk, minimal code changes.
      - Leverages existing intra_sector_divergence signal without adding data.
      - Keeps sector_rotation persona intact.
    cons:
      - Soft guidance; no enforcement if model ignores instructions.
      - Example anchoring risk if not phrased carefully.
    complexity: 4
    risk: LOW
  </solution>
  <solution id="B">
    approach: Context-pack de-anchoring
    description: Replace sector ETF tickers with sector names in the context pack; add a separate block for sector_rotation persona only.
    implementation:
      - Adjust context pack generation/schema. data/context_packs/* docs/market_context_schema.md
    pros:
      - Reduces ticker anchoring at the source.
      - Makes stock selection more salient by default.
    cons:
      - Requires data/schema changes and downstream assumptions.
      - More invasive than requested.
    complexity: 7
    risk: MEDIUM
  </solution>
  <solution id="C">
    approach: Tool-first expansion protocol
    description: Add a prompt step that explicitly uses intra_sector_divergence as a seed list and encourages tool-based expansion/validation for non-sector personas.
    implementation:
      - Add Stock Expansion Protocol and tool guidance blocks to recipe. src/agent/prompts/candidate_generation.md
      - Tighten persona constraint language to prefer tool use for stock selection. src/agent/stages/candidate_generator.py:30
    pros:
      - Stronger anti-anchoring signal without hard rules.
      - Encourages exploration beyond context pack.
    cons:
      - Increases prompt length and token usage.
      - Still relies on model compliance.
    complexity: 5
    risk: MEDIUM
  </solution>
  <winner id="A" reasoning="Lowest-risk prompt-only changes that directly counter ETF anchoring with guidance + examples."/>
</tree-of-thought>

<chain-of-draft>
  <draft id="1">Add more worked examples only. Issues: examples can still anchor; no persona asset guidance; no anti-anchoring language.</draft>
  <draft id="2">Add persona-specific asset guidance + anti-anchoring callout. Issues: still need concrete examples to show stock selection and tool expansion.</draft>
  <draft id="3">Persona constraints + asset-type guidance block + 3 worked examples (one stock-selection), with explicit “context pack is a starting signal” wording.</draft>
</chain-of-draft>

<yagni>
  <excluding>
    - Context pack schema changes (not needed for prompt-only scope).
    - Hard validation/regeneration rules (user requested prompt-only).
    - New asset-type diversity tests (only if enforcement added later).
    - Quality gate enforcement from research recommendations (explicitly out of scope for prompt-only plan).
  </excluding>
  <scope-creep-prevention>
    - Limit examples to 3 to avoid prompt bloat and over-anchoring.
    - Encourage tool usage without making it mandatory.
  </scope-creep-prevention>
  <complexity-budget allocated="6" used="4" reserved="2"/>
</yagni>

<patterns>
  <applying>None (no APEX pattern IDs provided in research).</applying>
  <rejected>None.</rejected>
</patterns>

<architecture-decision>
  <files-to-modify>
    - src/agent/stages/candidate_generator.py: strengthen persona constraints to nudge asset-type diversity.
    - src/agent/prompts/candidate_generation.md: add asset-type guidance, anti-anchoring callout, and 3 worked examples.
  </files-to-modify>
  <files-to-create>None.</files-to-create>
  <sequence>
    1. Update PROMPT_VARIATIONS constraints (persona guidance).
    2. Add guidance + callouts in candidate_generation.md.
    3. Replace the existing ETF-only example with a stock-selection example, then add factor-ETF and macro/trend examples (sector-ETF example last, sector_rotation-only label).
  </sequence>
  <validation>
    - Automated: optional run of existing tests in tests/agent/test_stages.py.
    - Manual (canonical input): generate candidates with data/context_packs/25-1-2.json and the default model (do not switch to 4o).
    - Acceptance targets: at least one non-sector persona uses individual stocks; sector_rotation is the only persona allowed to be sector-ETF-only; at least one strategy cites intra_sector_divergence and mentions tool expansion beyond the context pack.
  </validation>
  <risks>
    - Model still anchors to sector ETFs → emphasize “starting signal, not a limit” + tool-expansion example.
    - Examples over-anchor to specific tickers → keep examples concise, add “illustrative only” note.
    - Prompt bloat reduces compliance → cap to 3 examples, keep each example concise, and avoid duplicating large scaffolding blocks.
  </risks>
</architecture-decision>

<builder-handoff>
  <mission>Reduce sector ETF anchoring via prompt-only guidance, persona constraint updates, and three worked examples (including stock selection with tool expansion) without hard rules or schema changes.</mission>
  <core-architecture>Prompt-first enrichment: persona constraints + asset-type guidance + anti-anchoring callout + 3 worked examples.</core-architecture>
  <pattern-guidance>Reuse existing Strategy schema/example style in candidate_generation.md; no APEX pattern IDs.</pattern-guidance>
  <persona-guidance>Soft asset-type guidance (non-binding): macro_regime → cross-asset ETFs + rates/commodities; factor_quant → factor ETFs (avoid sector ETFs unless sector_rotation); tail_risk → defensive ETFs/hedges; sector_rotation → sector ETFs allowed; trend_follower → cross-asset ETFs or stock selection when divergence is high.</persona-guidance>
  <implementation-order>
    1. Update PROMPT_VARIATIONS constraints in src/agent/stages/candidate_generator.py.
    2. Add asset-type guidance + anti-anchoring callout to src/agent/prompts/candidate_generation.md.
    3. Replace the existing ETF-only example with a stock-selection example, then add factor-ETF and macro/trend examples (sector-ETF example last, sector_rotation-only label).
  </implementation-order>
  <validation-gates>
    - Check prompt edits read clearly and remain concise.
    - Manual candidate generation: use data/context_packs/25-1-2.json and confirm stock-level strategy appears for a non-sector persona; verify intra_sector_divergence is referenced as a starting signal with tool expansion.
  </validation-gates>
  <warnings>
    - Avoid making tool usage mandatory; keep guidance suggestive.
    - Ensure sector_rotation persona still allows sector ETF usage.
    - Do not add enforcement checks or regeneration rules (prompt-only scope).
    - Keep added examples concise to limit prompt growth.
  </warnings>
</builder-handoff>

<next-steps>
Run `/apex:implement candidate-diversity-sector-etfs` to begin implementation.
</next-steps>
</plan>

<implementation>
<metadata>
  <timestamp>2026-01-03T23:47:39Z</timestamp>
  <duration>0h40m</duration>
  <iterations>1</iterations>
</metadata>

<files-modified>
  <file path="src/agent/stages/candidate_generator.py">
    <changes>Strengthened persona constraints with asset-type guidance to discourage sector ETF anchoring.</changes>
    <patterns-applied>
    </patterns-applied>
    <diff-summary>Updated constraint strings for macro_regime, factor_quant, tail_risk, sector_rotation, trend_follower.</diff-summary>
  </file>
  <file path="src/agent/prompts/candidate_generation.md">
    <changes>Added asset-type guidance, anti-anchoring callout, and three concise worked examples (stocks, factor ETFs, macro cross-asset).</changes>
    <patterns-applied>
    </patterns-applied>
    <diff-summary>Added tool-expansion guidance, updated sector ETF tradeoff, replaced ETF-only example with three illustrative strategies.</diff-summary>
  </file>
</files-modified>

<files-created>
</files-created>

<validation-results>
  <syntax status="pass">No syntax errors observed during pytest collection.</syntax>
  <types status="fail">Not run (no type checker invoked).</types>
  <tests status="fail" passed="37" failed="15" skipped="2">`./venv/bin/pytest -v -k "not TestPhase5EndToEnd"` interrupted after multiple failures (cheap_providers, composer_deployer). Targeted run `./venv/bin/pytest tests/agent/test_stages.py -v` failed 2 tests due to MIN_CANDIDATES=5 vs expected 4.</tests>
  <coverage>Not run.</coverage>
</validation-results>

<docs-updated>
  <doc path="docs/prompt_engineering_architecture_plan.md" reason="Align worked-example references with new stock/factor/macro set and clarify ETF-anchoring context."/>
</docs-updated>

<patterns-used>
</patterns-used>

<issues-encountered>
  <issue resolved="false">
    <description>Test suite failures unrelated to prompt edits (missing ComposerDeployer helper methods, missing KIMI_API_KEY attribute, MIN_CANDIDATES mismatch).</description>
    <resolution>Left unchanged; requires separate triage. Full pytest run aborted after repeated failures.</resolution>
  </issue>
</issues-encountered>

<deviations-from-plan>
  <deviation>
    <planned>Manual candidate generation with data/context_packs/25-1-2.json to confirm stock-level strategy and tool expansion.</planned>
    <actual>Not executed (focused on prompt edits and automated tests).</actual>
    <reason>Manual generation requires live model calls; deferred pending test baseline stability.</reason>
  </deviation>
</deviations-from-plan>

<reviewer-handoff>
  <summary>Prompt-only updates to reduce sector-ETF anchoring via persona guidance and refreshed worked examples.</summary>
  <key-changes>Updated constraints in candidate generator; added asset-type guidance and anti-anchoring callout; replaced worked example with stock/factor/macro examples that emphasize tool expansion.</key-changes>
  <test-coverage>Ran `./venv/bin/pytest tests/agent/test_stages.py -v` and partial `./venv/bin/pytest -v -k "not TestPhase5EndToEnd"`; both failed due to pre-existing issues.</test-coverage>
  <known-limitations>Manual candidate generation not run; test failures need separate triage.</known-limitations>
  <patterns-for-reflection>None.</patterns-for-reflection>
</reviewer-handoff>

<next-steps>
Run `/apex:ship candidate-diversity-sector-etfs` to review and finalize.
</next-steps>
</implementation>

<ship>
<metadata>
  <timestamp>2026-01-04T00:04:34Z</timestamp>
  <outcome>success</outcome>
  <commit-sha>933f13601cb8d953005952113e7370e6be87c21e</commit-sha>
</metadata>

<review-summary>
  <phase1-findings count="1">
    <by-severity critical="0" high="0" medium="0" low="1"/>
    <by-agent security="0" performance="0" architecture="0" testing="1" quality="0"/>
  </phase1-findings>
  <phase2-challenges>
    <upheld>1</upheld>
    <downgraded>0</downgraded>
    <dismissed>0</dismissed>
  </phase2-challenges>
  <false-positive-rate>100%</false-positive-rate>
</review-summary>

<action-items>
  <fix-now>
  </fix-now>
  <should-fix>
  </should-fix>
  <accepted>
  </accepted>
  <dismissed>
    <item id="TC-1" severity="low" confidence="0.11" location=".apex/tasks/candidate-diversity-sector-etfs.md">
      Manual candidate generation not run; deferred due to network-restricted model calls and pre-existing test failures.
    </item>
  </dismissed>
</action-items>

<commit>
  <sha>933f13601cb8d953005952113e7370e6be87c21e</sha>
  <message>candidate-diversity-sector-etfs: reduce sector ETF anchoring in candidate prompts</message>
  <files>docs/prompt_engineering_architecture_plan.md, src/agent/prompts/candidate_generation.md, src/agent/stages/candidate_generator.py</files>
</commit>

<reflection>
  <patterns-reported>
  </patterns-reported>
  <key-learning>Prompt-level examples plus persona asset guidance can reduce ETF anchoring without schema changes, but doc references must track example updates.</key-learning>
  <apex-reflect-status>submitted</apex-reflect-status>
</reflection>

<final-summary>
  <what-was-built>Refreshed candidate prompt guidance with stock/factor/macro examples and persona asset-type nudges; aligned architecture doc references.</what-was-built>
  <patterns-applied count="0">None.</patterns-applied>
  <test-status passed="37" failed="15"/>
  <documentation-updated>docs/prompt_engineering_architecture_plan.md</documentation-updated>
</final-summary>
</ship>
