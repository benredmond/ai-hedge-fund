---
id: HhzUU-szjGijHrwnEtkIe
identifier: model-support-2026-01-05
title: Model support research for upcoming workflow run
created: 2026-01-05T19:14:57Z
updated: 2026-01-05T20:09:57Z
phase: implement
status: active
---

# Model support research for upcoming workflow run

<research>
<metadata>
  <timestamp>2026-01-05T19:17:25.017803Z</timestamp>
  <agents-deployed>5</agents-deployed>
  <files-analyzed>11</files-analyzed>
  <confidence>8</confidence>
  <adequacy-score>0.82</adequacy-score>
  <ambiguities-resolved>0</ambiguities-resolved>
</metadata>

<context-pack-refs>
  <!-- Shorthand for downstream phases -->
  ctx.patterns = apex-patterns section
  ctx.impl = codebase-patterns section
  ctx.web = web-research section
  ctx.history = git-history section
  ctx.docs = documentation section (from documentation-researcher)
  ctx.risks = risks section
  ctx.exec = recommendations.winner section
</context-pack-refs>

<executive-summary>
Current model routing is centralized in `src/agent/strategy_creator.py` and expects `provider:model-name` strings. OpenAI is the default, with DeepSeek and Kimi routed through OpenAI-compatible endpoints by setting `OPENAI_BASE_URL` and swapping in `DEEPSEEK_API_KEY` / `KIMI_API_KEY`. Anthropic models should work as-is via `anthropic:` prefixes. The requested OpenAI GPT-5.2 “thinking” model and Claude Opus 4.5 are supported by pydantic-ai, but they need correct official model IDs. The current reasoning detection uses name heuristics (“thinking”/“reasoning”), which will not classify `gpt-5.2` as a reasoning model unless updated or overridden.

Gemini 3 Pro is not currently special-cased. Pydantic AI supports Gemini via `google-gla:` or `google-vertex:` providers and expects a `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) plus optional install extra. That implies at least a docs/env update (and possibly a small provider detection update in candidate generation). DeepSeek V3.2 maps cleanly to `deepseek-chat`, and Kimi K2 “thinking” maps to `kimi-k2-thinking` or `kimi-k2-thinking-turbo`; both should work through the existing OpenAI-compatible path, but the configured Kimi base URL should be verified against current Moonshot docs.
</executive-summary>

<web-research>
  <official-docs>
    OpenAI GPT-5.2 API model IDs and “thinking” behavior: https://openai.com/index/introducing-gpt-5-2-in-the-api and https://help.openai.com/en/articles/10362446-api-model-availability. Anthropic Claude Opus 4.5 API name and thinking controls: https://www.anthropic.com/news/claude-opus-4-5. Google Gemini 3 Pro preview model names and API key requirements: https://ai.google.dev/gemini-api/docs/models/gemini#gemini-3-pro-preview. DeepSeek API model list and base URL: https://api-docs.deepseek.com/quick_start/parameter_settings. Kimi K2 thinking model names: https://platform.moonshot.ai/blog/kimi-k2-thinking.
  </official-docs>
  <best-practices>
    Use provider-specific prefixes supported by pydantic-ai for Gemini (`google-gla:` / `google-vertex:`) and ensure optional extras are installed (`pydantic-ai[google]`) before running Gemini models. Pydantic AI documents Google provider and API key usage: https://ai.pydantic.dev/models/gemini/. For OpenAI-compatible providers, ensure base URLs and API keys are correctly set per run; avoid leaking `OPENAI_BASE_URL` across providers.
  </best-practices>
  <security-concerns>
    Ensure separate API keys for each provider are stored in env vars (not committed). Switching providers by mutating `OPENAI_BASE_URL` and `OPENAI_API_KEY` can accidentally route subsequent OpenAI runs to non-OpenAI endpoints if not reset. If multiple providers are used in one process, prefer explicit per-model client settings.
  </security-concerns>
  <gap-analysis>
    Requested names (“OpenAI 5.2 thinking”, “Gemini 3 Pro”, “Claude Opus 4.5”, “Kimi K2 thinking”, “DeepSeek v3.2”) do not match exact API model IDs used by providers. The repo does not document `GOOGLE_API_KEY` / Gemini setup, and reasoning detection logic does not classify `gpt-5.2` as reasoning by name. Kimi base URL in code is `https://api.moonshot.ai/v1` and should be verified against current Moonshot documentation (some docs reference `api.moonshot.cn/v1`).
  </gap-analysis>
</web-research>

