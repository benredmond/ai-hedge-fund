"""
Pydantic models for AI agent outputs.

Strategy: Represents a trading strategy with assets, weights, and rebalancing logic.
Charter: Represents the strategic reasoning document for a strategy.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field, field_validator
from pydantic.fields import FieldInfo
from enum import Enum


class WeightsDict(dict[str, float]):
    """Dictionary that iterates over numeric weight values for legacy list semantics."""

    def __iter__(self):
        return iter(self.values())

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
        thesis_document: Comprehensive investment thesis with causal reasoning (optional for backward compatibility)
        rebalancing_rationale: How rebalancing implements strategy edge (required, 150-800 chars)
        name: Strategy name/identifier
        assets: List of tickers to invest in
        weights: Asset allocation (must sum to 1.0)
        rebalance_frequency: How often to rebalance
        logic_tree: Conditional logic for dynamic allocation (can be empty dict for static allocation)
    """

    # ========== REASONING FIELD (FIRST for chain-of-thought) ==========
    thesis_document: str = Field(
        default="",
        max_length=2000,
        description="Comprehensive investment thesis: market analysis, edge explanation, regime fit, risk factors (200-2000 chars when provided)"
    )

    rebalancing_rationale: str = Field(
        ...,
        min_length=150,
        max_length=800,
        description="Explicit explanation of how rebalancing method implements the strategy's edge. Must describe what rebalancing does to winners/losers and connect to edge mechanism."
    )

    # ========== EXECUTION FIELDS ==========
    name: str = Field(..., min_length=1, max_length=200)
    assets: List[str] = Field(..., min_length=1, max_length=50)
    logic_tree: Dict[str, Any] = Field(default_factory=dict)
    weights: Dict[str, float]
    rebalance_frequency: RebalanceFrequency

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
        """Convert raw weights into numeric mapping compatible with list iteration."""
        assets = info.data.get("assets", [])

        def _coerce_numeric(value: Any, asset: str) -> float:
            try:
                return float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Weight for asset '{asset}' must be numeric, got {value!r}"
                ) from exc

        # If already mapping, coerce values to float and wrap in custom dict
        if isinstance(v, dict):
            return WeightsDict({asset: _coerce_numeric(weight, asset) for asset, weight in v.items()})

        # If it's a list, convert to dict using assets order
        if isinstance(v, list):
            if len(v) != len(assets):
                raise ValueError(
                    f"Weights list length ({len(v)}) must match assets length ({len(assets)})"
                )
            return WeightsDict({asset: _coerce_numeric(weight, asset) for asset, weight in zip(assets, v)})

        raise ValueError(f"Weights must be a dict or list, got {type(v)}")

    @field_validator("weights")
    @classmethod
    def weights_valid(
        cls, v: Dict[str, float], info: ValidationInfo
    ) -> Dict[str, float]:
        """
        Validate weights dict matches assets and sums to 1.0.

        For dynamic strategies (logic_tree non-empty): allows empty weights or partial weights
        For static strategies (logic_tree empty): requires weights for all assets
        """
        if not isinstance(v, WeightsDict):
            v = WeightsDict(v)

        # Get assets and logic_tree from model data
        assets = info.data.get("assets", [])
        logic_tree = info.data.get("logic_tree", {})

        # CASE 1: Dynamic strategy (logic_tree is non-empty)
        # Allocation is defined in logic_tree branches, so weights can be empty or partial
        if logic_tree:
            # Allow empty weights - allocation defined in logic_tree
            if not v:
                return WeightsDict({})

            # If weights provided, they must be subset of assets (no extra assets)
            extra_assets = set(v.keys()) - set(assets)
            if extra_assets:
                raise ValueError(
                    f"Weights contain assets not in assets list: {extra_assets}"
                )

            # If weights provided, they should sum to 1.0 (with tolerance)
            # This covers cases where logic_tree uses weights as default allocation
            total = sum(v.values())
            if not 0.99 <= total <= 1.01:
                raise ValueError(
                    f"Weights sum to {total:.4f}, must be between 0.99 and 1.01"
                )

            # Normalize if within tolerance
            if total != 1.0:
                normalized = WeightsDict({k: val / total for k, val in v.items()})
                return normalized

            return WeightsDict(v)

        # CASE 2: Static strategy (logic_tree is empty)
        # Strict validation - weights must cover ALL assets and sum to 1.0
        if not v:
            raise ValueError(
                "Weights cannot be empty for static strategies (no logic_tree). "
                "Either provide weights for all assets OR add conditional logic to logic_tree."
            )

        if not assets:
            raise ValueError("Strategy must have at least 1 asset")

        # Check weights cover exactly the assets list
        if set(v.keys()) != set(assets):
            raise ValueError(
                "Weights must cover all assets (no more, no less) for static strategies. "
                f"Assets: {sorted(assets)}, Weights: {sorted(v.keys())}"
            )

        # Check weights sum to 1.0 (with tolerance for LLM rounding)
        total = sum(v.values())
        if not 0.99 <= total <= 1.01:
            raise ValueError(
                f"Weights sum to {total:.4f}, must be between 0.99 and 1.01"
            )

        # Normalize if within tolerance
        if total != 1.0:
            normalized = WeightsDict({k: val / total for k, val in v.items()})
            return normalized

        return WeightsDict(v)

    @field_validator("rebalance_frequency", mode="before")
    @classmethod
    def normalize_frequency(cls, v: str) -> str:
        """Normalize frequency to lowercase for enum matching"""
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator("thesis_document")
    @classmethod
    def validate_thesis_quality(cls, v: str) -> str:
        """Validate thesis quality only if provided (allows empty for backward compat)."""
        if not v:  # Allow empty for backward compatibility
            return v

        if len(v) < 200:
            raise ValueError(
                f"thesis_document must be ≥200 chars when provided (got {len(v)}). "
                f"Provide comprehensive investment thesis or leave empty."
            )

        # Check for placeholder text
        placeholder_phrases = ["TODO", "TBD", "to be determined", "N/A", "placeholder"]
        if any(phrase.lower() in v.lower() for phrase in placeholder_phrases):
            raise ValueError(
                f"Cannot use placeholder text in thesis_document. "
                f"Found prohibited phrase in: {v[:100]}..."
            )

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

    # No validator for minimum threshold - filtering happens in winner_selector.py
    # Dimensions can score 1-5; candidates with total_score <3.0 are filtered during selection


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


