"""Tests for the StreamlitChat interface components."""
import pytest
from streamlitchat.chat_interface import ChatInterface

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