<codebase-patterns>
  <primary-pattern location="src/agent/strategy_creator.py:355">Model routing is based on `provider:model` strings; DeepSeek/Kimi are detected when provider is `openai` and `model_name` starts with `deepseek` or `kimi`, then `OPENAI_API_KEY` and `OPENAI_BASE_URL` are rewritten for that run.</primary-pattern>
  <conventions>Model identifiers must include a prefix (validated in `create_agent`); default model comes from `DEFAULT_MODEL` env var; stage-specific `ModelSettings` are computed via `get_model_settings` using `is_reasoning_model` heuristics.</conventions>
  <reusable-snippets>Provider detection in `CandidateGenerator._detect_provider()` (src/agent/stages/candidate_generator.py:222) is the only place with provider-specific prompt tweaks; add “gemini” handling here if desired.</reusable-snippets>
  <testing-patterns>No dedicated tests for model routing/providers were found; existing tests focus on market context. Consider adding lightweight unit tests around `is_reasoning_model` and `create_agent` env handling if changes are made.</testing-patterns>
  <inconsistencies>Docs mention Kimi/DeepSeek usage via `openai:` prefixes, but pydantic-ai supports dedicated providers (`moonshotai`, `deepseek`). Env var naming in repo uses `KIMI_API_KEY` while pydantic-ai docs use `MOONSHOTAI_API_KEY`.</inconsistencies>
</codebase-patterns>

<apex-patterns>
  <pattern id="APEX.SYSTEM:PAT:AUTO:ImFaZC3j" trust="★☆☆☆☆" uses="1" success="N/A">Prompt inspection via mocked create_agent (low-trust auto pattern; not strongly applicable).</pattern>
  <anti-patterns>None identified from APEX patterns.</anti-patterns>
</apex-patterns>

<documentation>
  <architecture-context>CLAUDE.md / AGENTS.md describe LLM env vars and default model usage. docs/TOKEN_MANAGEMENT.md documents SUMMARIZATION_MODEL defaults.</architecture-context>
  <past-decisions>Docs indicate `openai:` prefixed model IDs and recommend DeepSeek/Kimi via OpenAI-compatible endpoints.</past-decisions>
  <historical-learnings>None specific to provider changes; most learnings are about token management and workflow structure.</historical-learnings>
  <docs-to-update>AGENTS.md and CLAUDE.md to add Gemini env vars and official model IDs; docs/TOKEN_MANAGEMENT.md if summarization model defaults change; docs/mcp_setup.md if model lists are updated.</docs-to-update>
</documentation>

<git-history>
  <similar-changes>Recent commits include increases to max_tokens for reasoning models and prompt changes (e.g., b48f94f5 “increase max_tokens for reasoning models in candidate generation”). No recent commits explicitly on provider routing.</similar-changes>
  <evolution>Model support is centralized in strategy_creator; reasoning-specific tuning appears in stage classes and token settings.</evolution>
</git-history>

<risks>
  <risk probability="M" impact="M">Incorrect model IDs (e.g., “openai 5.2 thinking”) can lead to API errors; verify official IDs before run.</risk>
  <risk probability="M" impact="M">`OPENAI_BASE_URL` persists after DeepSeek/Kimi runs; subsequent OpenAI runs in the same process may hit the wrong endpoint unless reset.</risk>
  <risk probability="L" impact="M">Gemini provider requires optional dependency and API key; missing either causes runtime failures.</risk>
</risks>

<recommendations>
  <solution id="A" name="Minimal-change config update">
    <philosophy>Use existing provider routing; only update model IDs and env vars.</philosophy>
    <path>Map each requested model to its official API ID; set required env vars; update docs; optionally add Gemini provider handling to prompt tweaks.</path>
    <pros>Fastest, least risk; no code changes required for DeepSeek/Kimi/Claude/OpenAI.</pros>
    <cons>Reasoning detection for GPT-5.2 remains heuristic; Gemini gets no special prompt tuning.</cons>
    <risk-level>Low</risk-level>
  </solution>
  <solution id="B" name="Small code tweak for reasoning & Gemini detection">
    <philosophy>Targeted updates to improve correctness for new models.</philosophy>
    <path>Extend `is_reasoning_model` to recognize GPT-5.2 (and DeepSeek reasoner if used); add “gemini/google” to provider detection; optionally reset `OPENAI_BASE_URL` when provider is openai and model_name is not OpenAI-compatible.</path>
    <pros>Better defaults, fewer surprises; still minimal changes.</pros>
    <cons>Requires code edits and basic tests.</cons>
    <risk-level>Low</risk-level>
  </solution>
  <solution id="C" name="Provider registry + explicit clients">
    <philosophy>Centralize provider config and avoid global env mutation.</philosophy>
    <path>Introduce a model registry mapping model IDs to provider, base_url, API key env var, and reasoning flags; pass through pydantic-ai model settings directly without mutating process-wide env vars.</path>
    <pros>Most robust for multi-provider workflows; prevents base_url bleed.</pros>
    <cons>Largest change; more testing required.</cons>
    <risk-level>Medium</risk-level>
  </solution>
  <winner id="B" reasoning="A small update yields the most practical safety: correct reasoning defaults for GPT-5.2, explicit Gemini detection, and optional base_url reset without a full refactor."/>
