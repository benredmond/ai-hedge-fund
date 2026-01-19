---
id: Lj23wX9rPBaLESAd4H99Yw
identifier: together-kimi-k2-thinking-2026-01-18
title: Add Together Kimi K2 Thinking support (provider prefix)
created: 2026-01-18T15:10:46Z
updated: 2026-01-18T16:50:53Z
phase: plan
status: active
---

# Add Together Kimi K2 Thinking support (provider prefix)

<research>
<metadata>
  <timestamp>2026-01-18T15:10:46Z</timestamp>
  <agents-deployed>5</agents-deployed>
  <files-analyzed>7</files-analyzed>
  <confidence>8</confidence>
  <adequacy-score>0.81</adequacy-score>
  <ambiguities-resolved>1</ambiguities-resolved>
</metadata>

<context-pack-refs>
  <!-- Shorthand for downstream phases -->
  ctx.patterns = pattern-library section
  ctx.impl = codebase-patterns section
  ctx.web = web-research section
  ctx.history = git-history section
  ctx.docs = documentation section (from documentation-researcher)
  ctx.risks = risks section
  ctx.exec = recommendations.winner section
</context-pack-refs>

<executive-summary>
The codebase routes OpenAI-compatible providers by mutating OPENAI_API_KEY and OPENAI_BASE_URL inside create_agent based on model naming. DeepSeek and Kimi/Moonshot are handled under the openai: provider, and their support is gated by DEEPSEEK_API_KEY/KIMI_API_KEY checks. This is centralized in src/agent/strategy_creator.py and mirrored by CLI env validation and workflow auto-fallback model selection. Adding Together support for Kimi K2 Thinking should follow the same pattern: accept a new provider prefix (together:), swap in TOGETHER_API_KEY and Together’s base URL, then restore original OpenAI env values on exit.

Official Together docs confirm OpenAI compatibility via base_url https://api.together.xyz/v1 and a Together API key, and list moonshotai/Kimi-K2-Thinking as a serverless model with its own quickstart. This suggests routing via Together is feasible and the model string is correct, but the implementation should avoid bleeding OPENAI_BASE_URL across runs. Updates are needed in env validation, fallback model auto-selection, and documentation to reflect the new provider.
</executive-summary>

<web-research>
  <official-docs>
    Together OpenAI compatibility: requires TOGETHER_API_KEY and base_url https://api.together.xyz/v1 for OpenAI-compatible clients. https://docs.together.ai/docs/openai-api-compatibility
    Kimi K2 Thinking quickstart: model ID moonshotai/Kimi-K2-Thinking and reasoning/content split in responses. https://docs.together.ai/docs/kimi-k2-thinking-quickstart
    Together serverless models list includes moonshotai/Kimi-K2-Thinking. https://docs.together.ai/docs/inference-models
  </official-docs>
  <best-practices>
    Prefer OpenAI-compatible client configuration using a dedicated base URL and API key per provider to avoid accidental cross-routing; restore OPENAI_BASE_URL after provider-specific runs.
  </best-practices>
  <security-concerns>
    Mutating OPENAI_API_KEY/OPENAI_BASE_URL at runtime can leak provider configuration across later requests if not restored. TOGETHER_API_KEY must be stored in env and never logged.
  </security-concerns>
  <gap-analysis>
    The repo lacks Together provider handling: no TOGETHER_API_KEY in CLI validation, no Together fallback model in workflow, and docs only mention KIMI_API_KEY for Kimi/Moonshot. create_agent only supports Kimi via Moonshot’s API, not Together.
  </gap-analysis>
</web-research>

