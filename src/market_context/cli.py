#!/usr/bin/env python3
"""CLI for market context pack generation."""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from src.market_context.assembler import assemble_market_context_pack
from src.market_context.validation import validate_context_pack


def load_api_key():
    """Load FRED API key from .env file."""
    # Load from .env file in project root
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)

    api_key = os.getenv('FRED_API_KEY')
    if not api_key:
        print("❌ Error: FRED_API_KEY not found in .env file")
        print("Please add your FRED API key to .env:")
        print("  FRED_API_KEY=your_key_here")
        sys.exit(1)

    return api_key


def generate_context_pack(args):
    """Generate market context pack."""
    print("🔍 Generating market context pack...")
    print(f"📅 Anchor date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load API key
    api_key = load_api_key()

    # Generate context pack
    try:
        context_pack = assemble_market_context_pack(fred_api_key=api_key)
        print("✅ Context pack generated successfully!")
        print()
    except Exception as e:
        print(f"❌ Error generating context pack: {e}")
        sys.exit(1)

    # Validate
    print("🔎 Validating context pack...")
    is_valid, errors = validate_context_pack(context_pack)

    if is_valid:
        print("✅ Validation passed!")
        print()
    else:
        print("⚠️  Validation warnings:")
        for error in errors:
            print(f"  - {error}")
        print()

    # Print summary
    print_summary(context_pack)

    # Save to file if requested
    if args.output:
        save_context_pack(context_pack, args.output)

    return context_pack


def print_summary(context_pack):
    """Print human-readable summary of context pack."""
    print("=" * 70)
    print("MARKET CONTEXT SUMMARY")
    print("=" * 70)
    print()

    # Metadata
    metadata = context_pack['metadata']
    print(f"📅 Anchor Date: {metadata['anchor_date']}")
    print(f"🏷️  Version: {metadata['version']}")
    print()

    # Regime snapshot
    regime = context_pack['regime_snapshot']
    print("📊 MARKET REGIME")
    
    # Handle time series data (v2.0) vs single values (v1.0)
    spy_vs_200 = regime['trend']['SPY_vs_200d_ma']
    if isinstance(spy_vs_200, dict):
        spy_current = spy_vs_200.get('current', 0)
        spy_12m = spy_vs_200.get('12m_ago')
        if spy_current is not None and spy_12m is not None:
            print(f"  Trend: {regime['trend']['regime'].upper()} (SPY {spy_current:+.2f}% vs 200d MA, was {spy_12m:+.2f}% 12m ago)")
        elif spy_current is not None:
            print(f"  Trend: {regime['trend']['regime'].upper()} (SPY {spy_current:+.2f}% vs 200d MA)")
        else:
            print(f"  Trend: {regime['trend']['regime'].upper()}")
    else:
        if spy_vs_200 is not None:
            print(f"  Trend: {regime['trend']['regime'].upper()} (SPY {spy_vs_200:+.2f}% vs 200d MA)")
        else:
            print(f"  Trend: {regime['trend']['regime'].upper()}")
    
    vix_current_data = regime['volatility']['VIX_current']
    if isinstance(vix_current_data, dict):
        vix_val = vix_current_data.get('current')
        vix_12m = vix_current_data.get('12m_ago')
        if vix_val is not None and vix_12m is not None:
            print(f"  Volatility: {regime['volatility']['regime'].upper()} (VIX: {vix_val:.2f}, was {vix_12m:.2f} 12m ago)")
        elif vix_val is not None:
            print(f"  Volatility: {regime['volatility']['regime'].upper()} (VIX: {vix_val:.2f})")
        else:
            print(f"  Volatility: {regime['volatility']['regime'].upper()}")
    else:
        if vix_current_data is not None:
            print(f"  Volatility: {regime['volatility']['regime'].upper()} (VIX: {vix_current_data:.2f})")
        else:
            print(f"  Volatility: {regime['volatility']['regime'].upper()}")
    
    breadth_data = regime['breadth']['sectors_above_50d_ma_pct']
    if isinstance(breadth_data, dict):
        breadth_val = breadth_data.get('current')
        breadth_12m = breadth_data.get('12m_ago')
        if breadth_val is not None and breadth_12m is not None:
            print(f"  Breadth: {breadth_val:.1f}% sectors above 50d MA (was {breadth_12m:.1f}% 12m ago)")
        elif breadth_val is not None:
            print(f"  Breadth: {breadth_val:.1f}% sectors above 50d MA")
        else:
            print(f"  Breadth: N/A")
    else:
        if breadth_data is not None:
            print(f"  Breadth: {breadth_data:.1f}% sectors above 50d MA")
        else:
            print(f"  Breadth: N/A")

    # Sector dispersion
    if 'dispersion' in regime:
        dispersion = regime['dispersion']
        print(f"  Dispersion: {dispersion['regime'].upper()} (σ: {dispersion['sector_return_std_30d']:.2f}%)")
    print()

    # Sector leadership
    print("  Top 3 Sectors:")
    for ticker, perf in regime['sector_leadership']['leaders']:
        print(f"    {ticker}: {perf:+.2f}%")
    print()

    print("  Bottom 3 Sectors:")
    for ticker, perf in regime['sector_leadership']['laggards']:
        print(f"    {ticker}: {perf:+.2f}%")
    print()

    # Factor regime
    factor = regime['factor_regime']
    print(f"  Factor Regime: {factor['value_vs_growth']['regime'].replace('_', ' ').title()}")
    
    # Handle time series factor premiums
    momentum = factor['momentum_premium_30d']
    quality = factor['quality_premium_30d']
    size = factor['size_premium_30d']
    
    if isinstance(momentum, dict):
        mom_current = momentum.get('current')
        mom_12m = momentum.get('12m_ago')
        if mom_current is not None and mom_12m is not None:
            print(f"    Momentum premium: {mom_current:+.2f}% (was {mom_12m:+.2f}% 12m ago)")
        elif mom_current is not None:
            print(f"    Momentum premium: {mom_current:+.2f}%")
        else:
            print(f"    Momentum premium: N/A")
    else:
        if momentum is not None:
            print(f"    Momentum premium: {momentum:+.2f}%")
        else:
            print(f"    Momentum premium: N/A")
    
    if isinstance(quality, dict):
        qual_current = quality.get('current')
        qual_12m = quality.get('12m_ago')
        if qual_current is not None and qual_12m is not None:
            print(f"    Quality premium: {qual_current:+.2f}% (was {qual_12m:+.2f}% 12m ago)")
        elif qual_current is not None:
            print(f"    Quality premium: {qual_current:+.2f}%")
        else:
            print(f"    Quality premium: N/A")
    else:
        if quality is not None:
            print(f"    Quality premium: {quality:+.2f}%")
        else:
            print(f"    Quality premium: N/A")
    
    if isinstance(size, dict):
        size_current = size.get('current')
        size_12m = size.get('12m_ago')
        if size_current is not None and size_12m is not None:
            print(f"    Size premium: {size_current:+.2f}% (was {size_12m:+.2f}% 12m ago)")
        elif size_current is not None:
            print(f"    Size premium: {size_current:+.2f}%")
        else:
            print(f"    Size premium: N/A")
    else:
        if size is not None:
            print(f"    Size premium: {size:+.2f}%")
        else:
            print(f"    Size premium: N/A")
    print()

    # Benchmark performance
    if 'benchmark_performance' in context_pack:
        benchmarks = context_pack['benchmark_performance']
        print("📈 BENCHMARK PERFORMANCE")
        print(f"  {'Ticker':12s} {'30d':>12s} {'60d':>12s} {'90d':>12s} {'YTD':>12s}")
        print(f"  {'-'*60}")
        
        for ticker in ['SPY', 'QQQ', 'AGG', '60_40', 'risk_parity']:
            if ticker in benchmarks:
                bench = benchmarks[ticker]
                display_name = ticker.replace('_', '/').upper()
                
                ret_30d = bench['returns'].get('30d')
                ret_60d = bench['returns'].get('60d')
                ret_90d = bench['returns'].get('90d')
                ret_ytd = bench['returns'].get('ytd')
                
                ret_30d_str = f"{ret_30d:+6.2f}%" if ret_30d is not None else "N/A"
                ret_60d_str = f"{ret_60d:+6.2f}%" if ret_60d is not None else "N/A"
                ret_90d_str = f"{ret_90d:+6.2f}%" if ret_90d is not None else "N/A"
                ret_ytd_str = f"{ret_ytd:+6.2f}%" if ret_ytd is not None else "N/A"
                
                print(f"  {display_name:12s} {ret_30d_str:>12s} {ret_60d_str:>12s} {ret_90d_str:>12s} {ret_ytd_str:>12s}")
        print()
        
        # Show vol and Sharpe for 30d only
        print(f"  {'Ticker':12s} {'Vol 30d':>12s} {'Sharpe 30d':>12s} {'Max DD 30d':>12s}")
        print(f"  {'-'*60}")
        for ticker in ['SPY', 'QQQ', 'AGG', '60_40', 'risk_parity']:
            if ticker in benchmarks:
                bench = benchmarks[ticker]
                display_name = ticker.replace('_', '/').upper()
                
                vol_30d = bench['volatility_annualized'].get('30d')
                sharpe_30d = bench['sharpe_ratio'].get('30d')
                dd_30d = bench['max_drawdown'].get('30d')
                
                vol_str = f"{vol_30d:6.2f}%" if vol_30d is not None else "N/A"
                sharpe_str = f"{sharpe_30d:6.2f}" if sharpe_30d is not None else "N/A"
                dd_str = f"{dd_30d:6.2f}%" if dd_30d is not None else "N/A"
                
                print(f"  {display_name:12s} {vol_str:>12s} {sharpe_str:>12s} {dd_str:>12s}")
        print()

    # Macro indicators
    macro = context_pack['macro_indicators']
    print("💰 MACRO INDICATORS")
    rates = macro['interest_rates']
    
    # Helper function to format time series or single value
    def format_indicator(data, unit='%', decimals=2):
        if isinstance(data, dict):
            current = data.get('current', 0)
            m12 = data.get('12m_ago', current)
            if current is None or m12 is None:
                return f"N/A"
            # Handle pandas Series
            if hasattr(current, 'item'):
                current = current.item()
            if hasattr(m12, 'item'):
                m12 = m12.item()
            change = current - m12
            arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
            return f"{current:.{decimals}f}{unit} ({arrow} {abs(change):.{decimals}f}{unit} from 12m ago)"
        else:
            # Handle pandas Series
            if hasattr(data, 'item'):
                data = data.item()
            return f"{data:.{decimals}f}{unit}" if data is not None else "N/A"
    
    fed_funds = rates['fed_funds_rate']
    if isinstance(fed_funds, dict):
        print(f"  Fed Funds Rate: {format_indicator(fed_funds)}")
    else:
        print(f"  Fed Funds Rate: {fed_funds:.2f}%")
    
    treasury_10y = rates['treasury_10y']
    if isinstance(treasury_10y, dict):
        print(f"  10Y Treasury: {format_indicator(treasury_10y)}")
    else:
        print(f"  10Y Treasury: {treasury_10y:.2f}%")
    
    treasury_2y = rates['treasury_2y']
    if isinstance(treasury_2y, dict):
        print(f"  2Y Treasury: {format_indicator(treasury_2y)}")
    else:
        print(f"  2Y Treasury: {treasury_2y:.2f}%")
    
    yield_curve = rates['yield_curve_2s10s']
    if isinstance(yield_curve, dict):
        yc_current = yield_curve.get('current', 0)
        inverted = "(INVERTED)" if yc_current and yc_current < 0 else ""
        print(f"  Yield Curve (2s10s): {format_indicator(yield_curve)} {inverted}")
    else:
        inverted = "(INVERTED)" if yield_curve < 0 else ""
        print(f"  Yield Curve (2s10s): {yield_curve:+.2f}% {inverted}")
    print()

    inflation = macro['inflation']
    cpi = inflation['cpi_yoy']
    if isinstance(cpi, dict):
        print(f"  CPI (YoY): {format_indicator(cpi)}")
    else:
        print(f"  CPI (YoY): {cpi:.2f}%")
    
    core_cpi = inflation['core_cpi_yoy']
    if isinstance(core_cpi, dict):
        print(f"  Core CPI (YoY): {format_indicator(core_cpi)}")
    else:
        print(f"  Core CPI (YoY): {core_cpi:.2f}%")
    
    if 'tips_spread_10y' in inflation:
        tips = inflation['tips_spread_10y']
        if isinstance(tips, dict):
            print(f"  10Y TIPS Spread (market inflation expectations): {format_indicator(tips)}")
        else:
            if tips is not None:
                print(f"  10Y TIPS Spread (market inflation expectations): {tips:.2f}%")
    print()

    employment = macro['employment']
    unemp = employment['unemployment_rate']
    if isinstance(unemp, dict):
        print(f"  Unemployment Rate: {format_indicator(unemp)}")
    else:
        print(f"  Unemployment Rate: {unemp:.2f}%")
    
    payrolls = employment['nonfarm_payrolls']
    if isinstance(payrolls, dict):
        print(f"  Nonfarm Payrolls: {format_indicator(payrolls, 'k', 0)}")
    else:
        print(f"  Nonfarm Payrolls: {payrolls:,.0f}k")
    
    wages = employment['wage_growth_yoy']
    if isinstance(wages, dict):
        print(f"  Wage Growth (YoY): {format_indicator(wages)}")
    else:
        print(f"  Wage Growth (YoY): {wages:.2f}%")
    
    if 'initial_claims_4wk_avg' in employment:
        claims = employment['initial_claims_4wk_avg']
        if isinstance(claims, dict):
            # Convert from raw count to thousands
            claims_converted = {}
            for key, val in claims.items():
                claims_converted[key] = round(val / 1000, 0) if val is not None else None
            print(f"  Initial Claims (4-wk avg): {format_indicator(claims_converted, 'k', 0)}")
        else:
            if claims is not None:
                print(f"  Initial Claims (4-wk avg): {claims/1000:,.0f}k")
    print()

    # Manufacturing & Production
    if 'manufacturing' in macro:
        manufacturing = macro['manufacturing']
        print("🏭 MANUFACTURING & PRODUCTION")
        
        ind_prod = manufacturing.get('industrial_production_index')
        if ind_prod:
            if isinstance(ind_prod, dict):
                print(f"  Industrial Production Index: {format_indicator(ind_prod, '', 1)}")
            else:
                if ind_prod is not None:
                    print(f"  Industrial Production Index: {ind_prod:.1f}")
        
        housing = manufacturing.get('housing_starts_thousands')
        if housing:
            if isinstance(housing, dict):
                print(f"  Housing Starts: {format_indicator(housing, 'k units', 0)}")
            else:
                if housing is not None:
                    print(f"  Housing Starts: {housing:,.0f}k units")
        print()

    # Consumer
    if 'consumer' in macro:
        consumer = macro['consumer']
        print("🛒 CONSUMER INDICATORS")
        
        confidence = consumer.get('confidence_index')
        if confidence:
            if isinstance(confidence, dict):
                print(f"  Consumer Confidence Index: {format_indicator(confidence, '', 1)}")
            else:
                if confidence is not None:
                    print(f"  Consumer Confidence Index: {confidence:.1f}")
        
        retail = consumer.get('retail_sales_yoy_pct')
        if retail:
            if isinstance(retail, dict):
                print(f"  Retail Sales (YoY): {format_indicator(retail)}")
            else:
                if retail is not None:
                    print(f"  Retail Sales (YoY): {retail:.2f}%")
        print()

    # Credit Conditions
    if 'credit_conditions' in macro:
        credit = macro['credit_conditions']
        print("💳 CREDIT CONDITIONS")
        
        ig_spread = credit.get('investment_grade_spread_bps')
        if ig_spread:
            if isinstance(ig_spread, dict):
                print(f"  Investment Grade Spread: {format_indicator(ig_spread, ' bps', 0)}")
            else:
                if ig_spread is not None:
                    print(f"  Investment Grade Spread: {ig_spread:.0f} bps")
        
        hy_spread = credit.get('high_yield_spread_bps')
        if hy_spread:
            if isinstance(hy_spread, dict):
                print(f"  High Yield Spread: {format_indicator(hy_spread, ' bps', 0)}")
            else:
                if hy_spread is not None:
                    print(f"  High Yield Spread: {hy_spread:.0f} bps")
        print()

    # Monetary Liquidity
    if 'monetary_liquidity' in macro:
        liquidity = macro['monetary_liquidity']
        print("💵 MONETARY LIQUIDITY")
        
        m2 = liquidity.get('m2_supply_yoy_pct')
        if m2:
            if isinstance(m2, dict):
                print(f"  M2 Money Supply (YoY): {format_indicator(m2)}")
            else:
                if m2 is not None:
                    print(f"  M2 Money Supply (YoY): {m2:.2f}%")
        
        fed_bs = liquidity.get('fed_balance_sheet_billions')
        if fed_bs:
            if isinstance(fed_bs, dict):
                print(f"  Fed Balance Sheet: {format_indicator(fed_bs, 'B', 0)}")
            else:
                if fed_bs is not None:
                    print(f"  Fed Balance Sheet: {fed_bs:,.0f}B")
        print()

    # International Context
    if 'international' in macro:
        intl = macro['international']
        print("🌍 INTERNATIONAL CONTEXT")
        
        dxy = intl.get('dollar_index_30d_return')
        if dxy:
            if isinstance(dxy, dict):
                print(f"  Dollar Index (30d return): {format_indicator(dxy)}")
            else:
                if dxy is not None:
                    print(f"  Dollar Index (30d return): {dxy:+.2f}%")
        
        em = intl.get('emerging_markets_rel_return_30d')
        if em:
            if isinstance(em, dict):
                print(f"  EM vs SPY (30d relative): {format_indicator(em)}")
            else:
                if em is not None:
                    print(f"  EM vs SPY (30d relative): {em:+.2f}%")
        print()

    # Commodities
    if 'commodities' in macro:
        commodities = macro['commodities']
        print("🥇 COMMODITIES")
        
        gold = commodities.get('gold_return_30d')
        if gold:
            if isinstance(gold, dict):
                print(f"  Gold (30d return): {format_indicator(gold)}")
            else:
                if gold is not None:
                    print(f"  Gold (30d return): {gold:+.2f}%")
        
        oil = commodities.get('oil_return_30d')
        if oil:
            if isinstance(oil, dict):
                print(f"  Oil (30d return): {format_indicator(oil)}")
            else:
                if oil is not None:
                    print(f"  Oil (30d return): {oil:+.2f}%")
        print()

    # Recession Indicators
    if 'recession_indicators' in macro:
        recession = macro['recession_indicators']
        print("⚠️  RECESSION INDICATORS")
        
        sahm = recession.get('sahm_rule_value')
        if sahm is not None:
            print(f"  Sahm Rule: {sahm:.2f} {'⚠️  (≥0.50 signals recession)' if sahm >= 0.50 else '(normal)'}")
        
        nber = recession.get('nber_recession_binary')
        if nber is not None:
            status = "IN RECESSION" if nber == 1 else "Expansion"
            print(f"  NBER Status: {status}")
        print()

    # Recent events
    events = context_pack['recent_events']
    print(f"📰 RECENT EVENTS ({len(events)} events)")
    for event in events[:5]:  # Show first 5
        print(f"  [{event['date']}] {event['headline'][:70]}")
    if len(events) > 5:
        print(f"  ... and {len(events) - 5} more events")
    print()

    # Regime tags
    tags = context_pack['regime_tags']
    print(f"🏷️  REGIME TAGS: {', '.join(tags)}")
    print()
    print("=" * 70)


def save_context_pack(context_pack, output_path):
    """Save context pack to JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(context_pack, f, indent=2)

    print(f"💾 Saved to: {output_path}")
    print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate market context pack for AI trading strategy evaluation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate and display context pack
  python -m src.market_context.cli generate

  # Generate and save to file
  python -m src.market_context.cli generate --output data/context_packs/latest.json

  # Generate with custom output directory
  python -m src.market_context.cli generate -o data/context_packs/$(date +%Y-%m-%d).json
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate market context pack')
    generate_parser.add_argument(
        '-o', '--output',
        help='Output file path (default: print to stdout only)',
        type=str
    )

    args = parser.parse_args()

    if args.command == 'generate':
        generate_context_pack(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
