"""Deploy winning strategy to Composer.trade as a symphony."""

import asyncio
import copy
import json
import logging
import os
import re
import traceback
import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from src.agent.mcp_config import create_composer_server

# Enable debug logging for pydantic_ai when DEBUG_PROMPTS is set (skip noisy HTTP logs)
if os.getenv("DEBUG_PROMPTS", "0") == "1":
    logging.getLogger("pydantic_ai").setLevel(logging.DEBUG)
    # Suppress noisy HTTP logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

from src.agent.strategy_creator import (
    create_agent,
    load_prompt,
    DEFAULT_MODEL,
    get_model_settings,
)
from src.agent.models import Strategy, Charter


class SymphonyConfirmation(BaseModel):
    """Simple confirmation model - model just confirms deployment."""

    ready_to_deploy: bool = Field(
        description="True if the strategy is ready to deploy"
    )
    symphony_name: str = Field(
        description="Name for the symphony (short, descriptive)"
    )
    symphony_description: str = Field(
        description="Brief description of the strategy (1-2 sentences)"
    )


def _classify_error(e: Exception) -> tuple[str, str]:
    """
    Classify an exception into an error type and actionable message.

    Returns:
        Tuple of (error_type, user_message)
    """
    error_str = str(e).lower()

    # Authentication errors
    if "401" in error_str or "unauthorized" in error_str:
        return "AUTH", (
            "Composer credentials invalid or expired. "
            "Check COMPOSER_API_KEY and COMPOSER_API_SECRET in .env"
        )
    if "403" in error_str or "forbidden" in error_str:
        return "AUTH", (
            "Composer access forbidden. Your API key may lack required permissions."
        )

    # Rate limiting
    if "429" in error_str or "rate" in error_str or "too many" in error_str:
        return "RATE_LIMIT", "Composer rate limit exceeded. Will retry with backoff."

    # Schema/validation errors
    if "schema" in error_str or "invalid" in error_str or "required" in error_str:
        return "SCHEMA", f"Symphony schema validation failed: {e}"

    # Network errors
    if "timeout" in error_str or "connection" in error_str or "network" in error_str:
        return "NETWORK", f"Network error connecting to Composer: {e}"

    # Unknown - include full details
    return "UNKNOWN", f"Unexpected error: {type(e).__name__}: {e}"


def _get_exchange(ticker: str) -> str:
    """Map ticker to exchange code."""
    etfs = {
        "SPY", "QQQ", "IWM", "DIA", "TLT", "GLD", "SLV", "VTI", "VOO", "BND",
        "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY", "XLC",
        "BIL", "SHY", "IEF", "AGG", "LQD", "HYG", "EMB", "VNQ", "ARKK", "SMH",
        "VIXY", "UVXY", "VXX",  # Volatility ETFs
    }
    if ticker in etfs:
        return "ARCX"
    nasdaq = {
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA", "NFLX",
        "ADBE", "CRM", "PYPL", "INTC", "AMD", "QCOM", "CSCO", "AVGO", "TXN", "COST", "PEP",
    }
    if ticker in nasdaq:
        return "XNAS"
    return "XNYS"


_FILTER_SORT_BY_MAP = {
    "cumulative_return": "cumulative-return",
    "moving_average_return": "moving-average-return",
    "moving_average_price": "moving-average-price",
    "relative_strength_index": "relative-strength-index",
    "standard_deviation_return": "standard-deviation-return",
    "standard_deviation_price": "standard-deviation-price",
    "max_drawdown": "max-drawdown",
    "current_price": "current-price",
}