</recommendations>

<next-steps>
Run `/apex:plan model-support-2026-01-05` to create architecture from these findings.
</next-steps>
</research>


<plan>
<metadata>
  <timestamp>2026-01-05T19:56:40.020454Z</timestamp>
  <chosen-solution>B</chosen-solution>
  <complexity>3</complexity>
  <risk>LOW</risk>
</metadata>

<chain-of-thought>
chain_of_thought:
  current_state:
    what_exists:
      - src/agent/strategy_creator.py:33 uses name heuristics ("thinking"/"reasoning") to flag reasoning models
      - src/agent/stages/candidate_generator.py:222 detects provider for prompt tweaks; lacks Gemini
      - src/agent/strategy_creator.py:365 mutates OPENAI_BASE_URL for DeepSeek/Kimi without reset
    how_it_got_here:
      - git: b48f94f5 (reasoning max_tokens increases) indicates reasoning models are already special-cased
    dependencies:
      - pydantic-ai model naming conventions
      - environment variables (OPENAI_API_KEY, DEEPSEEK_API_KEY, KIMI_API_KEY)
  problem_decomposition:
    core_problem: "Update model handling so new providers are treated as reasoning by default and Gemini is detected, without breaking OpenAI routing."
    sub_problems:
      - Reasoning detection should default true with explicit non-reasoning allowlist
      - Provider detection should include Gemini for prompt guidance
      - Avoid OPENAI_BASE_URL bleed across runs
      - Document new model IDs and env vars
  hidden_complexity:
    - OPENAI_BASE_URL is process-wide and can persist across runs; need explicit reset
    - Some provider model IDs do not include "thinking" in their names
  success_criteria:
    automated:
      - No syntax errors in modified files
    manual:
      - Reasoning detection returns true for the five target model families
      - Gemini provider detection routes to provider "gemini"
      - OPENAI_BASE_URL resets when provider is real OpenAI
      - Docs list new env vars and model IDs
</chain-of-thought>

<tree-of-thought>
  <solution id="A">
    <approach>Minimal config-only update</approach>
    <description>Update docs and .env guidance only; keep heuristics as-is.</description>
    <implementation>Docs only.</implementation>
    <patterns_used>[]</patterns_used>
    <pros>Zero code risk; fast.</pros>
    <cons>Reasoning models misclassified; Gemini not detected for prompt tweaks; base_url bleed remains.</cons>
    <complexity>1</complexity>
    <risk>LOW</risk>
  </solution>
  <solution id="B">
    <approach>Small code tweaks + docs</approach>
    <description>Default to reasoning models, add explicit non-reasoning allowlist, add Gemini detection, reset OPENAI_BASE_URL when provider is OpenAI, update docs.</description>
    <implementation>Modify strategy_creator.py and candidate_generator.py; update AGENTS.md and CLAUDE.md.</implementation>
    <patterns_used>[]</patterns_used>
    <pros>Fixes reasoning defaults and Gemini handling with minimal change surface.</pros>
    <cons>Small behavior change could affect legacy non-reasoning models if allowlist incomplete.</cons>
    <complexity>3</complexity>
    <risk>LOW</risk>
  </solution>
  <solution id="C">
    <approach>Provider registry refactor</approach>
    <description>Centralize model registry and avoid global env mutation.</description>
    <implementation>Introduce registry module + refactor create_agent.</implementation>
    <patterns_used>[]</patterns_used>
    <pros>Most robust for multi-provider.</pros>
    <cons>Largest change, not needed for immediate goal.</cons>
    <complexity>6</complexity>
    <risk>MEDIUM</risk>
  </solution>
  <winner id="B" reasoning="Matches user preference for reasoning-by-default, Gemini detection, and base_url reset with minimal code changes."/>
</tree-of-thought>

