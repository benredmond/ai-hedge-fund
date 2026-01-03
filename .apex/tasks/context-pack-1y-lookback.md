---
id: 6euFzYsFtjMSd_pXw32j7
identifier: context-pack-1y-lookback
title: Context pack generator: use 1y lookback instead of YTD
created: 2026-01-03T00:00:33Z
updated: 2026-01-03T01:24:28Z
phase: complete
status: complete
---

# Context pack generator: use 1y lookback instead of YTD

<research>
<metadata>
  <timestamp>2026-01-03T00:19:53Z</timestamp>
  <agents-deployed>4</agents-deployed>
  <files-analyzed>7</files-analyzed>
  <confidence>7.0</confidence>
  <adequacy-score>0.7</adequacy-score>
  <ambiguities-resolved>2</ambiguities-resolved>
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
The benchmark performance generator currently calculates YTD returns by anchoring at January 1 and labels the output as "ytd". This is implemented in `fetch_benchmark_performance` and surfaced in the CLI summary as "YTD"; tests assert the presence of the `ytd` key. Early in a new year this can yield unstable or missing results, which is the breakage you called out.

Decision: replace the `ytd` key with `1y` across code, tests, CLI output, and docs, and compute the trailing lookback as 365 calendar days (anchor_date - timedelta(days=365)). This removes the year-boundary failure while keeping the period definition explicit.
</executive-summary>

<web-research>
  <official-docs>Network access restricted; no external docs fetched.</official-docs>
  <best-practices>Trailing 12-month windows avoid year-boundary discontinuities; schema labels should match computed periods.</best-practices>
  <security-concerns>None identified.</security-concerns>
  <gap-analysis>v2 spec and CLI label YTD; change to trailing 1y requires coordinated updates in code, tests, and docs.</gap-analysis>
</web-research>

<codebase-patterns>
  <primary-pattern location="src/market_context/fetchers.py:730">`fetch_benchmark_performance` calculates 30/60/90-day metrics via `calc_period_metrics` and computes YTD via a Jan 1 anchor.</primary-pattern>
  <conventions>Benchmark returns stored under `benchmark_performance[...]["returns"]` with keys `30d`, `60d`, `90d`, `ytd`; composite benchmarks iterate over `periods` list.</conventions>
  <reusable-snippets>`calc_period_metrics` in `src/market_context/fetchers.py` provides return/vol/sharpe/max drawdown for arbitrary periods.</reusable-snippets>
  <testing-patterns>`tests/market_context/test_fetchers.py` asserts the `ytd` key exists in benchmark returns.</testing-patterns>
  <inconsistencies>`docs/market_context_schema.md` still describes a v1.0 30d-only schema while implementation is v2.0 multi-period.</inconsistencies>
</codebase-patterns>

<apex-patterns>
  <pattern id="APEX.SYSTEM:PAT:AUTO:G3HIvD1-" trust="★☆☆☆☆" uses="0" success="0%">No relevant patterns for time-window return changes.</pattern>
  <anti-patterns>None identified.</anti-patterns>
</apex-patterns>

<documentation>
  <architecture-context>`docs/MARKET_CONTEXT_V2_SPEC.md` defines multi-period benchmark returns including YTD.</architecture-context>
  <past-decisions>YTD added with v2.0 expansion of benchmark performance.</past-decisions>
  <historical-learnings>Schema documentation lags implementation; any period change should update spec + CLI labels.</historical-learnings>
  <docs-to-update>`docs/MARKET_CONTEXT_V2_SPEC.md`, `docs/market_context_schema.md`, and any CLI output references to YTD.</docs-to-update>
</documentation>

<git-history>
  <similar-changes>403f500 (v2.0 expansion), 538f34c (leading indicators), 0aff114 (regime_tags removal), 5f1cfd7 (intra-sector divergence).</similar-changes>
  <evolution>Benchmark performance expanded to multi-period in v2.0; YTD introduced there.</evolution>
</git-history>

<risks>
  <risk probability="M" impact="M">Renaming the `ytd` key to `1y` could break downstream consumers/tests unless updated consistently.</risk>
  <risk probability="L" impact="M">Keeping the `ytd` label while using trailing 1y could confuse users unless clarified in CLI/docs.</risk>
</risks>

