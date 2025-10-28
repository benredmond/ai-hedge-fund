"""
Pydantic models for AI agent outputs.

Strategy: Represents a trading strategy with assets, weights, and rebalancing logic.
Charter: Represents the strategic reasoning document for a strategy.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field, field_validator
from pydantic.fields import FieldInfo
from enum import Enum

# Try to import ValidationInfo, fall back to using 'info' param without type hint
try:
    from pydantic import ValidationInfo
except ImportError:
    # For older Pydantic versions, we'll use Any type
    ValidationInfo = Any  # type: ignore


class RebalanceFrequency(str, Enum):
    """Valid rebalancing frequencies for strategies"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Strategy(BaseModel):
    """
    Trading strategy specification.

    Attributes:
        name: Strategy name/identifier
        assets: List of tickers to invest in
        weights: Asset allocation (must sum to 1.0)
        rebalance_frequency: How often to rebalance
        logic_tree: Conditional logic for dynamic allocation (can be empty dict for static allocation)
    """

    name: str = Field(..., min_length=1, max_length=200)
    assets: List[str] = Field(..., min_length=1, max_length=50)
    weights: Dict[str, float]
    rebalance_frequency: RebalanceFrequency
    logic_tree: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("assets")
    @classmethod
    def assets_not_empty(cls, v: List[str]) -> List[str]:
        """Ensure assets list is not empty"""
        if not v:
            raise ValueError("Strategy must have at least 1 asset")
        if len(v) != len(set(v)):
            raise ValueError("Assets list contains duplicates")
        return v

    @field_validator("weights", mode="before")
    @classmethod
    def convert_weights_to_dict(cls, v, info: ValidationInfo):
        """Convert list weights to dict format if needed (AI compatibility)"""
        # If already a dict, pass through to main validator
        if isinstance(v, dict):
            return v

        # If it's a list, convert to dict using assets
        if isinstance(v, list):
            assets = info.data.get("assets", [])
            if len(v) != len(assets):
                raise ValueError(
                    f"Weights list length ({len(v)}) must match assets length ({len(assets)})"
                )
            return dict(zip(assets, v))

        raise ValueError(f"Weights must be a dict or list, got {type(v)}")

    @field_validator("weights")
    @classmethod
    def weights_valid(
        cls, v: Dict[str, float], info: ValidationInfo
    ) -> Dict[str, float]:
        """Validate weights dict matches assets and sums to 1.0"""
        if not v:
            raise ValueError("Weights cannot be empty")

        # Get assets from model data
        assets = info.data.get("assets", [])

        # Check weights cover exactly the assets list
        if set(v.keys()) != set(assets):
            raise ValueError("Weights must cover all assets (no more, no less)")

        # Check weights sum to 1.0 (with tolerance for LLM rounding)
        total = sum(v.values())
        if not 0.99 <= total <= 1.01:
            raise ValueError(
                f"Weights sum to {total:.4f}, must be between 0.99 and 1.01"
            )

        # Normalize if within tolerance
        if total != 1.0:
            normalized = {k: val / total for k, val in v.items()}
            return normalized

        return v

    @field_validator("rebalance_frequency", mode="before")
    @classmethod
    def normalize_frequency(cls, v: str) -> str:
        """Normalize frequency to lowercase for enum matching"""
        if isinstance(v, str):
            return v.lower()
        return v


class Charter(BaseModel):
    """
    Strategy charter document.

    Attributes:
        market_thesis: Current market analysis and rationale
        strategy_selection: Why this strategy was chosen over alternatives
        expected_behavior: How strategy should perform under different conditions
        failure_modes: Conditions where strategy is expected to fail
        outlook_90d: 90-day forward outlook
    """

    market_thesis: str = Field(..., min_length=10, max_length=5000)
    strategy_selection: str = Field(..., min_length=10, max_length=5000)
    expected_behavior: str = Field(..., min_length=10, max_length=5000)
    failure_modes: List[str] = Field(..., min_length=1, max_length=20)
    outlook_90d: str = Field(..., min_length=10, max_length=2000)

    @field_validator("failure_modes")
    @classmethod
    def failure_modes_meaningful(cls, v: List[str]) -> List[str]:
        """Ensure each failure mode is meaningful (not too short)"""
        if not v:
            raise ValueError("Charter must have at least 1 failure mode")

        for i, mode in enumerate(v):
            if len(mode) < 10:
                raise ValueError(
                    f"Failure mode {i + 1} must be at least 10 characters long, got: '{mode}'"
                )

        return v


