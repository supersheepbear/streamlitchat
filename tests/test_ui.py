"""Tests for the UI components of StreamlitChat."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from streamlitchat.ui import ChatUI
from streamlitchat.chat_interface import ChatInterface
import streamlit as st
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
def mock_st(mocker):
    """Fixture to mock Streamlit components."""
    # Patch streamlit where it's imported in the UI module
    mock_st = mocker.patch('streamlitchat.ui.st', autospec=True)
    
    # Create a session state mock with dict-like behavior
    session_state = MagicMock()
    session_state.__getitem__ = lambda self, key: getattr(self, key, None)
    session_state.__setitem__ = lambda self, key, value: setattr(self, key, value)
    session_state.settings = {
        'model': 'gpt-3.5-turbo',
        'api_params': {
            'temperature': 0.7,
            'top_p': 0.9,
            'presence_penalty': 0.0,
            'frequency_penalty': 0.0
        },
        'theme': 'light'
    }
    mock_st.session_state = session_state
    
    # Mock sidebar with context manager behavior
    sidebar = MagicMock()
    
    # Configure slider to return the value from session state
    def slider_mock(*args, **kwargs):
        if 'Temperature' in args:
            return session_state.settings['api_params']['temperature']
        elif 'Top P' in args:
            return session_state.settings['api_params']['top_p']
        return kwargs.get('value')
        
    sidebar.slider = MagicMock(side_effect=slider_mock)
    mock_st.sidebar = MagicMock()
    mock_st.sidebar.__enter__ = MagicMock(return_value=sidebar)
    mock_st.sidebar.__exit__ = MagicMock()
    
    # Mock other commonly used streamlit functions
    mock_st.experimental_get_query_params = MagicMock(return_value={})
    mock_st.experimental_set_query_params = MagicMock()
    mock_st.markdown = MagicMock()
    mock_st.chat_input = MagicMock()
    mock_st.empty = MagicMock()
    mock_st.error = MagicMock()
    
    return mock_st

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
    
    # Find the keyboard shortcut script among markdown calls
    keyboard_script_found = False
    for call in mock_st.markdown.call_args_list:
        if 'document.addEventListener(\'keydown\'' in call[0][0]:
            keyboard_script_found = True
            assert 'Enter' in call[0][0]
            assert 'ctrl+l' in call[0][0]
            assert call[1]['unsafe_allow_html'] is True
            break
    
    assert keyboard_script_found, "Keyboard shortcut script not found in markdown calls"

@pytest.mark.asyncio
async def test_api_parameters_persistence():
    """Test that API parameters persist between sessions."""
    with patch("streamlit.session_state") as mock_state:
        # Setup mock state
        mock_state.settings = {
            'model': 'gpt-3.5-turbo',
            'api_params': {
                'temperature': 0.7,
                'top_p': 0.9,
                'presence_penalty': 0.0,
                'frequency_penalty': 0.0
            },
            'theme': 'light'
        }
        
        # Setup with test mode
        chat_ui = ChatUI(ChatInterface(test_mode=True), test_mode=True)
        
        # Get settings
        settings = chat_ui._render_sidebar()
        
        # Verify all values
        assert settings['temperature'] == 0.7
        assert settings['top_p'] == 0.9
        assert settings['presence_penalty'] == 0.0
        assert settings['frequency_penalty'] == 0.0

@pytest.mark.asyncio
async def test_settings_persistence_save(mock_st):
    """Test saving settings to persistent storage."""
    # Setup
    chat_interface = ChatInterface(test_mode=True)
    chat_ui = ChatUI(chat_interface)
    
    # Reset the mock to clear initialization calls
    mock_st.experimental_set_query_params.reset_mock()
    
    # Set values in chat interface
    chat_interface.model_name = 'gpt-4'
    chat_interface.temperature = 0.8
    chat_interface.top_p = 0.95
    chat_interface.presence_penalty = 1.5
    chat_interface.frequency_penalty = 1.2
    
    # Set theme in session state
    mock_st.session_state.settings['theme'] = 'light'
    
    # Expected settings
    expected_settings = {
        'model': 'gpt-4',
        'api_params': {
            'temperature': 0.8,
            'top_p': 0.95,
            'presence_penalty': 1.5,
            'frequency_penalty': 1.2
        },
        'theme': 'light'
    }
    
    # Call save settings
    chat_ui._save_settings()
    
    # Verify settings were saved
    mock_st.experimental_set_query_params.assert_called_once_with(settings=expected_settings)

@pytest.mark.asyncio
async def test_settings_persistence_load(mock_st):
    """Test loading settings from persistent storage."""
    # Setup
    chat_ui = ChatUI(ChatInterface(test_mode=True))
    
    # Mock stored settings
    stored_settings = {
        'model': 'gpt-4',
        'api_params': {
            'temperature': 0.8,
            'top_p': 0.95,
            'presence_penalty': 1.5,
            'frequency_penalty': 1.2
        },
        'theme': 'dark'
    }
    
    # Mock query parameters
    mock_st.experimental_get_query_params.return_value = {'settings': stored_settings}
    
    # Call load settings
    chat_ui._load_settings()
    
    # Verify settings were loaded correctly
    assert chat_ui.chat_interface.model_name == stored_settings['model']
    assert chat_ui.chat_interface.temperature == stored_settings['api_params']['temperature']
    assert chat_ui.chat_interface.top_p == stored_settings['api_params']['top_p']
    assert mock_st.session_state.settings == stored_settings

@pytest.mark.asyncio
async def test_settings_persistence_default(mock_st):
    """Test default settings when no stored settings exist."""
    # Setup
    chat_interface = ChatInterface(test_mode=True)
    chat_ui = ChatUI(chat_interface)
    
    # Mock empty query parameters
    mock_st.experimental_get_query_params.return_value = {}
    
    # Call load settings explicitly (bypassing initialization)
    chat_ui._initialize_default_settings()
    
    # Expected default settings
    expected_settings = {
        'model': 'gpt-3.5-turbo',
        'api_params': {
            'temperature': 0.7,
            'top_p': 0.9,
            'presence_penalty': 0.0,
            'frequency_penalty': 0.0
        },
        'theme': 'light'
    }
    
    # Verify default settings
    assert chat_interface.model_name == expected_settings['model']
    assert chat_interface.temperature == expected_settings['api_params']['temperature']
    assert chat_interface.top_p == expected_settings['api_params']['top_p']
    assert chat_interface.presence_penalty == expected_settings['api_params']['presence_penalty']
    assert chat_interface.frequency_penalty == expected_settings['api_params']['frequency_penalty']
    assert mock_st.session_state.settings == expected_settings

@pytest.fixture
def mock_session_state():
    """Fixture for mocking session state."""
    with patch("streamlit.session_state") as mock_state:
        mock_state.settings = {
            'model': 'gpt-3.5-turbo',
            'api_params': {
                'temperature': 0.7,
                'top_p': 0.9,
                'presence_penalty': 0.0,
                'frequency_penalty': 0.0
            },
            'theme': 'light'
        }
        mock_state.messages = []
        mock_state.is_processing = False
        mock_state.keyboard_trigger = None
        yield mock_state

@pytest.mark.asyncio
async def test_temperature_setting():
    """Test temperature setting."""
    with patch("streamlit.session_state") as mock_state:
        # Setup mock state
        mock_state.settings = {
            'model': 'gpt-3.5-turbo',
            'api_params': {
                'temperature': 0.7,
                'top_p': 0.9,
                'presence_penalty': 0.0,
                'frequency_penalty': 0.0
            },
            'theme': 'light'
        }
        
        # Setup with test mode
        chat_ui = ChatUI(ChatInterface(test_mode=True), test_mode=True)
        
        # Get settings
        settings = chat_ui._render_sidebar()
        
        # Verify temperature value
        assert settings['temperature'] == 0.7

@pytest.mark.asyncio
async def test_top_p_setting():
    """Test top_p setting."""
    with patch("streamlit.session_state") as mock_state:
        # Setup mock state
        mock_state.settings = {
            'model': 'gpt-3.5-turbo',
            'api_params': {
                'temperature': 0.7,
                'top_p': 0.9,
                'presence_penalty': 0.0,
                'frequency_penalty': 0.0
            },
            'theme': 'light'
        }
        
        # Setup with test mode
        chat_ui = ChatUI(ChatInterface(test_mode=True), test_mode=True)
        
        # Get settings
        settings = chat_ui._render_sidebar()
        
        # Verify top_p value
        assert settings['top_p'] == 0.9

@pytest.mark.asyncio
async def test_api_parameters_persistence(mock_session_state):
    """Test that API parameters persist between sessions."""
    # Setup with test mode
    chat_ui = ChatUI(ChatInterface(test_mode=True), test_mode=True)
    
    # Set custom values in session state
    mock_session_state.settings['api_params'].update({
        'temperature': 0.8,
        'top_p': 0.95,
        'presence_penalty': 1.5,
        'frequency_penalty': 1.2
    })
    
    # Get settings
    settings = chat_ui._render_sidebar()
    
    # Verify all values
    assert settings['temperature'] == 0.8
    assert settings['top_p'] == 0.95
    assert settings['presence_penalty'] == 1.5
    assert settings['frequency_penalty'] == 1.2
    
    # Verify chat interface was updated
    assert chat_ui.chat_interface.temperature == 0.8
    assert chat_ui.chat_interface.top_p == 0.95
    assert chat_ui.chat_interface.presence_penalty == 1.5
    assert chat_ui.chat_interface.frequency_penalty == 1.2

@pytest.mark.asyncio
async def test_conversation_persistence():
    """Test conversation persistence between sessions."""
    # Setup
    chat_ui = ChatUI(ChatInterface(test_mode=True))
    
    # Mock messages
    test_messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "I'm doing well, thanks!"}
    ]
    
    # Set messages in session state
    st.session_state.messages = test_messages
    
    # Save conversation
    chat_ui._save_conversation()
    
    # Create new UI instance (simulating new session)
    new_chat_ui = ChatUI(ChatInterface(test_mode=True))
    
    # Verify messages were restored
    assert st.session_state.messages == test_messages

@pytest.mark.asyncio
async def test_conversation_persistence_with_max_messages():
    """Test conversation persistence with message limit."""
    chat_ui = ChatUI(ChatInterface(test_mode=True))
    
    # Generate many messages
    test_messages = []
    for i in range(100):  # More than max limit
        test_messages.extend([
            {"role": "user", "content": f"Message {i}"},
            {"role": "assistant", "content": f"Response {i}"}
        ])
    
    st.session_state.messages = test_messages
    # Enforce limit immediately when setting messages
    chat_ui._enforce_message_limit()
    
    # Save conversation
    chat_ui._save_conversation()
    
    # Create new UI instance
    new_chat_ui = ChatUI(ChatInterface(test_mode=True))
    
    # Verify only recent messages were kept
    assert len(st.session_state.messages) <= chat_ui.MAX_STORED_MESSAGES
    assert st.session_state.messages[-1] == test_messages[-1]  # Most recent message preserved

@pytest.mark.asyncio
async def test_theme_customization(mock_st):
    """Test theme customization functionality."""
    # Setup mock session state
    mock_st.session_state.settings = {
        'model': 'gpt-3.5-turbo',
        'api_params': {
            'temperature': 0.7,
            'top_p': 0.9,
            'presence_penalty': 0.0,
            'frequency_penalty': 0.0
        },
        'theme': 'light'
    }
    
    chat_ui = ChatUI(ChatInterface(test_mode=True))
    
    # Test default theme
    assert mock_st.session_state.settings['theme'] == 'light'
    
    # Test theme change
    chat_ui._update_theme('dark')
    assert mock_st.session_state.settings['theme'] == 'dark'
    
    # Mock stored settings for new instance
    stored_settings = {
        'model': 'gpt-3.5-turbo',
        'api_params': {
            'temperature': 0.7,
            'top_p': 0.9,
            'presence_penalty': 0.0,
            'frequency_penalty': 0.0
        },
        'theme': 'dark'
    }
    mock_st.experimental_get_query_params.return_value = {'settings': stored_settings}
    
    # Test theme persistence
    new_chat_ui = ChatUI(ChatInterface(test_mode=True))
    assert mock_st.session_state.settings['theme'] == 'dark'
    
    # Test invalid theme
    with pytest.raises(ValueError):
        chat_ui._update_theme('invalid_theme')

@pytest.mark.asyncio
async def test_theme_affects_styling():
    """Test that theme changes affect UI styling."""
    chat_ui = ChatUI(ChatInterface(test_mode=True))
    
    # Test light theme styles
    light_styles = chat_ui._get_theme_styles('light')
    assert light_styles['background_color'] == '#ffffff'
    assert light_styles['text_color'] == '#000000'
    
    # Test dark theme styles
    dark_styles = chat_ui._get_theme_styles('dark')
    assert dark_styles['background_color'] == '#1E1E1E'
    assert dark_styles['text_color'] == '#ffffff'
