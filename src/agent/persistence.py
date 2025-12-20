"""
Persistence layer for workflow results.

Saves WorkflowResult to JSON files for cohort tracking and analysis.
Uses atomic write pattern to prevent data corruption.
"""

import json
import os
import re
from pathlib import Path
from typing import Any

from src.agent.models import WorkflowResult


# Regex for valid cohort IDs (alphanumeric, underscores, hyphens)
COHORT_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

# Base directory for cohort data
COHORTS_DIR = Path("data/cohorts")


def validate_cohort_id(cohort_id: str) -> None:
    """
    Validate cohort_id to prevent directory traversal attacks.

    Args:
        cohort_id: Cohort identifier (e.g., "2025-Q1", "cohort_001")

    Raises:
        ValueError: If cohort_id contains invalid characters
    """
    if not cohort_id:
        raise ValueError("cohort_id cannot be empty")

    if not COHORT_ID_PATTERN.match(cohort_id):
        raise ValueError(
            f"Invalid cohort_id '{cohort_id}'. "
            f"Must contain only alphanumeric characters, underscores, and hyphens."
        )


def save_workflow_result(
    result: WorkflowResult,
    cohort_id: str,
    base_dir: Path | None = None,
) -> Path | None:
    """
    Save WorkflowResult to cohort strategies file.

    Appends the result to data/cohorts/{cohort_id}/strategies.json.
    Uses atomic write pattern (temp file + os.replace) to prevent corruption.

    Args:
        result: WorkflowResult to persist
        cohort_id: Cohort identifier (e.g., "2025-Q1")
        base_dir: Override base directory (for testing). Defaults to data/cohorts.

    Returns:
        Path to the saved file, or None if save failed

    Note:
        This function logs errors but does not raise exceptions.
        Workflow should not fail if persistence fails.
    """
    try:
        # Validate cohort_id
        validate_cohort_id(cohort_id)

        # Determine paths
        base = base_dir or COHORTS_DIR
        cohort_dir = base / cohort_id
        strategies_file = cohort_dir / "strategies.json"
        temp_file = cohort_dir / "strategies.json.tmp"

        # Create directory
        cohort_dir.mkdir(parents=True, exist_ok=True)

        # Load existing strategies or start fresh
        strategies: list[dict[str, Any]] = []
        if strategies_file.exists():
            try:
                with open(strategies_file) as f:
                    data = json.load(f)
                    strategies = data.get("strategies", [])
            except json.JSONDecodeError:
                print(f"⚠️  Corrupted strategies.json in {cohort_id}, starting fresh")
                strategies = []

        # Serialize new result
        result_dict = result.model_dump(mode="json")
        strategies.append(result_dict)

        # Prepare output data
        output_data = {
            "cohort_id": cohort_id,
            "strategies": strategies,
        }

        # Atomic write: write to temp file, then replace
        with open(temp_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)

        os.replace(temp_file, strategies_file)

        print(f"💾 Saved workflow result to: {strategies_file}")
        print(f"   Total strategies in cohort: {len(strategies)}")

        return strategies_file

    except ValueError as e:
        # Validation errors (invalid cohort_id)
        print(f"❌ Persistence validation error: {e}")
        return None

    except PermissionError as e:
        print(f"❌ Persistence permission error: {e}")
        return None

    except OSError as e:
        print(f"❌ Persistence OS error: {e}")
        # Clean up temp file if it exists
        try:
            if temp_file.exists():
                temp_file.unlink()
        except Exception:
            pass
        return None

    except Exception as e:
        print(f"❌ Unexpected persistence error: {e}")
        return None
