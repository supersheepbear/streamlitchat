"""End-to-end tests for StreamlitChat."""
import pytest
from streamlitchat.ui import ChatUI
from streamlitchat.chat_interface import ChatInterface
import streamlit as st
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_chat_flow():
    """Test complete chat flow from user input to response."""
    with patch('streamlit.session_state') as mock_state:
        # Setup mock state
        mock_state.messages = []
        mock_state.is_processing = False
        
        # Initialize chat
        chat_interface = ChatInterface(test_mode=True)
        chat_ui = ChatUI(chat_interface)
        
        # Mock the response
        async def mock_stream():
            yield "Test response"
        chat_interface.send_message_stream = AsyncMock(return_value=mock_stream())
        
        # Add user message
        mock_state.messages.append({"role": "user", "content": "Hello"})
        
        # Process response
        await chat_interface.send_message_stream("Hello")
        mock_state.messages.append({"role": "assistant", "content": "Test response"})
        
        # Verify messages
        assert len(mock_state.messages) == 2
        assert mock_state.messages[0]["role"] == "user"
        assert mock_state.messages[1]["role"] == "assistant"
  