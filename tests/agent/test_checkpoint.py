"""
Unit tests for checkpoint/resume functionality.

Tests the persistence layer checkpoint operations (save, load, clear)
and WorkflowCheckpoint model serialization.
"""

import json
import pytest
from datetime import datetime, timezone

from src.agent.models import (
    Strategy,
    EdgeScorecard,
    SelectionReasoning,
    Charter,
    WorkflowStage,
    WorkflowCheckpoint,
    RebalanceFrequency,
)
from src.agent.persistence import (
    save_checkpoint,
    load_checkpoint,
    clear_checkpoint,
    CHECKPOINT_FILENAME,
)


# === Fixtures ===

@pytest.fixture
def sample_market_context():
    """Minimal market context for testing."""
    return {
        "metadata": {
            "anchor_date": "2025-01-15",
            "generated_at": "2025-01-15T10:00:00Z",
        },
        "regime_tags": ["bull_market", "low_volatility"],
        "regime_snapshot": {
            "trend": "bull",
            "volatility": "low",
        },
    }


@pytest.fixture
def sample_strategy():
    """Create a valid Strategy instance for testing."""
    return Strategy(
        name="Test Momentum Strategy",
        assets=["SPY", "QQQ", "TLT"],
        weights={"SPY": 0.4, "QQQ": 0.4, "TLT": 0.2},
        rebalance_frequency=RebalanceFrequency.MONTHLY,
        rebalancing_rationale="Monthly rebalancing captures momentum while limiting turnover costs. By reallocating at month-end, we capture the documented monthly momentum effect and reduce whipsaw from daily noise.",
        thesis_document="",
    )


@pytest.fixture
def sample_scorecard():
    """Create a valid EdgeScorecard instance for testing."""
    return EdgeScorecard(
        thesis_quality=4,
        edge_economics=3,
        risk_framework=4,
        regime_awareness=3,
        strategic_coherence=4,
    )


@pytest.fixture
def sample_selection_reasoning():
    """Create a valid SelectionReasoning instance for testing."""
    return SelectionReasoning(
        winner_index=0,
        why_selected="This strategy was selected for its strong risk-adjusted return potential and clear thesis around momentum investing in the current low-volatility bull market regime.",
        tradeoffs_accepted="Accepting higher correlation to equities in exchange for simplicity and lower fees.",
        alternatives_rejected=["Strategy B", "Strategy C"],
        conviction_level=0.85,
    )


@pytest.fixture
def sample_charter():
    """Create a valid Charter instance for testing."""
    return Charter(
        market_thesis="Current market conditions favor momentum strategies. Low volatility and positive breadth suggest trend continuation.",
        strategy_selection="Selected based on composite ranking across edge scorecard dimensions with emphasis on regime fit.",
        expected_behavior="Strategy should outperform in trending markets and underperform during sharp reversals or regime changes.",
        failure_modes=[
            "Sharp market reversal with VIX spike above 30",
            "Factor rotation away from momentum toward value",
            "Liquidity crisis affecting ETF tracking",
        ],
        outlook_90d="Expect continued trend following with moderate volatility. Monitor for signs of regime change.",
    )


@pytest.fixture
def sample_checkpoint(sample_market_context, sample_strategy, sample_scorecard):
    """Create a complete checkpoint for testing."""
    now = datetime.now(timezone.utc).isoformat()
    return WorkflowCheckpoint(
        last_completed_stage=WorkflowStage.SCORING,
        created_at=now,
        updated_at=now,
        model="openai:gpt-4o",
        cohort_id="test-cohort-2025",
        market_context=sample_market_context,
        candidates=[sample_strategy] * 5,
        scorecards=[sample_scorecard] * 5,
        winner=None,
        selection_reasoning=None,
        charter=None,
        symphony_id=None,
        deployed_at=None,
        strategy_summary=None,
    )


# === WorkflowStage Tests ===

