"""
Tests for ComposerDeployer stage.

Tests:
- _parse_condition() parsing various condition string formats
- _build_if_structure() building Composer IF node trees
- _build_symphony_json() generating symphony JSON for static and conditional strategies
- _extract_symphony_data() method with various response formats
- Deploy graceful degradation when credentials missing
- Integration with mocked MCP responses
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os
import uuid

from src.agent.stages.composer_deployer import (
    ComposerDeployer,
    _parse_condition,
    _build_if_structure,
    _build_symphony_json,
    _get_exchange,
)
from src.agent.models import (
    Strategy,
    Charter,
    RebalanceFrequency,
    EdgeType,
    StrategyArchetype,
)


@pytest.fixture
def sample_strategy():
    """Create a minimal valid Strategy for testing."""
    return Strategy(
        name="Test Momentum Strategy",
        # thesis_document must be ≥200 chars when provided, or empty
        thesis_document=(
            "This is a momentum-based strategy focusing on tech sector leadership. "
            "The strategy exploits behavioral biases where investors underreact to "
            "positive earnings surprises and strong relative strength. By holding "
            "winners and cutting losers systematically, we capture the premium "
            "associated with continuation patterns in equity returns."
        ),
        rebalancing_rationale=(
            "Monthly rebalancing captures medium-term momentum while avoiding excessive "
            "transaction costs. Winners are held to let profits run, losers are cut to "
            "preserve capital. This frequency balances signal quality with execution costs."
        ),
        assets=["AAPL", "MSFT", "GOOGL"],
        weights={"AAPL": 0.4, "MSFT": 0.35, "GOOGL": 0.25},
        rebalance_frequency=RebalanceFrequency.MONTHLY,
        logic_tree={},
        edge_type=EdgeType.BEHAVIORAL,
        archetype=StrategyArchetype.MOMENTUM,
    )


@pytest.fixture
def sample_charter():
    """Create a minimal valid Charter for testing."""
    return Charter(
        market_thesis="Current market favors momentum strategies due to clear tech leadership.",
        strategy_selection="Momentum selected over mean reversion due to trending market regime.",
        expected_behavior="Expect 10-15% annualized returns with moderate drawdowns in trending markets.",
        failure_modes=[
            "Sudden regime shift to mean reversion market",
            "Tech sector rotation causing leadership change",
            "Black swan event triggering flight to safety",
        ],
        outlook_90d="Continued tech outperformance expected with moderate volatility.",
    )


@pytest.fixture
def sample_market_context():
    """Create minimal market context for testing."""
    return {
        "regime_snapshot": {
            "trend": "bull",
            "volatility_regime": "normal",
        },
        "macro_indicators": {
            "fed_funds_rate": 5.25,
        },
    }


class TestExtractSymphonyData:
    """Test _extract_symphony_data() method with various response formats."""

    def setup_method(self):
        """Create deployer instance for each test."""
        self.deployer = ComposerDeployer()

    def test_extract_from_json_double_quotes(self):
        """Extract symphony_id from JSON with double quotes."""
        mock_result = MagicMock()
        mock_result.output = '{"symphony_id": "abc123def456", "status": "created"}'

        symphony_id, description = self.deployer._extract_symphony_data(mock_result)

        assert symphony_id == "abc123def456"
        assert description is None  # No description in this response

    def test_extract_from_json_single_quotes(self):
        """Extract symphony_id from JSON with single quotes."""
        mock_result = MagicMock()
        mock_result.output = "{'symphony_id': 'xyz789abc123', 'status': 'saved'}"

        symphony_id, description = self.deployer._extract_symphony_data(mock_result)

        assert symphony_id == "xyz789abc123"
        assert description is None

    def test_extract_from_key_value_with_equals(self):
        """Extract symphony_id from key=value format."""
        mock_result = MagicMock()
        mock_result.output = "Symphony created successfully. symphony_id=my_strategy_001"

        symphony_id, description = self.deployer._extract_symphony_data(mock_result)

        assert symphony_id == "my_strategy_001"
        assert description is None

    def test_extract_from_key_value_with_colon(self):
        """Extract symphony_id from key:value format."""
        mock_result = MagicMock()
        mock_result.output = "Created new symphony. symphony_id: test-symphony-2024"

        symphony_id, description = self.deployer._extract_symphony_data(mock_result)

        assert symphony_id == "test-symphony-2024"
        assert description is None

    def test_extract_generic_id_pattern(self):
        """Extract from generic id= pattern when symphony_id not found."""
        mock_result = MagicMock()
        mock_result.output = "Symphony saved with id=abcdefghij1234567890"

        symphony_id, description = self.deployer._extract_symphony_data(mock_result)

        assert symphony_id == "abcdefghij1234567890"
        assert description is None

    def test_extract_from_data_attribute(self):
        """Extract symphony_id when result has data attribute instead of output."""
        mock_result = MagicMock(spec=[])  # No output attribute
        mock_result.data = '{"symphony_id": "data_attr_id_123"}'

        symphony_id, description = self.deployer._extract_symphony_data(mock_result)

        assert symphony_id == "data_attr_id_123"
        assert description is None

    def test_extract_from_str_fallback(self):
        """Extract symphony_id from str() of result as fallback."""
        mock_result = {"symphony_id": "dict_fallback_id"}

        symphony_id, description = self.deployer._extract_symphony_data(mock_result)

        assert symphony_id == "dict_fallback_id"
        assert description is None

    def test_returns_none_when_no_id_found(self):
        """Return None when no symphony_id pattern found."""
        mock_result = MagicMock()
        mock_result.output = "Operation completed successfully."

        symphony_id, description = self.deployer._extract_symphony_data(mock_result)

        assert symphony_id is None
        assert description is None

    def test_returns_none_for_empty_output(self):
        """Return None for empty output."""
        mock_result = MagicMock()
        mock_result.output = ""

        symphony_id, description = self.deployer._extract_symphony_data(mock_result)

        assert symphony_id is None
        assert description is None

    def test_short_generic_id_ignored(self):
        """Generic id pattern requires 10+ chars to avoid false positives."""
        mock_result = MagicMock()
        mock_result.output = "id=short"  # Only 5 chars, should not match generic pattern

        symphony_id, description = self.deployer._extract_symphony_data(mock_result)

        assert symphony_id is None
        assert description is None

    def test_prefers_symphony_id_over_generic_id(self):
        """symphony_id pattern takes precedence over generic id pattern."""
        mock_result = MagicMock()
        # Generic id appears first in text, but symphony_id pattern should match first
        # due to pattern order in the code (symphony_id patterns checked before generic id)
        # Using JSON format which matches pattern 0 (double quotes with colon)
        mock_result.output = 'Created id=generic123456789 with "symphony_id": "preferred_id_123"'

        symphony_id, description = self.deployer._extract_symphony_data(mock_result)

        # Should match symphony_id JSON pattern (first in list) before generic id pattern
        assert symphony_id == "preferred_id_123"
        assert description is None


class TestDeployGracefulDegradation:
    """Test deploy() graceful degradation when credentials missing."""

    @pytest.mark.asyncio
    async def test_deploy_returns_none_without_api_key(
        self, sample_strategy, sample_charter, sample_market_context, monkeypatch
    ):
        """Deploy returns (None, None, None) when COMPOSER_API_KEY not set."""
        monkeypatch.delenv("COMPOSER_API_KEY", raising=False)
        monkeypatch.delenv("COMPOSER_API_SECRET", raising=False)

        deployer = ComposerDeployer()
        symphony_id, deployed_at, strategy_summary = await deployer.deploy(
            strategy=sample_strategy,
            charter=sample_charter,
            market_context=sample_market_context,
        )

        assert symphony_id is None
        assert deployed_at is None
        assert strategy_summary is None

    @pytest.mark.asyncio
    async def test_deploy_returns_none_without_api_secret(
        self, sample_strategy, sample_charter, sample_market_context, monkeypatch
    ):
        """Deploy returns (None, None, None) when COMPOSER_API_SECRET not set."""
        monkeypatch.setenv("COMPOSER_API_KEY", "test-key")
        monkeypatch.delenv("COMPOSER_API_SECRET", raising=False)

        deployer = ComposerDeployer()
        symphony_id, deployed_at, strategy_summary = await deployer.deploy(
            strategy=sample_strategy,
            charter=sample_charter,
            market_context=sample_market_context,
        )

        assert symphony_id is None
        assert deployed_at is None
        assert strategy_summary is None

    @pytest.mark.asyncio
    async def test_deploy_prints_warning_without_credentials(
        self, sample_strategy, sample_charter, sample_market_context, monkeypatch, capsys
    ):
        """Deploy prints warning when credentials not set."""
        monkeypatch.delenv("COMPOSER_API_KEY", raising=False)
        monkeypatch.delenv("COMPOSER_API_SECRET", raising=False)

        deployer = ComposerDeployer()
        await deployer.deploy(
            strategy=sample_strategy,
            charter=sample_charter,
            market_context=sample_market_context,
        )

        captured = capsys.readouterr()
        assert "Composer deployment skipped" in captured.out


class TestBuildPrompts:
    """Test prompt building methods."""

    def setup_method(self):
        """Create deployer instance for each test."""
        self.deployer = ComposerDeployer()

    def test_build_system_prompt_loads_from_file(self):
        """System prompt loads from prompts/system/composer_deployment_system.md."""
        system_prompt = self.deployer._build_system_prompt()

        # Verify it loaded content (auto-injected tool docs make it long)
        assert len(system_prompt) > 1000

        # Verify it contains expected content
        assert "Composer" in system_prompt or "symphony" in system_prompt.lower()

    def test_build_deployment_prompt_includes_strategy(
        self, sample_strategy, sample_charter, sample_market_context
    ):
        """Deployment prompt includes full strategy details."""
        prompt = self.deployer._build_deployment_prompt(
            sample_strategy, sample_charter, sample_market_context
        )

        # Verify strategy name is included
        assert sample_strategy.name in prompt

        # Verify assets are included
        for asset in sample_strategy.assets:
            assert asset in prompt

        # Verify thesis_document is included (not truncated)
        assert sample_strategy.thesis_document in prompt

        # Verify rebalancing_rationale is included
        assert sample_strategy.rebalancing_rationale in prompt

    def test_build_deployment_prompt_includes_charter_context(
        self, sample_strategy, sample_charter, sample_market_context
    ):
        """Deployment prompt includes charter context."""
        prompt = self.deployer._build_deployment_prompt(
            sample_strategy, sample_charter, sample_market_context
        )

        # Charter context is truncated to 500 chars each
        assert sample_charter.market_thesis[:500] in prompt or "market_thesis" in prompt


class TestDeployWithMockedAgent:
    """Test deploy() with mocked agent responses."""

    @pytest.mark.asyncio
    async def test_deploy_extracts_symphony_id_from_agent_response(
        self, sample_strategy, sample_charter, sample_market_context, monkeypatch
    ):
        """Deploy extracts symphony_id from agent response."""
        # Set credentials
        monkeypatch.setenv("COMPOSER_API_KEY", "test-key")
        monkeypatch.setenv("COMPOSER_API_SECRET", "test-secret")

        # Create mock agent result
        mock_result = MagicMock()
        mock_result.output = '{"symphony_id": "mock_symphony_123", "status": "created"}'

        # Create mock agent
        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_result)

        # Create async context manager mock
        async def mock_agent_ctx(*args, **kwargs):
            class MockCtx:
                async def __aenter__(self):
                    return mock_agent

                async def __aexit__(self, *args):
                    pass

            return MockCtx()

        with patch(
            "src.agent.stages.composer_deployer.create_agent", side_effect=mock_agent_ctx
        ):
            deployer = ComposerDeployer()
            symphony_id, deployed_at, strategy_summary = await deployer.deploy(
                strategy=sample_strategy,
                charter=sample_charter,
                market_context=sample_market_context,
            )

        assert symphony_id == "mock_symphony_123"
        assert deployed_at is not None
        # Verify deployed_at is ISO format timestamp
        assert "T" in deployed_at
        # strategy_summary may be None if not extracted from tool call args
        # (this test uses simple output, not message parts with tool calls)

    @pytest.mark.asyncio
    async def test_deploy_returns_none_when_no_symphony_id_in_response(
        self, sample_strategy, sample_charter, sample_market_context, monkeypatch
    ):
        """Deploy returns (None, None, None) when agent response has no symphony_id."""
        monkeypatch.setenv("COMPOSER_API_KEY", "test-key")
        monkeypatch.setenv("COMPOSER_API_SECRET", "test-secret")

        # Create mock agent result without symphony_id
        mock_result = MagicMock()
        mock_result.output = "Operation completed but no symphony was created."

        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_result)

        async def mock_agent_ctx(*args, **kwargs):
            class MockCtx:
                async def __aenter__(self):
                    return mock_agent

                async def __aexit__(self, *args):
                    pass

            return MockCtx()

        with patch(
            "src.agent.stages.composer_deployer.create_agent", side_effect=mock_agent_ctx
        ):
            deployer = ComposerDeployer()
            symphony_id, deployed_at, strategy_summary = await deployer.deploy(
                strategy=sample_strategy,
                charter=sample_charter,
                market_context=sample_market_context,
            )

        assert symphony_id is None
        assert deployed_at is None
        assert strategy_summary is None

    @pytest.mark.asyncio
    async def test_deploy_handles_agent_exception_gracefully(
        self, sample_strategy, sample_charter, sample_market_context, monkeypatch, capsys
    ):
        """Deploy returns (None, None, None) and logs error when agent raises exception."""
        monkeypatch.setenv("COMPOSER_API_KEY", "test-key")
        monkeypatch.setenv("COMPOSER_API_SECRET", "test-secret")

        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(side_effect=Exception("API connection failed"))

        async def mock_agent_ctx(*args, **kwargs):
            class MockCtx:
                async def __aenter__(self):
                    return mock_agent

                async def __aexit__(self, *args):
                    pass

            return MockCtx()

        with patch(
            "src.agent.stages.composer_deployer.create_agent", side_effect=mock_agent_ctx
        ):
            deployer = ComposerDeployer()
            symphony_id, deployed_at, strategy_summary = await deployer.deploy(
                strategy=sample_strategy,
                charter=sample_charter,
                market_context=sample_market_context,
            )

        assert symphony_id is None
        assert deployed_at is None
        assert strategy_summary is None

        captured = capsys.readouterr()
        assert "[ERROR:ComposerDeployer] Deployment failed" in captured.out


class TestRetryBehavior:
    """Test retry behavior for rate limits and errors."""

    @pytest.mark.asyncio
    async def test_retries_on_rate_limit_error(
        self, sample_strategy, sample_charter, sample_market_context, monkeypatch
    ):
        """Deploy retries on rate limit errors with backoff."""
        monkeypatch.setenv("COMPOSER_API_KEY", "test-key")
        monkeypatch.setenv("COMPOSER_API_SECRET", "test-secret")

        # Track number of calls
        call_count = 0
        success_result = MagicMock()
        success_result.output = '{"symphony_id": "retry_success_123"}'

        async def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Rate limit exceeded (429)")
            return success_result

        mock_agent = AsyncMock()
        mock_agent.run = mock_run

        async def mock_agent_ctx(*args, **kwargs):
            class MockCtx:
                async def __aenter__(self):
                    return mock_agent

                async def __aexit__(self, *args):
                    pass

            return MockCtx()

        with patch(
            "src.agent.stages.composer_deployer.create_agent", side_effect=mock_agent_ctx
        ):
            with patch("asyncio.sleep", new_callable=AsyncMock):  # Skip actual sleep
                deployer = ComposerDeployer()
                symphony_id, deployed_at, strategy_summary = await deployer.deploy(
                    strategy=sample_strategy,
                    charter=sample_charter,
                    market_context=sample_market_context,
                )

        assert call_count == 3
        assert symphony_id == "retry_success_123"

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(
        self, sample_strategy, sample_charter, sample_market_context, monkeypatch, capsys
    ):
        """Deploy fails after max retries exceeded."""
        monkeypatch.setenv("COMPOSER_API_KEY", "test-key")
        monkeypatch.setenv("COMPOSER_API_SECRET", "test-secret")

        call_count = 0

        async def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent error")

        mock_agent = AsyncMock()
        mock_agent.run = mock_run

        async def mock_agent_ctx(*args, **kwargs):
            class MockCtx:
                async def __aenter__(self):
                    return mock_agent

                async def __aexit__(self, *args):
                    pass

            return MockCtx()

        with patch(
            "src.agent.stages.composer_deployer.create_agent", side_effect=mock_agent_ctx
        ):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                deployer = ComposerDeployer()
                symphony_id, deployed_at, strategy_summary = await deployer.deploy(
                    strategy=sample_strategy,
                    charter=sample_charter,
                    market_context=sample_market_context,
                )

        assert call_count == 3  # Max attempts
        assert symphony_id is None
        assert deployed_at is None
        assert strategy_summary is None


@pytest.mark.integration
class TestComposerDeployerIntegration:
    """Integration tests requiring live Composer endpoint."""

    @pytest.mark.asyncio
    async def test_live_deployment(
        self, sample_strategy, sample_charter, sample_market_context
    ):
        """
        Test actual deployment to Composer.

        Requires:
        - COMPOSER_API_KEY set in environment
        - COMPOSER_API_SECRET set in environment
        - Network access to https://mcp.composer.trade/mcp/
        """
        if not os.getenv("COMPOSER_API_KEY") or not os.getenv("COMPOSER_API_SECRET"):
            pytest.skip(
                "COMPOSER_API_KEY and COMPOSER_API_SECRET required for integration test"
            )

        deployer = ComposerDeployer()
        symphony_id, deployed_at, strategy_summary = await deployer.deploy(
            strategy=sample_strategy,
            charter=sample_charter,
            market_context=sample_market_context,
        )

        # Should either succeed or gracefully fail
        if symphony_id is not None:
            assert len(symphony_id) > 0
            assert deployed_at is not None
            assert "T" in deployed_at  # ISO format
            # strategy_summary may or may not be present depending on response


class TestParseCondition:
    """Test _parse_condition() with various condition string formats."""

    def test_simple_price_gt_number(self):
        """Parse 'VIXY_price > 35'."""
        result = _parse_condition("VIXY_price > 35")

        assert result["comparator"] == "gt"
        assert result["lhs-val"] == "VIXY"
        assert result["lhs-fn"] == "current-price"
        assert result["lhs-fn-params"] == {}
        assert result["rhs-val"] == 35
        assert result["rhs-fixed-value?"] is True
        assert result["rhs-fn"] is None

    def test_price_lt_number(self):
        """Parse 'SPY_price < 400'."""
        result = _parse_condition("SPY_price < 400")

        assert result["comparator"] == "lt"
        assert result["lhs-val"] == "SPY"
        assert result["lhs-fn"] == "current-price"
        assert result["rhs-val"] == 400
        assert result["rhs-fixed-value?"] is True

    def test_gte_comparator(self):
        """Parse 'VIX_price >= 20'."""
        result = _parse_condition("VIX_price >= 20")

        assert result["comparator"] == "gte"
        assert result["lhs-val"] == "VIX"
        assert result["rhs-val"] == 20

    def test_lte_comparator(self):
        """Parse 'SPY_price <= 500'."""
        result = _parse_condition("SPY_price <= 500")

        assert result["comparator"] == "lte"

    def test_eq_comparator(self):
        """Parse 'TEST == 100'."""
        result = _parse_condition("TEST == 100")

        assert result["comparator"] == "eq"

    def test_price_vs_moving_average(self):
        """Parse 'SPY_price > SPY_200d_MA'."""
        result = _parse_condition("SPY_price > SPY_200d_MA")

        assert result["comparator"] == "gt"
        assert result["lhs-val"] == "SPY"
        assert result["lhs-fn"] == "current-price"
        assert result["rhs-val"] == "SPY"
        assert result["rhs-fixed-value?"] is False
        assert result["rhs-fn"] == "moving-average-price"
        assert result["rhs-fn-params"] == {"window": 200}

    def test_50d_moving_average(self):
        """Parse 'QQQ_price < QQQ_50d_MA'."""
        result = _parse_condition("QQQ_price < QQQ_50d_MA")

        assert result["rhs-fn"] == "moving-average-price"
        assert result["rhs-fn-params"] == {"window": 50}

    def test_cumulative_return(self):
        """Parse 'SPY_cumulative_return_30d > 0.05'."""
        result = _parse_condition("SPY_cumulative_return_30d > 0.05")

        assert result["lhs-val"] == "SPY"
        assert result["lhs-fn"] == "cumulative-return"
        assert result["lhs-fn-params"] == {"window": 30}
        assert result["rhs-val"] == 0.05
        assert result["rhs-fixed-value?"] is True

    def test_rsi_indicator(self):
        """Parse 'SPY_RSI_14d > 70'."""
        result = _parse_condition("SPY_RSI_14d > 70")

        assert result["lhs-val"] == "SPY"
        assert result["lhs-fn"] == "relative-strength-index"
        assert result["lhs-fn-params"] == {"window": 14}
        assert result["rhs-val"] == 70

    def test_ema_indicator(self):
        """Parse 'SPY_EMA_21d > 450'."""
        result = _parse_condition("SPY_EMA_21d > 450")

        assert result["lhs-val"] == "SPY"
        assert result["lhs-fn"] == "exponential-moving-average-price"
        assert result["lhs-fn-params"] == {"window": 21}

    def test_float_rhs_value(self):
        """Parse condition with float value on RHS."""
        result = _parse_condition("SPY_cumulative_return_60d > 0.15")

        assert result["rhs-val"] == 0.15
        assert result["rhs-fixed-value?"] is True

    def test_negative_number(self):
        """Parse condition with negative number."""
        result = _parse_condition("SPY_cumulative_return_30d > -0.10")

        assert result["rhs-val"] == -0.10

    def test_whitespace_handling(self):
        """Parse condition with extra whitespace."""
        result = _parse_condition("  VIXY_price   >   35  ")

        assert result["lhs-val"] == "VIXY"
        assert result["rhs-val"] == 35

    def test_no_comparator_raises_error(self):
        """Raise ValueError when no comparator found."""
        with pytest.raises(ValueError, match="No comparator found"):
            _parse_condition("VIXY_price 35")

    def test_invalid_format_raises_error(self):
        """Raise ValueError for invalid format with multiple comparators."""
        with pytest.raises(ValueError, match="Invalid condition format"):
            _parse_condition("A > B > C")


class TestBuildIfStructure:
    """Test _build_if_structure() building Composer IF node trees."""

    def test_basic_if_structure(self):
        """Build IF structure from basic logic_tree."""
        logic_tree = {
            "condition": "VIXY_price > 35",
            "if_true": {
                "assets": ["BIL"],
                "weights": {"BIL": 1.0},
            },
            "if_false": {
                "assets": ["SPY", "QQQ"],
                "weights": {"SPY": 0.6, "QQQ": 0.4},
            },
        }

        result = _build_if_structure(logic_tree)

        # Check root IF node
        assert result["step"] == "if"
        assert result["weight"] is None
        assert "id" in result
        assert len(result["children"]) == 2

    def test_true_branch_structure(self):
        """Verify true branch has correct is-else-condition and condition fields."""
        logic_tree = {
            "condition": "VIXY_price > 35",
            "if_true": {"assets": ["BIL"], "weights": {"BIL": 1.0}},
            "if_false": {"assets": ["SPY"], "weights": {"SPY": 1.0}},
        }

        result = _build_if_structure(logic_tree)
        true_branch = result["children"][0]

        assert true_branch["step"] == "if-child"
        assert true_branch["is-else-condition?"] is False
        assert true_branch["comparator"] == "gt"
        assert true_branch["lhs-val"] == "VIXY"
        assert true_branch["lhs-fn"] == "current-price"
        assert true_branch["rhs-val"] == 35
        assert true_branch["rhs-fixed-value?"] is True

    def test_false_branch_structure(self):
        """Verify false branch has is-else-condition? = true."""
        logic_tree = {
            "condition": "VIXY_price > 35",
            "if_true": {"assets": ["BIL"], "weights": {"BIL": 1.0}},
            "if_false": {"assets": ["SPY"], "weights": {"SPY": 1.0}},
        }

        result = _build_if_structure(logic_tree)
        false_branch = result["children"][1]

        assert false_branch["step"] == "if-child"
        assert false_branch["is-else-condition?"] is True
        assert false_branch["weight"] is None

    def test_specified_weights_generates_wt_cash_specified(self):
        """wt-cash-specified used when weights sum to ~1.0."""
        logic_tree = {
            "condition": "SPY_price > SPY_200d_MA",
            "if_true": {
                "assets": ["SPY", "QQQ"],
                "weights": {"SPY": 0.6, "QQQ": 0.4},
            },
            "if_false": {
                "assets": ["BIL"],
                "weights": {"BIL": 1.0},
            },
        }

        result = _build_if_structure(logic_tree)
        true_branch = result["children"][0]
        weight_node = true_branch["children"][0]

        assert weight_node["step"] == "wt-cash-specified"
        assert len(weight_node["children"]) == 2

        # Check allocations
        spy_node = next(c for c in weight_node["children"] if c["ticker"] == "SPY")
        assert spy_node["allocation"] == 0.6

    def test_equal_weights_generates_wt_cash_equal(self):
        """wt-cash-equal used when no weights or weights don't sum to 1.0."""
        logic_tree = {
            "condition": "VIXY_price > 35",
            "if_true": {"assets": ["BIL"], "weights": {}},  # Empty weights
            "if_false": {"assets": ["SPY", "QQQ"], "weights": {}},
        }

        result = _build_if_structure(logic_tree)
        false_branch = result["children"][1]
        weight_node = false_branch["children"][0]

        assert weight_node["step"] == "wt-cash-equal"
        # No allocation field on children
        for child in weight_node["children"]:
            assert "allocation" not in child

    def test_asset_nodes_have_required_fields(self):
        """Asset nodes have step, id, ticker, exchange, name, weight."""
        logic_tree = {
            "condition": "AAPL_price > 200",
            "if_true": {"assets": ["AAPL"], "weights": {"AAPL": 1.0}},
            "if_false": {"assets": ["BIL"], "weights": {"BIL": 1.0}},
        }

        result = _build_if_structure(logic_tree)
        true_branch = result["children"][0]
        weight_node = true_branch["children"][0]
        asset = weight_node["children"][0]

        assert asset["step"] == "asset"
        assert "id" in asset
        assert asset["ticker"] == "AAPL"
        assert asset["exchange"] == "XNAS"  # AAPL is on NASDAQ
        assert asset["name"] == "AAPL"
        assert asset["weight"] is None

    def test_etf_exchange_mapping(self):
        """ETFs get ARCX exchange."""
        logic_tree = {
            "condition": "VIXY_price > 35",
            "if_true": {"assets": ["BIL"], "weights": {"BIL": 1.0}},
            "if_false": {"assets": ["SPY"], "weights": {"SPY": 1.0}},
        }

        result = _build_if_structure(logic_tree)
        true_branch = result["children"][0]
        weight_node = true_branch["children"][0]
        bil_asset = weight_node["children"][0]

        assert bil_asset["exchange"] == "ARCX"  # BIL is an ETF

    def test_all_nodes_have_uuid_ids(self):
        """All nodes have valid UUID format ids."""
        logic_tree = {
            "condition": "SPY_price > 400",
            "if_true": {"assets": ["SPY"], "weights": {"SPY": 1.0}},
            "if_false": {"assets": ["BIL"], "weights": {"BIL": 1.0}},
        }

        result = _build_if_structure(logic_tree)

        # Validate IF node id
        uuid.UUID(result["id"])

        # Validate all children recursively
        def check_ids(node):
            if "id" in node:
                uuid.UUID(node["id"])  # Raises if invalid
            for child in node.get("children", []):
                check_ids(child)

        check_ids(result)


