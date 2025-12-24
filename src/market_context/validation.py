"""Context pack validation utilities."""

from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List


def validate_context_pack(pack: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate market context pack for data quality and temporal consistency.

    Checks:
    - No future data leakage (all dates <= anchor_date)
    - Required fields present
    - Data freshness (generated_at within 1 hour of anchor_date)
    - Schema correctness

    Returns:
        (is_valid, list_of_error_messages)
    """
    errors = []

    # Check required top-level fields
    required_fields = ["metadata", "regime_snapshot", "macro_indicators", "recent_events"]
    for field in required_fields:
        if field not in pack:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Validate metadata
    metadata = pack["metadata"]
    required_metadata = ["anchor_date", "data_cutoff", "generated_at", "version"]
    for field in required_metadata:
        if field not in metadata:
            errors.append(f"Missing metadata field: {field}")

    if errors:
        return False, errors

    # Parse dates
    try:
        anchor_date = datetime.fromisoformat(metadata["anchor_date"])
        generated_at = datetime.fromisoformat(metadata["generated_at"])
    except (ValueError, TypeError) as e:
        errors.append(f"Invalid date format: {e}")
        return False, errors

    # Check data freshness (generated_at should be close to anchor_date)
    time_diff = abs((anchor_date - generated_at).total_seconds())
    if time_diff > 3600:  # 1 hour
        errors.append(f"Data appears stale: generated_at is {time_diff/60:.1f} minutes from anchor_date")

    # Check for future data leakage in events
    for event in pack["recent_events"]:
        if "date" in event:
            try:
                event_date = datetime.fromisoformat(event["date"])
                if event_date > anchor_date:
                    errors.append(f"Future data leakage: event dated {event['date']} after anchor {metadata['anchor_date']}")
            except (ValueError, TypeError):
                errors.append(f"Invalid event date format: {event.get('date', 'unknown')}")

    # Check regime_snapshot structure
    if not isinstance(pack["regime_snapshot"], dict):
        errors.append("regime_snapshot must be a dictionary")

    # Check macro_indicators structure
    if not isinstance(pack["macro_indicators"], dict):
        errors.append("macro_indicators must be a dictionary")

    return (len(errors) == 0, errors)