<codebase-patterns>
  <primary-pattern location="src/agent/strategy_creator.py:632">Provider routing for OpenAI-compatible services happens by swapping OPENAI_API_KEY and OPENAI_BASE_URL based on model name (DeepSeek/Kimi) and restoring after use.</primary-pattern>
  <conventions>Model identifiers must be provider:model; gemini is aliased to google-gla. Provider-specific fallbacks are built from env keys in src/agent/workflow.py. CLI enforces at least one provider key in src/agent/cli.py.</conventions>
  <reusable-snippets>Provider detection relies on substring matching (rate_limit.detect_provider in src/agent/rate_limit.py) which already detects "moonshot"/"kimi" in the full model string.</reusable-snippets>
  <testing-patterns>Integration tests call Kimi via Moonshot using KIMI_API_KEY (tests/agent/test_kimi_k2_integration.py). Cheap-provider tests validate Kimi create_agent success and missing-key errors (tests/agent/test_cheap_providers.py).</testing-patterns>
  <inconsistencies>Docs list Kimi under KIMI_API_KEY, while Together’s docs position Kimi K2 Thinking under Together with a different API key and base URL.</inconsistencies>
</codebase-patterns>

<pattern-library>
  <pattern id="PAT:LOCAL:OPENAI_COMPAT_ENV_SWITCH" confidence="★★★☆☆" uses="1" success="N/A">Switch OPENAI_API_KEY/OPENAI_BASE_URL per provider run, then restore (observed in DeepSeek/Kimi handling).</pattern>
  <anti-patterns>Hard-coding provider URLs without env override; leaving OPENAI_BASE_URL set across subsequent OpenAI runs.</anti-patterns>
</pattern-library>

<documentation>
  <architecture-context>CLAUDE.md and AGENTS.md document provider env vars and model IDs; src/agent/cli.py enforces required env vars.</architecture-context>
  <past-decisions>Model routing centralized in strategy_creator with env swapping for OpenAI-compatible providers (DeepSeek/Kimi).</past-decisions>
  <historical-learnings>No prior Together integration; recent commits focused on provider reasoning behavior and fallback handling.</historical-learnings>
  <docs-to-update>CLAUDE.md, AGENTS.md, and CLI help text to include TOGETHER_API_KEY and new together: model string examples.</docs-to-update>
</documentation>

<git-history>
  <similar-changes>Recent strategy_creator changes: 9b82d90 (DeepSeek tool-call reasoning), 5019c52 (Anthropic sampling params), cd6e287 (model routing defaults).</similar-changes>
  <evolution>Provider handling consolidated in strategy_creator with env swapping; workflow fallbacks assembled from env keys.</evolution>
</git-history>

<risks>
  <risk probability="M" impact="M">Together’s OpenAI compatibility relies on correct base_url and key handling; mistakes can misroute OpenAI traffic or fail tool calls. Mitigation: encapsulate Together routing and restore envs deterministically.</risk>
  <risk probability="L" impact="M">Kimi K2 Thinking streams reasoning/content; pydantic-ai may not surface reasoning fields uniformly. Mitigation: treat reasoning as optional; keep existing extraction logic tolerant.</risk>
</risks>

<recommendations>
  <solution id="A" name="Provider prefix + env swap">
    <philosophy>Minimal change aligned with existing DeepSeek/Kimi routing.</philosophy>
    <path>Add together: provider handling in create_agent; set OPENAI_API_KEY=TOGETHER_API_KEY and OPENAI_BASE_URL=https://api.together.xyz/v1; update CLI env validation, workflow fallback, docs, and add a lightweight test.</path>
    <pros>Smallest diff; consistent with existing OpenAI-compatible provider handling; low risk to unrelated flows.</pros>
    <cons>Relies on global env mutation and assumes Together OpenAI compatibility stays stable.</cons>
    <risk-level>Low</risk-level>
  </solution>
  <solution id="B" name="Dedicated Together provider object">
    <philosophy>Prefer explicit provider instances over global env mutation.</philosophy>
    <path>Create an OpenAIChatModel with a Together-configured provider (base_url + key), keep original model string for logging, bypass env mutation for Together only.</path>
    <pros>Isolation from global env; less risk of cross-routing.</pros>
    <cons>More code churn; diverges from existing DeepSeek/Kimi pattern.</cons>
    <risk-level>Medium</risk-level>
  </solution>
  <solution id="C" name="Generalize OpenAI-compatible providers">
    <philosophy>Unified config map for DeepSeek/Kimi/Together with a single routing path.</philosophy>
    <path>Introduce provider registry with base_url + env key mapping; refactor create_agent to use the registry for openai-compatible services.</path>
    <pros>Cleaner architecture; easier to add future providers.</pros>
    <cons>Higher scope; more refactor risk than requested.</cons>
    <risk-level>Medium</risk-level>
  </solution>
  <winner id="A" reasoning="Matches existing pattern, minimizes change surface, and satisfies provider prefix requirement."/>
