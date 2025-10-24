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
    QUARTERLY = "quarterly"


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

    @field_validator('assets')
    @classmethod
    def assets_not_empty(cls, v: List[str]) -> List[str]:
        """Ensure assets list is not empty"""
        if not v:
            raise ValueError("Strategy must have at least 1 asset")
        if len(v) != len(set(v)):
            raise ValueError("Assets list contains duplicates")
        return v

    @field_validator('weights')
    @classmethod
    def weights_valid(cls, v: Dict[str, float], info: ValidationInfo) -> Dict[str, float]:
        """Validate weights dict matches assets and sums to 1.0"""
        if not v:
            raise ValueError("Weights cannot be empty")

        # Get assets from model data
        assets = info.data.get('assets', [])

        # Check weights cover exactly the assets list
        if set(v.keys()) != set(assets):
            raise ValueError("Weights must cover all assets (no more, no less)")

        # Check weights sum to 1.0 (with tolerance for LLM rounding)
        total = sum(v.values())
        if not 0.99 <= total <= 1.01:
            raise ValueError(f"Weights sum to {total:.4f}, must be between 0.99 and 1.01")

        # Normalize if within tolerance
        if total != 1.0:
            normalized = {k: val / total for k, val in v.items()}
            return normalized

        return v

    @field_validator('rebalance_frequency', mode='before')
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

    @field_validator('failure_modes')
    @classmethod
    def failure_modes_meaningful(cls, v: List[str]) -> List[str]:
        """Ensure each failure mode is meaningful (not too short)"""
        if not v:
            raise ValueError("Charter must have at least 1 failure mode")

        for i, mode in enumerate(v):
            if len(mode) < 10:
                raise ValueError(
                    f"Failure mode {i+1} must be at least 10 characters long, got: '{mode}'"
                )

        return v
