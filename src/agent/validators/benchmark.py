"""Benchmark comparison validator for professional standards."""

import re
from typing import List

from src.agent.models import Strategy
from src.agent.validators.base import BaseValidator


class BenchmarkValidator(BaseValidator):
    """
    Validates that strategies include explicit benchmark comparison.

    Professional investors expect strategies to answer: "Why not just buy SPY?"
    This validator checks for:
    1. Benchmark mentions (SPY, QQQ, AGG, sector ETFs, 60/40)
    2. Alpha quantification (vs benchmark, +X bps, outperform)

    Priority 3 (SUGGESTION) - recommends but doesn't block workflow.
    """

    BENCHMARKS = [
        "spy",
        "qqq",
        "agg",
        "xlf",
        "xle",
        "xlk",
        "xlv",
        "xly",
        "xlp",
        "xli",
        "xlb",
        "xlu",
        "xlre",
        "xlc",
        "60/40",
        "risk parity",
    ]

    ALPHA_PATTERNS = [
        r"vs\s+spy",
        r"vs\s+qqq",
        r"vs\s+\w{3,4}",  # vs XLF, vs AGG
        r"\+\d+\s*bps",
        r"\+\d+\.\d+%",
        r"outperform",
        r"alpha",
        r"excess return",
        r"beat\s+\w+",
    ]

    def validate(self, strategy: Strategy) -> List[str]:
        """
        Validate benchmark comparison in strategy thesis.

        Args:
            strategy: Strategy to validate

        Returns:
            List of error messages (Priority 3 SUGGESTION format)
        """
        errors = []
        thesis_lower = strategy.thesis_document.lower()

        # Check for benchmark mentions
        has_benchmark = any(
            benchmark in thesis_lower for benchmark in self.BENCHMARKS
        )

        if not has_benchmark:
            errors.append(
                f"Priority 3 (SUGGESTION): Strategy '{strategy.name}' should compare "
                "to passive benchmarks (SPY, QQQ, sector ETFs, 60/40). Professional "
                "investors expect answer to: 'Why not just buy the benchmark?'"
            )
            return errors  # No benchmark → skip alpha check

        # Check for alpha quantification
        has_alpha = any(
            re.search(pattern, thesis_lower) for pattern in self.ALPHA_PATTERNS
        )

        if not has_alpha:
            errors.append(
                f"Priority 3 (SUGGESTION): Strategy '{strategy.name}' mentions benchmarks "
                "but should quantify expected alpha (e.g., 'vs SPY', '+150 bps', 'outperform by X%')"
            )

        return errors
