"""
Runtime schema patching for MCP tools.

This module provides hooks to fix schema issues in MCP tools at runtime,
specifically for Composer.trade where the official schema diverges from
the required API format.
"""

from typing import List, Any
from pydantic_ai.tools import ToolDefinition, RunContext


async def fix_composer_tool_call(
    ctx: RunContext[Any], call_tool_func, name: str, args: dict[str, Any]
) -> Any:
    """
    Intercept Composer tool calls to fix symphony structure before sending.

    LLMs often hallucinate 'children' on Asset nodes even when schema forbids it.
    This hook cleans the symphony_score before it reaches the Composer API.
    """
    if name in ["composer_create_symphony", "composer_save_symphony"]:
        if "symphony_score" in args:
            import os
            debug = os.getenv("DEBUG_PROMPTS", "0") == "1"

            if debug:
                import json
                print(f"\n[DEBUG:fix_composer_tool_call] BEFORE fix:")
                print(json.dumps(args["symphony_score"], indent=2, default=str)[:2000])

            # Fix the symphony structure
            _fix_symphony_node(args["symphony_score"])

            if debug:
                print(f"\n[DEBUG:fix_composer_tool_call] AFTER fix:")
                print(json.dumps(args["symphony_score"], indent=2, default=str)[:2000])

    # Call the actual tool
    return await call_tool_func(name, args, metadata=None)


def _fix_symphony_node(node: dict, parent_children: list = None, index: int = None) -> None:
    """
    Recursively fix symphony nodes.

    - Remove 'children' from Asset nodes (they're leaf nodes)
    - Ensure 'weight' is null
    - Remove invalid nodes (assets missing ticker/exchange)
    - Remove 'empty' step nodes
    """
    if not isinstance(node, dict):
        return

    step = node.get("step", "")

    # Remove 'empty' nodes entirely
    if step == "empty":
        if parent_children is not None and index is not None:
            parent_children[index] = None  # Mark for removal
        return

    # Asset nodes should NOT have children
    if step == "asset":
        # Remove children if present
        node.pop("children", None)
        # Remove is-else-condition? if present
        node.pop("is-else-condition?", None)
        # Ensure weight is null
        node["weight"] = None

        # Check required fields - if missing, mark for removal
        if not node.get("ticker") or not node.get("exchange"):
            if parent_children is not None and index is not None:
                parent_children[index] = None  # Mark for removal
        return

    # For all other nodes, ensure weight is null and recurse into children
    node["weight"] = None

    children = node.get("children", [])
    if isinstance(children, list):
        for i, child in enumerate(children):
            _fix_symphony_node(child, children, i)
        # Remove None entries (marked for removal)
        node["children"] = [c for c in children if c is not None]


async def fix_composer_schema(
    ctx: RunContext, tool_defs: List[ToolDefinition]
) -> List[ToolDefinition]:
    """
    Runtime hook to patch Composer tool schemas.

    Fixes known issues where the MCP schema conflicts with the required Symphony structure:
    1. Forces 'weight' to be null on ALL nodes (removes WeightMap option).
    2. Adds 'allocation' field to Assets.
    3. Removes 'children' and 'is-else-condition?' from Assets.
    """
    import os
    debug = os.getenv("DEBUG_PROMPTS", "0") == "1"

    for tool in tool_defs:
        if tool.name in ["composer_create_symphony", "composer_save_symphony"]:
            if tool.parameters_json_schema:
                if debug:
                    import json
                    print(f"\n[DEBUG:schema_fixes] BEFORE patching {tool.name}:")
                    print(json.dumps(tool.parameters_json_schema, indent=2)[:2000])

                _patch_symphony_schema(tool.parameters_json_schema)

                if debug:
                    print(f"\n[DEBUG:schema_fixes] AFTER patching {tool.name}:")
                    print(json.dumps(tool.parameters_json_schema, indent=2)[:2000])

    return tool_defs


def _patch_symphony_schema(schema: dict) -> None:
    """
    Recursively patch the symphony schema definitions.

    Patches ALL node types to enforce weight: null.
    """
    defs = schema.get("$defs", {})
    if not defs:
        return

    for name, definition in defs.items():
        _patch_any_node(definition)


def _patch_any_node(definition: dict) -> None:
    """Patch any node definition in the schema."""
    if not isinstance(definition, dict):
        return

    props = definition.get("properties", {})
    if not props:
        return

    # FIX 1: Force weight to null on ALL nodes (root, if, if-child, wt-*, asset)
    if "weight" in props:
        props["weight"] = {
            "type": "null",
            "title": "Weight",
            "description": "MUST be null on all nodes. Do NOT use WeightMap.",
        }

    # Detect if this is an Asset node (has ticker + exchange)
    is_asset = "ticker" in props and "exchange" in props

    if is_asset:
        # FIX 2: Add allocation field (missing from schema)
        if "allocation" not in props:
            props["allocation"] = {
                "anyOf": [{"type": "number"}, {"type": "null"}],
                "title": "Allocation",
                "description": "Decimal weight (0.0-1.0). Required if parent is wt-cash-specified.",
                "default": None
            }

        # FIX 3: Remove children and is-else-condition? if present (Asset should be leaf)
        props.pop("children", None)
        props.pop("is-else-condition?", None)

        # FIX 4: Prevent additional properties (stops model from adding children, is-else-condition?, etc.)
        definition["additionalProperties"] = False
