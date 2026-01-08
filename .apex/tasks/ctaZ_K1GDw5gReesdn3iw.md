<debug>
<metadata>
  <timestamp>2026-01-08T02:45:15Z</timestamp>
  <duration>00:25</duration>
  <hypotheses-tested>1</hypotheses-tested>
</metadata>

<reproduction>
  <reproducible>true</reproducible>
  <steps>source .env && ./venv/bin/python - &lt;&lt;'PY'
from src.agent.stages.composer_deployer import _parse_condition
_parse_condition("VIXY_price &gt; VIXY_20d_MA")
PY</steps>
  <minimal-case>inline _parse_condition call</minimal-case>
</reproduction>

<investigation>
  <evidence>
    <error-message>ValueError Unsupported operand format: 'VIXY_20d_MA'. Use TICKER or TICKER_price / TICKER_200d_MA / TICKER_cumulative_return_Nd / TICKER_RSI_Nd / TICKER_EMA_Nd.</error-message>
    <stack-trace>n/a (direct ValueError from _parse_condition)</stack-trace>
    <related-commits>n/a</related-commits>
    <pattern-matches>none</pattern-matches>
  </evidence>

  <hypotheses>
    <hypothesis id="1" status="confirmed">
      <title>_parse_condition lacks support for generic TICKER_&lt;N&gt;d_MA</title>
      <evidence>Generated strategy uses VIXY_20d_MA; parser only recognizes 50d/200d MA.</evidence>
      <test-result>Reproduced ValueError; added regex for TICKER_&lt;N&gt;d_MA and test now passes.</test-result>
    </hypothesis>
    <hypothesis id="2" status="untested">
      <title>Candidate validation path allows unsupported operands through</title>
      <evidence>Syntax errors are non-blocking and may return original candidates.</evidence>
      <test-result>Not tested.</test-result>
    </hypothesis>
    <hypothesis id="3" status="untested">
      <title>Prompt guidance biases model toward 20d MA without parser support</title>
      <evidence>Strategy text mentions VIXY 20d MA.</evidence>
      <test-result>Not tested.</test-result>
    </hypothesis>
  </hypotheses>
</investigation>

<root-cause>
  <description>Composer deployer condition parser did not recognize generic moving-average operands like VIXY_20d_MA, but the generator/strategy used that format.</description>
  <five-whys>n/a</five-whys>
</root-cause>

<fix>
  <description>Add regex support for TICKER_&lt;N&gt;d_MA in _parse_condition and add regression test.</description>
  <files-modified>src/agent/stages/composer_deployer.py; tests/agent/test_composer_deployer.py</files-modified>
  <test-added>tests/agent/test_composer_deployer.py::TestParseCondition::test_20d_moving_average</test-added>
</fix>

<reflection>
  <patterns-used>
    <pattern id="none" outcome="n/a">No APEX patterns matched.</pattern>
  </patterns-used>
  <learnings>
    <learning>Keep condition parser formats aligned with generator outputs; add tests for new operand formats.</learning>
  </learnings>
  <prevention>Add regression tests for each supported operand format and update error messages when formats expand.</prevention>
</reflection>
</debug>
