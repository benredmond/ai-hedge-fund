"""
Tests for workflow persistence layer.

Tests save_workflow_result() function including:
- New file creation
- Append to existing file
- Invalid cohort_id validation
- Serialization roundtrip
- Error handling
"""

import json
import pytest
from pathlib import Path

from src.agent.persistence import save_workflow_result, validate_cohort_id, COHORT_ID_PATTERN
from src.agent.models import (
    WorkflowResult,
    Strategy,
    Charter,
    EdgeScorecard,
    SelectionReasoning,
    RebalanceFrequency,
    EdgeType,
    StrategyArchetype,
)


@pytest.fixture
def sample_strategy() -> Strategy:
    """Create a minimal valid Strategy for testing."""
    return Strategy(
        name="Test Strategy",
        assets=["SPY", "QQQ", "TLT"],
        weights={"SPY": 0.4, "QQQ": 0.4, "TLT": 0.2},
        rebalance_frequency=RebalanceFrequency.MONTHLY,
        rebalancing_rationale="Monthly rebalancing captures momentum while limiting transaction costs. Winners are trimmed and losers added to, maintaining target allocation and capturing mean reversion.",
        edge_type=EdgeType.RISK_PREMIUM,
        archetype=StrategyArchetype.MOMENTUM,
    )


@pytest.fixture
def sample_charter() -> Charter:
    """Create a minimal valid Charter for testing."""
    return Charter(
        market_thesis="Current market conditions favor risk-on positioning with controlled volatility exposure. " * 5,
        strategy_selection="This strategy was selected for its balance of growth and defensive positioning. " * 5,
        expected_behavior="Expected to outperform in trending markets while limiting drawdowns in corrections. " * 5,
        failure_modes=[
            "Severe market correction with correlation spike across all asset classes",
            "Rapid interest rate increases causing bond losses without equity gains",
            "Extended sideways market reducing momentum signals effectiveness",
        ],
        outlook_90d="Over the next 90 days, we expect moderate volatility with continued upward bias. " * 5,
    )


@pytest.fixture
def sample_scorecard() -> EdgeScorecard:
    """Create a valid EdgeScorecard for testing."""
    return EdgeScorecard(
        thesis_quality=4,
        edge_economics=3,
        risk_framework=4,
        regime_awareness=4,
        strategic_coherence=4,
    )


@pytest.fixture
def sample_workflow_result(sample_strategy, sample_charter, sample_scorecard) -> WorkflowResult:
    """Create a complete WorkflowResult for testing."""
    # Create 5 candidates (required by WorkflowResult)
    candidates = []
    for i in range(5):
        candidates.append(Strategy(
            name=f"Candidate {i+1}",
            assets=["SPY", "QQQ", f"ETF{i}"],
            weights={"SPY": 0.4, "QQQ": 0.3, f"ETF{i}": 0.3},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            rebalancing_rationale="Monthly rebalancing captures momentum while limiting transaction costs. Winners are trimmed and losers added to, maintaining target allocation. This frequency balances responsiveness with cost efficiency.",
            edge_type=EdgeType.RISK_PREMIUM,
            archetype=StrategyArchetype.MOMENTUM,
        ))

    # Use first candidate as winner
    winner = candidates[0]

    return WorkflowResult(
        strategy=winner,
        charter=sample_charter,
        all_candidates=candidates,
        scorecards=[sample_scorecard for _ in range(5)],
        selection_reasoning=SelectionReasoning(
            winner_index=0,
            why_selected="Selected for strong thesis quality and regime awareness. The strategy demonstrates clear understanding of current market dynamics and positions appropriately for expected conditions.",
            tradeoffs_accepted="Accepting slightly lower edge economics score in favor of better risk framework and regime fit.",
            alternatives_rejected=["Candidate 2", "Candidate 3", "Candidate 4", "Candidate 5"],
            conviction_level=0.85,
        ),
        symphony_id="test_symphony_123",
        deployed_at="2025-01-15T12:00:00Z",
    )