<recommendations>
  <solution id="A" name="Trailing 1y behind existing ytd key">
    <philosophy>Minimize schema breakage by reusing the existing key.</philosophy>
    <path>Compute 1y lookback using trailing 365 calendar days, keep `ytd` key, update comments/CLI label if desired.</path>
    <pros>Minimal code churn; avoids downstream breaking changes.</pros>
    <cons>Key name becomes semantically misleading unless renamed or clarified.</cons>
    <risk-level>Low</risk-level>
  </solution>
  <solution id="B" name="Rename to 1y across schema">
    <philosophy>Make schema semantics explicit and aligned with calculation.</philosophy>
    <path>Replace `ytd` with `1y` in fetchers, composite calculations, CLI output, tests, and docs; compute `1y` as trailing 365 calendar days (anchor_date - timedelta(days=365)).</path>
    <pros>Clear semantics; avoids misleading labels.</pros>
    <cons>Requires broader updates; potential downstream break.</cons>
    <risk-level>Medium</risk-level>
  </solution>
  <solution id="C" name="Configurable annual period">
    <philosophy>Allow flexible period definition for benchmarks.</philosophy>
    <path>Add parameter to `fetch_benchmark_performance` to toggle `ytd` vs trailing `1y`; default to trailing 365-day lookback; update CLI to pass default.</path>
    <pros>Backward compatibility and flexibility.</pros>
    <cons>More complexity for limited benefit if only one mode is needed.</cons>
    <risk-level>Medium</risk-level>
  </solution>
  <winner id="B" reasoning="User preference for explicit schema: rename to `1y` everywhere and define 365-day trailing window."/>
</recommendations>

<next-steps>
Run `/apex:plan context-pack-1y-lookback` to create architecture from these findings.
</next-steps>
</research>

<plan>
<metadata>
  <timestamp>2026-01-03T00:19:53Z</timestamp>
  <status>ready</status>
</metadata>

<architecture-decision>
  <summary>Replace benchmark YTD with trailing 1y (365 calendar days) and rename key from `ytd` to `1y`.</summary>
  <files-to-modify>
    <file path="src/market_context/fetchers.py">Update benchmark period calculation, keys, and composite period lists.</file>
    <file path="src/market_context/cli.py">Update benchmark table header and return key access to `1y`.</file>
    <file path="tests/market_context/test_fetchers.py">Update benchmark return expectations to include `1y` instead of `ytd`.</file>
    <file path="docs/MARKET_CONTEXT_V2_SPEC.md">Replace YTD references and example keys with `1y`.</file>
  </files-to-modify>
  <files-to-create />
  <risks>
    <risk>Renaming the `ytd` key is breaking for downstream consumers unless all references are updated.</risk>
  </risks>
</architecture-decision>

<patterns>
  <applying>None</applying>
</patterns>

<builder-handoff>
  <mission>Implement trailing 1y benchmark return with 365-day lookback and rename `ytd` to `1y` across code, tests, CLI, and docs.</mission>
  <core-architecture>
    - Compute `one_year_start = anchor_date - timedelta(days=365)`
    - Find nearest trading day within tolerance and derive `one_year_days = len(prices) - idx`
    - Use `calc_period_metrics(prices, one_year_days)` to compute return
    - Replace `ytd` keys with `1y` and update composite period lists/conditionals
  </core-architecture>
  <pattern-guidance>None</pattern-guidance>
  <implementation-order>
    1. Update `fetch_benchmark_performance` logic and docstrings in `src/market_context/fetchers.py`.
    2. Replace composite period lists and `ytd` conditionals in `src/market_context/fetchers.py`.
    3. Update CLI header and key access in `src/market_context/cli.py`.
    4. Update `tests/market_context/test_fetchers.py` to expect `1y`.
    5. Update `docs/MARKET_CONTEXT_V2_SPEC.md` to document `1y` instead of `ytd`.
  </implementation-order>
  <validation-gates>
    - python -m compileall src/market_context
    - pytest tests/market_context/test_fetchers.py::TestFetchBenchmarkPerformance -v (skip if network restricted)
  </validation-gates>
  <warnings>
    - Do not run TestPhase5EndToEnd.
    - Ensure all `ytd` references in benchmark performance are updated to `1y`.
  </warnings>
</builder-handoff>
</plan>

<implementation>
<metadata>
  <timestamp>2026-01-03T01:18:58Z</timestamp>
  <duration>~45m</duration>
  <iterations>2</iterations>
</metadata>