</recommendations>

<task-contract version="1">
  <intent>Add support for model identifier together:moonshotai/Kimi-K2-Thinking using Together’s OpenAI-compatible API.</intent>
  <in-scope>Provider prefix handling in create_agent; TOGETHER_API_KEY + base URL wiring; CLI env validation; workflow fallback model inclusion; documentation updates; optional lightweight tests.</in-scope>
  <out-of-scope>Removing KIMI_API_KEY support; refactoring all OpenAI-compatible providers; changing model scoring logic.</out-of-scope>
  <acceptance-criteria>
    <criterion id="AC-1">Given TOGETHER_API_KEY is set, when create_agent is called with model together:moonshotai/Kimi-K2-Thinking, then the agent is created using Together’s base URL and no KIMI_API_KEY is required.</criterion>
    <criterion id="AC-2">CLI env validation accepts TOGETHER_API_KEY as a valid provider key and documentation lists the new provider/model string.</criterion>
    <criterion id="AC-3">Workflow fallback models include together:moonshotai/Kimi-K2-Thinking when TOGETHER_API_KEY is present (unless user-provided fallbacks override).</criterion>
  </acceptance-criteria>
  <non-functional>
    <performance>No meaningful regressions; keep existing timeouts and model settings.</performance>
    <security>Never log TOGETHER_API_KEY; ensure OPENAI_BASE_URL is restored after Together runs.</security>
    <compatibility>Maintain backward compatibility for OpenAI, Anthropic, Gemini, DeepSeek, and Kimi via Moonshot.</compatibility>
  </non-functional>
  <amendments>
    <!-- Append amendments in plan/implement/ship with explicit rationale and version bump -->
  </amendments>
</task-contract>

<next-steps>
Run `/apex:plan together-kimi-k2-thinking-2026-01-18` to create architecture from these findings.
</next-steps>
</research>

<plan>
<metadata>
  <timestamp>2026-01-18T16:50:53Z</timestamp>
  <chosen-solution>A</chosen-solution>
  <complexity>4</complexity>
  <risk>LOW</risk>
</metadata>

<contract-validation>
  <contract-version>1</contract-version>
  <status>aligned</status>
  <acceptance-criteria-coverage>
    <criterion id="AC-1">Add together: provider routing in create_agent with TOGETHER_API_KEY and Together base URL; keep KIMI_API_KEY path for openai:kimi-* unchanged.</criterion>
    <criterion id="AC-2">Update CLI env validation + docs (CLAUDE.md, AGENTS.md) to include TOGETHER_API_KEY and together:moonshotai/Kimi-K2-Thinking example.</criterion>
    <criterion id="AC-3">Add Together fallback in workflow when TOGETHER_API_KEY is present.</criterion>
  </acceptance-criteria-coverage>
  <out-of-scope-confirmation>No provider registry refactor, no redirection of openai:kimi-* to Together, no new CLI commands.</out-of-scope-confirmation>
  <amendments-made>
    <amendment version="1" reason="none"/>
  </amendments-made>
</contract-validation>

<design-rationale>
design_rationale:
  current_state:
    what_exists:
      - src/agent/strategy_creator.py:632 provider-specific env swap for DeepSeek/Kimi under openai:
      - src/agent/cli.py:41 provider key validation limited to OPENAI/ANTHROPIC/DEEPSEEK/KIMI
      - src/agent/workflow.py:65 auto-fallbacks keyed off GOOGLE/DEEPSEEK/KIMI/ANTHROPIC
    how_it_got_here: "Provider routing centralized in create_agent (commit cd6e287)."
    dependencies:
      - pydantic_ai Agent + OpenAI-compatible provider behavior
      - OPENAI_API_KEY/OPENAI_BASE_URL env swapping for OpenAI-compatible providers
  problem_decomposition:
    core_problem: "Accept together:moonshotai/Kimi-K2-Thinking and route it through Together's OpenAI-compatible endpoint with TOGETHER_API_KEY."
    sub_problems:
      - Ensure pydantic-ai can execute a together: model string (provider aliasing or explicit OpenAIChatModel)
      - Keep Moonshot/Kimi routing intact for openai:kimi-* (Option A)
      - Update validation, fallback selection, and docs to recognize TOGETHER_API_KEY
  hidden_complexity:
    - pydantic-ai does not recognize provider "together" by default, so the model passed to Agent must be an OpenAI-compatible model object
    - OPENAI_BASE_URL must be restored to prevent cross-provider leakage
    - Model name casing (moonshotai/Kimi-K2-Thinking) should be preserved
  success_criteria:
    automated:
      - ./venv/bin/pytest tests/agent/test_cheap_providers.py -k together
    manual:
      - With TOGETHER_API_KEY set, create_agent(model="together:moonshotai/Kimi-K2-Thinking", ...) succeeds
