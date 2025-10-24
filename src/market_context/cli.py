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
    print(f"  Trend: {regime['trend']['regime'].upper()} (SPY {regime['trend']['SPY_vs_200d_ma']:+.2f}% vs 200d MA)")
    print(f"  Volatility: {regime['volatility']['regime'].upper()} (VIX: {regime['volatility']['VIX_current']:.2f})")
    print(f"  Breadth: {regime['breadth']['sectors_above_50d_ma_pct']:.1f}% sectors above 50d MA")

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
    print(f"    Momentum premium: {factor['momentum_premium_30d']:+.2f}%")
    print(f"    Quality premium: {factor['quality_premium_30d']:+.2f}%")
    print(f"    Size premium: {factor['size_premium_30d']:+.2f}%")
    print()

    # Benchmark performance
    if 'benchmark_performance_30d' in context_pack:
        benchmarks = context_pack['benchmark_performance_30d']
        print("📈 BENCHMARK PERFORMANCE (30d)")
        for ticker in ['SPY', 'QQQ', 'AGG', '60_40', 'risk_parity']:
            if ticker in benchmarks:
                bench = benchmarks[ticker]
                display_name = ticker.replace('_', '/').upper()
                print(f"  {display_name:12s} Return: {bench['return_pct']:+6.2f}%  Vol: {bench['volatility_annualized']:5.2f}%  Sharpe: {bench['sharpe_ratio']:5.2f}")
        print()

    # Macro indicators
    macro = context_pack['macro_indicators']
    print("💰 MACRO INDICATORS")
    rates = macro['interest_rates']
    print(f"  Fed Funds Rate: {rates['fed_funds_rate']:.2f}%")
    print(f"  10Y Treasury: {rates['treasury_10y']:.2f}%")
    print(f"  2Y Treasury: {rates['treasury_2y']:.2f}%")
    print(f"  Yield Curve (2s10s): {rates['yield_curve_2s10s']:+.2f}% {'(INVERTED)' if rates['yield_curve_2s10s'] < 0 else ''}")
    print()

    inflation = macro['inflation']
    print(f"  CPI (YoY): {inflation['cpi_yoy']:.2f}%")
    print(f"  Core CPI (YoY): {inflation['core_cpi_yoy']:.2f}%")
    print()

    employment = macro['employment']
    print(f"  Unemployment Rate: {employment['unemployment_rate']:.2f}%")
    print(f"  Nonfarm Payrolls: {employment['nonfarm_payrolls']:,.0f}k")
    print(f"  Wage Growth (YoY): {employment['wage_growth_yoy']:.2f}%")
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
