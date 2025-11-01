# yfinance MCP Tools

Access stock market data, historical prices, financial statements, and news via Yahoo Finance.

**Note:** Market regime analysis (trend, volatility, sector leadership, breadth, factor premiums) is already provided in the market context pack. Use these tools to:
- Verify or drill deeper into specific data points from the context pack
- Get historical price data for specific stocks/ETFs you're considering
- Check recent news for relevant stocks or sectors
- Analyze individual companies or ETFs not covered in the context pack

## Available Tools

### `stock_get_stock_info(ticker)`
Get company/ETF information including sector, market cap, description.

**Parameters:**
- `ticker`: Stock/ETF symbol (e.g., "SPY", "AAPL", "XLK")

**Returns:** Company info, sector classification, market cap, description

**Use cases:**
- Check what sector a stock belongs to
- Verify market cap for position sizing
- Get company description for thesis validation

### `stock_get_historical_stock_prices(ticker, period, interval)`
Get historical price data for stocks, ETFs, and indices.

**Parameters:**
- `ticker`: Stock/ETF symbol (e.g., "SPY", "QQQ", "AAPL")
- `period`: Time period ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
- `interval`: Data frequency ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo")

**Returns:** DataFrame with Open, High, Low, Close, Volume, and calculated indicators (moving averages, etc.)

**Use cases:**
- Get price history for specific stocks you're considering for a strategy
- Calculate custom technical indicators (RSI, MACD, etc.)
- Verify recent price movements mentioned in the context pack
- Analyze correlations between assets

**Recommended periods:**
- Recent momentum: `period="3mo"` to `period="6mo"`
- Trend analysis: `period="1y"` for 200-day MA
- Long-term patterns: `period="2y"` to `period="5y"`

### `stock_get_yahoo_finance_news(ticker)`
Get recent news headlines for a stock or market.

**Parameters:**
- `ticker`: Stock symbol or index (e.g., "AAPL", "SPY" for market news)

**Returns:** List of recent news headlines with timestamps

**Use cases:**
- Check for recent company-specific events (earnings, product launches, regulatory)
- Verify market events mentioned in context pack
- Get sentiment for specific stocks in your candidate strategies
- Check for catalysts that might drive near-term performance

### `stock_get_financial_statement(ticker, financial_type)`
Get financial statements for fundamental analysis (primarily for individual stocks).

**Parameters:**
- `ticker`: Stock symbol
- `financial_type`: "income", "balance", "cashflow"

**Returns:** Financial statement data

**Use cases:**
- Fundamental analysis for stock-picking strategies
- Verify financial health of companies in your portfolio
- Calculate valuation metrics (P/E, P/B, debt ratios)

## Key Tickers Reference

### Market Indices
- `SPY` - S&P 500 (US large cap benchmark)
- `QQQ` - Nasdaq 100 (tech-heavy)
- `^VIX` - CBOE Volatility Index
- `IWM` - Russell 2000 (small cap)
- `DIA` - Dow Jones Industrial Average

### Sector ETFs (11 GICS Sectors)
- `XLK` - Technology
- `XLF` - Financials
- `XLV` - Health Care
- `XLE` - Energy
- `XLY` - Consumer Discretionary
- `XLP` - Consumer Staples
- `XLU` - Utilities
- `XLI` - Industrials
- `XLB` - Materials
- `XLRE` - Real Estate
- `XLC` - Communication Services

### Factor ETFs
- `MTUM` - Momentum Factor
- `QUAL` - Quality Factor
- `VTV` - Value Stocks
- `VUG` - Growth Stocks
- `USMV` - Low Volatility
- `SIZE` - Small Cap Factor
- `VLUE` - Value Factor

### Bond ETFs
- `AGG` - US Aggregate Bonds
- `TLT` - 20+ Year Treasuries
- `SHY` - 1-3 Year Treasuries
- `LQD` - Investment Grade Corporate Bonds
- `HYG` - High Yield Corporate Bonds
- `BIL` - 1-3 Month T-Bills (cash proxy)

### Commodity & Alternative ETFs
- `GLD` - Gold
- `DBC` - Commodities Broad Basket
- `USO` - Crude Oil
- `UNG` - Natural Gas

### Inverse & Leveraged ETFs (for Composer strategies)
- `SH` - Short S&P 500
- `PSQ` - Short Nasdaq 100
- `UPRO` - 3x Long S&P 500
- `TQQQ` - 3x Long Nasdaq 100
- `TMF` - 3x Long 20+ Year Treasuries

## Common Usage Patterns

### Verify Context Pack Data
If the context pack says "XLK is the top sector with +15% vs SPY", you can verify:
```python
stock_get_historical_stock_prices("XLK", period="6mo", interval="1d")
stock_get_historical_stock_prices("SPY", period="6mo", interval="1d")
# Calculate 90-day returns to confirm
```

### Drill Deeper Into Specific Stocks
If you're creating a strategy with individual stocks:
```python
stock_get_stock_info("AAPL")  # Check sector, market cap
stock_get_historical_stock_prices("AAPL", period="1y", interval="1d")  # Price history
stock_get_yahoo_finance_news("AAPL")  # Recent news
```

### Check Correlation Between Assets
If building a diversified portfolio:
```python
stock_get_historical_stock_prices("TLT", period="1y", interval="1d")  # Bonds
stock_get_historical_stock_prices("GLD", period="1y", interval="1d")  # Gold
stock_get_historical_stock_prices("SPY", period="1y", interval="1d")  # Equities
# Calculate correlations to ensure true diversification
```

### Research Specific ETFs for Strategy
If you want to use a specific factor or sector ETF:
```python
stock_get_stock_info("MTUM")  # What is this ETF?
stock_get_historical_stock_prices("MTUM", period="2y", interval="1d")  # Performance history
```
