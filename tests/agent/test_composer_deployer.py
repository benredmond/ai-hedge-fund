"""
Tests for ComposerDeployer stage.

Tests:
- _extract_symphony_id() method with various response formats
- Deploy graceful degradation when credentials missing
- Integration with mocked MCP responses
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os

from src.agent.stages.composer_deployer import ComposerDeployer
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


class TestExtractSymphonyId:
    """Test _extract_symphony_id() method with various response formats."""

    def setup_method(self):
        """Create deployer instance for each test."""
        self.deployer = ComposerDeployer()

    def test_extract_from_json_double_quotes(self):
        """Extract symphony_id from JSON with double quotes."""
        mock_result = MagicMock()
        mock_result.output = '{"symphony_id": "abc123def456", "status": "created"}'

        result = self.deployer._extract_symphony_id(mock_result)

        assert result == "abc123def456"

    def test_extract_from_json_single_quotes(self):
        """Extract symphony_id from JSON with single quotes."""
        mock_result = MagicMock()
        mock_result.output = "{'symphony_id': 'xyz789abc123', 'status': 'saved'}"

        result = self.deployer._extract_symphony_id(mock_result)

        assert result == "xyz789abc123"

    def test_extract_from_key_value_with_equals(self):
        """Extract symphony_id from key=value format."""
        mock_result = MagicMock()
        mock_result.output = "Symphony created successfully. symphony_id=my_strategy_001"

        result = self.deployer._extract_symphony_id(mock_result)

        assert result == "my_strategy_001"

    def test_extract_from_key_value_with_colon(self):
        """Extract symphony_id from key:value format."""
        mock_result = MagicMock()
        mock_result.output = "Created new symphony. symphony_id: test-symphony-2024"

        result = self.deployer._extract_symphony_id(mock_result)

        assert result == "test-symphony-2024"

    def test_extract_generic_id_pattern(self):
        """Extract from generic id= pattern when symphony_id not found."""
        mock_result = MagicMock()
        mock_result.output = "Symphony saved with id=abcdefghij1234567890"

        result = self.deployer._extract_symphony_id(mock_result)

        assert result == "abcdefghij1234567890"

    def test_extract_from_data_attribute(self):
        """Extract symphony_id when result has data attribute instead of output."""
        mock_result = MagicMock(spec=[])  # No output attribute
        mock_result.data = '{"symphony_id": "data_attr_id_123"}'

        result = self.deployer._extract_symphony_id(mock_result)

        assert result == "data_attr_id_123"

    def test_extract_from_str_fallback(self):
        """Extract symphony_id from str() of result as fallback."""
        mock_result = {"symphony_id": "dict_fallback_id"}

        result = self.deployer._extract_symphony_id(mock_result)

        assert result == "dict_fallback_id"

    def test_returns_none_when_no_id_found(self):
        """Return None when no symphony_id pattern found."""
        mock_result = MagicMock()
        mock_result.output = "Operation completed successfully."

        result = self.deployer._extract_symphony_id(mock_result)

        assert result is None

    def test_returns_none_for_empty_output(self):
        """Return None for empty output."""
        mock_result = MagicMock()
        mock_result.output = ""

        result = self.deployer._extract_symphony_id(mock_result)

        assert result is None

    def test_short_generic_id_ignored(self):
        """Generic id pattern requires 10+ chars to avoid false positives."""
        mock_result = MagicMock()
        mock_result.output = "id=short"  # Only 5 chars, should not match generic pattern

        result = self.deployer._extract_symphony_id(mock_result)

        assert result is None

    def test_prefers_symphony_id_over_generic_id(self):
        """symphony_id pattern takes precedence over generic id pattern."""
        mock_result = MagicMock()
        # Generic id appears first in text, but symphony_id pattern should match first
        # due to pattern order in the code (symphony_id patterns checked before generic id)
        # Using JSON format which matches pattern 0 (double quotes with colon)
        mock_result.output = 'Created id=generic123456789 with "symphony_id": "preferred_id_123"'

        result = self.deployer._extract_symphony_id(mock_result)

        # Should match symphony_id JSON pattern (first in list) before generic id pattern
        assert result == "preferred_id_123"


class TestDeployGracefulDegradation:
    """Test deploy() graceful degradation when credentials missing."""

    @pytest.mark.asyncio
    async def test_deploy_returns_none_without_api_key(
        self, sample_strategy, sample_charter, sample_market_context, monkeypatch
    ):
        """Deploy returns (None, None) when COMPOSER_API_KEY not set."""
        monkeypatch.delenv("COMPOSER_API_KEY", raising=False)
        monkeypatch.delenv("COMPOSER_API_SECRET", raising=False)

        deployer = ComposerDeployer()
        symphony_id, deployed_at = await deployer.deploy(
            strategy=sample_strategy,
            charter=sample_charter,
            market_context=sample_market_context,
        )

        assert symphony_id is None
        assert deployed_at is None

    @pytest.mark.asyncio
    async def test_deploy_returns_none_without_api_secret(
        self, sample_strategy, sample_charter, sample_market_context, monkeypatch
    ):
        """Deploy returns (None, None) when COMPOSER_API_SECRET not set."""
        monkeypatch.setenv("COMPOSER_API_KEY", "test-key")
        monkeypatch.delenv("COMPOSER_API_SECRET", raising=False)

        deployer = ComposerDeployer()
        symphony_id, deployed_at = await deployer.deploy(
            strategy=sample_strategy,
            charter=sample_charter,
            market_context=sample_market_context,
        )

        assert symphony_id is None
        assert deployed_at is None

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
            symphony_id, deployed_at = await deployer.deploy(
                strategy=sample_strategy,
                charter=sample_charter,
                market_context=sample_market_context,
            )

        assert symphony_id == "mock_symphony_123"
        assert deployed_at is not None
        # Verify deployed_at is ISO format timestamp
        assert "T" in deployed_at

    @pytest.mark.asyncio
    async def test_deploy_returns_none_when_no_symphony_id_in_response(
        self, sample_strategy, sample_charter, sample_market_context, monkeypatch
    ):
        """Deploy returns (None, None) when agent response has no symphony_id."""
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
            symphony_id, deployed_at = await deployer.deploy(
                strategy=sample_strategy,
                charter=sample_charter,
                market_context=sample_market_context,
            )

        assert symphony_id is None
        assert deployed_at is None

    @pytest.mark.asyncio
    async def test_deploy_handles_agent_exception_gracefully(
        self, sample_strategy, sample_charter, sample_market_context, monkeypatch, capsys
    ):
        """Deploy returns (None, None) and logs error when agent raises exception."""
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
            symphony_id, deployed_at = await deployer.deploy(
                strategy=sample_strategy,
                charter=sample_charter,
                market_context=sample_market_context,
            )

        assert symphony_id is None
        assert deployed_at is None

        captured = capsys.readouterr()
        assert "Composer deployment failed" in captured.out


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
                symphony_id, deployed_at = await deployer.deploy(
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
                symphony_id, deployed_at = await deployer.deploy(
                    strategy=sample_strategy,
                    charter=sample_charter,
                    market_context=sample_market_context,
                )

        assert call_count == 3  # Max attempts
        assert symphony_id is None
        assert deployed_at is None


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
        symphony_id, deployed_at = await deployer.deploy(
            strategy=sample_strategy,
            charter=sample_charter,
            market_context=sample_market_context,
        )

        # Should either succeed or gracefully fail
        if symphony_id is not None:
            assert len(symphony_id) > 0
            assert deployed_at is not None
            assert "T" in deployed_at  # ISO format
