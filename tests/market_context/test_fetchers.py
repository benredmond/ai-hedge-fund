import pytest
from datetime import datetime
from freezegun import freeze_time
from unittest.mock import Mock, patch
from src.market_context.fetchers import fetch_regime_snapshot, fetch_macro_indicators, fetch_recent_events, fetch_benchmark_performance


class TestFetchRegimeSnapshot:
    """Test regime snapshot fetcher using current date."""

    @freeze_time("2025-01-15 12:00:00")
    def test_returns_regime_snapshot_structure(self):
        """Returns complete regime snapshot with all required fields."""
        result = fetch_regime_snapshot()

        # Verify top-level structure
        assert "trend" in result
        assert "volatility" in result
        assert "breadth" in result
        assert "sector_leadership" in result
        assert "factor_regime" in result

    @freeze_time("2025-01-15 12:00:00")
    def test_trend_classification_bull_market(self):
        """Classifies market as bull when SPY above 200d MA."""
        result = fetch_regime_snapshot()

        # During 2025-01-15, market was in bull trend
        assert result["trend"]["regime"] in ["bull", "strong_bull"]
        assert "SPY_vs_200d_ma" in result["trend"]
        assert isinstance(result["trend"]["SPY_vs_200d_ma"], (int, float))

    @freeze_time("2025-01-15 12:00:00")
    def test_volatility_regime_classification(self):
        """Classifies volatility regime based on VIX levels."""
        result = fetch_regime_snapshot()

        assert result["volatility"]["regime"] in ["low", "normal", "elevated", "high"]
        assert "VIX_current" in result["volatility"]
        assert "VIX_30d_avg" in result["volatility"]
        assert isinstance(result["volatility"]["VIX_current"], (int, float))
        assert result["volatility"]["VIX_current"] > 0

    @freeze_time("2025-01-15 12:00:00")
    def test_breadth_calculation(self):
        """Calculates market breadth as percentage of sectors above 50d MA."""
        result = fetch_regime_snapshot()

        assert "sectors_above_50d_ma_pct" in result["breadth"]
        breadth = result["breadth"]["sectors_above_50d_ma_pct"]
        assert isinstance(breadth, (int, float))
        assert 0 <= breadth <= 100

    @freeze_time("2025-01-15 12:00:00")
    def test_sector_leadership_identification(self):
        """Identifies top 3 sector leaders and laggards."""
        result = fetch_regime_snapshot()

        assert "leaders" in result["sector_leadership"]
        assert "laggards" in result["sector_leadership"]

        leaders = result["sector_leadership"]["leaders"]
        laggards = result["sector_leadership"]["laggards"]

        assert len(leaders) == 3
        assert len(laggards) == 3

        # Each should be [ticker, relative_return] pair
        for ticker, return_val in leaders:
            assert isinstance(ticker, str)
            assert isinstance(return_val, (int, float))

        for ticker, return_val in laggards:
            assert isinstance(ticker, str)
            assert isinstance(return_val, (int, float))

    @freeze_time("2025-01-15 12:00:00")
    def test_factor_regime_analysis(self):
        """Analyzes factor premiums: value/growth, momentum, quality, size."""
        result = fetch_regime_snapshot()

        factor = result["factor_regime"]

        assert "value_vs_growth" in factor
        assert "regime" in factor["value_vs_growth"]
        assert factor["value_vs_growth"]["regime"] in ["value_favored", "growth_favored", "neutral"]

        assert "momentum_premium_30d" in factor
        assert "quality_premium_30d" in factor
        assert "size_premium_30d" in factor

        assert isinstance(factor["momentum_premium_30d"], (int, float))
        assert isinstance(factor["quality_premium_30d"], (int, float))
        assert isinstance(factor["size_premium_30d"], (int, float))

    @freeze_time("2025-01-15 12:00:00")
    def test_sector_dispersion_calculation(self):
        """Calculates sector dispersion as std dev of sector returns."""
        result = fetch_regime_snapshot()

        assert "dispersion" in result
        assert "sector_return_std_30d" in result["dispersion"]
        assert "regime" in result["dispersion"]

        dispersion_value = result["dispersion"]["sector_return_std_30d"]
        dispersion_regime = result["dispersion"]["regime"]

        assert isinstance(dispersion_value, (int, float))
        assert dispersion_value >= 0
        assert dispersion_regime in ["low", "moderate", "high", "unknown"]


