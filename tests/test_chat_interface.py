"""Tests for the StreamlitChat interface components."""
from typing import Any, Dict, List, AsyncGenerator
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from streamlitchat.chat_interface import ChatInterface

# Mock response for OpenAI API
class MockResponse:
    def __init__(self, content: str):
        self.choices = [
            AsyncMock(
                message=AsyncMock(content=content),
                delta=AsyncMock(content=content)
            )
        ]

class MockStreamResponse:
    def __init__(self, content: str):
        self.content = content
        self.current_pos = 0
        self.chunk_size = 1
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.current_pos >= len(self.content):
            raise StopAsyncIteration
        
        chunk = self.content[self.current_pos:self.current_pos + self.chunk_size]
        self.current_pos += self.chunk_size
        return MockResponse(chunk)


@pytest.fixture
def chat_interface():
    """Fixture for creating a ChatInterface instance."""
    return ChatInterface(api_key="test-key", test_mode=True)


def test_chat_interface_initialization() -> None:
    """Test that ChatInterface initializes with correct default values."""
    chat = ChatInterface(test_mode=True)
    assert chat.model_name == "gpt-3.5-turbo"
    assert chat.api_key == ""
    assert len(chat.messages) == 0


def test_chat_interface_custom_initialization() -> None:
    """Test that ChatInterface initializes with custom values."""
    custom_model = "gpt-4"
    custom_api_key = "test-key"
    chat = ChatInterface(model_name=custom_model, api_key=custom_api_key, test_mode=True)
    assert chat.model_name == custom_model
    assert chat.api_key == custom_api_key


@pytest.mark.asyncio
async def test_send_message(chat_interface: ChatInterface) -> None:
    """Test sending a message through the chat interface."""
    message = "Hello, how are you?"
    expected_response = "I'm doing well, thank you!"

    # Mock the OpenAI client response
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content=expected_response))]
    
    mock_completions = AsyncMock()
    mock_completions.create = AsyncMock(return_value=mock_response)
    
    mock_chat = MagicMock()
    mock_chat.completions = mock_completions
    
    mock_client = AsyncMock()
    mock_client.chat = mock_chat

    with patch("streamlitchat.chat_interface.AsyncOpenAI", return_value=mock_client):
        response = await chat_interface.send_message(message)
        assert response == expected_response
        assert len(chat_interface.messages) == 2  # User message and assistant response
        assert chat_interface.messages[0]["content"] == message
        assert chat_interface.messages[1]["content"] == expected_response


@pytest.mark.asyncio
async def test_streaming_response(chat_interface: ChatInterface) -> None:
    """Test streaming response from the chat interface."""
    message = "Hello, how are you?"
    expected_chunks = ["I'm", " doing", " well", ", thank", " you!"]

    # Mock streaming response chunks
    async def mock_stream():
        for chunk in expected_chunks:
            yield AsyncMock(choices=[AsyncMock(delta=AsyncMock(content=chunk))])

    mock_completions = AsyncMock()
    mock_completions.create = AsyncMock(return_value=mock_stream())
    
    mock_chat = MagicMock()
    mock_chat.completions = mock_completions
    
    mock_client = AsyncMock()
    mock_client.chat = mock_chat

    with patch("streamlitchat.chat_interface.AsyncOpenAI", return_value=mock_client):
        chunks = []
        async for chunk in chat_interface.send_message_stream(message):
            chunks.append(chunk)
        
        assert chunks == expected_chunks
        assert len(chat_interface.messages) == 2
        assert chat_interface.messages[0]["content"] == message
        assert chat_interface.messages[1]["content"] == "".join(expected_chunks)


def test_clear_chat_history(chat_interface: ChatInterface) -> None:
    """Test clearing chat history."""
    chat_interface.messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    assert len(chat_interface.messages) == 2
    chat_interface.clear_history()
    assert len(chat_interface.messages) == 0


def test_export_chat_history(chat_interface: ChatInterface) -> None:
    """Test exporting chat history."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    chat_interface.messages = messages.copy()
    exported = chat_interface.export_history()
    assert exported == messages


def test_import_chat_history(chat_interface: ChatInterface) -> None:
    """Test importing chat history."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    chat_interface.import_history(messages)
    assert chat_interface.messages == messages


def test_validate_api_key(chat_interface: ChatInterface) -> None:
    """Test API key validation."""
    # Test empty API key
    with pytest.raises(ValueError, match="API key cannot be empty"):
        chat_interface.validate_api_key("")
    
    # Test invalid API key format
    with pytest.raises(ValueError, match="Invalid API key format"):
        chat_interface.validate_api_key("invalid-key-format")
    
    # Test valid API key format (starts with 'sk-' and has sufficient length)
    valid_key = "sk-" + "a" * 48
    assert chat_interface.validate_api_key(valid_key) is True
