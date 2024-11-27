"""Pytest configuration and shared fixtures."""
import pytest
import logging
from unittest.mock import patch, MagicMock
from streamlitchat.ui import ChatUI
from streamlitchat.chat_interface import ChatInterface

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

@pytest.fixture
def chat_ui():
    """Fixture for testing ChatUI with mocked Streamlit."""
    with patch("streamlit.chat_message") as mock_chat_message:
        with patch("streamlit.markdown") as mock_markdown:
            mock_context = MagicMock()
            mock_context.markdown = mock_markdown
            mock_chat_message.return_value.__enter__.return_value = mock_context
            
            mock_st = MagicMock()
            mock_st.chat_message = mock_chat_message
            mock_st.markdown = mock_markdown
            
            chat_ui = ChatUI(ChatInterface(test_mode=True), test_mode=True)
            yield chat_ui, mock_st
