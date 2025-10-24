import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
from src.market_context.validation import validate_context_pack


class TestValidateContextPack:
    """Test validation suite for context packs."""

    @freeze_time("2025-01-15 12:00:00")
    def test_valid_context_pack_passes(self):
        """Valid context pack passes all checks."""
        valid_pack = {
            "metadata": {
                "anchor_date": "2025-01-15T12:00:00",
                "data_cutoff": "2025-01-15T12:00:00",
                "generated_at": datetime.utcnow().isoformat(),
                "version": "v1.0.0"
            },
            "regime_snapshot": {
                "trend": {"regime": "bull"},
                "volatility": {"regime": "normal"}
            },
            "macro_indicators": {
                "interest_rates": {"fed_funds_rate": 5.25}
            },
            "recent_events": [
                {"date": "2025-01-10", "headline": "Test"}
            ],
            "regime_tags": ["bull", "volatility_normal"]
        }

        is_valid, errors = validate_context_pack(valid_pack)

        assert is_valid
        assert len(errors) == 0

    def test_detects_future_data_leakage(self):
        """Detects events with future dates."""
        pack_with_future = {
            "metadata": {
                "anchor_date": "2025-01-15T12:00:00",
                "data_cutoff": "2025-01-15T12:00:00",
                "generated_at": datetime.utcnow().isoformat(),
                "version": "v1.0.0"
            },
            "regime_snapshot": {},
            "macro_indicators": {},
            "recent_events": [
                {"date": "2025-01-20", "headline": "Future event!"}  # After anchor
            ],
            "regime_tags": []
        }

        is_valid, errors = validate_context_pack(pack_with_future)

        assert not is_valid
        assert any("future" in error.lower() for error in errors)

    def test_detects_missing_required_fields(self):
        """Detects missing required fields."""
        incomplete_pack = {
            "metadata": {
                "anchor_date": "2025-01-15T12:00:00"
            }
            # Missing other sections
        }

        is_valid, errors = validate_context_pack(incomplete_pack)

        assert not is_valid
        assert len(errors) > 0

    def test_validates_regime_tags_are_list(self):
        """Regime tags must be a list."""
        invalid_pack = {
            "metadata": {
                "anchor_date": "2025-01-15T12:00:00",
                "data_cutoff": "2025-01-15T12:00:00",
                "generated_at": datetime.utcnow().isoformat(),
                "version": "v1.0.0"
            },
            "regime_snapshot": {},
            "macro_indicators": {},
            "recent_events": [],
            "regime_tags": "not_a_list"  # Invalid type
        }

        is_valid, errors = validate_context_pack(invalid_pack)

        assert not is_valid
        assert any("regime_tags" in error.lower() for error in errors)

    @freeze_time("2025-01-15 12:00:00")
    def test_detects_stale_data(self):
        """Detects if generated_at is too far from anchor_date."""
        stale_pack = {
            "metadata": {
                "anchor_date": "2025-01-15T12:00:00",
                "data_cutoff": "2025-01-15T12:00:00",
                "generated_at": "2025-01-14T12:00:00",  # 24 hours old
                "version": "v1.0.0"
            },
            "regime_snapshot": {},
            "macro_indicators": {},
            "recent_events": [],
            "regime_tags": []
        }

        is_valid, errors = validate_context_pack(stale_pack)

        assert not is_valid
        assert any("stale" in error.lower() or "freshness" in error.lower() for error in errors)
