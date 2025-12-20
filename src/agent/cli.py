#!/usr/bin/env python3
"""CLI for AI trading strategy workflow execution.

Execute the complete strategy creation workflow from the command line.

Examples:
    # Run workflow with defaults
    python -m src.agent.cli run

    # Run with specific model and cohort ID
    python -m src.agent.cli run --model openai:gpt-4o --cohort-id 2025-Q1

    # Run with custom context pack
    python -m src.agent.cli run --context-pack data/context_packs/2025-12-20.json

    # Run with validation checks (optional assertions)
    python -m src.agent.cli run --validate
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.agent.workflow import create_strategy_workflow
from src.agent.strategy_creator import DEFAULT_MODEL


def load_env_vars():
    """Load and validate required environment variables.

    Required:
        - FRED_API_KEY: Federal Reserve Economic Data API key
        - At least one LLM provider key (OPENAI_API_KEY, ANTHROPIC_API_KEY,
          DEEPSEEK_API_KEY, or KIMI_API_KEY)
        - COMPOSER_API_KEY: Composer trading platform API key
        - COMPOSER_API_SECRET: Composer trading platform API secret

    Exits with code 1 if required variables are missing.
    """
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)

    missing_vars = []

    # FRED is always required (market context depends on it)
    if not os.getenv('FRED_API_KEY'):
        missing_vars.append('FRED_API_KEY')

    # At least one LLM provider key required
    llm_keys = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'DEEPSEEK_API_KEY', 'KIMI_API_KEY']
    if not any(os.getenv(key) for key in llm_keys):
        missing_vars.append('OPENAI_API_KEY (or ANTHROPIC_API_KEY, DEEPSEEK_API_KEY, KIMI_API_KEY)')

    # Composer keys required for deployment
    if not os.getenv('COMPOSER_API_KEY'):
        missing_vars.append('COMPOSER_API_KEY')
    if not os.getenv('COMPOSER_API_SECRET'):
        missing_vars.append('COMPOSER_API_SECRET')

    if missing_vars:
        print("Missing required environment variables:")
        for var in missing_vars:
            print(f"  {var}")
        print("\nPlease add them to your .env file:")
        print("  FRED_API_KEY=your_fred_key")
        print("  OPENAI_API_KEY=your_openai_key  # or other LLM provider")
        print("  COMPOSER_API_KEY=your_composer_key")
        print("  COMPOSER_API_SECRET=your_composer_secret")
        sys.exit(1)


async def run_workflow_async(args):
    """Execute the strategy workflow asynchronously.

    Args:
        args: Parsed CLI arguments containing:
            - context_pack: Path to market context JSON file
            - model: LLM model identifier (optional)
            - cohort_id: Cohort identifier for persistence (optional)
            - validate: Whether to run validation checks

    Returns:
        WorkflowResult with strategy, charter, and deployment info
    """
    # Load context pack
    context_pack_path = Path(args.context_pack)

    if not context_pack_path.exists():
        print(f"Context pack not found at: {context_pack_path}")
        print("\nGenerate one with:")
        print(f"  python -m src.market_context.cli generate -o {context_pack_path}")
        sys.exit(1)

    with open(context_pack_path) as f:
        market_context = json.load(f)

    # Determine model
    model = args.model or os.getenv('DEFAULT_MODEL', DEFAULT_MODEL)

    print("=" * 80)
    print("AI TRADING STRATEGY WORKFLOW")
    print("=" * 80)
    print(f"Context Pack: {context_pack_path}")
    print(f"  Anchor Date: {market_context['metadata']['anchor_date']}")
    print(f"  Regime: {', '.join(market_context.get('regime_tags', []))}")
    print(f"Model: {model}")
    if args.cohort_id:
        print(f"Cohort ID: {args.cohort_id}")
    print("=" * 80)
    print()

    # Execute workflow
    result = await create_strategy_workflow(
        market_context=market_context,
        model=model,
        cohort_id=args.cohort_id,
    )

    return result


def validate_result(result):
    """Run optional validation checks on workflow result.

    These mirror the assertions from the integration test but report
    as warnings rather than hard failures.

    Args:
        result: WorkflowResult from create_strategy_workflow()

    Returns:
        Tuple of (passed_count, warning_count, warnings_list)
    """
    warnings = []
    passed = 0

    # Validate candidates
    if len(result.all_candidates) == 5:
        passed += 1
    else:
        warnings.append(f"Expected 5 candidates, got {len(result.all_candidates)}")

    # Check unique ticker sets
    ticker_sets = [set(c.assets) for c in result.all_candidates]
    unique_sets = set(tuple(sorted(ts)) for ts in ticker_sets)
    if len(unique_sets) == len(result.all_candidates):
        passed += 1
    else:
        warnings.append("Not all candidates have unique ticker sets")

    # Validate scorecards
    if len(result.scorecards) == len(result.all_candidates):
        passed += 1
    else:
        warnings.append(f"Scorecard count mismatch: {len(result.scorecards)} vs {len(result.all_candidates)} candidates")

    # Check passing threshold
    passing = [sc for sc in result.scorecards if sc.total_score >= 3.0]
    if len(passing) >= 3:
        passed += 1
    else:
        warnings.append(f"Only {len(passing)}/5 candidates passed Edge Scorecard (minimum: 3)")

    # Validate winner
    if result.strategy in result.all_candidates:
        passed += 1
    else:
        warnings.append("Winner not found in candidates list")

    # Validate selection reasoning
    if result.selection_reasoning and result.selection_reasoning.why_selected:
        passed += 1
    else:
        warnings.append("Missing selection reasoning")

    # Validate charter
    if result.charter:
        passed += 1
        if result.charter.market_thesis and len(result.charter.market_thesis) > 100:
            passed += 1
        else:
            warnings.append("Charter market thesis too short or missing")

        if result.charter.failure_modes and len(result.charter.failure_modes) >= 2:
            passed += 1
        else:
            warnings.append("Charter missing failure modes (need at least 2)")
    else:
        warnings.append("Missing charter document")

    # Validate deployment
    if result.symphony_id:
        passed += 1
    else:
        warnings.append("Symphony not deployed to Composer")

    return passed, len(warnings), warnings


def run_workflow(args):
    """Synchronous wrapper for async workflow execution.

    Args:
        args: Parsed CLI arguments
    """
    try:
        result = asyncio.run(run_workflow_async(args))

        # Print success summary
        print("\n" + "=" * 80)
        print("WORKFLOW COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"\nWinner: {result.strategy.name}")
        print(f"Assets: {', '.join(result.strategy.assets)}")

        # Show weights
        if isinstance(result.strategy.weights, dict):
            weight_strs = [f"{asset}: {weight:.1%}" for asset, weight in result.strategy.weights.items()]
            print(f"Weights: {', '.join(weight_strs)}")

        # Show edge score
        winner_idx = result.selection_reasoning.winner_index
        if winner_idx < len(result.scorecards):
            print(f"Edge Score: {result.scorecards[winner_idx].total_score:.1f}/5")

        # Show deployment info
        if result.symphony_id:
            print(f"\nComposer Symphony ID: {result.symphony_id}")
            print(f"Deployed At: {result.deployed_at}")
        else:
            print("\nDeployment: Skipped (Composer unavailable)")

        print("=" * 80)

        # Run optional validation
        if args.validate:
            print("\n" + "-" * 40)
            print("VALIDATION RESULTS")
            print("-" * 40)
            passed, warning_count, warnings = validate_result(result)
            print(f"Checks passed: {passed}")
            if warnings:
                print(f"Warnings: {warning_count}")
                for w in warnings:
                    print(f"  - {w}")
            else:
                print("All validation checks passed!")
            print("-" * 40)

    except (BaseExceptionGroup, ExceptionGroup) as eg:
        error_str = str(eg)
        if '401 Unauthorized' in error_str and 'composer.trade' in error_str:
            print("\nComposer API credentials invalid or expired.")
            print("Please check COMPOSER_API_KEY and COMPOSER_API_SECRET in .env")
            sys.exit(1)
        raise

    except Exception as e:
        error_str = str(e)
        if '401 Unauthorized' in error_str and 'composer.trade' in error_str:
            print("\nComposer API credentials invalid or expired.")
            print("Please check COMPOSER_API_KEY and COMPOSER_API_SECRET in .env")
            sys.exit(1)
        print(f"\nWorkflow failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Execute AI trading strategy creation workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run workflow with defaults
  python -m src.agent.cli run

  # Run with specific model
  python -m src.agent.cli run --model openai:gpt-4o

  # Run with cohort ID for persistence
  python -m src.agent.cli run --cohort-id 2025-Q1

  # Run with custom context pack
  python -m src.agent.cli run --context-pack data/context_packs/2025-12-20.json

  # Run with validation checks
  python -m src.agent.cli run --validate

Required environment variables:
  FRED_API_KEY          - Federal Reserve Economic Data API key
  OPENAI_API_KEY        - OpenAI API key (or other LLM provider)
  COMPOSER_API_KEY      - Composer trading platform API key
  COMPOSER_API_SECRET   - Composer trading platform API secret
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Run command
    run_parser = subparsers.add_parser('run', help='Execute strategy creation workflow')
    run_parser.add_argument(
        '--context-pack',
        default='data/context_packs/latest.json',
        help='Path to market context pack JSON file (default: data/context_packs/latest.json)',
        type=str,
    )
    run_parser.add_argument(
        '--model',
        default=None,
        help=f'LLM model identifier (default: {DEFAULT_MODEL})',
        type=str,
    )
    run_parser.add_argument(
        '--cohort-id',
        default=None,
        help='Cohort identifier for persistence (e.g., 2025-Q1)',
        type=str,
    )
    run_parser.add_argument(
        '--validate',
        action='store_true',
        help='Run validation checks on workflow result',
    )

    args = parser.parse_args()

    if args.command == 'run':
        load_env_vars()
        run_workflow(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