class MacroRegime(BaseModel):
    """
    Macro regime classification and key indicators.

    Attributes:
        classification: Economic regime (expansion/slowdown/recession/recovery)
        key_indicators: Core macro data (rates, inflation, employment, growth) - optional
        sources: Data sources cited (e.g., "fred:FEDFUNDS")
    """

    classification: str = Field(..., pattern="^(expansion|slowdown|recession|recovery)$")
    key_indicators: Dict[str, str] | None = None
    sources: List[str] = Field(min_length=1)


class MarketRegime(BaseModel):
    """
    Market regime classification and leadership.

    Attributes:
        trend: Market trend direction (bull/bear)
        volatility: Volatility regime (low/normal/elevated/high)
        breadth: Market breadth description - optional
        sector_leadership: Top performing sectors - optional
        sector_weakness: Underperforming sectors - optional
        factor_premiums: Factor performance (momentum, quality, size, value vs growth) - optional
        sources: Data sources cited (e.g., "yfinance:SPY")
    """

    trend: str = Field(..., pattern="^(bull|bear)$")
    volatility: str = Field(..., pattern="^(low|normal|elevated|high)$")
    breadth: str | None = None
    sector_leadership: List[str] | None = None
    sector_weakness: List[str] | None = None
    factor_premiums: Dict[str, str] | None = None
    sources: List[str] = Field(min_length=1)


class ComposerPattern(BaseModel):
    """
    Relevant Composer symphony pattern.

    Attributes:
        name: Pattern/symphony name
        key_insight: Main insight or approach
        relevance: Why relevant to current regime
    """

    name: str
    key_insight: str
    relevance: str


class ResearchSynthesis(BaseModel):
    """
    Phase 1 research output with macro/market regime analysis.

    This structured output ensures the agent produces a complete market analysis
    before proceeding to candidate generation.

    Attributes:
        macro_regime: Economic regime classification and indicators
        market_regime: Market trend, volatility, breadth, and leadership
        composer_patterns: 3-5 relevant symphony patterns from Composer
    """

    macro_regime: MacroRegime
    market_regime: MarketRegime
    composer_patterns: List[ComposerPattern] = Field(min_length=3, max_length=5)


class WorkflowResult(BaseModel):
    """
    Complete workflow output from strategy creation process.

    Attributes:
        strategy: Selected winning strategy
        charter: Generated charter document
        all_candidates: All 5 generated candidates
        scorecards: Edge Scorecard evaluations for all candidates
        selection_reasoning: Why winner was chosen
    """

    strategy: Strategy
    charter: Charter
    all_candidates: List[Strategy] = Field(min_length=5, max_length=5)
    scorecards: List[EdgeScorecard] = Field(min_length=5, max_length=5)
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
