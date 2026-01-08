import pytest
from datetime import datetime
from freezegun import freeze_time
from unittest.mock import Mock, patch
from src.market_context.fetchers import fetch_regime_snapshot, fetch_macro_indicators, fetch_recent_events, fetch_benchmark_performance, fetch_intra_sector_divergence, SECTOR_TOP_HOLDINGS, _calculate_yoy_growth_time_series


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
        
        # v2.0: SPY_vs_200d_ma is now a time series dict
        spy_vs_ma = result["trend"]["SPY_vs_200d_ma"]
        assert isinstance(spy_vs_ma, dict)
        assert "current" in spy_vs_ma
        assert isinstance(spy_vs_ma["current"], (int, float, type(None)))

    @freeze_time("2025-01-15 12:00:00")
    def test_volatility_regime_classification(self):
        """Classifies volatility regime based on VIX levels."""
        result = fetch_regime_snapshot()

        assert result["volatility"]["regime"] in ["low", "normal", "elevated", "high"]
        assert "VIX_current" in result["volatility"]
        assert "VIX_30d_avg" in result["volatility"]
        
        # v2.0: VIX_current is now a time series dict
        vix_current = result["volatility"]["VIX_current"]
        assert isinstance(vix_current, dict)
        assert "current" in vix_current
        if vix_current["current"] is not None:
            assert vix_current["current"] > 0

    @freeze_time("2025-01-15 12:00:00")
    def test_breadth_calculation(self):
        """Calculates market breadth as percentage of sectors above 50d MA."""
        result = fetch_regime_snapshot()

        assert "sectors_above_50d_ma_pct" in result["breadth"]
        breadth = result["breadth"]["sectors_above_50d_ma_pct"]
        
        # v2.0: breadth is now a time series dict
        assert isinstance(breadth, dict)
        assert "current" in breadth
        if breadth["current"] is not None:
            assert 0 <= breadth["current"] <= 100

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

        # v2.0: factor premiums are now time series dicts
        momentum = factor["momentum_premium_30d"]
        quality = factor["quality_premium_30d"]
        size = factor["size_premium_30d"]
        
        assert isinstance(momentum, dict)
        assert isinstance(quality, dict)
        assert isinstance(size, dict)
        
        assert "current" in momentum
        assert "current" in quality
        assert "current" in size

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
        # v2.0: sentiment removed, added many new sections
        assert "manufacturing" in result
        assert "consumer" in result
        assert "credit_conditions" in result

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

        # v2.0: Interest rates are now time series dicts
        assert isinstance(rates["fed_funds_rate"], dict)
        assert isinstance(rates["treasury_10y"], dict)
        assert isinstance(rates["treasury_2y"], dict)
        assert isinstance(rates["yield_curve_2s10s"], dict)
        
        assert "current" in rates["fed_funds_rate"]
        assert "current" in rates["treasury_10y"]

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

        # v2.0: Inflation metrics are now time series dicts
        assert isinstance(inflation["cpi_yoy"], dict)
        assert isinstance(inflation["core_cpi_yoy"], dict)
        
        assert "current" in inflation["cpi_yoy"]
        assert "current" in inflation["core_cpi_yoy"]

    def test_yoy_growth_uses_actual_data_date(self):
        """YoY growth aligns to the actual data date when releases lag."""
        import pandas as pd

        dates = pd.date_range(start="2024-11-01", periods=13, freq="MS")
        values = list(range(100, 113))
        series = pd.Series(values, index=dates)

        mock_fred = Mock()
        mock_fred.get_series.return_value = series

        anchor_date = datetime(2026, 1, 5)
        result = _calculate_yoy_growth_time_series(mock_fred, "CPIAUCSL", anchor_date)

        assert result["current"] == pytest.approx(12.0, abs=0.01)

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

        # v2.0: Employment metrics are now time series dicts
        assert isinstance(employment["unemployment_rate"], dict)
        assert isinstance(employment["nonfarm_payrolls"], dict)
        assert isinstance(employment["wage_growth_yoy"], dict)
        
        assert "current" in employment["unemployment_rate"]
        assert "current" in employment["nonfarm_payrolls"]

    @patch('src.market_context.fetchers.Fred')
    def test_yield_curve_calculation(self, mock_fred_class):
        """Calculates yield curve spread correctly."""
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred

        # Mock pandas Series for time series data
        import pandas as pd
        
        def mock_get_series(series_id, **kwargs):
            # Return pandas Series with dates
            dates = pd.date_range(end='2025-01-15', periods=400, freq='D')
            if series_id == 'DGS10':
                return pd.Series([4.12] * 400, index=dates)
            elif series_id == 'DGS2':
                return pd.Series([4.35] * 400, index=dates)
            return pd.Series([0.0] * 400, index=dates)

        mock_fred.get_series.side_effect = mock_get_series

        result = fetch_macro_indicators(fred_api_key="test_key")

        # v2.0: Yield curve is now a time series dict
        # Yield curve should be 10y - 2y = 4.12 - 4.35 = -0.23 (inverted)
        yield_curve = result["interest_rates"]["yield_curve_2s10s"]
        assert isinstance(yield_curve, dict)
        assert "current" in yield_curve
        if yield_curve["current"] is not None:
            assert yield_curve["current"] == pytest.approx(-0.23, abs=0.01)

    @patch('src.market_context.fetchers.Fred')
    def test_leading_indicators_structure(self, mock_fred_class):
        """Returns complete leading indicators with all required fields."""
        mock_fred = Mock()
        mock_fred_class.return_value = mock_fred

        # Mock pandas Series for time series data
        import pandas as pd

        def mock_get_series(series_id, **kwargs):
            # Return pandas Series with dates
            dates = pd.date_range(end='2025-01-15', periods=400, freq='D')
            if series_id == 'T10Y3M':
                return pd.Series([0.15] * 400, index=dates)  # 15 bps spread
            elif series_id == 'BAMLH0A0HYM2':
                return pd.Series([4.50] * 400, index=dates)  # HY spread (4.5%)
            elif series_id == 'BAMLC0A4CBBB':
                return pd.Series([1.20] * 400, index=dates)  # IG spread (1.2%)
            elif series_id == 'USSLIND':
                return pd.Series([0.5] * 400, index=dates)   # LEI
            elif series_id == 'PERMIT':
                return pd.Series([1450.0] * 400, index=dates)  # Building permits
            elif series_id == 'AMTMNO':
                return pd.Series([550000.0] * 400, index=dates)  # Manufacturing orders
            return pd.Series([0.0] * 400, index=dates)

        mock_fred.get_series.side_effect = mock_get_series

        result = fetch_macro_indicators(fred_api_key="test_key")

        # Verify leading_indicators section exists
        assert "leading_indicators" in result
        leading = result["leading_indicators"]

        # Check all 5 indicators are present
        assert "yield_curve_3m10y" in leading
        assert "credit_spread_differential_bps" in leading
        assert "lei_composite" in leading
        assert "building_permits_thousands" in leading
        assert "manufacturing_new_orders_millions" in leading

        # Verify time series structure for each indicator
        for indicator_name in ["yield_curve_3m10y", "lei_composite", "building_permits_thousands", "manufacturing_new_orders_millions"]:
            indicator = leading[indicator_name]
            assert isinstance(indicator, dict)
            assert "current" in indicator
            assert "1m_ago" in indicator
            assert "12m_ago" in indicator

        # Verify credit spread differential is calculated (HY - IG in bps)
        credit_diff = leading["credit_spread_differential_bps"]
        assert isinstance(credit_diff, dict)
        assert "current" in credit_diff
        # HY (450 bps) - IG (120 bps) = 330 bps
        if credit_diff["current"] is not None:
            assert credit_diff["current"] == pytest.approx(330, abs=5)


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
        result = fetch_benchmark_performance()

        assert isinstance(result, dict)
        assert "SPY" in result
        assert "QQQ" in result
        assert "AGG" in result
        assert "60_40" in result
        assert "risk_parity" in result

    @freeze_time("2025-10-23 12:00:00")
    def test_benchmark_metrics_structure(self):
        """Each benchmark has multi-period returns, volatility, Sharpe, and max drawdown."""
        result = fetch_benchmark_performance()

        for ticker in ["SPY", "QQQ", "AGG"]:
            assert "returns" in result[ticker]
            assert "volatility_annualized" in result[ticker]
            assert "sharpe_ratio" in result[ticker]
            assert "max_drawdown" in result[ticker]

            # v2.0: Returns for multiple periods
            returns = result[ticker]["returns"]
            assert isinstance(returns, dict)
            assert "30d" in returns
            assert "60d" in returns
            assert "90d" in returns
            assert "1y" in returns
            
            # Volatility and Sharpe for multiple periods (not 1y)
            vol = result[ticker]["volatility_annualized"]
            sharpe = result[ticker]["sharpe_ratio"]
            assert isinstance(vol, dict)
            assert isinstance(sharpe, dict)
            assert "30d" in vol
            assert "30d" in sharpe

    @freeze_time("2025-10-23 12:00:00")
    def test_composite_benchmarks_calculated(self):
        """60/40 and risk parity portfolios are calculated correctly."""
        result = fetch_benchmark_performance()

        # 60/40 should exist with multi-period structure
        assert "60_40" in result
        assert "returns" in result["60_40"]
        assert "30d" in result["60_40"]["returns"]

        # Risk parity should exist with multi-period structure
        assert "risk_parity" in result
        assert "returns" in result["risk_parity"]
        assert "30d" in result["risk_parity"]["returns"]