class TestWorkflowStage:
    """Tests for WorkflowStage enum."""

    def test_stage_values(self):
        """All expected stages should exist."""
        assert WorkflowStage.CANDIDATES.value == "candidates"
        assert WorkflowStage.SCORING.value == "scoring"
        assert WorkflowStage.SELECTION.value == "selection"
        assert WorkflowStage.CHARTER.value == "charter"
        assert WorkflowStage.DEPLOYMENT.value == "deployment"
        assert WorkflowStage.COMPLETE.value == "complete"

    def test_stage_from_string(self):
        """Stage should be creatable from string value."""
        assert WorkflowStage("candidates") == WorkflowStage.CANDIDATES
        assert WorkflowStage("scoring") == WorkflowStage.SCORING


# === WorkflowCheckpoint Tests ===

class TestWorkflowCheckpoint:
    """Tests for WorkflowCheckpoint model."""

    def test_minimal_checkpoint(self, sample_market_context):
        """Checkpoint should be creatable with minimal fields."""
        now = datetime.now(timezone.utc).isoformat()
        checkpoint = WorkflowCheckpoint(
            last_completed_stage=WorkflowStage.CANDIDATES,
            created_at=now,
            updated_at=now,
            model="openai:gpt-4o",
            cohort_id="test-cohort",
            market_context=sample_market_context,
        )

        assert checkpoint.last_completed_stage == WorkflowStage.CANDIDATES
        assert checkpoint.candidates is None
        assert checkpoint.scorecards is None

    def test_get_resume_stage_candidates(self, sample_market_context):
        """Resume from CANDIDATES should return SCORING."""
        now = datetime.now(timezone.utc).isoformat()
        checkpoint = WorkflowCheckpoint(
            last_completed_stage=WorkflowStage.CANDIDATES,
            created_at=now,
            updated_at=now,
            model="test",
            cohort_id="test",
            market_context=sample_market_context,
        )

        assert checkpoint.get_resume_stage() == WorkflowStage.SCORING

    def test_get_resume_stage_scoring(self, sample_market_context):
        """Resume from SCORING should return SELECTION."""
        now = datetime.now(timezone.utc).isoformat()
        checkpoint = WorkflowCheckpoint(
            last_completed_stage=WorkflowStage.SCORING,
            created_at=now,
            updated_at=now,
            model="test",
            cohort_id="test",
            market_context=sample_market_context,
        )

        assert checkpoint.get_resume_stage() == WorkflowStage.SELECTION

    def test_get_resume_stage_complete(self, sample_market_context):
        """Resume from COMPLETE should return None."""
        now = datetime.now(timezone.utc).isoformat()
        checkpoint = WorkflowCheckpoint(
            last_completed_stage=WorkflowStage.COMPLETE,
            created_at=now,
            updated_at=now,
            model="test",
            cohort_id="test",
            market_context=sample_market_context,
        )

        assert checkpoint.get_resume_stage() is None

    def test_checkpoint_serialization_roundtrip(self, sample_checkpoint):
        """Checkpoint should serialize to JSON and back without loss."""
        # Serialize
        json_dict = sample_checkpoint.model_dump(mode="json")
        json_str = json.dumps(json_dict, default=str)

        # Deserialize
        parsed = json.loads(json_str)
        restored = WorkflowCheckpoint.model_validate(parsed)

        assert restored.last_completed_stage == sample_checkpoint.last_completed_stage
        assert restored.model == sample_checkpoint.model
        assert restored.cohort_id == sample_checkpoint.cohort_id
        assert len(restored.candidates) == 5
        assert len(restored.scorecards) == 5


# === Checkpoint Persistence Tests ===

