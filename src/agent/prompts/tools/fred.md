# FRED MCP Tools

Access 800,000+ Federal Reserve economic data series via the FRED (Federal Reserve Economic Data) API.

## ⚠️ CRITICAL: Token Efficiency Rules

**ALWAYS use the `limit` parameter to prevent token overflow!**

Without `limit`, FRED returns ALL historical data (often 100+ data points = 5000+ tokens per call). With proper limits, you get 12-24 data points = 500-1000 tokens per call. This is an **80-95% token reduction**.

### Required Parameters for Every Call

**For `fred_get_series`:**
- Monthly data: `limit=12` (1 year) or `limit=24` (2 years) MAX
- Daily data: `limit=30` (1 month) or `limit=90` (3 months) MAX
- Quarterly data: `limit=8` (2 years) MAX
- **Never call without `limit`** - this returns ALL data and will overflow tokens!

**For `fred_search`:**
- Standard search: `limit=10` (top 10 matches)
- Broader search: `limit=25` MAX
- **Never use default** - can return 1000+ results!

### Example: Good vs Bad

**❌ BAD (Token Overflow):**
```python
fred_get_series(series_id="FEDFUNDS")  # Returns 100+ data points, 5000+ tokens
fred_search(text="unemployment")        # Returns 1000+ results, 50000+ tokens
```

**✅ GOOD (Token Efficient):**
```python
fred_get_series(series_id="FEDFUNDS", limit=12, frequency="m")     # 12 points, ~500 tokens
fred_search(text="unemployment", limit=10)                          # 10 results, ~2000 tokens
```

### Token Impact Examples

| Call Type | Without `limit` | With `limit` | Reduction |
|-----------|----------------|--------------|-----------|
| Monthly series | 5,000 tokens | 500 tokens | 90% |
| Daily series | 10,000 tokens | 1,000 tokens | 90% |
| Search results | 50,000 tokens | 2,000 tokens | 96% |

## Available Tools

### `fred_search(text, limit)`
Search for economic series by keyword.

**Parameters:**
- `text`: Search query (e.g., "unemployment rate", "inflation")
- `limit`: Maximum results to return (REQUIRED - use 10-25)

**Returns:** List of series with id, title, observation dates

### `fred_get_series(series_id, observation_start, limit, frequency, aggregation_method)`
Get time series data for a specific series.

**Parameters:**
- `series_id`: Series identifier (e.g., "FEDFUNDS", "CPIAUCSL")
- `observation_start`: Start date (YYYY-MM-DD format)
- `limit`: Maximum observations to return (REQUIRED - see rules above)
- `frequency`: Data frequency ("d" daily, "m" monthly, "q" quarterly)
- `aggregation_method`: How to aggregate ("avg", "eop" end-of-period, "sum")

**Returns:** List of observations with date and value

### `fred_browse()`
Navigate FRED catalog by category.

**Returns:** Category tree structure

## Key Series IDs

### Interest Rates
- `FEDFUNDS` - Federal Funds Rate (monthly, use `limit=12-24`)
- `DGS10` - 10-Year Treasury (daily, use `limit=30-90`)
- `DGS2` - 2-Year Treasury (daily, use `limit=30-90`)
- `T10Y2Y` - 10Y-2Y Yield Spread (daily, use `limit=30-90`)

### Inflation
- `CPIAUCSL` - CPI All Urban Consumers (monthly, use `limit=12-24`)
- `CPILFESL` - Core CPI ex food & energy (monthly, use `limit=12-24`)
- `PCE` - Personal Consumption Expenditures (monthly, use `limit=12-24`)
- `T10YIE` - 10-Year Breakeven Inflation (daily, use `limit=30-90`)

### Employment
- `UNRATE` - Unemployment Rate (monthly, use `limit=12-24`)
- `PAYEMS` - Nonfarm Payrolls (monthly, use `limit=12-24`)
- `AHETPI` - Average Hourly Earnings (monthly, use `limit=12-24`)

### GDP & Activity
- `GDP` - Gross Domestic Product (quarterly, use `limit=8-12`)
- `INDPRO` - Industrial Production Index (monthly, use `limit=12-24`)
- `USSLIND` - Leading Economic Indicators (monthly, use `limit=12-24`)

## Recommended Query Strategy

For macro regime classification, fetch these indicators with appropriate limits:

```python
# Interest rates (monthly, 1 year)
fred_get_series("FEDFUNDS", observation_start="2023-01-01", limit=12, frequency="m", aggregation_method="eop")

# Treasury yields (daily, 3 months)
fred_get_series("DGS10", observation_start="2025-01-01", limit=90, frequency="d", aggregation_method="avg")
fred_get_series("DGS2", observation_start="2025-01-01", limit=90, frequency="d", aggregation_method="avg")

# Inflation (monthly, 2 years for trend)
fred_get_series("CPIAUCSL", observation_start="2023-01-01", limit=24, frequency="m", aggregation_method="avg", units="pc1")
fred_get_series("CPILFESL", observation_start="2023-01-01", limit=24, frequency="m", aggregation_method="avg", units="pc1")

# Employment (monthly, 2 years)
fred_get_series("UNRATE", observation_start="2023-01-01", limit=24, frequency="m", aggregation_method="eop")

# Growth (quarterly, 2 years)
fred_get_series("GDP", observation_start="2022-01-01", limit=12, frequency="q", aggregation_method="avg", units="pc1")
```

**Key principle:** Fetch only the data you need for regime classification. More data ≠ better analysis, and will cause token overflow.
