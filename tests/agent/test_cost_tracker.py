"""
Tests for CostTracker class.

Tests budget enforcement, cost estimation, and call logging.
"""

import pytest
from src.agent.cost_tracker import CostTracker, BudgetExceededError


class TestCostTrackerInitialization:
    """Test CostTracker initialization"""

    def test_cost_tracker_initializes_with_valid_budget(self):
        """CostTracker initializes with positive budget"""
        tracker = CostTracker(max_budget=10.0)

        assert tracker.max_budget == 10.0
        assert tracker.total_cost == 0.0
        assert len(tracker.call_log) == 0

    def test_cost_tracker_rejects_negative_budget(self):
        """CostTracker raises error for negative budget"""
        with pytest.raises(ValueError, match="non-negative"):
            CostTracker(max_budget=-5.0)

    def test_cost_tracker_accepts_zero_budget(self):
        """CostTracker accepts zero budget (for testing)"""
        tracker = CostTracker(max_budget=0.0)
        assert tracker.max_budget == 0.0


class TestCostEstimation:
    """Test cost estimation for different models"""

    def test_gpt4o_cost_estimation(self):
        """GPT-4o costs estimated correctly"""
        tracker = CostTracker(max_budget=10.0)

        # GPT-4o: $2.50/$10 per 1M tokens = $0.0025/$0.01 per 1K tokens
        # 1000 prompt + 500 completion = (1000 * 0.0025/1000) + (500 * 0.01/1000)
        # = 0.0025 + 0.005 = $0.0075
        cost = tracker.estimate_cost('openai:gpt-4o', 1000, 500)

        assert cost == pytest.approx(0.0075, abs=0.0001)

    def test_claude_cost_estimation(self):
        """Claude 3.5 Sonnet costs estimated correctly"""
        tracker = CostTracker(max_budget=10.0)

        # Claude: $3/$15 per 1M tokens = $0.003/$0.015 per 1K tokens
        # 1000 prompt + 500 completion = (1000 * 0.003/1000) + (500 * 0.015/1000)
        # = 0.003 + 0.0075 = $0.0105
        cost = tracker.estimate_cost('anthropic:claude-3-5-sonnet-20241022', 1000, 500)

        assert cost == pytest.approx(0.0105, abs=0.0001)

    def test_gemini_free_tier(self):
        """Gemini 2.0 Flash free tier costs zero"""
        tracker = CostTracker(max_budget=10.0)

        cost = tracker.estimate_cost('gemini:gemini-2.0-flash-exp', 10000, 5000)

        assert cost == 0.0

    def test_unknown_model_uses_default_pricing(self):
        """Unknown models use default pricing (Claude rates)"""
        tracker = CostTracker(max_budget=10.0)

        cost = tracker.estimate_cost('unknown:model', 1000, 500)

        # Should use default (same as Claude)
        expected = (1000 * 0.003/1000) + (500 * 0.015/1000)
        assert cost == pytest.approx(expected, abs=0.0001)


class TestBudgetEnforcement:
    """Test budget limit enforcement"""

    def test_budget_exceeded_raises_error(self):
        """BudgetExceededError raised when budget exceeded"""
        tracker = CostTracker(max_budget=1.0)

        # Large call should exceed budget
        # GPT-4o: $0.0025/$0.01 per 1K tokens
        # 200K prompt + 100K completion = (200 * 0.0025) + (100 * 0.01) = 0.5 + 1.0 = $1.50
        with pytest.raises(BudgetExceededError, match="Budget exceeded"):
            tracker.record_call('openai:gpt-4o', 200000, 100000)  # ~$1.50

    def test_budget_not_exceeded_succeeds(self):
        """Call within budget succeeds"""
        tracker = CostTracker(max_budget=1.0)

        # Small call should succeed
        tracker.record_call('openai:gpt-4o', 1000, 500)  # ~$0.0075

        assert tracker.total_cost < 1.0
        assert len(tracker.call_log) == 1

    def test_cumulative_budget_enforcement(self):
        """Multiple calls accumulate and enforce budget"""
        tracker = CostTracker(max_budget=0.04)

        # Each call costs ~$0.0125 (1K prompt + 1K completion)
        # First call OK
        tracker.record_call('openai:gpt-4o', 1000, 1000)  # ~$0.0125
        assert len(tracker.call_log) == 1

        # Second call OK
        tracker.record_call('openai:gpt-4o', 1000, 1000)  # ~$0.0250 cumulative
        assert len(tracker.call_log) == 2

        # Third call OK
        tracker.record_call('openai:gpt-4o', 1000, 1000)  # ~$0.0375 cumulative
        assert len(tracker.call_log) == 3

        # Fourth call exceeds budget ($0.05 > $0.04)
        with pytest.raises(BudgetExceededError):
            tracker.record_call('openai:gpt-4o', 1000, 1000)


class TestCallLogging:
    """Test call logging functionality"""

    def test_call_log_records_details(self):
        """Call log captures all call details"""
        tracker = CostTracker(max_budget=10.0)

        tracker.record_call('openai:gpt-4o', 1000, 500)

        assert len(tracker.call_log) == 1
        log_entry = tracker.call_log[0]

        assert log_entry['model'] == 'openai:gpt-4o'
        assert log_entry['prompt_tokens'] == 1000
        assert log_entry['completion_tokens'] == 500
        assert 'cost' in log_entry
        assert 'cumulative_cost' in log_entry

    def test_cumulative_cost_tracked_correctly(self):
        """Cumulative cost increments correctly"""
        tracker = CostTracker(max_budget=10.0)

        tracker.record_call('openai:gpt-4o', 1000, 500)
        first_cost = tracker.call_log[0]['cumulative_cost']

        tracker.record_call('openai:gpt-4o', 1000, 500)
        second_cost = tracker.call_log[1]['cumulative_cost']

        assert second_cost > first_cost
        assert second_cost == pytest.approx(first_cost * 2, abs=0.0001)


class TestCostSummary:
    """Test cost summary functionality"""

    def test_get_summary_returns_correct_info(self):
        """get_summary returns complete cost information"""
        tracker = CostTracker(max_budget=10.0)

        tracker.record_call('openai:gpt-4o', 1000, 500)
        tracker.record_call('openai:gpt-4o', 2000, 1000)

        summary = tracker.get_summary()

        assert 'total_cost' in summary
        assert 'call_count' in summary
        assert 'remaining_budget' in summary
        assert 'budget_used_pct' in summary

        assert summary['call_count'] == 2
        assert summary['total_cost'] > 0
        assert summary['remaining_budget'] < 10.0
        assert 0 < summary['budget_used_pct'] < 100

    def test_empty_tracker_summary(self):
        """Summary works for tracker with no calls"""
        tracker = CostTracker(max_budget=5.0)

        summary = tracker.get_summary()

        assert summary['total_cost'] == 0.0
        assert summary['call_count'] == 0
        assert summary['remaining_budget'] == 5.0
        assert summary['budget_used_pct'] == 0.0

    def test_budget_used_percentage_calculation(self):
        """Budget used percentage calculated correctly"""
        tracker = CostTracker(max_budget=1.0)

        # Spend approximately half the budget
        tracker.record_call('openai:gpt-4o', 20000, 10000)  # ~$0.15

        summary = tracker.get_summary()

        # Should be around 15% used
        assert 10 < summary['budget_used_pct'] < 20
