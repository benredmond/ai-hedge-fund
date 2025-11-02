import pytest
from datetime import datetime
from freezegun import freeze_time
from unittest.mock import Mock, patch
from src.market_context.assembler import assemble_market_context_pack


class TestAssembleMarketContextPack:
    """Test context pack assembler integration."""

    @freeze_time("2025-01-15 12:00:00")
    @patch('src.market_context.assembler.fetch_benchmark_performance')
    @patch('src.market_context.assembler.fetch_international_and_commodities')
    @patch('src.market_context.assembler.fetch_regime_snapshot')
    @patch('src.market_context.assembler.fetch_macro_indicators')
    @patch('src.market_context.assembler.fetch_recent_events')
    def test_returns_complete_structure(self, mock_events, mock_macro, mock_regime, mock_intl, mock_bench):
        """Returns complete context pack with all sections."""
        # Mock the fetcher responses
        mock_regime.return_value = {"trend": {"regime": "bull"}}
        mock_macro.return_value = {"interest_rates": {"fed_funds_rate": 5.25}}
        mock_intl.return_value = {}
        mock_events.return_value = [{"date": "2025-01-10", "headline": "Test"}]
        mock_bench.return_value = {"SPY": {"returns": {"30d": 2.5}}}

        result = assemble_market_context_pack(fred_api_key="test_key")

        assert "metadata" in result
        assert "regime_snapshot" in result
        assert "macro_indicators" in result
        assert "benchmark_performance" in result  # v2.0: renamed from benchmark_performance_30d
        assert "recent_events" in result
        assert "regime_tags" in result

    @freeze_time("2025-01-15 12:00:00")
    @patch('src.market_context.assembler.fetch_benchmark_performance')
    @patch('src.market_context.assembler.fetch_international_and_commodities')
    @patch('src.market_context.assembler.fetch_regime_snapshot')
    @patch('src.market_context.assembler.fetch_macro_indicators')
    @patch('src.market_context.assembler.fetch_recent_events')
    def test_metadata_correctness(self, mock_events, mock_macro, mock_regime, mock_intl, mock_bench):
        """Metadata includes anchor_date, generated_at, version."""
        mock_regime.return_value = {"trend": {"regime": "bull"}}
        mock_macro.return_value = {"interest_rates": {"fed_funds_rate": 5.25}}
        mock_intl.return_value = {}
        mock_events.return_value = []
        mock_bench.return_value = {}

        result = assemble_market_context_pack(fred_api_key="test_key")

        metadata = result["metadata"]
        assert "anchor_date" in metadata
        assert "data_cutoff" in metadata
        assert "generated_at" in metadata
        assert "version" in metadata

        # Anchor date should be current date
        assert metadata["anchor_date"].startswith("2025-01-15")
        # v2.0: version should be v2.0.0
        assert metadata["version"] == "v2.0.0"

    @freeze_time("2025-01-15 12:00:00")
    @patch('src.market_context.assembler.fetch_benchmark_performance')
    @patch('src.market_context.assembler.fetch_international_and_commodities')
    @patch('src.market_context.assembler.fetch_regime_snapshot')
    @patch('src.market_context.assembler.fetch_macro_indicators')
    @patch('src.market_context.assembler.fetch_recent_events')
    def test_regime_tags_generated(self, mock_events, mock_macro, mock_regime, mock_intl, mock_bench):
        """Generates regime tags for longitudinal analysis."""
        mock_regime.return_value = {
            "trend": {"regime": "bull", "SPY_vs_200d_ma": {"current": 5.87}},  # v2.0: time series
            "volatility": {"regime": "elevated", "VIX_current": {"current": 25.0}}
        }
        mock_macro.return_value = {
            "interest_rates": {"fed_funds_rate": {"current": 5.25}}  # v2.0: time series
        }
        mock_intl.return_value = {}
        mock_events.return_value = []
        mock_bench.return_value = {}

        result = assemble_market_context_pack(fred_api_key="test_key")

        tags = result["regime_tags"]
        assert isinstance(tags, list)
        assert len(tags) > 0

        # Should include trend tag
        assert any(tag in ["bull", "strong_bull", "bear", "strong_bear"] for tag in tags)

        # Should include volatility tag
        assert any("volatility" in tag for tag in tags)

    @freeze_time("2025-01-15 12:00:00")
    @patch('src.market_context.assembler.fetch_benchmark_performance')
    @patch('src.market_context.assembler.fetch_international_and_commodities')
    @patch('src.market_context.assembler.fetch_regime_snapshot')
    @patch('src.market_context.assembler.fetch_macro_indicators')
    @patch('src.market_context.assembler.fetch_recent_events')
    def test_calls_all_fetchers(self, mock_events, mock_macro, mock_regime, mock_intl, mock_bench):
        """Calls all data fetchers."""
        mock_regime.return_value = {"trend": {"regime": "bull"}}
        mock_macro.return_value = {"interest_rates": {"fed_funds_rate": 5.25}}
        mock_intl.return_value = {}
        mock_events.return_value = []
        mock_bench.return_value = {}

        assemble_market_context_pack(fred_api_key="test_key")

        mock_regime.assert_called_once()
        mock_macro.assert_called_once()
        mock_intl.assert_called_once()  # v2.0: new fetcher
        mock_events.assert_called_once_with(lookback_days=30)
        mock_bench.assert_called_once()  # v2.0: new fetcher
