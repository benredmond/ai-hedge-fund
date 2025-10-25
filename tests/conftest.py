"""
Pytest configuration and fixtures.

Loads .env file for all tests to ensure environment variables are available.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


def pytest_configure(config):
    """Load environment variables from .env file before running tests."""
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