def _parse_condition(condition_str: str) -> dict:
    """
    Parse a condition string into Composer if-child fields.

    Examples:
        "VIXY_price > 35" → {lhs-val: "VIXY", lhs-fn: "current-price", comparator: "gt", rhs-val: 35}
        "SPY_price > SPY_200d_MA" → {lhs-val: "SPY", lhs-fn: "current-price", rhs-val: "SPY", rhs-fn: "moving-average-price"}

    Returns dict with Composer if-child fields.
    """
    condition_str = condition_str.strip()

    # Composer IF nodes only support a single comparison (no AND/OR)
    if re.search(r'\b(and|or)\b', condition_str, re.IGNORECASE):
        raise ValueError(
            "Boolean operators (AND/OR) are not supported in logic_tree.condition. "
            "Use a single comparison."
        )
    if "!=" in condition_str:
        raise ValueError(
            "Comparator '!=' is not supported by Composer. "
            "Use '==' or invert the condition."
        )

    # Comparator mapping
    comparator_map = {
        ">": "gt",
        ">=": "gte",
        "<": "lt",
        "<=": "lte",
        "==": "eq",
    }

    # Function suffix mapping
    # NOTE: current-price is NOT valid for IF conditionals!
    # Use moving-average-price with window=1 as proxy for current price
    fn_suffix_map = {
        "_standard_deviation_return_": ("standard-deviation-return", r"_standard_deviation_return_(\d+)d"),
        "_standard_deviation_price_": ("standard-deviation-price", r"_standard_deviation_price_(\d+)d"),
        "_cumulative_return_": ("cumulative-return", r"_cumulative_return_(\d+)d"),
        "_RSI_": ("relative-strength-index", r"_RSI_(\d+)d"),
        "_200d_MA": ("moving-average-price", 200),
        "_50d_MA": ("moving-average-price", 50),
        "_EMA_": ("exponential-moving-average-price", r"_EMA_(\d+)d"),
        "_price": ("moving-average-price", 1),  # current-price NOT valid for conditionals
    }

    # Find the comparator
    comparator = None
    comparator_str = None
    for op in [">=", "<=", "==", ">", "<"]:  # Order matters: >= before >
        if op in condition_str:
            comparator = comparator_map[op]
            comparator_str = op
            break

    if not comparator:
        raise ValueError(f"No comparator found in condition: {condition_str}")

    # Split into left and right sides
    parts = condition_str.split(comparator_str)
    if len(parts) != 2:
        raise ValueError(f"Invalid condition format: {condition_str}")

    lhs_str = parts[0].strip()
    rhs_str = parts[1].strip()

    def parse_operand(operand: str) -> tuple:
        """Parse an operand like 'VIXY_price' or '35' into (ticker, fn, params, is_fixed)."""
        operand = operand.strip()

        # Check if it's a number
        try:
            value = float(operand)
            if value == int(value):
                value = int(value)
            return (value, None, None, True)  # None for params, not {}
        except ValueError:
            pass

        # Generic moving average format: TICKER_<N>d_MA (e.g., VIXY_20d_MA)
        ma_match = re.match(r"^([^_]+)_(\d+)d_MA$", operand, re.IGNORECASE)
        if ma_match:
            ticker = ma_match.group(1)
            window = int(ma_match.group(2))
            if not ticker:
                raise ValueError(
                    f"Unsupported operand format: '{operand}'. "
                    "Operand must start with a valid ticker symbol."
                )
            return (ticker.upper(), "moving-average-price", {"window": window}, False)

        # Parse ticker_function format
        operand_lower = operand.lower()
        for suffix, (fn_name, window_spec) in fn_suffix_map.items():
            suffix_lower = suffix.lower()
            if suffix_lower in operand_lower:
                # Extract ticker (everything before the suffix)
                suffix_index = operand_lower.find(suffix_lower)
                ticker = operand[:suffix_index]
                if not ticker:
                    # Handle case like "_price" at start
                    ticker = operand.replace(suffix, "").strip("_")
                if not ticker or "_" in ticker:
                    raise ValueError(
                        f"Unsupported operand format: '{operand}'. "
                        "Operand must start with a valid ticker symbol."
                    )

                params = None  # Default to None for paramless functions
                if window_spec is not None:
                    if isinstance(window_spec, int):
                        params = {"window": window_spec}
                    elif isinstance(window_spec, str):
                        # Regex pattern to extract window
                        match = re.search(window_spec, operand, re.IGNORECASE)
                        if match:
                            params = {"window": int(match.group(1))}

                return (ticker.upper(), fn_name, params, False)

        if "_" in operand:
            raise ValueError(
                f"Unsupported operand format: '{operand}'. "
                "Use TICKER or TICKER_price / TICKER_<N>d_MA / TICKER_200d_MA / "
                "TICKER_cumulative_return_Nd / TICKER_RSI_Nd / TICKER_EMA_Nd."
            )

        # Fallback: assume it's a ticker with moving-average-price(1) as proxy for current price
        # NOTE: current-price is NOT valid for IF conditionals!
        return (operand.upper(), "moving-average-price", {"window": 1}, False)

    lhs_ticker, lhs_fn, lhs_params, lhs_fixed = parse_operand(lhs_str)
    rhs_ticker, rhs_fn, rhs_params, rhs_fixed = parse_operand(rhs_str)

    if lhs_fixed and rhs_fixed:
        raise ValueError("Invalid condition: both operands are numeric.")

    if lhs_fixed and not rhs_fixed:
        inverse_map = {
            "gt": "lt",
            "gte": "lte",
            "lt": "gt",
            "lte": "gte",
            "eq": "eq",
        }
        comparator = inverse_map.get(comparator)
        if not comparator:
            raise ValueError(f"Unsupported comparator reversal for condition: {condition_str}")
        lhs_ticker, lhs_fn, lhs_params, lhs_fixed, rhs_ticker, rhs_fn, rhs_params, rhs_fixed = (
            rhs_ticker,
            rhs_fn,
            rhs_params,
            rhs_fixed,
            lhs_ticker,
            lhs_fn,
            lhs_params,
            lhs_fixed,
        )

    # When rhs is a fixed value, ALWAYS mirror lhs-fn (per working production example)
    # The docs say rhs-fn should be null, but actual working symphonies show it matches lhs-fn
    if rhs_fixed:
        rhs_fn = lhs_fn
        rhs_params = lhs_params.copy() if lhs_params else None  # None, not {}

    result = {
        "comparator": comparator,
        "lhs-val": lhs_ticker,
        "lhs-fn": lhs_fn,
        "lhs-fn-params": lhs_params,
        "lhs-window-days": None,  # Required field (deprecated but still needed)
        "rhs-val": rhs_ticker,
        "rhs-fixed-value?": rhs_fixed,
        "rhs-fn": rhs_fn,
        "rhs-fn-params": rhs_params,
        "rhs-window-days": None,  # Required field (deprecated but still needed)
    }

    return result


