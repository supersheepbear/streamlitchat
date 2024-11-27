"""Performance tests for StreamlitChat."""
import pytest
import time
import psutil
import asyncio
from streamlitchat.ui import ChatUI
from streamlitchat.chat_interface import ChatInterface
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.mark.performance
async def test_message_rendering_speed():
    """Test message rendering performance."""
    with patch('streamlit.session_state') as mock_state:
        # Setup test data
        mock_state.messages = [
            {"role": "user" if i % 2 == 0 else "assistant", 
             "content": f"Test message {i}"} 
            for i in range(1000)  # Test with 1000 messages
        ]
        mock_state.is_processing = False
        
        chat_ui = ChatUI(ChatInterface(test_mode=True))
        
        # Measure rendering time
        start_time = time.time()
        chat_ui._render_messages()
        render_time = time.time() - start_time
        
        # Should render within 100ms
        assert render_time < 0.1, f"Message rendering took {render_time:.3f}s"

@pytest.mark.performance
async def test_memory_usage():
    """Test memory usage during chat operations."""
    with patch('streamlit.session_state') as mock_state:
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Setup chat with large history
        mock_state.messages = [
            {"role": "user" if i % 2 == 0 else "assistant", 
             "content": f"Test message {i} " * 100}  # Large messages
            for i in range(100)
        ]
        mock_state.is_processing = False
        
        chat_ui = ChatUI(ChatInterface(test_mode=True))
        
        # Measure memory after operations
        chat_ui._render_messages()
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024, \
            f"Memory increase too high: {memory_increase / 1024 / 1024:.1f}MB"

@pytest.mark.performance
async def test_api_response_time():
    """Test API response time."""
    with patch('streamlit.session_state') as mock_state:
        mock_state.messages = []
        mock_state.is_processing = False
        
        chat_interface = ChatInterface(test_mode=True)
        chat_ui = ChatUI(chat_interface)
        
        # Measure API response time
        start_time = time.time()
        async def mock_stream():
            yield "Test response"
        chat_interface.send_message_stream = AsyncMock(return_value=mock_stream())
        
        await chat_interface.send_message_stream("Test message")
        response_time = time.time() - start_time
        
        # Response should be within 200ms
        assert response_time < 0.2, f"API response took {response_time:.3f}s"

@pytest.mark.performance
async def test_concurrent_requests():
    """Test handling of concurrent requests."""
    with patch('streamlit.session_state') as mock_state:
        mock_state.messages = []
        mock_state.is_processing = False
        
        chat_interface = ChatInterface(test_mode=True)
        chat_ui = ChatUI(chat_interface)
        
        # Setup mock response
        async def mock_stream():
            await asyncio.sleep(0.1)  # Simulate API delay
            yield "Test response"
        chat_interface.send_message_stream = AsyncMock(return_value=mock_stream())
        
        # Send multiple concurrent requests
        start_time = time.time()
        tasks = [
            chat_interface.send_message_stream(f"Message {i}")
            for i in range(5)
        ]
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Should handle requests efficiently
        assert total_time < 0.3, \
            f"Concurrent requests took {total_time:.3f}s" 