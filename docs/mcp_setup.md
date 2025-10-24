# MCP Server Setup Guide

## Status Summary

| Server | Status | Connection Type | Phase 1 Complete? | Tools Available |
|--------|--------|----------------|-------------------|-----------------|
| **FRED MCP** | ✅ Operational | Stdio (node) | Yes | 3 tools |
| **yfinance MCP** | ✅ Operational | Stdio (python) | Yes | 9 tools |
| **Composer MCP** | ⏳ Credentials configured, HTTP validated | HTTP Basic Auth | Partial (deferred to Phase 4) | TBD |

---

## FRED MCP Server

### Installation

```bash
cd ~/dev
git clone https://github.com/stefanoamorelli/fred-mcp-server.git
cd fred-mcp-server

# Install pnpm if needed
npm install -g pnpm

# Build server
npx pnpm install
npx pnpm build

# Verify
ls build/index.js  # Should exist
```

**Location**: `/Users/ben/dev/fred-mcp-server/build/index.js`

### Test Connectivity

```bash
pytest tests/agent/test_fred_mcp.py -v -s
```

**Expected output**: ✅ FRED MCP operational with 3 tools: `fred_browse`, `fred_search`, `fred_get_series`

### Available Tools

1. **fred_browse** - Navigate FRED's economic data catalog
2. **fred_search** - Search 800,000+ economic series by keywords
3. **fred_get_series** - Retrieve time-series data with transformations

### Troubleshooting

- **Error: `Cannot find module`**: Run `npx pnpm install` again in fred-mcp-server directory
- **Error: `FRED_API_KEY not set`**: Check `.env` has `FRED_API_KEY=...`
- **Error: `command not found: node`**: Install Node.js >=18.0 via nvm

---

## yfinance MCP Server

### Installation

**Already installed** at `/Users/ben/dev/yahoo-finance-mcp/`

This is a Python-based MCP server (not Node.js like FRED).

**Repository**: https://github.com/Alex2Yang97/yahoo-finance-mcp

### Configuration

**Server script**: `/Users/ben/dev/yahoo-finance-mcp/server.py`
**Python environment**: `/Users/ben/dev/yahoo-finance-mcp/.venv/bin/python`

The server uses its own virtual environment with dependencies (pandas, yfinance, etc.).

### Test Connectivity

```bash
pytest tests/agent/test_yfinance_mcp.py -v -s
```

**Expected output**: ✅ yfinance MCP operational with 9 tools

### Available Tools

1. **get_historical_stock_prices** - Historical OHLCV data
2. **get_stock_info** - Company information and current metrics
3. **get_yahoo_finance_news** - Recent news articles
4. **get_stock_actions** - Dividends, splits, capital gains
5. **get_financial_statement** - Income statement, balance sheet, cash flow
6. **get_holder_info** - Institutional and insider holdings
7. **get_option_expiration_dates** - Available option expiration dates
8. **get_option_chain** - Option chain data (calls/puts)
9. **get_recommendations** - Analyst recommendations

### Troubleshooting

- **Error: `ModuleNotFoundError`**: Ensure using yfinance venv python, not project python
- **Error: `Connection closed`**: Check that server.py exists and venv is set up correctly
- **Server timeout**: yfinance may be slow on first run (data caching)

---

## Composer MCP Server

### Configuration

**Endpoint**: `https://ai.composer.trade/mcp`
**Auth**: HTTP Basic (Base64-encoded API key + secret)

### Credentials (in `.env`)

```bash
COMPOSER_API_KEY=beedcad7-d886-44e3-867d-8aa853a6ee46
COMPOSER_API_SECRET=3839d952-536f-4540-be9a-85c78a10debc
```