class TestBuildSymphonyJson:
    """Test _build_symphony_json() for static and conditional strategies."""

    def test_static_strategy_uses_wt_cash_equal(self):
        """Static strategy (no logic_tree) uses wt-cash-equal."""
        result = _build_symphony_json(
            name="Test Strategy",
            description="A test strategy",
            tickers=["AAPL", "MSFT", "GOOGL"],
            rebalance="monthly",
            logic_tree=None,
        )

        symphony = result["symphony_score"]
        assert symphony["step"] == "root"
        assert symphony["name"] == "Test Strategy"
        assert len(symphony["children"]) == 1

        weight_node = symphony["children"][0]
        assert weight_node["step"] == "wt-cash-equal"
        assert len(weight_node["children"]) == 3

    def test_conditional_strategy_uses_if_structure(self):
        """Conditional strategy (with logic_tree) uses IF structure."""
        logic_tree = {
            "condition": "VIXY_price > 35",
            "if_true": {"assets": ["BIL"], "weights": {"BIL": 1.0}},
            "if_false": {"assets": ["SPY", "QQQ"], "weights": {"SPY": 0.6, "QQQ": 0.4}},
        }

        result = _build_symphony_json(
            name="Conditional Strategy",
            description="Risk-off when volatility high",
            tickers=["SPY", "QQQ", "BIL"],  # tickers ignored when logic_tree present
            rebalance="weekly",
            logic_tree=logic_tree,
        )

        symphony = result["symphony_score"]
        assert symphony["step"] == "root"
        assert symphony["rebalance"] == "weekly"
        assert len(symphony["children"]) == 1

        if_node = symphony["children"][0]
        assert if_node["step"] == "if"

    def test_empty_logic_tree_treated_as_static(self):
        """Empty dict logic_tree treated as static strategy."""
        result = _build_symphony_json(
            name="Test",
            description="Test",
            tickers=["SPY"],
            logic_tree={},
        )

        symphony = result["symphony_score"]
        weight_node = symphony["children"][0]
        assert weight_node["step"] == "wt-cash-equal"

    def test_incomplete_logic_tree_treated_as_static(self):
        """Logic tree missing required keys treated as static."""
        result = _build_symphony_json(
            name="Test",
            description="Test",
            tickers=["SPY"],
            logic_tree={"condition": "SPY > 400"},  # Missing if_true, if_false
        )

        symphony = result["symphony_score"]
        weight_node = symphony["children"][0]
        assert weight_node["step"] == "wt-cash-equal"

    def test_symphony_has_required_root_fields(self):
        """Symphony root has all required fields."""
        result = _build_symphony_json(
            name="My Strategy",
            description="Description here",
            tickers=["SPY"],
            rebalance="daily",
        )

        symphony = result["symphony_score"]
        assert "id" in symphony
        assert symphony["name"] == "My Strategy"
        assert symphony["description"] == "Description here"
        assert symphony["step"] == "root"
        assert symphony["weight"] is None
        assert symphony["rebalance"] == "daily"
        assert symphony["rebalance-corridor-width"] is None

    def test_output_includes_color_and_hashtag(self):
        """Output includes color and hashtag fields."""
        result = _build_symphony_json(
            name="Momentum Strategy",
            description="Test",
            tickers=["SPY"],
        )

        assert "color" in result
        assert result["color"].startswith("#")
        assert "hashtag" in result
        assert result["hashtag"].startswith("#")

    def test_hashtag_generated_from_name(self):
        """Hashtag is generated from first two words of name."""
        result = _build_symphony_json(
            name="Volatility Risk Off Strategy",
            description="Test",
            tickers=["SPY"],
        )

        assert result["hashtag"] == "#VolatilityRisk"

    def test_asset_class_is_equities(self):
        """Asset class is EQUITIES."""
        result = _build_symphony_json(
            name="Test",
            description="Test",
            tickers=["SPY"],
        )

        assert result["asset_class"] == "EQUITIES"


class TestGetExchange:
    """Test _get_exchange() ticker to exchange mapping."""

    def test_common_etfs_return_arcx(self):
        """Common ETFs return ARCX (NYSE Arca)."""
        etfs = ["SPY", "QQQ", "GLD", "TLT", "BIL", "VTI", "XLK", "XLE"]
        for etf in etfs:
            assert _get_exchange(etf) == "ARCX", f"{etf} should be ARCX"

    def test_volatility_etfs_return_arcx(self):
        """Volatility ETFs return ARCX."""
        vol_etfs = ["VIXY", "UVXY", "VXX"]
        for etf in vol_etfs:
            assert _get_exchange(etf) == "ARCX", f"{etf} should be ARCX"

    def test_nasdaq_stocks_return_xnas(self):
        """NASDAQ stocks return XNAS."""
        nasdaq = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]
        for stock in nasdaq:
            assert _get_exchange(stock) == "XNAS", f"{stock} should be XNAS"

    def test_unknown_stocks_return_xnys(self):
        """Unknown stocks default to XNYS (NYSE)."""
        nyse = ["JPM", "BAC", "WMT", "JNJ", "UNH"]
        for stock in nyse:
            assert _get_exchange(stock) == "XNYS", f"{stock} should default to XNYS"