def _build_if_structure(
    logic_tree: dict,
    rebalance: str = "monthly",
) -> dict:
    """
    Build Composer IF structure from Strategy.logic_tree.

    Args:
        logic_tree: Dict with {condition, if_true, if_false}
        rebalance: Rebalance frequency

    Returns:
        Composer IF node structure.
    """
    condition = logic_tree.get("condition", "")
    if_true = logic_tree.get("if_true", {})
    if_false = logic_tree.get("if_false", {})

    # Parse the condition
    condition_fields = _parse_condition(condition)

    def build_branch_assets(branch: dict, use_specified_weights: bool = True) -> list:
        """Build asset nodes for a branch."""
        assets = branch.get("assets", [])
        weights = branch.get("weights", {})

        asset_nodes = []
        for ticker in assets:
            node = {
                "id": str(uuid.uuid4()),
                "step": "asset",
                "ticker": ticker,
                "exchange": _get_exchange(ticker),
                "name": ticker,
                "weight": None,
            }
            # Add allocation if using specified weights
            if use_specified_weights and weights:
                allocation = weights.get(ticker, 1.0 / len(assets))
                node["allocation"] = allocation
            asset_nodes.append(node)

        return asset_nodes

    def normalize_branch_weights(branch: dict) -> dict | None:
        weights = branch.get("weights")
        if not weights:
            return None
        if not isinstance(weights, dict):
            raise ValueError(f"Branch weights must be a dict, got: {weights!r}")

        assets = branch.get("assets", [])
        if set(weights.keys()) != set(assets):
            raise ValueError(
                f"Branch weights keys must match assets. Assets={assets}, Weights={list(weights.keys())}"
            )

        normalized = {}
        for ticker, value in weights.items():
            try:
                weight = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Branch weight for {ticker} must be numeric, got: {value!r}") from exc
            if weight < 0:
                raise ValueError(f"Branch weight for {ticker} must be non-negative, got: {weight}")
            normalized[ticker] = weight

        total = sum(normalized.values())
        if not 0.99 <= total <= 1.01:
            raise ValueError(f"Branch weights sum to {total:.4f}, must be between 0.99 and 1.01")

        if total != 1.0:
            normalized = {ticker: weight / total for ticker, weight in normalized.items()}

        return normalized

    def is_conditional_branch(branch: dict) -> bool:
        return isinstance(branch, dict) and {"condition", "if_true", "if_false"}.issubset(branch.keys())

    def is_filter_leaf(branch: dict) -> bool:
        return isinstance(branch, dict) and "filter" in branch and "assets" in branch

    def is_weighting_leaf(branch: dict) -> bool:
        return isinstance(branch, dict) and "weighting" in branch and "assets" in branch

    def build_filter_node(branch: dict) -> dict:
        filter_spec = branch.get("filter", {})
        sort_by = filter_spec.get("sort_by")
        sort_by_fn = _FILTER_SORT_BY_MAP.get(sort_by)
        if not sort_by_fn:
            raise ValueError(f"Unsupported filter sort_by: {sort_by!r}")

        window = filter_spec.get("window")
        select = filter_spec.get("select")
        n_value = filter_spec.get("n")
        if sort_by == "current_price":
            if window is not None:
                raise ValueError("Filter window must be omitted for current_price.")
            sort_by_params = None
        else:
            if not isinstance(window, int) or window <= 0:
                raise ValueError(f"Filter window must be positive integer, got: {window!r}")
            sort_by_params = {"window": window}
        if select not in {"top", "bottom"}:
            raise ValueError(f"Filter select must be 'top' or 'bottom', got: {select!r}")
        if not isinstance(n_value, int) or n_value < 1:
            raise ValueError(f"Filter n must be integer >= 1, got: {n_value!r}")

        filter_node = {
            "id": str(uuid.uuid4()),
            "step": "filter",
            "weight": None,
            "sort-by-fn": sort_by_fn,
            "select-fn": select,
            "select-n": n_value,
            "children": build_branch_assets(branch, use_specified_weights=False),
        }
        if sort_by_params is not None:
            filter_node["sort-by-fn-params"] = sort_by_params

        return filter_node

    def build_weighting_node(branch: dict) -> dict:
        weighting_spec = branch.get("weighting", {})
        method = weighting_spec.get("method")
        window = weighting_spec.get("window")
        if method != "inverse_vol":
            raise ValueError(f"Unsupported weighting method: {method!r}")
        if not isinstance(window, int) or window <= 0:
            raise ValueError(f"Weighting window must be positive integer, got: {window!r}")

        return {
            "id": str(uuid.uuid4()),
            "step": "wt-inverse-vol",
            "weight": None,
            "window-days": window,
            "children": build_branch_assets(branch, use_specified_weights=False),
        }

    def build_branch_content(branch: dict) -> list:
        """
        Build content for an if-child branch.

        Based on working Composer symphony examples:
        - Single asset: goes directly under if-child (no wrapper)
        - Multiple assets: use wt-cash-specified when weights are provided, otherwise wt-cash-equal
        """
        if is_conditional_branch(branch):
            return [_build_if_structure(branch, rebalance)]

        if is_filter_leaf(branch):
            return [build_filter_node(branch)]

        if is_weighting_leaf(branch):
            return [build_weighting_node(branch)]

        assets = branch.get("assets", [])
        normalized_weights = normalize_branch_weights(branch)

        # Single asset: place directly (no wrapper needed)
        if len(assets) == 1:
            return build_branch_assets(branch, use_specified_weights=False)

        if normalized_weights:
            branch = dict(branch)
            branch["weights"] = normalized_weights
            return [{
                "id": str(uuid.uuid4()),
                "step": "wt-cash-specified",
                "weight": None,
                "children": build_branch_assets(branch, use_specified_weights=True),
            }]

        # Multiple assets without weights: use wt-cash-equal
        return [{
            "id": str(uuid.uuid4()),
            "step": "wt-cash-equal",
            "weight": None,
            "children": build_branch_assets(branch, use_specified_weights=False),
        }]

    # Build TRUE branch (if-child with is-else-condition? = false)
    true_branch = {
        "id": str(uuid.uuid4()),
        "step": "if-child",
        "is-else-condition?": False,
        "weight": None,
        **condition_fields,
        "children": build_branch_content(if_true),
    }

    # Build FALSE branch (if-child with is-else-condition? = true)
    false_branch = {
        "id": str(uuid.uuid4()),
        "step": "if-child",
        "is-else-condition?": True,
        "weight": None,
        "children": build_branch_content(if_false),
    }

    # Build IF node
    if_node = {
        "id": str(uuid.uuid4()),
        "step": "if",
        "weight": None,
        "children": [true_branch, false_branch],
    }

    return if_node