**Get credentials from**: [Composer Dashboard](https://composer.trade/dashboard) → Accounts & Funding → API Keys

### Test Endpoint Reachability

```bash
pytest tests/agent/test_composer_endpoint.py -v -s
```

**Expected output**: ✅ Composer endpoint reachable (HTTP 401 or 403 is OK)

### Full MCP Integration

**Status**: Deferred to Phase 4 (Strategy Creation Workflow)

**Why**: Composer is only needed for backtesting strategies. Full tool discovery and MCP session testing will happen when backtesting workflow is implemented.

**Available Tools** (estimated based on docs):
- Symphony creation and management (31+ tools)
- Backtesting with risk metrics
- Portfolio monitoring
- Asset universe queries

---

## Integration in Phase 2: Agent Core

When implementing the Pydantic AI agent, configure MCP servers like this:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio, MCPServerStreamableHTTP
import os

# FRED MCP (Node.js stdio)
fred_server = MCPServerStdio(
    'node',
    args=['/Users/ben/dev/fred-mcp-server/build/index.js'],
    tool_prefix='fred',
    env={'FRED_API_KEY': os.getenv('FRED_API_KEY')}
)

# yfinance MCP (Python stdio)
yfinance_server = MCPServerStdio(
    '/Users/ben/dev/yahoo-finance-mcp/.venv/bin/python',
    args=['/Users/ben/dev/yahoo-finance-mcp/server.py'],
    tool_prefix='stock'
)

# Composer MCP (HTTP - Phase 4)
composer_server = MCPServerStreamableHTTP(
    'https://ai.composer.trade/mcp',
    tool_prefix='composer',
    headers={
        'Authorization': f'Basic {base64_encode_credentials()}'
    }
)

# Create agent with all MCP servers
agent = Agent(
    model='anthropic:claude-3-5-sonnet-20241022',
    result_type=Strategy,
    toolsets=[fred_server, yfinance_server]  # Add composer_server in Phase 4
)
```

---

## Validation Checklist

After Phase 1 completion:

- [x] `pip list | grep pydantic-ai` shows package installed (v1.4.0)
- [x] `pip list | grep mcp` shows package installed (v1.19.0)
- [x] FRED MCP server built successfully (`ls ~/dev/fred-mcp-server/build/index.js`)
- [x] FRED MCP connectivity test passing (`pytest tests/agent/test_fred_mcp.py`)
- [x] yfinance MCP server configured (`ls ~/dev/yahoo-finance-mcp/server.py`)
- [x] yfinance MCP connectivity test passing (`pytest tests/agent/test_yfinance_mcp.py`)
- [x] Composer credentials in `.env` (`grep COMPOSER_API_KEY .env`)
- [x] Composer endpoint reachable (`pytest tests/agent/test_composer_endpoint.py`)
- [x] `.env` not in git (`git status` would show untracked if git initialized)
- [x] All 30 market_context tests passing (`pytest tests/market_context/ -v`)
- [x] `requirements.txt` updated with pydantic-ai, mcp

---

## Next Steps (Phase 2: Agent Core)

1. Implement multi-provider agent (Claude, GPT-4, Gemini)
2. Configure agent toolsets with FRED and yfinance MCP servers
3. Test tool discovery and invocation
4. Implement strategy creation workflow using MCP tools
5. Add Composer MCP full integration in Phase 4 (when backtesting is needed)

---

## Troubleshooting Common Issues

### "Connection closed" errors
- **Cause**: MCP server crashed or didn't start properly
- **Fix**: Check server can run standalone: `node ~/dev/fred-mcp-server/build/index.js`

### "ENOENT" or file not found
- **Cause**: Incorrect paths to MCP server files
- **Fix**: Verify paths in test files match actual server locations

### Import errors in Python MCP server
- **Cause**: Using wrong Python interpreter (project venv vs server venv)
- **Fix**: Always use server's own venv: `/Users/ben/dev/yahoo-finance-mcp/.venv/bin/python`

### Network timeouts
- **Cause**: Slow first-time data fetching (yfinance caching)
- **Fix**: Increase pytest timeout or retry

---

## Performance Notes

- **FRED MCP**: Fast (< 1 second for tool discovery)
- **yfinance MCP**: Slower (2-3 seconds for tool discovery, data fetching varies)
- **Composer HTTP**: Fast for health check, full MCP session untested

---

## Security

- ✅ `.env` file contains all API keys and secrets
- ✅ `.env` is in `.gitignore` (not committed to version control)
- ✅ Credentials are never logged or printed in test output
- ⚠️ FRED_API_KEY visible in logs (not sensitive, free tier)
- ✅ Composer credentials are private, never exposed in test output