</design-rationale>

<tree-of-thought>
  <solution id="A">
    approach: "Provider prefix + env swap (minimal)"
    description: "Add together: provider handling in create_agent that swaps OPENAI_API_KEY/OPENAI_BASE_URL to Together, then uses OpenAIChatModel for the model_name. Update CLI/env validation, fallback list, and docs."
    implementation: "Modify src/agent/strategy_creator.py, src/agent/cli.py, src/agent/workflow.py, CLAUDE.md, AGENTS.md; add small provider test."
    patterns_used: "PAT:LOCAL:OPENAI_COMPAT_ENV_SWITCH (★★★☆☆)"
    pros: "Small diff; consistent with existing DeepSeek/Kimi path; low risk."
    cons: "Relies on env mutation; depends on Together OpenAI compatibility stability."
    complexity: 4
    risk: LOW
  </solution>
  <solution id="B">
    approach: "Dedicated Together provider object"
    description: "Create a Together-specific OpenAIChatModel instance without env mutation, passing base_url and key via provider configuration."
    implementation: "Add provider configuration path in strategy_creator; keep CLI/workflow/docs updates."
    patterns_used: "None available in ctx.patterns"
    pros: "Avoids global env mutation; cleaner isolation."
    cons: "More code churn; diverges from existing provider handling patterns."
    complexity: 6
    risk: MEDIUM
  </solution>
  <solution id="C">
    approach: "Provider registry refactor"
    description: "Introduce a registry mapping provider prefix -> base_url/env var, and refactor create_agent to use the registry for OpenAI-compatible services."
    implementation: "New registry module + refactor in strategy_creator + updates across workflow/cli/docs."
    patterns_used: "None available in ctx.patterns"
    pros: "Scalable for future providers."
    cons: "Out of scope; higher regression risk."
    complexity: 7
    risk: MEDIUM
  </solution>
  <winner id="A" reasoning="Meets requirements with minimal change and aligns with existing OpenAI-compatible env swap pattern."/>
</tree-of-thought>

<chain-of-draft>
  <draft id="1">"Add together: prefix and set OPENAI_BASE_URL, assume pydantic-ai will accept provider string." Issue: pydantic-ai likely rejects unknown provider.</draft>
  <draft id="2">"Map together: to openai: internally and keep env swap." Issue: loses original model identifier and may change logging/metadata.</draft>
  <draft id="3">"Keep together: for reasoning/metadata, but pass an explicit OpenAIChatModel to Agent; env swap restored after run." Final approach.</draft>
</chain-of-draft>

<yagni>
  <excluding>
    - feature: "Provider registry refactor"
      why_not: "Not required for single new provider"
      cost_if_included: "High scope, regression risk"
      defer_until: "Multiple new providers need onboarding"
    - feature: "Redirect openai:kimi-* to Together"
      why_not: "User chose Option A; maintain Moonshot path"
      cost_if_included: "Behavior change for existing users"
      defer_until: "Explicit user request"
    - feature: "New Together integration tests that hit the network"
      why_not: "Not necessary for config wiring; avoid external calls"
      cost_if_included: "Flaky CI and key management"
      defer_until: "Need to validate Together connectivity in CI"
  </excluding>
  <scope-creep-prevention>
    - "Do not change summarization model behavior or reasoning heuristics"
    - "Do not introduce new CLI commands"
  </scope-creep-prevention>
  <complexity-budget allocated="6" used="4" reserved="2"/>
