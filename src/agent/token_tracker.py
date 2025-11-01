"""
Token usage tracking and analysis for AI agent workflows.

Tracks token consumption at each workflow checkpoint to identify where tokens are being used.
Uses tiktoken for accurate GPT-4/5 token counting.

Usage:
    tracker = TokenTracker(model="openai:gpt-5", enabled=True)

    # Before API call
    tracker.estimate_prompt(
        label="Phase 1: Research",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        tool_definitions_est=7000  # Estimate if not available
    )

    # After workflow
    tracker.print_report()
"""

from dataclasses import dataclass, field
from typing import Optional, Any
import json
import tiktoken


@dataclass
class TokenUsageSnapshot:
    """Records token usage at a specific checkpoint."""

    label: str
    system_prompt_tokens: int = 0
    user_prompt_tokens: int = 0
    tool_definitions_tokens: int = 0
    estimated_total: int = 0
    actual_prompt_tokens: Optional[int] = None
    actual_completion_tokens: Optional[int] = None
    actual_total_tokens: Optional[int] = None
    notes: str = ""


class TokenTracker:
    """
    Tracks token usage across workflow stages.

    Provides detailed breakdowns of where tokens are consumed to help identify
    optimization opportunities when hitting context limits.
    """

    def __init__(self, model: str = "openai:gpt-4o", enabled: bool = True):
        """
        Initialize token tracker.

        Args:
            model: Model identifier (e.g., "openai:gpt-5")
            enabled: Whether tracking is enabled (can disable via env var)
        """
        self.model = model
        self.enabled = enabled
        self.snapshots: list[TokenUsageSnapshot] = []

        # Initialize tiktoken encoder for GPT-4/5 (cl100k_base encoding)
        try:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            print(f"Warning: Failed to initialize tiktoken encoder: {e}")
            self.encoder = None
            self.enabled = False

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a string.

        Args:
            text: String to count tokens for

        Returns:
            Number of tokens (0 if encoder unavailable)
        """
        if not self.enabled or not self.encoder or not text:
            return 0

        try:
            return len(self.encoder.encode(text))
        except Exception as e:
            print(f"Warning: Failed to count tokens: {e}")
            return 0

    def count_tokens_json(self, obj: Any) -> int:
        """
        Count tokens in a JSON-serializable object.

        Args:
            obj: Object to serialize and count

        Returns:
            Number of tokens in JSON representation
        """
        if not self.enabled:
            return 0

        try:
            json_str = json.dumps(obj, indent=2)
            return self.count_tokens(json_str)
        except Exception as e:
            print(f"Warning: Failed to count JSON tokens: {e}")
            return 0

    def estimate_prompt(
        self,
        label: str,
        system_prompt: str = "",
        user_prompt: str = "",
        tool_definitions_est: int = 0,
        notes: str = ""
    ) -> TokenUsageSnapshot:
        """
        Estimate token usage before an API call.

        This is the main method to call BEFORE agent.run() to measure inputs.

        Args:
            label: Description of this checkpoint (e.g., "Phase 1: Research")
            system_prompt: System prompt text
            user_prompt: User prompt text
            tool_definitions_est: Estimated tokens for tool definitions (if known)
            notes: Additional notes about this checkpoint

        Returns:
            TokenUsageSnapshot with estimated counts
        """
        if not self.enabled:
            return TokenUsageSnapshot(label=label)

        # Count tokens in each component
        system_tokens = self.count_tokens(system_prompt)
        user_tokens = self.count_tokens(user_prompt)

        # Calculate total estimate
        estimated_total = system_tokens + user_tokens + tool_definitions_est

        snapshot = TokenUsageSnapshot(
            label=label,
            system_prompt_tokens=system_tokens,
            user_prompt_tokens=user_tokens,
            tool_definitions_tokens=tool_definitions_est,
            estimated_total=estimated_total,
            notes=notes
        )

        self.snapshots.append(snapshot)
        return snapshot

    def record_api_response(
        self,
        label: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int
    ):
        """
        Record actual token usage from API response metadata.

        Call this AFTER agent.run() if you can access the response metadata.

        Args:
            label: Label matching the estimate_prompt() call
            prompt_tokens: Actual prompt tokens from API
            completion_tokens: Actual completion tokens from API
            total_tokens: Actual total tokens from API
        """
        if not self.enabled:
            return

        # Find matching snapshot
        for snapshot in reversed(self.snapshots):
            if snapshot.label == label:
                snapshot.actual_prompt_tokens = prompt_tokens
                snapshot.actual_completion_tokens = completion_tokens
                snapshot.actual_total_tokens = total_tokens
                return

        # If no matching snapshot, create new one with actual data
        snapshot = TokenUsageSnapshot(
            label=label,
            actual_prompt_tokens=prompt_tokens,
            actual_completion_tokens=completion_tokens,
            actual_total_tokens=total_tokens
        )
        self.snapshots.append(snapshot)

    def print_report(self):
        """
        Print detailed token usage report.

        Shows breakdown of token usage at each checkpoint with estimates and actuals.
        """
        if not self.enabled or not self.snapshots:
            return

        print("\n" + "=" * 80)
        print("TOKEN USAGE REPORT")
        print("=" * 80)
        print(f"Model: {self.model}")
        print(f"Snapshots: {len(self.snapshots)}")
        print()

        total_estimated = 0
        total_actual = 0

        for i, snapshot in enumerate(self.snapshots, 1):
            print(f"{i}. {snapshot.label}")

            if snapshot.estimated_total > 0:
                print("   Estimated Breakdown:")
                print(f"     - System Prompt:      {snapshot.system_prompt_tokens:>7,} tokens")
                print(f"     - User Prompt:        {snapshot.user_prompt_tokens:>7,} tokens")
                if snapshot.tool_definitions_tokens > 0:
                    print(f"     - Tool Definitions:   {snapshot.tool_definitions_tokens:>7,} tokens")
                print(f"     - ESTIMATED TOTAL:    {snapshot.estimated_total:>7,} tokens")
                total_estimated += snapshot.estimated_total

            if snapshot.actual_total_tokens is not None:
                print("   Actual Usage (from API):")
                print(f"     - Prompt:             {snapshot.actual_prompt_tokens:>7,} tokens")
                print(f"     - Completion:         {snapshot.actual_completion_tokens:>7,} tokens")
                print(f"     - ACTUAL TOTAL:       {snapshot.actual_total_tokens:>7,} tokens")
                total_actual += snapshot.actual_total_tokens

                # Show gap if we have both estimates and actuals
                if snapshot.estimated_total > 0:
                    gap = snapshot.actual_total_tokens - snapshot.estimated_total
                    gap_pct = (gap / snapshot.actual_total_tokens * 100) if snapshot.actual_total_tokens > 0 else 0
                    print(f"     - Gap (actual - est): {gap:>7,} tokens ({gap_pct:+.1f}%)")

            if snapshot.notes:
                print(f"   Notes: {snapshot.notes}")

            print()

        print("-" * 80)
        print("SUMMARY")
        print("-" * 80)

        if total_estimated > 0:
            print(f"Total Estimated:     {total_estimated:>10,} tokens")

        if total_actual > 0:
            print(f"Total Actual:        {total_actual:>10,} tokens")

        if total_estimated > 0 and total_actual > 0:
            gap = total_actual - total_estimated
            gap_pct = (gap / total_actual * 100) if total_actual > 0 else 0
            print(f"Total Gap:           {gap:>10,} tokens ({gap_pct:+.1f}%)")
            print()
            print("NOTE: Large gaps suggest tokens consumed by:")
            print("  - Conversation history (tool call results)")
            print("  - Response formatting overhead")
            print("  - Additional context we're not tracking")

        print("=" * 80)

    def get_total_estimated(self) -> int:
        """Get total estimated tokens across all snapshots."""
        return sum(s.estimated_total for s in self.snapshots)

    def get_total_actual(self) -> int:
        """Get total actual tokens across all snapshots (0 if no actuals recorded)."""
        actuals = [s.actual_total_tokens for s in self.snapshots if s.actual_total_tokens is not None]
        return sum(actuals) if actuals else 0