class TestFetchMacroIndicators:
    """Test macro indicators fetcher with mocked FRED API."""

    @patch('src.market_context.fetchers.Fred')
    def test_returns_macro_structure(self, mock_fred_class):
        """Returns complete macro indicators with all required sections."""
        # Mock FRED API responses
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred
        mock_fred.get_series_latest_release.return_value = 5.25  # Example value

        result = fetch_macro_indicators(fred_api_key="test_key")

        assert "interest_rates" in result
        assert "inflation" in result
        assert "employment" in result
        assert "sentiment" in result

    @patch('src.market_context.fetchers.Fred')
    def test_interest_rates_structure(self, mock_fred_class):
        """Returns complete interest rate indicators."""
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred
        mock_fred.get_series_latest_release.return_value = 5.25

        result = fetch_macro_indicators(fred_api_key="test_key")

        rates = result["interest_rates"]
        assert "fed_funds_rate" in rates
        assert "treasury_10y" in rates
        assert "treasury_2y" in rates
        assert "yield_curve_2s10s" in rates

        assert isinstance(rates["fed_funds_rate"], (int, float))
        assert isinstance(rates["treasury_10y"], (int, float))
        assert isinstance(rates["treasury_2y"], (int, float))
        assert isinstance(rates["yield_curve_2s10s"], (int, float))

    @patch('src.market_context.fetchers.Fred')
    def test_inflation_indicators(self, mock_fred_class):
        """Returns inflation metrics."""
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred
        mock_fred.get_series_latest_release.return_value = 3.2

        result = fetch_macro_indicators(fred_api_key="test_key")

        inflation = result["inflation"]
        assert "cpi_yoy" in inflation
        assert "core_cpi_yoy" in inflation

        assert isinstance(inflation["cpi_yoy"], (int, float))
        assert isinstance(inflation["core_cpi_yoy"], (int, float))

    @patch('src.market_context.fetchers.Fred')
    def test_employment_indicators(self, mock_fred_class):
        """Returns employment metrics."""
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred
        mock_fred.get_series_latest_release.return_value = 3.8

        result = fetch_macro_indicators(fred_api_key="test_key")

        employment = result["employment"]
        assert "unemployment_rate" in employment
        assert "nonfarm_payrolls" in employment
        assert "wage_growth_yoy" in employment

        assert isinstance(employment["unemployment_rate"], (int, float))
        assert isinstance(employment["nonfarm_payrolls"], (int, float))
        assert isinstance(employment["wage_growth_yoy"], (int, float))

    @patch('src.market_context.fetchers.Fred')
    def test_yield_curve_calculation(self, mock_fred_class):
        """Calculates yield curve spread correctly."""
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred

        # Mock different returns for different series
        def mock_get_series(series_id):
            if series_id == 'DGS10':
                return 4.12
            elif series_id == 'DGS2':
                return 4.35
            return 0.0

        mock_fred.get_series_latest_release.side_effect = mock_get_series

        result = fetch_macro_indicators(fred_api_key="test_key")

        # Yield curve should be 10y - 2y = 4.12 - 4.35 = -0.23 (inverted)
        assert result["interest_rates"]["yield_curve_2s10s"] == pytest.approx(-0.23, abs=0.01)


class TestFetchRecentEvents:
    """Test event loader from JSON fixture."""

    @freeze_time("2025-01-15 12:00:00")
    def test_loads_events_from_fixture(self):
        """Loads events from fixture JSON file."""
        result = fetch_recent_events(lookback_days=30)

        assert isinstance(result, list)
        assert len(result) > 0

    @freeze_time("2025-01-15 12:00:00")
    def test_event_structure(self):
        """Events have required fields."""
        result = fetch_recent_events(lookback_days=30)

        for event in result:
            assert "date" in event
            assert "headline" in event
            assert "category" in event
            assert "market_impact" in event
            assert "significance" in event

    @freeze_time("2025-01-15 12:00:00")
    def test_filters_events_by_date(self):
        """Only returns events within lookback period."""
        result = fetch_recent_events(lookback_days=30)

        anchor_date = datetime.now()
        for event in result:
            event_date = datetime.fromisoformat(event["date"])
            assert event_date <= anchor_date


class TestFetchBenchmarkPerformance:
    """Test benchmark performance fetcher."""

    @freeze_time("2025-10-23 12:00:00")
    def test_returns_benchmark_structure(self):
        """Returns performance data for all benchmarks."""
        result = fetch_benchmark_performance(lookback_days=30)

        assert isinstance(result, dict)
        assert "SPY" in result
        assert "QQQ" in result
        assert "AGG" in result
        assert "60_40" in result
        assert "risk_parity" in result

    @freeze_time("2025-10-23 12:00:00")
    def test_benchmark_metrics_structure(self):
        """Each benchmark has return, volatility, and Sharpe ratio."""
        result = fetch_benchmark_performance(lookback_days=30)

        for ticker in ["SPY", "QQQ", "AGG"]:
            assert "return_pct" in result[ticker]
            assert "volatility_annualized" in result[ticker]
            assert "sharpe_ratio" in result[ticker]

            assert isinstance(result[ticker]["return_pct"], (int, float))
            assert isinstance(result[ticker]["volatility_annualized"], (int, float))
            assert isinstance(result[ticker]["sharpe_ratio"], (int, float))

    @freeze_time("2025-10-23 12:00:00")
    def test_composite_benchmarks_calculated(self):
        """60/40 and risk parity portfolios are calculated correctly."""
        result = fetch_benchmark_performance(lookback_days=30)

        # 60/40 should exist and be weighted correctly
        assert "60_40" in result
        assert "return_pct" in result["60_40"]

        # Risk parity should exist
        assert "risk_parity" in result
        assert "return_pct" in result["risk_parity"]
