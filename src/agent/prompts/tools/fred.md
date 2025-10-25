# FRED MCP Tools

Access 800,000+ Federal Reserve economic data series.

## Available Tools

- `fred_search(text)` - Search for economic series
- `fred_get_series(series_id, start_date, end_date)` - Get time series data
- `fred_browse()` - Navigate FRED catalog

## Key Series IDs

**Interest Rates:**
- `DFF` - Federal Funds Rate
- `DGS10` - 10-Year Treasury
- `DGS2` - 2-Year Treasury
- `T10Y2Y` - 10Y-2Y Yield Spread (recession indicator)

**Inflation:**
- `CPIAUCSL` - CPI (All Urban Consumers)
- `CPILFESL` - Core CPI (ex food & energy)
- `PCE` - Personal Consumption Expenditures

**Employment:**
- `UNRATE` - Unemployment Rate
- `PAYEMS` - Nonfarm Payrolls
- `AHETPI` - Average Hourly Earnings

**GDP & Activity:**
- `GDP` - Gross Domestic Product
- `INDPRO` - Industrial Production Index

## Usage Patterns

**Check recession signals:**
```python
fred_get_series("T10Y2Y", "2023-01-01", "2025-10-23")  # Yield curve
fred_get_series("UNRATE", "2023-01-01", "2025-10-23")  # Unemployment
```

**Inflation trend:**
```python
fred_get_series("CPIAUCSL", "2023-01-01", "2025-10-23")
```
