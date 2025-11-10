"""Execution cost validator for high-frequency strategies."""

from typing import List

from src.agent.models import Strategy
from src.agent.validators.base import BaseValidator


class CostValidator(BaseValidator):
    """
    Validates that high-frequency strategies address execution costs.

    Evidence shows costs can exceed alpha by 10x for high-turnover strategies:
    - VIX strategy: 10% cost vs 5% alpha (underwater from day 1)
    - Weekly sector rotation: 1.6% friction at $100M AUM

    This validator checks for cost discussion keywords in high-frequency strategies.
    Priority 3 (SUGGESTION) - recommends but doesn't block workflow.
    """

    HIGH_FREQUENCY = ["daily", "weekly"]

    COST_KEYWORDS = [
        "turnover",
        "friction",
        "transaction cost",
        "execution cost",
        "spread",
        "slippage",
        "trading cost",
        "bps",
        "basis point",
    ]

    def validate(self, strategy: Strategy) -> List[str]:
        """
        Validate execution cost discussion for high-frequency strategies.

        Args:
            strategy: Strategy to validate

        Returns:
            List of error messages (Priority 3 SUGGESTION format)
        """
        errors = []

        # Only validate high-frequency strategies
        if strategy.rebalance_frequency not in self.HIGH_FREQUENCY:
            return errors

        thesis_lower = strategy.thesis_document.lower()

        # Check for cost discussion
        has_cost_discussion = any(
            keyword in thesis_lower for keyword in self.COST_KEYWORDS
        )

        if not has_cost_discussion:
            errors.append(
                f"Priority 3 (SUGGESTION): Strategy '{strategy.name}' uses "
                f"{strategy.rebalance_frequency} rebalancing but doesn't address "
                "execution costs. Consider estimating: annual turnover, spread costs, "
                "market impact, and friction budget. High-frequency strategies can have "
                "costs exceeding alpha by 2-10x."
            )

        return errors
