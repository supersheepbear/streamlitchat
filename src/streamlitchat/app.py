"""Main application entry point for StreamlitChat.

This module serves as the entry point for the Streamlit application.
It initializes the chat interface and handles the main application flow.
"""

import asyncio
import streamlit as st
from typing import Optional
import logging
import os
from streamlitchat.ui import ChatUI
from streamlitchat.chat_interface import ChatInterface
from streamlitchat.logging_config import configure_logging, LogConfig, LogContext

logger = logging.getLogger(__name__)

async def main(test_mode: bool = False) -> Optional[ChatUI]:
    """Main application entry point.
    
    Args:
        test_mode: If True, returns the ChatUI instance for testing
        
    Returns:
        ChatUI instance if test_mode is True, None otherwise
    """
    # Check for test mode from environment variable
    test_mode = test_mode or os.getenv('STREAMLIT_TEST_MODE') == 'true'
    
    # Configure logging
    log_config = LogConfig()
    configure_logging(log_config)
    
    try:
        # Set page config first
        st.set_page_config(
            page_title="StreamlitChat",
            page_icon="💬",
            layout="wide"
        )
        
        # Set title
        st.title("StreamlitChat")
        
        # Initialize chat interface with API key from environment
        chat_interface = ChatInterface(test_mode=test_mode)
        
        # Create and render UI
        ui = ChatUI(chat_interface, test_mode=test_mode)
        
        # Generate request ID for this session
        with LogContext():
            logger.info("Starting new chat session")
            await ui.render()
        
        if test_mode:
            return ui
            
    except Exception as e:
        logger.error(f"Error in main app: {e}", exc_info=True)
        st.error(f"Application error: {str(e)}")
        if test_mode:
            raise  # Re-raise in test mode

if __name__ == "__main__":
    asyncio.run(main())