class TestCheckpointPersistence:
    """Tests for checkpoint save/load/clear operations."""

    def test_save_checkpoint_creates_file(self, tmp_path, sample_checkpoint):
        """save_checkpoint should create checkpoint.json file."""
        result = save_checkpoint(sample_checkpoint, "test-cohort", base_dir=tmp_path)

        assert result is not None
        assert result.exists()
        assert result.name == CHECKPOINT_FILENAME

    def test_save_checkpoint_creates_cohort_directory(self, tmp_path, sample_checkpoint):
        """save_checkpoint should create cohort directory if needed."""
        result = save_checkpoint(sample_checkpoint, "new-cohort", base_dir=tmp_path)

        cohort_dir = tmp_path / "new-cohort"
        assert cohort_dir.exists()
        assert cohort_dir.is_dir()

    def test_load_checkpoint_returns_checkpoint(self, tmp_path, sample_checkpoint):
        """load_checkpoint should return saved checkpoint."""
        save_checkpoint(sample_checkpoint, "test-cohort", base_dir=tmp_path)

        loaded = load_checkpoint("test-cohort", base_dir=tmp_path)

        assert loaded is not None
        assert loaded.last_completed_stage == sample_checkpoint.last_completed_stage
        assert loaded.model == sample_checkpoint.model

    def test_load_checkpoint_missing_returns_none(self, tmp_path):
        """load_checkpoint should return None for missing checkpoint."""
        result = load_checkpoint("nonexistent-cohort", base_dir=tmp_path)

        assert result is None

    def test_load_checkpoint_corrupted_returns_none(self, tmp_path):
        """load_checkpoint should return None for corrupted JSON."""
        cohort_dir = tmp_path / "corrupted-cohort"
        cohort_dir.mkdir(parents=True)
        checkpoint_file = cohort_dir / CHECKPOINT_FILENAME

        # Write invalid JSON
        checkpoint_file.write_text("{ invalid json }")

        result = load_checkpoint("corrupted-cohort", base_dir=tmp_path)

        assert result is None

    def test_load_checkpoint_invalid_schema_returns_none(self, tmp_path):
        """load_checkpoint should return None for invalid schema."""
        cohort_dir = tmp_path / "invalid-cohort"
        cohort_dir.mkdir(parents=True)
        checkpoint_file = cohort_dir / CHECKPOINT_FILENAME

        # Write valid JSON but invalid schema
        checkpoint_file.write_text('{"wrong_field": "value"}')

        result = load_checkpoint("invalid-cohort", base_dir=tmp_path)

        assert result is None

    def test_clear_checkpoint_removes_file(self, tmp_path, sample_checkpoint):
        """clear_checkpoint should delete checkpoint file."""
        save_checkpoint(sample_checkpoint, "test-cohort", base_dir=tmp_path)
        checkpoint_file = tmp_path / "test-cohort" / CHECKPOINT_FILENAME

        assert checkpoint_file.exists()

        result = clear_checkpoint("test-cohort", base_dir=tmp_path)

        assert result is True
        assert not checkpoint_file.exists()

    def test_clear_checkpoint_missing_returns_true(self, tmp_path):
        """clear_checkpoint should return True for missing checkpoint."""
        result = clear_checkpoint("nonexistent-cohort", base_dir=tmp_path)

        assert result is True

    def test_checkpoint_roundtrip_with_all_stages(
        self, tmp_path, sample_market_context, sample_strategy,
        sample_scorecard, sample_selection_reasoning, sample_charter
    ):
        """Full checkpoint with all stage outputs should roundtrip correctly."""
        now = datetime.now(timezone.utc).isoformat()
        full_checkpoint = WorkflowCheckpoint(
            last_completed_stage=WorkflowStage.DEPLOYMENT,
            created_at=now,
            updated_at=now,
            model="openai:gpt-4o",
            cohort_id="full-test",
            market_context=sample_market_context,
            candidates=[sample_strategy] * 5,
            scorecards=[sample_scorecard] * 5,
            winner=sample_strategy,
            selection_reasoning=sample_selection_reasoning,
            charter=sample_charter,
            symphony_id="symphony-12345",
            deployed_at="2025-01-15T12:00:00Z",
            strategy_summary="A momentum strategy for bull markets.",
        )

        # Save
        save_checkpoint(full_checkpoint, "full-test", base_dir=tmp_path)

        # Load
        loaded = load_checkpoint("full-test", base_dir=tmp_path)

        # Verify all fields
        assert loaded is not None
        assert loaded.last_completed_stage == WorkflowStage.DEPLOYMENT
        assert loaded.model == "openai:gpt-4o"
        assert len(loaded.candidates) == 5
        assert len(loaded.scorecards) == 5
        assert loaded.winner.name == sample_strategy.name
        assert loaded.selection_reasoning.winner_index == 0
        assert loaded.charter.market_thesis == sample_charter.market_thesis
        assert loaded.symphony_id == "symphony-12345"
        assert loaded.strategy_summary == "A momentum strategy for bull markets."


