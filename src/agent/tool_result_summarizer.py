"""
Tool result summarization to reduce token consumption in conversation history.

Uses the workflow's LLM to compress large tool results (FRED API, yfinance)
before they're added to the agent's conversation history.

Configuration:
    COMPRESS_MCP_RESULTS - Enable/disable compression (default: true)
    SUMMARIZATION_MODEL - Override model for summarization (optional, defaults to workflow model)

The summarization model is set automatically by the workflow via set_summarization_model().
"""

import os
import json
from typing import Any
from pydantic_ai import Agent


# Summarization prompt template
SUMMARIZATION_PROMPT = """You are a tool result summarizer. Extract ONLY the essential information from tool results to minimize tokens.

**Guidelines:**

For FRED series data (fred_get_series, fred_search):
- Series ID and name
- Latest value and date
- Trend direction (up/down/stable) over last 3 months
- OMIT: Full observation arrays, all historical data points

For stock/market data (stock_get_historical_stock_prices):
- Ticker symbol
- Date range
- Latest price and % change from start
- OMIT: Full price history arrays

For search results (fred_search, composer_search_symphonies):
- Top 3 most relevant results only
- Brief 1-line description per result
- OMIT: Full metadata, popularity scores, long descriptions

**Critical rules:**
1. Output ONLY valid JSON
2. Maximum 30 tokens in your response (HARD LIMIT)
3. Preserve numerical precision (don't round excessively)
4. Include units (%, $, basis points, etc.)
5. Be extremely concise - prefer single values over ranges

**Input (tool result to summarize):**
{tool_result}

**Output (compressed JSON summary):**"""


class SummarizationService:
    """
    Service for summarizing large tool results using an LLM.

    Reduces token consumption by compressing FRED API responses, stock data,
    and search results before they're added to conversation history.
    """

    def __init__(self, model: str, enabled: bool = True):
        """
        Initialize summarization service.

        Args:
            model: LLM model identifier (e.g., "openai:kimi-k2-thinking")
            enabled: Whether summarization is enabled
        """
        self.model = model
        self.enabled = enabled
        self.total_original_tokens = 0
        self.total_summarized_tokens = 0

        if enabled:
            # Create agent for summarization
            self.agent = Agent(
                model=model,
                output_type=str,  # Expect JSON string output
                system_prompt="You are a precise data summarizer. Output only valid JSON."
            )

    def should_summarize(self, tool_name: str, result: Any) -> bool:
        """
        Determine if a tool result should be summarized.

        Args:
            tool_name: Name of the tool that produced the result
            result: The tool result

        Returns:
            True if result should be summarized
        """
        if not self.enabled:
            return False

        # Only summarize large results from data-heavy tools
        if not tool_name.startswith(('fred_', 'stock_')):
            return False

        # Check result size
        try:
            result_str = json.dumps(result) if not isinstance(result, str) else result
            # Summarize if result is > 200 characters
            return len(result_str) > 200
        except:
            return False

    async def summarize(self, tool_name: str, result: Any) -> dict:
        """
        Summarize a tool result using LLM.

        Args:
            tool_name: Name of the tool that produced the result
            result: The tool result to summarize

        Returns:
            Dict with:
                - summary: Compressed version of the result
                - original_tokens: Estimated tokens in original result
                - summary_tokens: Estimated tokens in summary
                - savings: Token reduction amount
        """
        if not self.enabled:
            return {
                "summary": result,
                "original_tokens": 0,
                "summary_tokens": 0,
                "savings": 0
            }

        # Convert result to string for token counting
        result_str = json.dumps(result, indent=2) if not isinstance(result, str) else result

        # Estimate original tokens (rough: 1 token ≈ 4 characters)
        original_tokens = len(result_str) // 4

        # Format prompt
        prompt = SUMMARIZATION_PROMPT.format(tool_result=result_str)

        try:
            # Run summarization agent
            result_obj = await self.agent.run(prompt)
            summary = result_obj.output

            # Parse summary (should be JSON)
            try:
                summary_parsed = json.loads(summary)
            except json.JSONDecodeError:
                # If LLM didn't return valid JSON, use as-is
                summary_parsed = {"summary": summary}

            # Estimate summary tokens
            summary_str = json.dumps(summary_parsed)
            summary_tokens = len(summary_str) // 4

            # Track totals
            self.total_original_tokens += original_tokens
            self.total_summarized_tokens += summary_tokens

            return {
                "summary": summary_parsed,
                "original_tokens": original_tokens,
                "summary_tokens": summary_tokens,
                "savings": original_tokens - summary_tokens
            }

        except Exception as e:
            print(f"Warning: Summarization failed for {tool_name}: {e}")
            # Return original on error
            return {
                "summary": result,
                "original_tokens": original_tokens,
                "summary_tokens": original_tokens,
                "savings": 0
            }

    def get_stats(self) -> dict:
        """
        Get summarization statistics.

        Returns:
            Dict with total_original_tokens, total_summarized_tokens, total_savings
        """
        return {
            "total_original_tokens": self.total_original_tokens,
            "total_summarized_tokens": self.total_summarized_tokens,
            "total_savings": self.total_original_tokens - self.total_summarized_tokens,
            "savings_percent": (
                (self.total_original_tokens - self.total_summarized_tokens) / self.total_original_tokens * 100
                if self.total_original_tokens > 0 else 0
            )
        }

    def print_stats(self):
        """Print summarization statistics."""
        if not self.enabled:
            print("Tool result summarization: DISABLED")
            return

        stats = self.get_stats()

        print("\n" + "=" * 80)
        print("TOOL RESULT SUMMARIZATION STATS")
        print("=" * 80)
        print(f"Model: {self.model}")
        print(f"Original tokens:    {stats['total_original_tokens']:>10,}")
        print(f"Summarized tokens:  {stats['total_summarized_tokens']:>10,}")
        print(f"Savings:            {stats['total_savings']:>10,} ({stats['savings_percent']:.1f}%)")
        print("=" * 80)
