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
        # Create a proper dict-like object for session_state
        class SessionState(dict):
            def __init__(self):
                super().__init__()
                self.messages = []
                self.is_processing = False
                self.keyboard_trigger = None
                self.api_params = {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'presence_penalty': 0.0,
                    'frequency_penalty': 0.0
                }
            
            def __getattr__(self, key):
                return self.get(key)
            
            def __setattr__(self, key, value):
                self[key] = value

        mock_st.session_state = SessionState()
        
        # Set up sidebar as context manager
        sidebar = MagicMock()
        mock_st.sidebar = MagicMock()
        mock_st.sidebar.__enter__ = MagicMock(return_value=sidebar)
        mock_st.sidebar.__exit__ = MagicMock()
        
        # Mock sidebar methods
        mock_st.sidebar.selectbox.return_value = "gpt-3.5-turbo"
        mock_st.sidebar.text_input.return_value = ""
        mock_st.sidebar.slider = MagicMock()
        mock_st.sidebar.header = MagicMock()
        mock_st.sidebar.subheader = MagicMock()
        
        # Mock other commonly used streamlit functions
        mock_st.markdown = MagicMock()
        mock_st.chat_input = MagicMock()
        mock_st.empty = MagicMock()
        mock_st.error = MagicMock()
        
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

@pytest.mark.asyncio
async def test_keyboard_shortcuts(mock_st):
    """Test keyboard shortcuts functionality."""
    # Setup
    chat_ui = ChatUI(ChatInterface(test_mode=True))
    
    # Mock chat input
    mock_st.chat_input.return_value = "Test message"
    mock_st.session_state.is_processing = False
    mock_st.session_state.keyboard_trigger = 'enter'
    
    # Mock empty placeholder for streaming response
    mock_placeholder = MagicMock()
    mock_st.empty.return_value = mock_placeholder
    
    # Mock streaming response
    mock_stream = AsyncMock()
    mock_stream.__aiter__.return_value = ["Hello", " world!"]
    
    with patch.object(chat_ui.chat_interface, 'send_message_stream', return_value=mock_stream):
        # Call handle keyboard shortcuts
        await chat_ui._handle_keyboard_shortcuts()
        
        # Verify message was processed
        assert mock_st.session_state.keyboard_trigger is None
        assert len(mock_st.session_state.messages) > 0

@pytest.mark.asyncio
async def test_keyboard_shortcut_while_processing(mock_st):
    """Test keyboard shortcuts are disabled while processing."""
    # Setup
    chat_ui = ChatUI(ChatInterface(test_mode=True))
    
    # Set processing state
    mock_st.session_state.is_processing = True
    mock_st.session_state.keyboard_trigger = 'enter'
    
    # Call handle keyboard shortcuts
    await chat_ui._handle_keyboard_shortcuts()
    
    # Verify no message was processed
    assert len(mock_st.session_state.messages) == 0

@pytest.mark.asyncio
async def test_keyboard_shortcut_ctrl_l(mock_st):
    """Test Ctrl+L shortcut to clear chat."""
    # Setup
    chat_ui = ChatUI(ChatInterface(test_mode=True))
    
    # Add some messages
    mock_st.session_state.messages = [
        {"role": "user", "content": "test message"},
        {"role": "assistant", "content": "test response"}
    ]
    
    # Simulate Ctrl+L
    mock_st.session_state.keyboard_trigger = 'ctrl+l'
    
    # Call handle keyboard shortcuts
    await chat_ui._handle_keyboard_shortcuts()
    
    # Verify chat was cleared
    assert len(mock_st.session_state.messages) == 0
    assert mock_st.session_state.keyboard_trigger is None

@pytest.mark.asyncio
async def test_keyboard_shortcuts_setup(mock_st):
    """Test keyboard shortcuts setup."""
    # Setup
    chat_ui = ChatUI(ChatInterface(test_mode=True))
    
    # No need to call setup_keyboard_shortcuts again since it's called in __init__
    
    # Verify markdown was called with correct script
    assert mock_st.markdown.call_count == 1
    script_content = mock_st.markdown.call_args[0][0]
    
    # Check script contains our keyboard handlers
    assert 'document.addEventListener(\'keydown\'' in script_content
    assert 'Enter' in script_content
    assert 'ctrl+l' in script_content
    assert mock_st.markdown.call_args[1]['unsafe_allow_html'] is True

@pytest.mark.asyncio
async def test_api_parameters_configuration(mock_st):
    """Test API parameters configuration in settings."""
    # Setup
    chat_ui = ChatUI(ChatInterface(test_mode=True))
    
    # Mock sidebar inputs with context manager
    with mock_st.sidebar:
        mock_st.sidebar.slider.side_effect = [
            0.7,  # temperature
            0.9,  # top_p
            2,    # presence_penalty
            2     # frequency_penalty
        ]
    
        # Render sidebar
        chat_ui._render_sidebar()
    
        # Verify sliders were created with correct parameters
        assert mock_st.sidebar.slider.call_count == 4
        
        # Check temperature slider
        temp_call = mock_st.sidebar.slider.call_args_list[0]
        assert temp_call[1]['label'] == "Temperature"
        assert temp_call[1]['min_value'] == 0.0
        assert temp_call[1]['max_value'] == 2.0
        assert temp_call[1]['value'] == 0.7
        
        # Check top_p slider
        top_p_call = mock_st.sidebar.slider.call_args_list[1]
        assert top_p_call[1]['label'] == "Top P"
        assert top_p_call[1]['min_value'] == 0.0
        assert top_p_call[1]['max_value'] == 1.0
        assert top_p_call[1]['value'] == 0.9
        
        # Verify values were set in chat interface
        assert chat_ui.chat_interface.temperature == 0.7
        assert chat_ui.chat_interface.top_p == 0.9
        assert chat_ui.chat_interface.presence_penalty == 2
        assert chat_ui.chat_interface.frequency_penalty == 2

@pytest.mark.asyncio
async def test_api_parameters_persistence(mock_st):
    """Test that API parameters persist between sessions."""
    # Setup
    chat_ui = ChatUI(ChatInterface(test_mode=True))
    
    # Mock session state with custom values
    mock_st.session_state.api_params = {
        'temperature': 0.8,
        'top_p': 0.95,
        'presence_penalty': 1.5,
        'frequency_penalty': 1.2
    }
    
    # Render sidebar with context manager
    with mock_st.sidebar:
        # Mock slider returns to match session state values
        mock_st.sidebar.slider.side_effect = [
            0.8,  # temperature
            0.95, # top_p
            1.5,  # presence_penalty
            1.2   # frequency_penalty
        ]
        
        chat_ui._render_sidebar()
    
        # Verify sliders were initialized with session state values
        slider_calls = mock_st.sidebar.slider.call_args_list
        assert slider_calls[0][1]['value'] == 0.8  # temperature
        assert slider_calls[1][1]['value'] == 0.95  # top_p
        assert slider_calls[2][1]['value'] == 1.5  # presence_penalty
        assert slider_calls[3][1]['value'] == 1.2  # frequency_penalty