</yagni>

<patterns>
  <applying>
    - pattern_id: PAT:LOCAL:OPENAI_COMPAT_ENV_SWITCH
      confidence_rating: ★★★☆☆
      usage_stats: "1 use, success N/A"
      why_this_pattern: "Matches existing DeepSeek/Kimi routing mechanism"
      where_applying: "src/agent/strategy_creator.py (together provider env swap)"
      source: ctx.patterns
  </applying>
  <rejected>None</rejected>
</patterns>

<architecture-decision>
  <files-to-modify>
    - path: src/agent/strategy_creator.py
      purpose: "Add Together base URL constant and provider routing for together:"
      pattern: PAT:LOCAL:OPENAI_COMPAT_ENV_SWITCH
      validation: "Unit test: together create_agent succeeds with TOGETHER_API_KEY"
    - path: src/agent/cli.py
      purpose: "Allow TOGETHER_API_KEY in env validation and update help text"
      pattern: none
      validation: "Manual: CLI no longer errors when only TOGETHER_API_KEY is set"
    - path: src/agent/workflow.py
      purpose: "Include together:moonshotai/Kimi-K2-Thinking in auto fallbacks"
      pattern: none
      validation: "Manual: fallback list includes Together when key set"
    - path: CLAUDE.md
      purpose: "Document TOGETHER_API_KEY + together: model example"
      pattern: none
      validation: "Doc review"
    - path: AGENTS.md
      purpose: "Mirror CLAUDE.md updates for env/model docs"
      pattern: none
      validation: "Doc review"
    - path: tests/agent/test_cheap_providers.py
      purpose: "Add together provider create_agent test (skip if TOGETHER_API_KEY missing)"
      pattern: none
      validation: "pytest -k together"
  </files-to-modify>
  <files-to-create>None</files-to-create>
  <sequence>
    1. Add Together routing in create_agent with env swap + OpenAIChatModel and restore env.
    2. Update CLI env validation and workflow fallbacks for TOGETHER_API_KEY.
    3. Update docs (CLAUDE.md, AGENTS.md) and add lightweight test.
    4. Run targeted tests.
  </sequence>
  <validation>
    <automated>./venv/bin/pytest tests/agent/test_cheap_providers.py -k together</automated>
    <manual>Run create_agent with together:moonshotai/Kimi-K2-Thinking and confirm no KIMI_API_KEY required.</manual>
  </validation>
  <risks>
    - risk: "pydantic-ai rejects together: provider string"
      mitigation: "Pass explicit OpenAIChatModel for Together"
      detection: "Unit test fails to create agent"
    - risk: "OPENAI_BASE_URL leakage across runs"
      mitigation: "Restore env on exit for Together branch"
      detection: "Unexpected base URL in subsequent OpenAI calls"
  </risks>
</architecture-decision>

<builder-handoff>
  <mission>Implement together: provider support for Kimi K2 Thinking via Together, without changing openai:kimi-* behavior.</mission>
  <core-architecture>Solution A: env swap + OpenAIChatModel for Together, plus CLI/workflow/docs updates.</core-architecture>
  <pattern-guidance>PAT:LOCAL:OPENAI_COMPAT_ENV_SWITCH in src/agent/strategy_creator.py.</pattern-guidance>
  <implementation-order>
    1. strategy_creator: Together routing + base URL constant + model_for_agent handling
    2. cli/workflow: env validation + fallback list
    3. docs + tests
  </implementation-order>
  <validation-gates>
    - pytest -k together
    - manual create_agent call with TOGETHER_API_KEY
  </validation-gates>
  <warnings>
    - Do not redirect openai:kimi-* to Together (Option A)
    - Do not run TestPhase5EndToEnd
  </warnings>
</builder-handoff>

<next-steps>
Run `/apex:implement together-kimi-k2-thinking-2026-01-18` to begin implementation.
</next-steps>
</plan>

<implementation>
<!-- Populated by /apex:implement -->
</implementation>

<ship>
<!-- Populated by /apex:ship -->
</ship>