<chain-of-draft>
  <draft id="1">Set explicit reasoning allowlist for the five target models. Concern: misses future reasoning models.</draft>
  <draft id="2">Switch to reasoning-by-default; add explicit non-reasoning allowlist. Concern: defining allowlist safely.</draft>
  <draft id="3">Implement reasoning-by-default with a small non-reasoning allowlist + explicit Gemini detection + OpenAI base_url reset. Keep docs updated to avoid surprises.</draft>
</chain-of-draft>

<yagni>
  <excluding>
    - feature: Full provider registry refactor
      why_not: Not needed for immediate run
      cost_if_included: Medium refactor and testing
      defer_until: Multiple providers in same long-running process cause issues
    - feature: Dedicated tests for all providers
      why_not: Low risk change, no existing test framework for LLM providers
      cost_if_included: Adds new test scaffolding
      defer_until: Next stability iteration
    - feature: Dynamic model capability discovery
      why_not: Requires API calls and extra dependencies
      cost_if_included: Medium
      defer_until: When provider catalog changes frequently
  </excluding>
  <scope-creep-prevention>
    - "Overhauling MCP config" : Not needed for this change
    - "Adding new env management library" : Keep env usage simple
  </scope-creep-prevention>
  <complexity-budget allocated="5" used="3" reserved="2"/>
</yagni>

<patterns>
  <applying>
    <pattern id="src/agent/strategy_creator.py:is_reasoning_model" trust_score="N/A" usage_stats="local" why_this_pattern="Central reasoning detection used by all stages" where_applying="src/agent/strategy_creator.py:33" source="ctx.impl"/>
    <pattern id="src/agent/stages/candidate_generator.py:_detect_provider" trust_score="N/A" usage_stats="local" why_this_pattern="Provider-specific prompt guidance" where_applying="src/agent/stages/candidate_generator.py:222" source="ctx.impl"/>
  </applying>
  <rejected></rejected>
</patterns>

<architecture-decision>
  <files-to-modify>
    <file path="src/agent/strategy_creator.py">
      <purpose>Reasoning-by-default logic + OpenAI base URL reset</purpose>
      <pattern>src/agent/strategy_creator.py:is_reasoning_model</pattern>
      <validation>Static inspection + lint-free</validation>
    </file>
    <file path="src/agent/stages/candidate_generator.py">
      <purpose>Add Gemini provider detection for prompt tweaks</purpose>
      <pattern>src/agent/stages/candidate_generator.py:_detect_provider</pattern>
      <validation>Static inspection + lint-free</validation>
    </file>
    <file path="AGENTS.md">
      <purpose>Document Gemini API key, google-gla prefix, new model IDs, reasoning default</purpose>
      <pattern>Documentation update</pattern>
      <validation>Manual review</validation>
    </file>
    <file path="CLAUDE.md">
      <purpose>Mirror AGENTS.md updates</purpose>
      <pattern>Documentation update</pattern>
      <validation>Manual review</validation>
    </file>
  </files-to-modify>
  <files-to-create></files-to-create>
  <sequence>
    1) Update reasoning detection + OPENAI_BASE_URL reset in strategy_creator.py
    2) Add Gemini detection in candidate_generator.py
    3) Update docs (AGENTS.md, CLAUDE.md)
  </sequence>
  <validation>
    <automated>None (skip heavy tests per instructions)</automated>
    <manual>Smoke read updated files</manual>
  </validation>
  <risks>
    <risk>Non-reasoning models might be misclassified; mitigate with explicit non-reasoning allowlist and doc note.</risk>
    <risk>Resetting OPENAI_BASE_URL could override custom setups; mitigate by only resetting for provider==openai and non-compat models.</risk>
  </risks>
</architecture-decision>

<builder-handoff>
  <mission>Implement reasoning-by-default detection, Gemini provider detection, and OpenAI base_url reset; update docs to include Gemini API key and new model IDs.</mission>
  <core-architecture>Solution B: minimal code tweaks and doc updates.</core-architecture>
  <pattern-guidance>Use existing `is_reasoning_model` and `_detect_provider` functions as modification points.</pattern-guidance>
  <implementation-order>
    1) Modify `is_reasoning_model` to return True by default; add explicit non-reasoning allowlist
    2) Add Gemini detection in `_detect_provider` (e.g., match "gemini"/"google")
    3) Reset OPENAI_BASE_URL for real OpenAI models (non-deepseek/kimi)
    4) Update AGENTS.md and CLAUDE.md with Gemini env vars + model ID examples + reasoning default note
  </implementation-order>
  <validation-gates>
    - No syntax errors in modified Python files
    - Doc content reflects new defaults and model names
  </validation-gates>
  <warnings>
    - Ensure allowlist doesn’t accidentally treat common legacy models as reasoning unless desired
    - Avoid altering model strings; only adjust detection logic and env reset
  </warnings>
