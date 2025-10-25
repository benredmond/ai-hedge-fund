"""
AI Agent module for trading strategy creation.

This module provides:
- Pydantic models for Strategy and Charter outputs
- MCP server configuration and lifecycle management
- Multi-provider agent factory (Claude, GPT-4, Gemini)
"""

from src.agent.models import Strategy, Charter, RebalanceFrequency
from src.agent.strategy_creator import (
    create_agent,
    load_prompt
)
from src.agent.mcp_config import get_mcp_servers

__all__ = [
    # Models
    "Strategy",
    "Charter",
    "RebalanceFrequency",
    # Agent factory
    "create_agent",
    # Utilities
    "load_prompt",
    "get_mcp_servers"
]
