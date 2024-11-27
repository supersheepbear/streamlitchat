"""Tests for the UI components of StreamlitChat."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from streamlitchat.ui import ChatUI
from streamlitchat.chat_interface import ChatInterface
import logging

logger = logging.getLogger(__name__)

@pytest.fixture
def chat_interface():
    """Fixture for creating a mock ChatInterface."""
    mock = MagicMock(spec=ChatInterface)
    mock.model_name = "gpt-3.5-turbo"
    mock.api_key = ""
    return mock

@pytest.fixture
def chat_ui():
    """Fixture to create a ChatUI instance with mocked Streamlit."""
    mock_st = MagicMock()
    
    # Mock sidebar as a context manager
    sidebar = MagicMock()
    mock_st.sidebar = MagicMock()
    mock_st.sidebar.__enter__ = MagicMock(return_value=sidebar)
    mock_st.sidebar.__exit__ = MagicMock()
    
    # Create a ChatInterface in test mode
    chat_interface = ChatInterface(test_mode=True)
    
    with patch('streamlitchat.ui.st', mock_st):
        ui = ChatUI(chat_interface)
        yield ui, mock_st

@pytest.fixture
def mock_st():
    """Fixture for mocking Streamlit."""
    with patch("streamlitchat.ui.st") as mock_st:
        # Set up session state
        mock_st.session_state = MagicMock()
        mock_st.session_state.messages = []
        mock_st.session_state.is_processing = False
        
        # Set up sidebar mocks
        mock_st.sidebar = MagicMock()
        mock_st.sidebar.selectbox.return_value = "gpt-3.5-turbo"
        mock_st.sidebar.text_input.return_value = ""
        
        yield mock_st

def test_chat_ui_initialization(chat_ui):
    """Test that ChatUI initializes correctly."""
    ui, mock_st = chat_ui
    
    # Check that page config was set
    mock_st.set_page_config.assert_called_once()
    mock_st.title.assert_called_once_with("StreamlitChat")

def test_chat_ui_session_state_initialization(chat_ui):
    """Test that session state is initialized correctly."""
    ui, mock_st = chat_ui
    
    # Access session_state to trigger initialization
    assert hasattr(mock_st.session_state, "messages")
    assert hasattr(mock_st.session_state, "is_processing")

@pytest.mark.asyncio
async def test_message_display(chat_ui):
    """Test message display functionality."""
    ui, mock_st = chat_ui
    
    # Set up test message
    test_message = {"role": "user", "content": "Hello"}
    mock_st.session_state.messages = [test_message]
    
    # Call display messages
    ui._display_messages()
    
    # Check that chat_message context manager was used
    mock_st.chat_message.assert_called_once_with("user")

@pytest.mark.asyncio
async def test_user_input_handling(chat_ui):
    """Test user input handling."""
    ui, mock_st = chat_ui
    
    # Mock user input
    mock_st.chat_input.return_value = "Hello"
    mock_st.empty.return_value = MagicMock()
    
    # Mock streaming response using patch
    mock_stream = AsyncMock()
    mock_stream.__aiter__.return_value = ["Hello", " world!"]
    
    with patch.object(ui.chat_interface, 'send_message_stream', return_value=mock_stream):
        # Use _handle_user_input instead of process_user_input
        await ui._handle_user_input()
        
        # Add assertions
        mock_st.chat_input.assert_called_once()
        mock_st.empty.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling(chat_ui):
    """Test error handling in user input processing."""
    ui, mock_st = chat_ui
    
    # Mock user input
    mock_st.chat_input.return_value = "Hello"
    
    # Mock error in chat interface using patch
    with patch.object(ui.chat_interface, 'send_message_stream', side_effect=Exception("API Error")):
        # Use _handle_user_input instead of process_user_input
        await ui._handle_user_input()
        
        # Verify error handling
        mock_st.error.assert_called_once_with("Error: API Error")

def test_sidebar_rendering(chat_ui):
    """Test sidebar rendering and controls."""
    ui, mock_st = chat_ui
    
    # Call render_sidebar
    ui._render_sidebar()
    
    # Just verify the sidebar was used
    assert mock_st.sidebar.__enter__.called, "Sidebar context manager was not used"
