"""Approved signal tickers and proxy mappings for Composer-compatible conditions."""

APPROVED_SIGNAL_TICKERS = {
    "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO",
    "RSP", "MDY", "USMV", "SPLV", "VIG", "SCHD",
    "TLT", "IEF", "AGG", "BIL", "SHY",
    "TIP", "LQD", "HYG", "BND", "MUB",
    "GLD", "SLV", "VNQ",
    "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY", "XLC",
    "SOXX",
    "SMH", "XBI", "IBB", "KRE", "KBE", "XOP", "XME", "XHB", "XRT", "IYT", "IGV",
    "VTV", "VUG", "MTUM", "QUAL", "IWD", "IWF",
    "DBC", "USO", "UNG", "DBA",
    "UUP", "FXE", "FXY",
    "VIXY",
}

PROXY_TICKER_MAP = {
    "VIX": "VIXY",
    "DXY": "UUP",
    "TNX": "IEF",
    "US10Y": "IEF",
    "WTI": "USO",
    "GOLD": "GLD",
    "SILVER": "SLV",
}

ALLOWED_ABSOLUTE_PRICE_TICKERS = {
    "VIXY",
}