class BacktestResult(BaseModel):
    """
    Composer backtest results.

    Attributes:
        sharpe_ratio: Risk-adjusted return metric
        max_drawdown: Maximum peak-to-trough decline (negative value)
        total_return: Cumulative return over backtest period
        volatility_annualized: Annualized standard deviation of returns
        positive_days_pct: Percentage of positive return days (optional)
    """

    sharpe_ratio: float
    max_drawdown: float = Field(le=0)  # Must be negative or zero
    total_return: float
    volatility_annualized: float = Field(gt=0)
    positive_days_pct: float | None = None


class EdgeScorecard(BaseModel):
    """
    5-dimension strategy evaluation scorecard.

    All dimensions scored 1-5:
    - 1: Inadequate (severe deficiencies)
    - 2: Weak (below threshold, likely to fail)
    - 3: Acceptable (minimum viable quality)
    - 4: Strong (above average, well-executed)
    - 5: Institutional Grade (best-in-class, clear competitive advantage)

    Attributes:
        thesis_quality: Does the strategy articulate a clear, falsifiable investment thesis with causal reasoning?
        edge_economics: Why does this edge exist, and why hasn't it been arbitraged away?
        risk_framework: Does the strategist understand the risk profile, failure modes, and risk-adjusted expectations?
        regime_awareness: Does the strategy fit current market conditions with adaptation logic?
        strategic_coherence: Do all strategy elements support a unified thesis with feasible execution?
    """

    thesis_quality: int = Field(ge=1, le=5)
    edge_economics: int = Field(ge=1, le=5)
    risk_framework: int = Field(ge=1, le=5)
    regime_awareness: int = Field(ge=1, le=5)
    strategic_coherence: int = Field(ge=1, le=5)

    @property
    def total_score(self) -> float:
        """Average score across all 5 dimensions"""
        return (
            self.thesis_quality
            + self.edge_economics
            + self.risk_framework
            + self.regime_awareness
            + self.strategic_coherence
        ) / 5

    @field_validator(
        "thesis_quality",
        "edge_economics",
        "risk_framework",
        "regime_awareness",
        "strategic_coherence",
    )
    @classmethod
    def dimension_above_threshold(cls, v: int) -> int:
        """Ensure each dimension meets minimum threshold of 3"""
        if v < 3:
            raise ValueError(
                f"Edge Scorecard dimension scored {v}, minimum threshold is 3"
            )
        return v


class SelectionReasoning(BaseModel):
    """
    Reasoning for why winner was selected over alternatives.

    Attributes:
        winner_index: Index (0-4) of selected strategy in candidates list
        why_selected: Detailed explanation of selection (min 100 chars)
        tradeoffs_accepted: Key tradeoffs accepted in choosing this strategy (50-2000 chars)
        alternatives_rejected: List of 4 rejected alternatives with brief rejection reasons
        conviction_level: Confidence in selection (0.0-1.0), based on score delta and consistency
    """

    winner_index: int = Field(ge=0, le=4)
    why_selected: str = Field(min_length=100, max_length=5000)
    tradeoffs_accepted: str = Field(min_length=50, max_length=2000)
    alternatives_rejected: List[str] = Field(min_length=4, max_length=4)
    conviction_level: float = Field(ge=0.0, le=1.0)

    @field_validator("alternatives_rejected")
    @classmethod
    def alternatives_not_empty(cls, v: List[str]) -> List[str]:
        """Ensure all alternative names are meaningful"""
        if not v:
            raise ValueError("Must have 4 rejected alternatives")

        for alt in v:
            if len(alt) < 1:
                raise ValueError("Alternative description cannot be empty")

        return v


class WorkflowResult(BaseModel):
    """
    Complete workflow output from strategy creation process.

    Attributes:
        strategy: Selected winning strategy
        charter: Generated charter document
        all_candidates: All 5 generated candidates
        scorecards: Edge Scorecard evaluations for all candidates
        backtests: Backtest results for all candidates
        selection_reasoning: Why winner was chosen
    """

    strategy: Strategy
    charter: Charter
    all_candidates: List[Strategy] = Field(min_length=5, max_length=5)
    scorecards: List[EdgeScorecard] = Field(min_length=5, max_length=5)
    backtests: List[BacktestResult] = Field(min_length=5, max_length=5)
    selection_reasoning: SelectionReasoning

    @field_validator("all_candidates")
    @classmethod
    def exactly_five_candidates(cls, v: List[Strategy]) -> List[Strategy]:
        """Ensure exactly 5 candidates were generated"""
        if len(v) != 5:
            raise ValueError(f"Must have exactly 5 candidates, got {len(v)}")
        return v

    @field_validator("strategy")
    @classmethod
    def winner_in_candidates(cls, v: Strategy, info: ValidationInfo) -> Strategy:
        """Ensure selected strategy is one of the candidates"""
        candidates = info.data.get("all_candidates", [])
        if candidates and v not in candidates:
            raise ValueError("Selected strategy must be one of the 5 candidates")
        return v