def _build_symphony_json(
    name: str,
    description: str,
    tickers: list[str],
    rebalance: str = "monthly",
    logic_tree: dict | None = None,
) -> dict:
    """
    Build valid Composer symphony JSON structure for save_symphony.

    This is done in Python to avoid LLM hallucination issues with nested JSON.

    Args:
        name: Symphony name
        description: Symphony description
        tickers: List of asset tickers (used for static strategies)
        rebalance: Rebalance frequency
        logic_tree: Optional conditional logic tree {condition, if_true, if_false}

    Returns dict with:
        - symphony_score: The symphony structure
        - color: Required hex color for the symphony
        - hashtag: Required hashtag identifier
        - asset_class: EQUITIES or CRYPTO
    """
    debug = os.getenv("DEBUG_PROMPTS", "0") == "1"

    # Check if this is a conditional strategy
    has_conditional_logic = (
        logic_tree
        and isinstance(logic_tree, dict)
        and "condition" in logic_tree
        and "if_true" in logic_tree
        and "if_false" in logic_tree
    )
    has_filter_root = (
        logic_tree
        and isinstance(logic_tree, dict)
        and "filter" in logic_tree
        and "assets" in logic_tree
    )
    has_weighting_root = (
        logic_tree
        and isinstance(logic_tree, dict)
        and "weighting" in logic_tree
        and "assets" in logic_tree
    )

    if has_weighting_root:
        raise ValueError("Root-level weighting leaves are not supported in symphony generation.")

    if has_conditional_logic:
        # Build IF structure for conditional strategies
        if debug:
            print(f"[DEBUG:_build_symphony_json] Building conditional IF structure")
            print(f"[DEBUG:_build_symphony_json] logic_tree: {logic_tree}")

        if_node = _build_if_structure(logic_tree, rebalance)

        # CRITICAL: if node must be wrapped in wt-cash-equal (root children must be weighting nodes)
        # Structure: root → wt-cash-equal → if → if-child branches
        symphony_score = {
            "id": str(uuid.uuid4()),
            "name": name,
            "step": "root",
            "weight": None,
            "rebalance": rebalance,
            "description": description,
            "rebalance-corridor-width": None,
            "children": [{
                "id": str(uuid.uuid4()),
                "step": "wt-cash-equal",
                "weight": None,
                "children": [if_node],
            }],
        }
    elif has_filter_root:
        filter_spec = logic_tree.get("filter", {})
        sort_by = filter_spec.get("sort_by")
        sort_by_fn = _FILTER_SORT_BY_MAP.get(sort_by)
        if not sort_by_fn:
            raise ValueError(f"Unsupported filter sort_by: {sort_by!r}")

        window = filter_spec.get("window")
        select = filter_spec.get("select")
        n_value = filter_spec.get("n")
        if sort_by == "current_price":
            if window is not None:
                raise ValueError("Filter window must be omitted for current_price.")
            sort_by_params = None
        else:
            if not isinstance(window, int) or window <= 0:
                raise ValueError(f"Filter window must be positive integer, got: {window!r}")
            sort_by_params = {"window": window}
        if select not in {"top", "bottom"}:
            raise ValueError(f"Filter select must be 'top' or 'bottom', got: {select!r}")
        if not isinstance(n_value, int) or n_value < 1:
            raise ValueError(f"Filter n must be integer >= 1, got: {n_value!r}")

        asset_nodes = []
        for ticker in logic_tree.get("assets", []):
            asset_nodes.append({
                "id": str(uuid.uuid4()),
                "step": "asset",
                "ticker": ticker,
                "exchange": _get_exchange(ticker),
                "name": ticker,
                "weight": None,
            })

        filter_node = {
            "id": str(uuid.uuid4()),
            "step": "filter",
            "weight": None,
            "sort-by-fn": sort_by_fn,
            "select-fn": select,
            "select-n": n_value,
            "children": asset_nodes,
        }
        if sort_by_params is not None:
            filter_node["sort-by-fn-params"] = sort_by_params

        symphony_score = {
            "id": str(uuid.uuid4()),
            "name": name,
            "step": "root",
            "weight": None,
            "rebalance": rebalance,
            "description": description,
            "rebalance-corridor-width": None,
            "children": [{
                "id": str(uuid.uuid4()),
                "step": "wt-cash-equal",
                "weight": None,
                "children": [filter_node],
            }],
        }
    else:
        # Build flat equal-weight structure for static strategies
        if debug:
            print(f"[DEBUG:_build_symphony_json] Building static wt-cash-equal structure")

        asset_nodes = []
        for ticker in tickers:
            asset_nodes.append({
                "id": str(uuid.uuid4()),
                "step": "asset",
                "ticker": ticker,
                "exchange": _get_exchange(ticker),
                "name": ticker,
                "weight": None,
            })

        symphony_score = {
            "id": str(uuid.uuid4()),
            "name": name,
            "step": "root",
            "weight": None,
            "rebalance": rebalance,
            "description": description,
            "rebalance-corridor-width": None,
            "children": [{
                "id": str(uuid.uuid4()),
                "step": "wt-cash-equal",
                "weight": None,
                "children": asset_nodes,
            }],
        }

    # Generate hashtag from name (remove spaces, add #)
    hashtag = "#" + "".join(name.split()[:2])

    return {
        "symphony_score": symphony_score,
        "color": "#17BAFF",  # Blue (from Composer's allowed palette)
        "hashtag": hashtag,
    }


