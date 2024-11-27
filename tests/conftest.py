"""Pytest configuration and shared fixtures."""
import pytest
import logging

@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for tests."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "ui: mark test as ui test"
    )
