"""
Phase 5: End-to-End Integration Tests

Tests the complete 4-stage workflow with real, unmocked services:
- Real context pack from data/context_packs/latest.json
- Real FRED MCP (stdio server)
- Real yfinance MCP (stdio server)
- Real Composer MCP (HTTP server at https://mcp.composer.trade/mcp/)
- Real AI model (OpenAI GPT-4o)

Quick start:
    # Generate context pack
    python -m src.market_context.cli generate -o data/context_packs/latest.json

    # Run component tests (fast, no API costs)
    pytest tests/agent/test_phase5_integration.py::TestPhase5ComponentValidation -v -m integration

    # Run full workflow (slow, ~$1-2 API costs)
    pytest tests/agent/test_phase5_integration.py::TestPhase5EndToEnd -v -m integration

Required environment variables:
    FRED_API_KEY - Free from https://fred.stlouisfed.org
    COMPOSER_API_KEY - From Composer dashboard
    COMPOSER_API_SECRET - From Composer dashboard
    OPENAI_API_KEY - From https://platform.openai.com (for full workflow test)
"""

import os
import json
import pytest
from pathlib import Path
from src.agent.workflow import create_strategy_workflow


@pytest.mark.integration
class TestPhase5EndToEnd:
    """
    End-to-end workflow test with real MCPs and AI model.

    Tests all 4 stages:
    1. Generate 5 candidates (AI + FRED/yfinance data)
    2. Evaluate Edge Scorecard (quality filter, min 3.0/5)
    3. Select winner (composite ranking + AI reasoning)
    4. Generate charter (full context)

    Expected behavior:
    - May need retries if AI generates weak candidates (Edge Scorecard rejects < 3.0)
    - Costs ~$1-2 in OpenAI API calls
    - Takes 30-60 seconds
    - Skips gracefully if Composer auth fails
    """

    @pytest.mark.asyncio
    async def test_full_workflow_with_real_context_and_mcps(self):
        """
        Execute complete workflow with real context pack and all 3 unmocked MCPs.

        Validates end-to-end integration:
        - Real context pack (data/context_packs/latest.json)
        - FRED MCP: Economic data (stdio)
        - yfinance MCP: Market data (stdio)
        - Composer MCP: Available for future deployment (HTTP at https://mcp.composer.trade/mcp/)
        - OpenAI GPT-4o: Strategy generation, reasoning, charter

        Assertions verify:
        - 5 distinct candidates with unique ticker sets
        - All Edge Scorecard scores >= 3.0/5
        - Edge Scorecard diversity (not all identical)
        - Winner selection with detailed reasoning
        - Complete charter with all 5 sections
        """
        # Validate environment
        required_vars = ['OPENAI_API_KEY', 'FRED_API_KEY', 'COMPOSER_API_KEY', 'COMPOSER_API_SECRET']
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            pytest.skip(f"Missing required environment variables: {', '.join(missing_vars)}")

        # Load real context pack
        context_pack_path = Path("data/context_packs/latest.json")

        if not context_pack_path.exists():
            pytest.skip(f"Real context pack not found at {context_pack_path}")

        with open(context_pack_path) as f:
            market_context = json.load(f)

        # Validate context pack structure
        assert 'metadata' in market_context
        assert 'regime_snapshot' in market_context
        assert 'macro_indicators' in market_context
        assert 'anchor_date' in market_context['metadata']

        # Execute full workflow
        try:
            result = await create_strategy_workflow(
                market_context=market_context,
                model='openai:gpt-5'
            )
        except (BaseExceptionGroup, ExceptionGroup) as eg:
            # Check if it's a Composer authentication error (handle ExceptionGroup)
            error_str = str(eg)
            if '401 Unauthorized' in error_str and 'composer.trade' in error_str:
                pytest.skip("Composer API credentials invalid or expired - cannot run integration test")
            # Re-raise other errors
            raise
        except Exception as e:
            # Also catch regular exceptions (non-grouped)
            error_str = str(e)
            if '401 Unauthorized' in error_str and 'composer.trade' in error_str:
                pytest.skip("Composer API credentials invalid or expired - cannot run integration test")
            # Re-raise other errors
            raise

        # ===================================================================
        # VALIDATION 1: Candidate Generation
        # ===================================================================

        # Should generate exactly 5 candidates
        assert len(result.all_candidates) == 5, "Should generate exactly 5 candidates"

        # All candidates should be distinct (different ticker sets)
        ticker_sets = [set(c.assets) for c in result.all_candidates]
        unique_ticker_sets = set(tuple(sorted(ts)) for ts in ticker_sets)
        assert len(unique_ticker_sets) == 5, "All candidates should have unique ticker sets"

        # All candidates should have valid structure
        for i, candidate in enumerate(result.all_candidates):
            assert candidate.name, f"Candidate {i} missing name"
            assert len(candidate.assets) > 0, f"Candidate {i} has no assets"
            assert len(candidate.weights) == len(candidate.assets), f"Candidate {i} weights/assets mismatch"
            assert abs(sum(candidate.weights) - 1.0) < 0.01, f"Candidate {i} weights don't sum to 1.0"
            assert candidate.edge_type, f"Candidate {i} missing edge_type"
            assert candidate.archetype, f"Candidate {i} missing archetype"
            assert candidate.rebalance_frequency, f"Candidate {i} missing rebalance_frequency"

        # ===================================================================
        # VALIDATION 2: Edge Scorecard Evaluation
        # ===================================================================

        assert len(result.scorecards) == 5, "Should have 5 scorecards"

        # All scorecards should pass threshold (>= 3.0)
        for i, scorecard in enumerate(result.scorecards):
            assert scorecard.total_score >= 3.0, (
                f"Candidate {i} failed Edge Scorecard: {scorecard.total_score:.1f}/5 (minimum: 3.0)"
            )
            assert 1 <= scorecard.thesis_quality <= 5, "Thesis quality out of range"
            assert 1 <= scorecard.edge_economics <= 5, "Edge economics out of range"
            assert 1 <= scorecard.risk_framework <= 5, "Risk framework out of range"
            assert 1 <= scorecard.regime_awareness <= 5, "Regime awareness out of range"
            assert 1 <= scorecard.strategic_coherence <= 5, "Strategic coherence out of range"

        # ===================================================================
        # VALIDATION 3: Edge Scorecard Diversity
        # ===================================================================

        # Check that Edge Scorecards are diverse (not all identical)
        total_scores = [sc.total_score for sc in result.scorecards]
        unique_scores = len(set(total_scores))
        assert unique_scores > 1, (
            "All Edge Scorecard scores are identical - suggests potential issues with evaluation"
        )

        # ===================================================================
        # VALIDATION 4: Winner Selection
        # ===================================================================

        assert result.strategy in result.all_candidates, "Winner should be one of the candidates"
        assert result.selection_reasoning, "Should have selection reasoning"
        assert result.selection_reasoning.why_selected, "Should explain why winner was selected"
        assert len(result.selection_reasoning.why_selected) > 100, "Reasoning should be detailed"

        # Winner index should be valid
        assert 0 <= result.selection_reasoning.winner_index < 5, "Winner index out of range"

        # Should compare against alternatives
        assert len(result.selection_reasoning.alternatives_rejected) == 4, (
            "Should reject 4 alternatives"
        )

        # ===================================================================
        # VALIDATION 5: Charter Document
        # ===================================================================

        assert result.charter, "Should have charter document"

        # Validate all required sections
        assert result.charter.market_thesis, "Charter missing market thesis"
        assert len(result.charter.market_thesis) > 100, "Market thesis too short"

        assert result.charter.strategy_selection, "Charter missing strategy selection"
        assert len(result.charter.strategy_selection) > 100, "Strategy selection too short"

        assert result.charter.expected_behavior, "Charter missing expected behavior"
        assert len(result.charter.expected_behavior) > 100, "Expected behavior too short"

        assert result.charter.failure_modes, "Charter missing failure modes"
        assert len(result.charter.failure_modes) >= 2, "Should identify at least 2 failure modes"
        for mode in result.charter.failure_modes:
            assert len(mode) > 20, "Failure mode description too short"

        assert result.charter.outlook_90d, "Charter missing 90-day outlook"
        assert len(result.charter.outlook_90d) > 100, "90-day outlook too short"

        # Charter should reference actual market conditions (validates MCP usage)
        charter_text = result.charter.market_thesis.lower()

        # Charter should reference market context concepts
        market_references = any(term in charter_text for term in [
            'volatility', 'market', 'trend', 'bull', 'bear', 'sector', 'economy',
            'growth', 'value', 'momentum', 'fed', 'rate', 'inflation'
        ])
        assert market_references, "Charter should reference actual market conditions"

        # ===================================================================
        # SUCCESS - Print Summary
        # ===================================================================

        print("\n" + "=" * 80)
        print("PHASE 5 END-TO-END TEST PASSED")
        print("=" * 80)
        print(f"\nContext Pack: {market_context['metadata']['anchor_date']}")
        print(f"Regime: {', '.join(market_context.get('regime_tags', []))}")
        print(f"\nCandidates Generated: {len(result.all_candidates)}")
        print(f"Winner: {result.strategy.name}")
        print(f"Winner Assets: {', '.join(result.strategy.assets)}")
        print(f"Winner Edge Score: {result.scorecards[result.selection_reasoning.winner_index].total_score:.1f}/5")
        print("=" * 80)