class TestValidateCohortId:
    """Tests for cohort_id validation."""

    def test_valid_cohort_ids(self):
        """Valid cohort IDs should pass validation."""
        valid_ids = [
            "2025-Q1",
            "cohort_001",
            "test-cohort",
            "Q1_2025",
            "abc123",
            "a",
        ]
        for cohort_id in valid_ids:
            validate_cohort_id(cohort_id)  # Should not raise

    def test_empty_cohort_id_rejected(self):
        """Empty cohort_id should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_cohort_id("")

    def test_path_traversal_rejected(self):
        """Path traversal attempts should be rejected."""
        invalid_ids = [
            "../etc/passwd",
            "../../secrets",
            "cohort/../other",
            "/absolute/path",
            "cohort/nested",
        ]
        for cohort_id in invalid_ids:
            with pytest.raises(ValueError, match="Invalid cohort_id"):
                validate_cohort_id(cohort_id)

    def test_special_characters_rejected(self):
        """Special characters should be rejected."""
        invalid_ids = [
            "cohort!",
            "cohort@123",
            "cohort#1",
            "cohort$",
            "cohort%",
            "cohort with spaces",
            "cohort.json",
        ]
        for cohort_id in invalid_ids:
            with pytest.raises(ValueError, match="Invalid cohort_id"):
                validate_cohort_id(cohort_id)


class TestSaveWorkflowResult:
    """Tests for save_workflow_result function."""

    def test_save_new_file(self, tmp_path, sample_workflow_result):
        """Should create new strategies.json file."""
        result_path = save_workflow_result(
            sample_workflow_result,
            cohort_id="2025-Q1",
            base_dir=tmp_path,
        )

        assert result_path is not None
        assert result_path.exists()
        assert result_path.name == "strategies.json"

        # Verify content
        with open(result_path) as f:
            data = json.load(f)

        assert data["cohort_id"] == "2025-Q1"
        assert len(data["strategies"]) == 1
        assert data["strategies"][0]["symphony_id"] == "test_symphony_123"

    def test_append_to_existing(self, tmp_path, sample_workflow_result):
        """Should append to existing strategies.json file."""
        # Save first result
        save_workflow_result(
            sample_workflow_result,
            cohort_id="2025-Q1",
            base_dir=tmp_path,
        )

        # Modify and save second result
        sample_workflow_result.symphony_id = "second_symphony_456"
        result_path = save_workflow_result(
            sample_workflow_result,
            cohort_id="2025-Q1",
            base_dir=tmp_path,
        )

        # Verify both are present
        with open(result_path) as f:
            data = json.load(f)

        assert len(data["strategies"]) == 2
        assert data["strategies"][0]["symphony_id"] == "test_symphony_123"
        assert data["strategies"][1]["symphony_id"] == "second_symphony_456"

    def test_invalid_cohort_id_returns_none(self, tmp_path, sample_workflow_result):
        """Invalid cohort_id should return None without raising."""
        result = save_workflow_result(
            sample_workflow_result,
            cohort_id="../../../etc/passwd",
            base_dir=tmp_path,
        )

        assert result is None

    def test_creates_cohort_directory(self, tmp_path, sample_workflow_result):
        """Should create cohort directory if it doesn't exist."""
        cohort_dir = tmp_path / "new-cohort"
        assert not cohort_dir.exists()

        save_workflow_result(
            sample_workflow_result,
            cohort_id="new-cohort",
            base_dir=tmp_path,
        )

        assert cohort_dir.exists()
        assert (cohort_dir / "strategies.json").exists()

    def test_serialization_roundtrip(self, tmp_path, sample_workflow_result):
        """Saved data should be loadable and match original."""
        result_path = save_workflow_result(
            sample_workflow_result,
            cohort_id="roundtrip-test",
            base_dir=tmp_path,
        )

        with open(result_path) as f:
            data = json.load(f)

        saved_strategy = data["strategies"][0]

        # Verify key fields
        assert saved_strategy["strategy"]["name"] == sample_workflow_result.strategy.name
        assert saved_strategy["strategy"]["assets"] == sample_workflow_result.strategy.assets
        assert saved_strategy["charter"]["market_thesis"] == sample_workflow_result.charter.market_thesis
        assert saved_strategy["symphony_id"] == sample_workflow_result.symphony_id
        assert saved_strategy["deployed_at"] == sample_workflow_result.deployed_at
        assert saved_strategy["selection_reasoning"]["winner_index"] == 0
        assert len(saved_strategy["all_candidates"]) == 5
        assert len(saved_strategy["scorecards"]) == 5

    def test_handles_corrupted_existing_file(self, tmp_path, sample_workflow_result):
        """Should handle corrupted existing JSON gracefully."""
        cohort_dir = tmp_path / "corrupted-cohort"
        cohort_dir.mkdir(parents=True)

        # Create corrupted file
        with open(cohort_dir / "strategies.json", 'w') as f:
            f.write("{ invalid json }")

        # Should succeed despite corrupted file
        result_path = save_workflow_result(
            sample_workflow_result,
            cohort_id="corrupted-cohort",
            base_dir=tmp_path,
        )

        assert result_path is not None

        # Should have started fresh with just the new strategy
        with open(result_path) as f:
            data = json.load(f)

        assert len(data["strategies"]) == 1

    def test_json_is_human_readable(self, tmp_path, sample_workflow_result):
        """Saved JSON should be formatted with indent for readability."""
        result_path = save_workflow_result(
            sample_workflow_result,
            cohort_id="readable-test",
            base_dir=tmp_path,
        )

        content = result_path.read_text()

        # Should have newlines and indentation
        assert "\n" in content
        assert "  " in content  # 2-space indent

    def test_saves_model_with_strategy(self, tmp_path, sample_workflow_result):
        """Model identifier should be saved with each strategy entry."""
        result_path = save_workflow_result(
            sample_workflow_result,
            cohort_id="model-test",
            model="openai:gpt-4o",
            base_dir=tmp_path,
        )

        with open(result_path) as f:
            data = json.load(f)

        assert data["strategies"][0]["model"] == "openai:gpt-4o"

    def test_model_none_when_not_provided(self, tmp_path, sample_workflow_result):
        """Model should be None if not provided (backward compat)."""
        result_path = save_workflow_result(
            sample_workflow_result,
            cohort_id="no-model-test",
            base_dir=tmp_path,
        )

        with open(result_path) as f:
            data = json.load(f)

        assert data["strategies"][0]["model"] is None


class TestCohortIdPattern:
    """Tests for the COHORT_ID_PATTERN regex."""

    def test_pattern_matches_valid(self):
        """Pattern should match valid cohort IDs."""
        valid = ["2025-Q1", "cohort_001", "test", "a-b_c"]
        for s in valid:
            assert COHORT_ID_PATTERN.match(s), f"Should match: {s}"

    def test_pattern_rejects_invalid(self):
        """Pattern should reject invalid cohort IDs."""
        invalid = ["../", "a/b", "a b", "a.b", ""]
        for s in invalid:
            assert not COHORT_ID_PATTERN.match(s), f"Should reject: {s}"
