"""End-to-end tests for StreamlitChat UI flows."""
import pytest
from streamlit.testing.v1 import AppTest
import streamlit as st
import sys
from pathlib import Path
import asyncio
from unittest.mock import AsyncMock, patch
import logging
import os

# Add src directory to Python path for testing
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from streamlitchat.app import main
from streamlitchat.chat_interface import ChatInterface
from streamlitchat.ui import ChatUI

logger = logging.getLogger(__name__)

@pytest.fixture
async def app_test():
    """Fixture for Streamlit app testing."""
    # Set test mode via environment variable instead of argv
    os.environ['STREAMLIT_TEST_MODE'] = 'true'
    
    app = AppTest.from_file("src/streamlitchat/app.py")
    app.run()
    await asyncio.sleep(0.2)  # Increased wait time for app initialization
    
    yield app
    
    # Clean up
    os.environ.pop('STREAMLIT_TEST_MODE', None)

@pytest.mark.e2e
async def test_complete_chat_flow(app_test):
    """Test complete chat interaction flow from start to finish."""
    # Initialize session state
    app_test.session_state.messages = []
    app_test.session_state.is_processing = False
    
    # Verify initial UI elements
    assert len(app_test.title) > 0, "Title not found"
    assert app_test.title[0].value == "StreamlitChat"
    
    # Wait for chat input to appear
    await asyncio.sleep(0.1)
    assert len(app_test.chat_input) > 0, "Chat input not found"
    
    # Test sending a message
    with patch('streamlitchat.chat_interface.ChatInterface.send_message_stream') as mock_stream:
        # Setup mock response
        async def mock_aiter():
            yield "Hello"
            yield " there!"
        
        mock_stream.return_value = mock_aiter()
        
        # Send message
        app_test.chat_input[0].set_value("Hi")
        app_test.chat_input[0].run()  # Trigger the input
        await asyncio.sleep(0.2)  # Wait for UI update
        
        # Run again to process the response
        app_test._run()
        await asyncio.sleep(0.2)  # Wait for response processing
        
        # Verify message appears in chat
        assert "messages" in app_test.session_state
        messages = app_test.session_state["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hi"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Hello there!"

@pytest.mark.e2e
async def test_settings_interaction(app_test):
    """Test interaction with settings sidebar."""
    # Initialize session state
    app_test.session_state.settings = {
        'api_params': {
            'temperature': 0.7,
            'top_p': 0.9,
            'presence_penalty': 0.0,
            'frequency_penalty': 0.0
        },
        'theme': 'light'
    }
    
    # Wait for sidebar elements to load
    await asyncio.sleep(0.1)
    
    # Verify sidebar elements exist
    assert len(app_test.slider) > 0, "Temperature slider not found"
    assert len(app_test.selectbox) > 0, "Theme selector not found"
    
    # Test temperature slider
    temp_slider = app_test.slider[0]
    assert temp_slider.label == "Temperature"
    temp_slider.set_value(0.8)
    temp_slider.run()  # Trigger the slider
    await asyncio.sleep(0.1)
    assert app_test.session_state["settings"]["api_params"]["temperature"] == 0.8

@pytest.mark.e2e
async def test_error_handling_flow(app_test):
    """Test error handling in UI."""
    # Initialize session state
    app_test.session_state.messages = []
    app_test.session_state.is_processing = False
    
    await asyncio.sleep(0.1)  # Wait for UI to load
    
    # Verify chat input exists
    assert len(app_test.chat_input) > 0, "Chat input not found"
    
    # Test API error
    with patch('streamlitchat.chat_interface.ChatInterface.send_message_stream',
              side_effect=Exception("API Error")):
        app_test.chat_input[0].set_value("Hello")
        app_test.chat_input[0].run()  # Trigger the input
        await asyncio.sleep(0.2)
        
        # Verify error message appears
        assert len(app_test.error) > 0, "Error message not found"
        assert "API Error" in app_test.error[0].value

@pytest.mark.e2e
async def test_keyboard_shortcuts(app_test):
    """Test keyboard shortcuts functionality."""
    # Initialize session state
    app_test.session_state.messages = []
    app_test.session_state.is_processing = False
    app_test.session_state.keyboard_trigger = 'enter'
    
    await asyncio.sleep(0.1)  # Wait for UI to load
    
    # Verify chat input exists
    assert len(app_test.chat_input) > 0, "Chat input not found"
    
    # Test Enter to send
    app_test.chat_input[0].set_value("Test message")
    app_test.chat_input[0].run()  # Trigger the input
    await asyncio.sleep(0.2)
    
    # Verify message was added
    assert len(app_test.session_state.messages) > 0

@pytest.mark.e2e
async def test_message_pagination(app_test):
    """Test message pagination functionality."""
    await asyncio.sleep(0.1)  # Wait for UI to load
    
    # Initialize session state with messages
    app_test.session_state.messages = [
        {"role": "user", "content": f"Message {i}"}
        for i in range(20)
    ]
    app_test.session_state.current_page = 0
    
    # Force UI update
    app_test._run()
    await asyncio.sleep(0.2)  # Wait for messages to render
    
    # Verify pagination buttons exist
    assert len(app_test.button) >= 2, "Pagination buttons not found"
    
    # Test next page button
    app_test.button[1].click()  # Next page button
    app_test.button[1].run()  # Trigger the button
    app_test._run()  # Process the button click
    await asyncio.sleep(0.1)
    assert app_test.session_state.current_page == 1
    
    # Test previous page button
    app_test.button[0].click()  # Previous page button
    app_test.button[0].run()  # Trigger the button
    app_test._run()  # Process the button click
    await asyncio.sleep(0.1)
    assert app_test.session_state.current_page == 0
  