<files-modified>
  <file path="src/market_context/fetchers.py">
    <changes>Replace YTD benchmark return with trailing 1y (365-day) lookback and rename keys to `1y`.</changes>
    <patterns-applied />
    <diff-summary>Renamed ytd variables/keys, updated period lists, and adjusted docstrings/comments.</diff-summary>
  </file>
  <file path="src/market_context/cli.py">
    <changes>Display 1Y in benchmark table and read `1y` return key.</changes>
    <patterns-applied />
    <diff-summary>Updated header label and return lookup variable names.</diff-summary>
  </file>
  <file path="tests/market_context/test_fetchers.py">
    <changes>Expect `1y` return key instead of `ytd`.</changes>
    <patterns-applied />
    <diff-summary>Updated benchmark return assertions/comment.</diff-summary>
  </file>
  <file path="docs/MARKET_CONTEXT_V2_SPEC.md">
    <changes>Document `1y` benchmark period instead of YTD.</changes>
    <patterns-applied />
    <diff-summary>Replaced YTD references and example keys with `1y`.</diff-summary>
  </file>
</files-modified>

<files-created />

<validation-results>
  <syntax status="pass">python -m compileall src/market_context</syntax>
  <types status="pass">Not run (no type checker configured)</types>
  <tests status="pass" passed="35" failed="0" skipped="0">pytest tests/market_context/ -v (network-enabled); warnings: datetime.utcnow deprecation, invalid value in YoY calc.</tests>
  <coverage>Not run</coverage>
</validation-results>

<patterns-used />

<issues-encountered>
  <issue resolved="true">
    <description>Initial benchmark tests failed due to restricted network (yfinance DNS).</description>
    <resolution>Re-ran tests with network access; all passed.</resolution>
  </issue>
</issues-encountered>

<deviations-from-plan />

<reviewer-handoff>
  <summary>Benchmark performance now uses trailing 1y (365-day) returns and exposes them under `1y` across code, CLI, tests, and docs.</summary>
  <key-changes>Renamed `ytd` -> `1y` in fetchers and composites; updated CLI label and v2 spec; adjusted tests.</key-changes>
  <test-coverage>pytest tests/market_context/ -v (35 passed, 9 warnings).</test-coverage>
  <known-limitations>Warnings remain from existing datetime.utcnow deprecation and YoY calc runtime warnings.</known-limitations>
  <patterns-for-reflection>None</patterns-for-reflection>
</reviewer-handoff>

<next-steps>
Run `/apex:ship context-pack-1y-lookback` to review and finalize.
</next-steps>
</implementation>

<ship>
<metadata>
  <timestamp>2026-01-03T01:24:28Z</timestamp>
  <outcome>success</outcome>
  <commit-sha>4f7253e649ad444c557213bb8442daf19e59d220</commit-sha>
</metadata>

<review-summary>
  <phase1-findings count="0">
    <by-severity critical="0" high="0" medium="0" low="0"/>
    <by-agent security="0" performance="0" architecture="0" testing="0" quality="0"/>
  </phase1-findings>
  <phase2-challenges>
    <upheld>0</upheld>
    <downgraded>0</downgraded>
    <dismissed>0</dismissed>
  </phase2-challenges>
  <false-positive-rate>0%</false-positive-rate>
  <note>Automated review agents unavailable in this environment; manual review performed.</note>
</review-summary>

<action-items>
  <fix-now />
  <should-fix />
  <accepted />
  <dismissed />
</action-items>

<commit>
  <sha>4f7253e649ad444c557213bb8442daf19e59d220</sha>
  <message>fix(market-context): replace YTD with 1Y lookback period</message>
  <files>
  <file>docs/MARKET_CONTEXT_V2_SPEC.md</file>
  <file>src/market_context/cli.py</file>
  <file>src/market_context/fetchers.py</file>
  <file>tests/market_context/test_fetchers.py</file>
  </files>
</commit>

<reflection>
  <patterns-reported />
  <key-learning>Trailing 365-day benchmark windows avoid YTD edge cases; renaming period keys requires coordinated updates in fetchers, CLI, tests, and docs.</key-learning>
  <apex-reflect-status>submitted</apex-reflect-status>
</reflection>

<final-summary>
  <what-was-built>Benchmarks now expose trailing 1y returns (365-day lookback) under the `1y` key with updated CLI output, tests, and v2 spec.</what-was-built>
  <patterns-applied count="0"></patterns-applied>
  <test-status passed="35" failed="0"/>
  <documentation-updated>docs/MARKET_CONTEXT_V2_SPEC.md</documentation-updated>
</final-summary>
</ship>
