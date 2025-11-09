"""
Baseline Generation Script for Candidate Quality Improvement

Runs 10 test candidate generations and records metrics to establish baseline
before implementing quality improvements.

Usage:
    python scripts/generate_baseline.py
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

from src.agent.stages.candidate_generator import CandidateGenerator
from src.market_context.assembler import assemble_market_context_pack
from src.token_tracking import TokenTracker


async def generate_single_run(run_id: int, market_context: dict, model: str) -> Dict[str, Any]:
    """Generate candidates for a single run and collect metrics."""
    print(f"\n{'='*60}")
    print(f"Run {run_id}/10")
    print(f"{'='*60}")

    generator = CandidateGenerator()
    tracker = TokenTracker()

    try:
        candidates = await generator.generate(market_context, model)

        # Collect metrics
        metrics = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "candidate_count": len(candidates),
            "token_usage": tracker.total_tokens,
            "candidates": []
        }

        # Analyze each candidate
        for i, candidate in enumerate(candidates, 1):
            candidate_metrics = {
                "name": candidate.name,
                "archetype": candidate.archetype,
                "edge_type": candidate.edge_type,
                "asset_count": len(candidate.assets),
                "has_logic_tree": bool(candidate.logic_tree),
                "rebalance_frequency": candidate.rebalance_frequency,
                "max_weight": max(candidate.weights.values()) if candidate.weights else 0,
                "thesis_length": len(candidate.thesis_document),
                "rationale_length": len(candidate.rebalancing_rationale)
            }

            # Check for quantification keywords
            thesis_lower = candidate.thesis_document.lower()
            candidate_metrics["has_sharpe"] = "sharpe" in thesis_lower
            candidate_metrics["has_alpha"] = "alpha" in thesis_lower
            candidate_metrics["has_drawdown"] = "drawdown" in thesis_lower or "dd" in thesis_lower
            candidate_metrics["has_benchmark"] = any(b in thesis_lower for b in ["spy", "qqq", "agg", "60/40"])

            # Check for conditional keywords
            conditional_keywords = ["if ", "when ", "rotate", "dynamic", "tactical", "vix >"]
            candidate_metrics["has_conditional_keywords"] = any(k in thesis_lower for k in conditional_keywords)

            metrics["candidates"].append(candidate_metrics)

        # Run validation
        validation_errors = generator._validate_semantics(candidates, market_context)
        metrics["validation_error_count"] = len(validation_errors)
        metrics["validation_errors"] = validation_errors

        # Compute aggregate scores
        metrics["avg_thesis_length"] = sum(c["thesis_length"] for c in metrics["candidates"]) / len(candidates)
        metrics["avg_asset_count"] = sum(c["asset_count"] for c in metrics["candidates"]) / len(candidates)
        metrics["avg_max_weight"] = sum(c["max_weight"] for c in metrics["candidates"]) / len(candidates)
        metrics["pct_with_logic_tree"] = sum(c["has_logic_tree"] for c in metrics["candidates"]) / len(candidates)
        metrics["pct_with_quantification"] = sum(
            c["has_sharpe"] or c["has_alpha"] or c["has_drawdown"]
            for c in metrics["candidates"]
        ) / len(candidates)
        metrics["pct_with_conditional_keywords"] = sum(
            c["has_conditional_keywords"] for c in metrics["candidates"]
        ) / len(candidates)

        return metrics

    except Exception as e:
        print(f"❌ Run {run_id} failed: {e}")
        return {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": str(e)
        }


async def main():
    """Run 10 baseline generations and save results."""
    print("="*60)
    print("BASELINE GENERATION - Phase 0a")
    print("="*60)
    print("\nGenerating market context pack...")

    # Get environment variables
    fred_api_key = os.getenv('FRED_API_KEY')
    if not fred_api_key:
        raise ValueError("FRED_API_KEY not found in environment")

    model = os.getenv('DEFAULT_MODEL', 'openai:gpt-4o')
    print(f"Using model: {model}")

    # Generate market context once (reuse for all runs)
    market_context = assemble_market_context_pack(fred_api_key=fred_api_key)
    print("✅ Market context generated")

    # Run 10 generations
    results = []
    for run_id in range(1, 11):
        metrics = await generate_single_run(run_id, market_context, model)
        results.append(metrics)

        # Brief pause between runs
        await asyncio.sleep(2)

    # Aggregate results
    successful_runs = [r for r in results if r.get("success")]
    failed_runs = [r for r in results if not r.get("success")]

    aggregate = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "total_runs": 10,
            "successful_runs": len(successful_runs),
            "failed_runs": len(failed_runs)
        },
        "aggregate_metrics": {},
        "runs": results
    }

    if successful_runs:
        aggregate["aggregate_metrics"] = {
            "avg_candidate_count": sum(r["candidate_count"] for r in successful_runs) / len(successful_runs),
            "avg_token_usage": sum(r["token_usage"] for r in successful_runs) / len(successful_runs),
            "avg_validation_errors": sum(r["validation_error_count"] for r in successful_runs) / len(successful_runs),
            "avg_thesis_length": sum(r["avg_thesis_length"] for r in successful_runs) / len(successful_runs),
            "avg_asset_count": sum(r["avg_asset_count"] for r in successful_runs) / len(successful_runs),
            "avg_max_weight": sum(r["avg_max_weight"] for r in successful_runs) / len(successful_runs),
            "avg_pct_with_logic_tree": sum(r["pct_with_logic_tree"] for r in successful_runs) / len(successful_runs),
            "avg_pct_with_quantification": sum(r["pct_with_quantification"] for r in successful_runs) / len(successful_runs),
            "avg_pct_with_conditional_keywords": sum(r["pct_with_conditional_keywords"] for r in successful_runs) / len(successful_runs),
        }

    # Save results
    output_path = Path("data/baselines/pre_improvements.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(aggregate, f, indent=2)

    print(f"\n{'='*60}")
    print("BASELINE GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"\n✅ Successful runs: {len(successful_runs)}/10")
    print(f"❌ Failed runs: {len(failed_runs)}/10")

    if successful_runs:
        print(f"\n📊 Aggregate Metrics:")
        for key, value in aggregate["aggregate_metrics"].items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")

    print(f"\n💾 Results saved to: {output_path}")

    return aggregate


if __name__ == "__main__":
    asyncio.run(main())
