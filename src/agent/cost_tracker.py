"""
Cost tracking and budget enforcement for AI agent workflows.

Tracks API costs across multiple provider calls and enforces budget limits.
"""

from typing import List, Dict


class BudgetExceededError(Exception):
    """Raised when API costs exceed budget limit"""
    pass


class CostTracker:
    """
    Track API costs and enforce budget limits.

    Usage:
        >>> tracker = CostTracker(max_budget=10.0)
        >>> tracker.record_call('openai:gpt-4o', 1000, 500)
        >>> print(f"Total cost: ${tracker.total_cost:.2f}")
        Total cost: $0.01

    Attributes:
        max_budget: Maximum allowed cost in USD
        total_cost: Cumulative cost across all calls
        call_log: List of all API calls with costs
    """

    def __init__(self, max_budget: float):
        """
        Initialize cost tracker with budget limit.

        Args:
            max_budget: Maximum allowed cost in USD

        Raises:
            ValueError: If max_budget is negative
        """
        if max_budget < 0:
            raise ValueError(f"max_budget must be non-negative, got {max_budget}")

        self.max_budget = max_budget
        self.total_cost = 0.0
        self.call_log: List[Dict] = []

    def estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost based on model pricing.

        Pricing as of October 2024:
        - Claude 3.5 Sonnet: $3/$15 per 1M tokens (input/output)
        - GPT-4o: $2.50/$10 per 1M tokens
        - Gemini 2.0 Flash: Free tier

        Args:
            model: Model identifier (e.g., 'openai:gpt-4o')
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Estimated cost in USD
        """
        # Pricing table (per 1000 tokens)
        pricing = {
            'anthropic:claude-3-5-sonnet-20241022': {
                'input': 0.003 / 1000,   # $3 per 1M tokens
                'output': 0.015 / 1000   # $15 per 1M tokens
            },
            'openai:gpt-4o': {
                'input': 0.0025 / 1000,  # $2.50 per 1M tokens
                'output': 0.010 / 1000   # $10 per 1M tokens
            },
            'gemini:gemini-2.0-flash-exp': {
                'input': 0.0 / 1000,     # Free tier
                'output': 0.0 / 1000
            }
        }

        # Use default pricing if model not found
        model_pricing = pricing.get(model, {
            'input': 0.003 / 1000,
            'output': 0.015 / 1000
        })

        cost = (prompt_tokens * model_pricing['input'] +
                completion_tokens * model_pricing['output'])

        return cost

    def record_call(self, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        """
        Record API call and check budget.

        Args:
            model: Model identifier
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Raises:
            BudgetExceededError: If total cost exceeds max_budget
        """
        cost = self.estimate_cost(model, prompt_tokens, completion_tokens)
        self.total_cost += cost

        self.call_log.append({
            'model': model,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'cost': cost,
            'cumulative_cost': self.total_cost
        })

        if self.total_cost > self.max_budget:
            raise BudgetExceededError(
                f"Budget exceeded: ${self.total_cost:.2f} > ${self.max_budget:.2f}"
            )

    def get_summary(self) -> Dict:
        """
        Get cost summary.

        Returns:
            Dictionary with total_cost, call_count, and remaining_budget
        """
        return {
            'total_cost': self.total_cost,
            'call_count': len(self.call_log),
            'remaining_budget': self.max_budget - self.total_cost,
            'budget_used_pct': (self.total_cost / self.max_budget * 100) if self.max_budget > 0 else 0
        }
