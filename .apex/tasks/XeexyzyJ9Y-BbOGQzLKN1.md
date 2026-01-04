---
id: XeexyzyJ9Y-BbOGQzLKN1
identifier: composer-deploy-exceptioninfo
title: Debug: Composer deploy failed with clojure.lang.ExceptionInfo (missing symphony_id)
created: 2026-01-04T05:33:41Z
updated: 2026-01-04T05:55:35Z
phase: implement
status: active
---

# Debug: Composer deploy failed with clojure.lang.ExceptionInfo (missing symphony_id)

<debug>
<metadata>
  <timestamp>2026-01-04T05:33:41Z</timestamp>
  <duration>~1h</duration>
  <hypotheses-tested>2</hypotheses-tested>
</metadata>

<reproduction>
  <reproducible>true</reproducible>
  <steps>1) set -a; source .env; set +a; 2) run ./venv/bin/python snippet calling _build_symphony_json with condition 'sectors_above_50d_ma_pct > 50 AND VIX_current < 18'; 3) call _call_composer_api and observe Composer response {'type': 'exception', 'class': 'clojure.lang.ExceptionInfo'}.</steps>
  <minimal-case>Ad-hoc shell snippet (not saved) invoking src/agent/stages/composer_deployer._build_symphony_json and _call_composer_api.</minimal-case>
</reproduction>

<investigation>
  <evidence>
    <error-message>Composer save_symphony returns {'type': 'exception', 'class': 'clojure.lang.ExceptionInfo'}; symphony_id missing.</error-message>
    <stack-trace>Composer response did not include a stack trace.</stack-trace>
    <related-commits>5b70dd3 (recent composer IF parsing changes), 4492205 (logic_tree builder added).</related-commits>
    <pattern-matches>APEX.SYSTEM:PAT:AUTO:ImFaZC3j (low trust, not directly applicable).</pattern-matches>
  </evidence>

  <hypotheses>
    <hypothesis id="1" status="confirmed">
      <title>Boolean AND/OR in logic_tree condition generates invalid Composer predicate</title>
      <evidence>_parse_condition splits on a single comparator; AND/OR leaves an invalid RHS string; Composer rejects the JSON.</evidence>
      <test-result>Repro with AND returns Composer ExceptionInfo; post-fix _build_symphony_json raises ValueError before API call.</test-result>
    </hypothesis>
    <hypothesis id="2" status="confirmed">
      <title>Non-ticker operands with underscores (e.g., sectors_above_50d_ma_pct) are mis-parsed as tickers</title>
      <evidence>Operand parsed as ticker because suffix match succeeds; Composer has no such asset/indicator.</evidence>
      <test-result>Added operand validation; unit test confirms unsupported format now raises ValueError.</test-result>
    </hypothesis>
  </hypotheses>
</investigation>

<root-cause>
  <description>Composer IF predicates only support a single comparison using supported ticker/indicator operands. The logic_tree condition included AND and context-pack variables, which _parse_condition previously accepted and passed through to Composer, causing an ExceptionInfo response and missing symphony_id.</description>
  <five-whys>Not used.</five-whys>
</root-cause>

<fix>
  <description>Hardened _parse_condition to reject boolean operators and unsupported operand formats before building the symphony JSON; added unit tests for these cases.</description>
  <files-modified>src/agent/stages/composer_deployer.py, tests/agent/test_composer_deployer.py</files-modified>
  <test-added>tests/agent/test_composer_deployer.py (new parse_condition error cases)</test-added>
</fix>

<reflection>
  <patterns-used>
    <pattern id="APEX.SYSTEM:PAT:AUTO:ImFaZC3j" outcome="failed">Pattern was unrelated to Composer predicate parsing.</pattern>
  </patterns-used>
  <learnings>
    <learning>Composer IF predicates accept only single comparisons; compound logic must be avoided or converted before deployment.</learning>
  </learnings>
  <prevention>Validate logic_tree conditions for Composer compatibility before deployment; reject AND/OR and unknown operand formats early.</prevention>
</reflection>
</debug>

<implementation>
<metadata>
  <timestamp>2026-01-04T05:55:35Z</timestamp>
  <summary>Enable nested logic_tree conditions, validate Composer-compatible conditions earlier, and add regression tests.</summary>
</metadata>

<files-modified>
  <file>src/agent/models.py</file>
  <file>src/agent/stages/composer_deployer.py</file>
  <file>src/agent/stages/candidate_generator.py</file>
  <file>src/agent/prompts/candidate_generation.md</file>
  <file>src/agent/prompts/system/candidate_generation_system.md</file>
  <file>tests/agent/test_models.py</file>
  <file>tests/agent/test_composer_deployer.py</file>
  <file>tests/agent/test_candidate_generation_integration.py</file>
  <file>tests/agent/test_threshold_hygiene.py</file>
</files-modified>

<tests>
  <test>./venv/bin/pytest tests/agent/test_models.py -k "nested_logic_tree"</test>
  <test>./venv/bin/pytest tests/agent/test_composer_deployer.py -k "boolean_operator or unknown_operand"</test>
  <test>./venv/bin/pytest tests/agent/test_composer_deployer.py -k "nested_condition_builds_nested_if"</test>
  <test>./venv/bin/pytest tests/agent/test_candidate_generation_integration.py -k "boolean_condition_requires_nested_logic_tree"</test>
</tests>

<notes>
  <item>Composer condition validation now rejects AND/OR and unsupported operands in candidate generation.</item>
  <item>Nested logic_tree conditions are supported and rendered as nested IF nodes in Composer.</item>
</notes>

<docs-updated>
  <doc path="(none)" reason="No documentation updates required for this change."/>
</docs-updated>
</implementation>