async def _call_composer_api(symphony_json: dict) -> dict:
    """
    Call Composer MCP API to create symphony using pydantic_ai's session management.

    Uses MCPServerStreamableHTTP.direct_call_tool() which handles:
    - Session initialization (gets Mcp-Session-Id)
    - Proper MCP protocol handshake
    - Tool invocation with session context

    Returns:
        API response dict with symphony_id
    """
    debug = os.getenv("DEBUG_PROMPTS", "0") == "1"

    def convert_allocations_to_weight_map(payload: dict) -> dict:
        """Convert allocation fields to WeightMap for MCP schema compatibility."""
        converted = copy.deepcopy(payload)

        def walk(node) -> None:
            if isinstance(node, dict):
                if node.get("step") == "asset" and "allocation" in node:
                    allocation = node.pop("allocation")
                    try:
                        num = round(float(allocation) * 100, 4)
                    except (TypeError, ValueError):
                        num = allocation
                    node["weight"] = {"num": num, "den": 100}
                for value in node.values():
                    if isinstance(value, (dict, list)):
                        walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(converted)
        return converted

    # MCP schema expects WeightMap, not allocation
    symphony_payload = convert_allocations_to_weight_map(symphony_json)

    if debug:
        print(f"\n[DEBUG:_call_composer_api] Symphony JSON:")
        print(json.dumps(symphony_payload, indent=2, default=str))

    # Create Composer MCP server (handles auth via mcp_config)
    server = create_composer_server()

    async with server:
        if debug:
            # List available tools for debugging
            tools = await server.list_tools()
            tool_names = [t.name for t in tools]
            print(f"[DEBUG:_call_composer_api] Available tools: {tool_names}")

        # Call save_symphony tool directly (bypasses LLM, no hallucination)
        # Note: save_symphony actually saves and returns symphony_id
        # create_symphony only validates/previews without saving
        result = await server.direct_call_tool("save_symphony", symphony_payload)

        if debug:
            print(f"[DEBUG:_call_composer_api] Result: {result}")

        # direct_call_tool returns the parsed tool result directly
        # For save_symphony, this is a dict with symphony_id and version_id
        if isinstance(result, dict):
            return result

        # Fallback: try to parse as JSON if it's a string
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"raw_response": result}

        return {"result": str(result)}


