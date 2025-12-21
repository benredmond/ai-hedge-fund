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

from src.agent.models import WorkflowResult, WorkflowCheckpoint


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
    model: str | None = None,
    base_dir: Path | None = None,
) -> Path | None:
    """
    Save WorkflowResult to cohort strategies file.

    Appends the result to data/cohorts/{cohort_id}/strategies.json.
    Uses atomic write pattern (temp file + os.replace) to prevent corruption.

    Args:
        result: WorkflowResult to persist
        cohort_id: Cohort identifier (e.g., "2025-Q1")
        model: LLM model identifier (e.g., "openai:gpt-4o")
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
        result_dict["model"] = model
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


# Checkpoint file name (per cohort)
CHECKPOINT_FILENAME = "checkpoint.json"


def save_checkpoint(
    checkpoint: WorkflowCheckpoint,
    cohort_id: str,
    base_dir: Path | None = None,
) -> Path | None:
    """
    Save workflow checkpoint atomically.

    Creates/updates data/cohorts/{cohort_id}/checkpoint.json with current
    workflow state. Uses atomic write pattern (temp + os.replace) to prevent
    corruption on crash.

    Args:
        checkpoint: WorkflowCheckpoint with current state
        cohort_id: Cohort identifier (e.g., "2025-Q1")
        base_dir: Override base directory (for testing)

    Returns:
        Path to checkpoint file, or None if save failed

    Note:
        Logs errors but does not raise exceptions (graceful degradation).
    """
    temp_file = None
    try:
        validate_cohort_id(cohort_id)

        base = base_dir or COHORTS_DIR
        cohort_dir = base / cohort_id
        checkpoint_file = cohort_dir / CHECKPOINT_FILENAME
        temp_file = cohort_dir / f"{CHECKPOINT_FILENAME}.tmp"

        cohort_dir.mkdir(parents=True, exist_ok=True)

        # Serialize checkpoint using Pydantic's JSON mode (handles enums)
        checkpoint_dict = checkpoint.model_dump(mode="json")

        # Atomic write
        with open(temp_file, 'w') as f:
            json.dump(checkpoint_dict, f, indent=2, default=str)

        os.replace(temp_file, checkpoint_file)

        print(f"💾 Checkpoint saved: stage={checkpoint.last_completed_stage.value}")
        return checkpoint_file

    except ValueError as e:
        print(f"❌ Checkpoint validation error: {e}")
        return None

    except PermissionError as e:
        print(f"❌ Checkpoint permission error: {e}")
        return None

    except OSError as e:
        print(f"❌ Checkpoint OS error: {e}")
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass
        return None

    except Exception as e:
        print(f"❌ Unexpected checkpoint error: {e}")
        return None


def load_checkpoint(
    cohort_id: str,
    base_dir: Path | None = None,
) -> WorkflowCheckpoint | None:
    """
    Load workflow checkpoint if it exists.

    Reads data/cohorts/{cohort_id}/checkpoint.json and validates schema.

    Args:
        cohort_id: Cohort identifier
        base_dir: Override base directory (for testing)

    Returns:
        WorkflowCheckpoint if exists and valid, None otherwise

    Note:
        Returns None for missing file, corrupted JSON, or invalid schema.
    """
    try:
        validate_cohort_id(cohort_id)

        base = base_dir or COHORTS_DIR
        checkpoint_file = base / cohort_id / CHECKPOINT_FILENAME

        if not checkpoint_file.exists():
            return None

        with open(checkpoint_file) as f:
            data = json.load(f)

        # Validate and deserialize using Pydantic
        checkpoint = WorkflowCheckpoint.model_validate(data)

        print(f"📂 Loaded checkpoint: stage={checkpoint.last_completed_stage.value}")
        return checkpoint

    except json.JSONDecodeError as e:
        print(f"⚠️  Corrupted checkpoint file: {e}")
        return None

    except ValueError as e:
        # Pydantic validation error or invalid cohort_id
        print(f"⚠️  Invalid checkpoint: {e}")
        return None

    except Exception as e:
        print(f"⚠️  Failed to load checkpoint: {e}")
        return None


def clear_checkpoint(
    cohort_id: str,
    base_dir: Path | None = None,
) -> bool:
    """
    Delete checkpoint file after successful workflow completion.

    Args:
        cohort_id: Cohort identifier
        base_dir: Override base directory (for testing)

    Returns:
        True if deleted or didn't exist, False on error
    """
    try:
        validate_cohort_id(cohort_id)

        base = base_dir or COHORTS_DIR
        checkpoint_file = base / cohort_id / CHECKPOINT_FILENAME

        if checkpoint_file.exists():
            checkpoint_file.unlink()
            print(f"🗑️  Checkpoint cleared for cohort: {cohort_id}")

        return True

    except ValueError as e:
        print(f"❌ Clear checkpoint validation error: {e}")
        return False

    except PermissionError as e:
        print(f"❌ Clear checkpoint permission error: {e}")
        return False

    except OSError as e:
        print(f"❌ Clear checkpoint OS error: {e}")
        return False

    except Exception as e:
        print(f"❌ Unexpected clear checkpoint error: {e}")
        return False