class TestFetchIntraSectorDivergence:
    """Test intra-sector divergence fetcher."""

    @freeze_time("2025-01-15 12:00:00")
    def test_returns_valid_structure_for_known_sector(self):
        """Returns top/bottom performers with expected keys for valid sector."""
        result = fetch_intra_sector_divergence(["XLK"])

        # Should return data for XLK
        assert "XLK" in result

        # Verify structure
        xlk = result["XLK"]
        assert "top" in xlk
        assert "bottom" in xlk
        assert "spread_pct" in xlk
        assert "holdings_analyzed" in xlk

    @freeze_time("2025-01-15 12:00:00")
    def test_ignores_unknown_sector_tickers(self):
        """Silently skips sectors not in SECTOR_TOP_HOLDINGS."""
        result = fetch_intra_sector_divergence(["FAKE_SECTOR", "INVALID"])

        assert result == {}

    @freeze_time("2025-01-15 12:00:00")
    def test_top_n_limits_results(self):
        """Returns exactly top_n top and bottom performers."""
        result = fetch_intra_sector_divergence(["XLK"], top_n=3)

        if "XLK" in result:
            assert len(result["XLK"]["top"]) == 3
            assert len(result["XLK"]["bottom"]) == 3

    @freeze_time("2025-01-15 12:00:00")
    def test_multiple_sectors_returns_all(self):
        """Can fetch divergence for multiple sectors."""
        result = fetch_intra_sector_divergence(["XLK", "XLF", "XLE"])

        # At least some should succeed (API permitting)
        assert len(result) >= 1

    @freeze_time("2025-01-15 12:00:00")
    def test_spread_pct_calculated_correctly(self):
        """Spread is difference between best and worst performer."""
        result = fetch_intra_sector_divergence(["XLK"], top_n=1)

        if "XLK" in result:
            top_ret = result["XLK"]["top"][0][1]
            bottom_ret = result["XLK"]["bottom"][0][1]
            expected_spread = round(top_ret - bottom_ret, 2)
            assert result["XLK"]["spread_pct"] == expected_spread

    @freeze_time("2025-01-15 12:00:00")
    def test_top_bottom_are_lists_of_pairs(self):
        """Top and bottom are lists of [ticker, return] pairs."""
        result = fetch_intra_sector_divergence(["XLF"], top_n=2)

        if "XLF" in result:
            for ticker, return_val in result["XLF"]["top"]:
                assert isinstance(ticker, str)
                assert isinstance(return_val, (int, float))

            for ticker, return_val in result["XLF"]["bottom"]:
                assert isinstance(ticker, str)
                assert isinstance(return_val, (int, float))

    def test_sector_top_holdings_has_all_sectors(self):
        """SECTOR_TOP_HOLDINGS contains all 11 sector ETFs."""
        expected_sectors = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLP", "XLY", "XLU", "XLRE", "XLC", "XLB"]

        for sector in expected_sectors:
            assert sector in SECTOR_TOP_HOLDINGS
            assert len(SECTOR_TOP_HOLDINGS[sector]) == 15  # 15 holdings each
