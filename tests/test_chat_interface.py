"""Tests for the StreamlitChat interface components."""
import pytest
from streamlitchat.chat_interface import ChatInterface
import time
from collections import deque

@pytest.fixture
def chat_interface():
    """Create a test ChatInterface instance without OpenAI client."""
    return ChatInterface(test_mode=True)

def test_chat_interface_initialization(chat_interface):
    """Test basic initialization."""
    assert chat_interface.model_name == "gpt-3.5-turbo"
    assert len(chat_interface.messages) == 0

def test_chat_interface_custom_initialization():
    """Test initialization with custom values."""
    custom_model = "gpt-4"
    custom_api_key = "test-key"
    chat = ChatInterface(
        model_name=custom_model, 
        api_key=custom_api_key, 
        test_mode=True
    )
    assert chat.model_name == custom_model
    assert chat.api_key == custom_api_key

def test_chat_history_operations(chat_interface):
    """Test chat history management operations."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"}
    ]
    
    # Test import
    chat_interface.import_history(messages)
    assert chat_interface.messages == messages
    
    # Test export
    exported = chat_interface.export_history()
    assert exported == messages
    
    # Test clear
    chat_interface.clear_history()
    assert len(chat_interface.messages) == 0

def test_validate_api_key():
    """Test API key validation."""
    chat = ChatInterface(test_mode=True)
    
    # Test empty key
    with pytest.raises(ValueError, match="API key cannot be empty"):
        chat.validate_api_key("")
    
    # Test invalid format
    with pytest.raises(ValueError, match="Invalid API key format"):
        chat.validate_api_key("invalid-key")
    
    # Test valid format
    valid_key = "sk-" + "a" * 48
    assert chat.validate_api_key(valid_key) is True

@pytest.mark.asyncio
async def test_api_response_caching():
    """Test that API responses are properly cached."""
    chat = ChatInterface(test_mode=True)
    
    # Test message and context
    message = "Hello"
    context = "Previous conversation"
    
    # Mock cached response
    cached_response = "Cached response"
    cache_key = chat._generate_cache_key(message, context)
    chat.response_cache[cache_key] = cached_response
    
    # Should return cached response without API call
    response = await chat.get_cached_response(message, context)
    assert response == cached_response
    
    # Test cache miss
    new_message = "New message"
    response = await chat.get_cached_response(new_message, context)
    assert response is None

@pytest.mark.asyncio
async def test_api_rate_limiting():
    """Test API rate limiting functionality."""
    chat = ChatInterface(test_mode=True)
    
    # Set rate limit
    chat.requests_per_minute = 60
    chat.request_window = 60  # seconds
    
    # Test within rate limit
    assert chat.can_make_request() is True
    
    # Simulate max requests
    chat.request_timestamps = deque([time.time()] * 60, maxlen=60)
    assert chat.can_make_request() is False
    
    # Test request queue
    await chat.queue_request("Test message")
    assert chat.request_queue.qsize() == 1

@pytest.mark.asyncio
async def test_batch_processing():
    """Test batch processing of API requests."""
    chat = ChatInterface(test_mode=True)
    
    # Add multiple requests
    messages = ["Message 1", "Message 2", "Message 3"]
    for msg in messages:
        await chat.queue_request(msg)
    
    # Process batch
    responses = await chat.process_batch()
    assert len(responses) == len(messages)
    
    # Verify response format
    for i, response in enumerate(responses):
        expected = f"Test response to Message {i+1}"
        assert response == expected
