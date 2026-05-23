"""Pytest configuration and shared fixtures for the test suite."""

import sys
import os

import pytest

# Add data_api to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data_api"))


@pytest.fixture(scope="session")
def analyst_token():
    """Generate a valid analyst JWT token for the test session."""
    from app.auth import create_access_token
    return create_access_token(data={"sub": "test_analyst", "role": "analyst"})


@pytest.fixture(scope="session")
def admin_token():
    """Generate a valid admin JWT token for the test session."""
    from app.auth import create_access_token
    return create_access_token(data={"sub": "test_admin", "role": "admin"})