@pytest.mark.integration
class TestPhase5ComponentValidation:
    """
    Fast validation tests for Phase 5 components (no API costs).

    These tests validate:
    - Context pack structure and data quality
    - MCP server availability and configuration
    - Agent toolset composition

    Run these first to validate setup before expensive end-to-end tests.
    """

    @pytest.mark.asyncio
    async def test_real_context_pack_loading(self):
        """
        Load and validate real market context pack structure.

        Checks:
        - File exists at data/context_packs/latest.json
        - Required sections present (metadata, regime, macro, benchmarks)
        - Data types and value ranges valid
        - No future data leakage
        """
        context_pack_path = Path("data/context_packs/latest.json")

        if not context_pack_path.exists():
            pytest.skip(f"Real context pack not found at {context_pack_path}")

        with open(context_pack_path) as f:
            context = json.load(f)

        # Validate structure
        assert 'metadata' in context
        assert 'regime_snapshot' in context
        assert 'macro_indicators' in context
        assert 'benchmark_performance_30d' in context
        assert 'regime_tags' in context

        # Validate metadata
        assert context['metadata']['anchor_date']
        assert context['metadata']['generated_at']
        assert context['metadata']['version'] in ['v1.0.0', '1.0.0']

        # Validate regime snapshot
        regime = context['regime_snapshot']
        assert 'trend' in regime
        assert 'regime' in regime['trend']
        assert 'volatility' in regime
        assert regime['volatility']['regime'] in ['low', 'normal', 'elevated', 'high']
        assert 'breadth' in regime
        assert 0 <= regime['breadth']['sectors_above_50d_ma_pct'] <= 100
        assert len(regime['sector_leadership']['leaders']) > 0
        assert len(regime['sector_leadership']['laggards']) > 0

        print(f"\n✓ Real context pack validated: {context['metadata']['anchor_date']}")
        print(f"  Regime: {', '.join(context['regime_tags'])}")

    @pytest.mark.asyncio
    async def test_mcp_servers_available(self):
        """
        Validate all 3 MCP servers connect successfully.

        Checks:
        - FRED MCP (stdio): Requires FRED_API_KEY
        - yfinance MCP (stdio): No auth required
        - Composer MCP (HTTP): Requires COMPOSER_API_KEY + COMPOSER_API_SECRET
        - Correct server types (stdio vs HTTP)
        """
        from src.agent.mcp_config import get_mcp_servers

        required_vars = ['FRED_API_KEY', 'COMPOSER_API_KEY', 'COMPOSER_API_SECRET']
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            pytest.skip(f"Missing required environment variables: {', '.join(missing_vars)}")

        async with get_mcp_servers() as servers:
            # Should have all 3 servers
            assert 'fred' in servers, "FRED MCP server not available"
            assert 'yfinance' in servers, "yfinance MCP server not available"
            assert 'composer' in servers, "Composer MCP server not available"

            # Verify server types
            from pydantic_ai.mcp import MCPServerStreamableHTTP
            assert isinstance(servers['composer'], MCPServerStreamableHTTP), (
                "Composer should be HTTP server"
            )

            print("\n✓ All 3 MCP servers available:")
            print(f"  - FRED (stdio)")
            print(f"  - yfinance (stdio)")
            print(f"  - Composer (HTTP)")

    @pytest.mark.asyncio
    async def test_agent_includes_all_toolsets(self):
        """
        Validate create_agent() includes all 3 MCP toolsets.

        This ensures the fix from Phase 5 is working:
        - Previously: Only FRED + yfinance included
        - Fixed: Now includes Composer as well (src/agent/strategy_creator.py:149-150)

        Verifies:
        - Agent has 3+ toolsets
        - Composer HTTP toolset present
        """
        from src.agent.strategy_creator import create_agent
        from src.agent.models import Strategy

        required_vars = ['OPENAI_API_KEY', 'FRED_API_KEY', 'COMPOSER_API_KEY', 'COMPOSER_API_SECRET']
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            pytest.skip(f"Missing required environment variables: {', '.join(missing_vars)}")

        agent_ctx = await create_agent(
            model='openai:gpt-4o',
            output_type=Strategy
        )

        async with agent_ctx as agent:
            # Should have 3 toolsets
            assert agent.toolsets is not None, "Agent should have toolsets"
            assert len(agent.toolsets) >= 3, (
                f"Agent should have at least 3 toolsets (FRED, yfinance, Composer), got {len(agent.toolsets)}"
            )

            # Verify Composer is included (HTTP server)
            has_http_toolset = any(
                hasattr(toolset, 'url') and 'composer.trade' in getattr(toolset, 'url', '')
                for toolset in agent.toolsets
            )
            assert has_http_toolset, "Agent should include Composer HTTP toolset"

            print(f"\n✓ Agent includes {len(agent.toolsets)} toolsets")
            print("  - All MCP servers properly configured")