# === Integration Tests ===

class TestCheckpointIntegration:
    """Integration tests for checkpoint in workflow context."""

    def test_checkpoint_preserves_weights_dict(self, tmp_path, sample_market_context):
        """Strategy weights should survive checkpoint roundtrip."""
        now = datetime.now(timezone.utc).isoformat()

        strategy = Strategy(
            name="Weight Test",
            assets=["SPY", "QQQ"],
            weights={"SPY": 0.6, "QQQ": 0.4},
            rebalance_frequency=RebalanceFrequency.WEEKLY,
            rebalancing_rationale="Weekly rebalancing maintains target weights while capturing momentum signals. This frequency balances transaction costs against tracking error. By rebalancing weekly, we ensure that the portfolio stays aligned with the intended allocation while minimizing unnecessary trading.",
        )

        checkpoint = WorkflowCheckpoint(
            last_completed_stage=WorkflowStage.CANDIDATES,
            created_at=now,
            updated_at=now,
            model="test",
            cohort_id="weight-test",
            market_context=sample_market_context,
            candidates=[strategy],
        )

        save_checkpoint(checkpoint, "weight-test", base_dir=tmp_path)
        loaded = load_checkpoint("weight-test", base_dir=tmp_path)

        assert loaded is not None
        # Weights should be accessible as dict
        assert loaded.candidates[0].weights["SPY"] == pytest.approx(0.6, rel=1e-6)
        assert loaded.candidates[0].weights["QQQ"] == pytest.approx(0.4, rel=1e-6)

    def test_checkpoint_preserves_enum_values(self, tmp_path, sample_market_context):
        """Enum values should survive checkpoint roundtrip."""
        now = datetime.now(timezone.utc).isoformat()

        from src.agent.models import EdgeType, StrategyArchetype

        strategy = Strategy(
            name="Enum Test",
            assets=["SPY"],
            weights={"SPY": 1.0},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            rebalancing_rationale="Monthly rebalancing is appropriate for this single-asset strategy as it minimizes transaction costs while maintaining the intended exposure. This frequency is sufficient for momentum capture while avoiding excessive trading costs that would erode returns.",
            edge_type=EdgeType.BEHAVIORAL,
            archetype=StrategyArchetype.MOMENTUM,
        )

        checkpoint = WorkflowCheckpoint(
            last_completed_stage=WorkflowStage.CANDIDATES,
            created_at=now,
            updated_at=now,
            model="test",
            cohort_id="enum-test",
            market_context=sample_market_context,
            candidates=[strategy],
        )

        save_checkpoint(checkpoint, "enum-test", base_dir=tmp_path)
        loaded = load_checkpoint("enum-test", base_dir=tmp_path)

        assert loaded is not None
        assert loaded.candidates[0].edge_type == EdgeType.BEHAVIORAL
        assert loaded.candidates[0].archetype == StrategyArchetype.MOMENTUM
        assert loaded.candidates[0].rebalance_frequency == RebalanceFrequency.MONTHLY
