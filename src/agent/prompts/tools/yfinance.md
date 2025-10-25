# yfinance MCP Tools

Access stock market data, historical prices, financial statements, and news.

## Available Tools

- `stock_get_stock_info(ticker)` - Company info, sector, market cap
- `stock_get_historical_stock_prices(ticker, period, interval)` - Price history
- `stock_get_yahoo_finance_news(ticker)` - Recent news headlines
- `stock_get_financial_statement(ticker, financial_type)` - Income, balance sheet, cash flow

## Usage Patterns

**Check sector performance:**
```python
stock_get_stock_info("XLK")  # Tech sector ETF
stock_get_historical_stock_prices("XLK", "3mo", "1d")
```

**Analyze factor ETFs:**
```python
stock_get_stock_info("MTUM")  # Momentum
stock_get_stock_info("QUAL")  # Quality
stock_get_stock_info("SIZE")  # Small cap
```

**Get market breadth data:**
Check SPY, QQQ, and sector ETFs (XLK, XLF, XLV, XLE, XLY, XLP, XLI, XLB, XLRE, XLU, XLC)
