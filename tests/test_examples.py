"""Tests for example applications."""
import pytest
from streamlit.testing.v1 import AppTest
import os
import sys
from pathlib import Path

# Add src directory to Python path for testing
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

@pytest.fixture
def basic_chat_test():
    """Fixture for testing basic chat example."""
    os.environ['STREAMLIT_TEST_MODE'] = 'true'
    app = AppTest.from_file("examples/basic_chat.py")
    app.run()
    yield app
    os.environ.pop('STREAMLIT_TEST_MODE', None)

def test_basic_chat_initialization(basic_chat_test):
    """Test basic chat example initialization."""
    # Verify title
    assert len(basic_chat_test.title) > 0
    assert "StreamlitChat Basic Example" in basic_chat_test.title[0].value
    
    # Verify chat interface is ready
    assert any("Chat interface ready!" in element.value 
              for element in basic_chat_test.markdown)
    
    # Verify chat input exists
    assert len(basic_chat_test.chat_input) > 0

def test_basic_chat_interaction(basic_chat_test):
    """Test basic chat interaction."""
    # Send a test message
    basic_chat_test.chat_input[0].set_value("Hello")
    basic_chat_test.chat_input[0].run()
    
    # Verify message appears in session state
    assert "messages" in basic_chat_test.session_state
    messages = basic_chat_test.session_state["messages"]
    assert len(messages) > 0
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello" 