class ComposerDeployer:
    """
    Stage 5: Deploy strategy to Composer.trade.

    Design:
    - LLM confirms deployment and provides name/description
    - Python builds the symphony JSON (no LLM hallucination)
    - Direct API call to Composer (no MCP tool schema issues)
    """

    async def deploy(
        self,
        strategy: Strategy,
        charter: Charter,
        market_context: dict,
        model: str = DEFAULT_MODEL,
    ) -> tuple[str | None, str | None, str | None]:
        """
        Deploy strategy to Composer.trade.

        Args:
            strategy: Winning strategy to deploy
            charter: Generated charter document
            market_context: Market context pack (for regime info)
            model: LLM model identifier

        Returns:
            Tuple of (symphony_id, deployed_at, description) or (None, None, None) if deployment skipped/failed.
        """
        # Check credentials first
        api_key = os.getenv("COMPOSER_API_KEY")
        api_secret = os.getenv("COMPOSER_API_SECRET")

        if not api_key or not api_secret:
            print("⚠️  Composer deployment skipped: COMPOSER_API_KEY/SECRET not set")
            return None, None, None

        try:
            return await self._run_with_retries(
                strategy=strategy,
                charter=charter,
                market_context=market_context,
                model=model,
            )
        except Exception as e:
            error_type, error_msg = _classify_error(e)
            print(f"\n{'='*80}")
            print(f"[ERROR:ComposerDeployer] Deployment failed")
            print(f"[ERROR:ComposerDeployer] Type: {error_type}")
            print(f"[ERROR:ComposerDeployer] Message: {error_msg}")
            print(f"[ERROR:ComposerDeployer] Strategy: {strategy.name}")
            print(f"[ERROR:ComposerDeployer] Assets: {strategy.assets}")
            tb_lines = traceback.format_exc().split('\n')[:10]
            print(f"[ERROR:ComposerDeployer] Traceback:")
            for line in tb_lines:
                if line.strip():
                    print(f"  {line}")
            print(f"{'='*80}\n")
            return None, None, None

    async def _run_with_retries(
        self,
        strategy: Strategy,
        charter: Charter,
        market_context: dict,
        model: str,
        max_attempts: int = 3,
        base_delay: float = 5.0,
    ) -> tuple[str | None, str | None, str | None]:
        """Run deployment with exponential backoff retry."""
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                return await self._deploy_once(
                    strategy=strategy,
                    charter=charter,
                    market_context=market_context,
                    model=model,
                )
            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                error_type, error_msg = _classify_error(e)
                print(f"\n{'='*80}")
                print(f"[ERROR:ComposerDeployer] Attempt {attempt}/{max_attempts} failed")
                print(f"[ERROR:ComposerDeployer] Exception: {type(e).__name__}: {e}")
                print(f"[ERROR:ComposerDeployer] Classified as: {error_type}")
                print(f"{'='*80}\n")

                is_rate_limit = "rate" in error_str or "429" in error_str

                if attempt < max_attempts:
                    wait_time = base_delay * (2 ** (attempt - 1)) if is_rate_limit else base_delay
                    print(f"⚠️  Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                    continue

                raise

        if last_error:
            raise last_error

        raise RuntimeError("Deployment failed without raising an error")

    async def _deploy_once(
        self,
        strategy: Strategy,
        charter: Charter,
        market_context: dict,
        model: str,
    ) -> tuple[str | None, str | None, str | None]:
        """Single deployment attempt."""
        debug = os.getenv("DEBUG_PROMPTS", "0") == "1"

        # Step 1: Get LLM confirmation and description (no tool calling)
        confirmation = await self._get_llm_confirmation(
            strategy=strategy,
            charter=charter,
            market_context=market_context,
            model=model,
        )

        if not isinstance(confirmation, SymphonyConfirmation):
            symphony_id, description = self._extract_symphony_data(confirmation)
            if symphony_id:
                deployed_at = datetime.now(timezone.utc).isoformat()
                print(f"✅ Symphony deployed: {symphony_id}")
                return symphony_id, deployed_at, description
            print("❌ Failed to parse LLM deployment response")
            return None, None, None

        if not confirmation.ready_to_deploy:
            print("⚠️  LLM declined to deploy strategy")
            return None, None, None

        # Step 2: Build symphony JSON in Python (no LLM hallucination)
        symphony_json = _build_symphony_json(
            name=confirmation.symphony_name,
            description=confirmation.symphony_description,
            tickers=strategy.assets,
            rebalance=strategy.rebalance_frequency.value,
            logic_tree=strategy.logic_tree,  # Pass conditional logic if present
        )

        if debug:
            print(f"\n[DEBUG:ComposerDeployer] Built symphony JSON:")
            print(json.dumps(symphony_json, indent=2, default=str))

        # Step 3: Call Composer API directly
        print(f"📤 Deploying symphony: {confirmation.symphony_name}")
        response = await _call_composer_api(symphony_json)

        # Step 4: Extract symphony_id from response
        symphony_id = self._extract_symphony_id(response)

        if symphony_id:
            deployed_at = datetime.now(timezone.utc).isoformat()
            print(f"✅ Symphony deployed: {symphony_id}")
            return symphony_id, deployed_at, confirmation.symphony_description
        else:
            print(f"❌ Failed to extract symphony_id from response")
            if debug:
                print(f"[DEBUG] Response: {response}")
            return None, None, None

    async def _get_llm_confirmation(
        self,
        strategy: Strategy,
        charter: Charter,
        market_context: dict | None,
        model: str,
    ) -> SymphonyConfirmation:
        """Get LLM confirmation for deployment (no tool calling)."""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_deployment_prompt(strategy, charter, market_context)

        model_settings = get_model_settings(model, stage="composer_deployment")

        # Create agent WITHOUT Composer tools - just structured output
        agent_ctx = await create_agent(
            model=model,
            output_type=SymphonyConfirmation,
            system_prompt=system_prompt,
            include_fred=False,
            include_yfinance=False,
            include_composer=False,  # No tools!
            history_limit=5,
            model_settings=model_settings,
        )

        async with agent_ctx as agent:
            result = await agent.run(user_prompt)
            return result.output

    def _build_system_prompt(self) -> str:
        """Load the Composer deployment system prompt."""
        return load_prompt("system/composer_deployment_system.md", include_tools=False)

    def _build_deployment_prompt(
        self,
        strategy: Strategy,
        charter: Charter,
        market_context: dict | None = None,
    ) -> str:
        """Build deployment prompt with a concise strategy summary."""
        logic_tree_summary = json.dumps(strategy.logic_tree, indent=2) if strategy.logic_tree else "{}"

        return (
            "Provide a symphony name and 1-2 sentence description only. "
            "Do NOT re-evaluate, critique, or decline; assume approval is final.\n\n"
            "Strategy summary (for naming/description only):\n"
            f"- Candidate name: {strategy.name}\n"
            f"- Assets: {', '.join(strategy.assets)}\n"
            f"- Weights: {strategy.weights}\n"
            f"- Rebalance: {strategy.rebalance_frequency.value}\n"
            f"- Logic Tree: {logic_tree_summary}\n\n"
            "Return the structured SymphonyConfirmation output."
        )

    def _extract_symphony_data(self, result) -> tuple[Optional[str], Optional[str]]:
        """Extract symphony_id and description from agent output or raw response."""
        raw = None
        if hasattr(result, "output"):
            raw = result.output
        elif hasattr(result, "data"):
            raw = result.data
        else:
            raw = result

        if isinstance(raw, dict):
            symphony_id = raw.get("symphony_id")
            description = raw.get("description") or raw.get("symphony_description")
            if symphony_id:
                return symphony_id, description
            raw_str = json.dumps(raw)
        else:
            raw_str = str(raw) if raw is not None else ""

        if not raw_str:
            return None, None

        patterns = [
            r'"symphony_id"\s*:\s*"([^"]+)"',
            r"'symphony_id'\s*:\s*'([^']+)'",
            r"symphony_id\s*[:=]\s*([A-Za-z0-9_-]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, raw_str)
            if match:
                return match.group(1), None

        generic_match = re.search(r"\bid\s*=\s*([A-Za-z0-9_-]{10,})", raw_str)
        if generic_match:
            return generic_match.group(1), None

        return None, None

    def _extract_symphony_id(self, response: dict) -> Optional[str]:
        """Extract symphony_id from MCP response."""
        # MCP response format: {"jsonrpc": "2.0", "id": "...", "result": {...}}
        result = response.get("result", {})

        # Handle different response structures
        if isinstance(result, dict):
            # Direct symphony_id in result
            if "symphony_id" in result:
                return result["symphony_id"]

            # Nested in content array (MCP tool response format)
            content = result.get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        text = item.get("text", "")
                        if isinstance(text, str) and "symphony_id" in text:
                            # Try to parse as JSON
                            try:
                                parsed = json.loads(text)
                                if "symphony_id" in parsed:
                                    return parsed["symphony_id"]
                            except json.JSONDecodeError:
                                pass

        # Fallback: search for symphony_id pattern in full response
        import re
        response_str = json.dumps(response)
        match = re.search(r'"symphony_id"\s*:\s*"([^"]+)"', response_str)
        if match:
            return match.group(1)

        return None