</builder-handoff>

<next-steps>
Run `/apex:implement model-support-2026-01-05` to begin implementation.
</next-steps>
</plan>


<implementation>
<metadata>
  <timestamp>2026-01-05T20:09:57Z</timestamp>
  <duration>0.5h</duration>
  <iterations>1</iterations>
</metadata>

<files-modified>
  <file path="src/agent/strategy_creator.py">
    <changes>Defaulted reasoning detection to true with an explicit non-reasoning allowlist; reset OpenAI base URL for non-compatible models.</changes>
    <patterns-applied>
      <pattern id="src/agent/strategy_creator.py:is_reasoning_model">Updated reasoning detection to use allowlisted non-reasoning prefixes.</pattern>
    </patterns-applied>
    <diff-summary>Added reasoning allowlist and safe base URL reset for OpenAI providers.</diff-summary>
  </file>
  <file path="src/agent/stages/candidate_generator.py">
    <changes>Added Gemini provider detection and count enforcement guidance.</changes>
    <patterns-applied>
      <pattern id="src/agent/stages/candidate_generator.py:_detect_provider">Added Gemini/Google detection for provider-specific guidance.</pattern>
    </patterns-applied>
    <diff-summary>Extended provider detection and Gemini-specific count guidance.</diff-summary>
  </file>
  <file path="AGENTS.md">
    <changes>Documented Gemini API key, updated model ID examples, noted reasoning defaults.</changes>
    <patterns-applied>
      <pattern id="none">Documentation update only.</pattern>
    </patterns-applied>
    <diff-summary>Added Google API key and updated model examples for GPT-5.2, Opus 4.5, Gemini 3 Pro preview.</diff-summary>
  </file>
  <file path="CLAUDE.md">
    <changes>Mirrored AGENTS.md updates for Gemini and model IDs.</changes>
    <patterns-applied>
      <pattern id="none">Documentation update only.</pattern>
    </patterns-applied>
    <diff-summary>Synced environment variable and model ID guidance.</diff-summary>
  </file>
</files-modified>

<files-created>
</files-created>

<validation-results>
  <syntax status="pass">python -m py_compile src/agent/strategy_creator.py src/agent/stages/candidate_generator.py</syntax>
  <types status="pass">Not run (no type check configured; per plan).</types>
  <tests status="pass" passed="0" failed="0" skipped="0">Not run (per plan).</tests>
  <coverage>Not run.</coverage>
</validation-results>

<docs-updated>
  <doc path="CLAUDE.md" reason="Documented Gemini API key, updated model ID examples, and clarified reasoning defaults."/>
</docs-updated>

<patterns-used>
  <pattern id="src/agent/strategy_creator.py:is_reasoning_model" location="src/agent/strategy_creator.py:33" outcome="worked">
    Reasoning-by-default allowlist added for non-reasoning families.
  </pattern>
  <pattern id="src/agent/stages/candidate_generator.py:_detect_provider" location="src/agent/stages/candidate_generator.py:222" outcome="worked">
    Gemini provider detection added for prompt guidance.
  </pattern>
</patterns-used>

<issues-encountered>
</issues-encountered>

<deviations-from-plan>
</deviations-from-plan>

<reviewer-handoff>
  <summary>Updated reasoning detection and provider handling for new models; docs now include Gemini and current model IDs.</summary>
  <key-changes>Reasoning defaults to true with explicit allowlist; OpenAI base URL reset for non-compat models; Gemini detection and guidance; docs updated.</key-changes>
  <test-coverage>Syntax check only (py_compile); no unit/integration tests run.</test-coverage>
  <known-limitations>Reasoning allowlist may need expansion as new non-reasoning models are added; OPENAI_API_KEY still overwritten for DeepSeek/Kimi runs.</known-limitations>
  <patterns-for-reflection>src/agent/strategy_creator.py:is_reasoning_model, src/agent/stages/candidate_generator.py:_detect_provider</patterns-for-reflection>
</reviewer-handoff>

<next-steps>
Run `/apex:ship model-support-2026-01-05` to review and finalize.
</next-steps>
</implementation>

<ship>
<!-- Populated by /apex:ship -->
</ship>
