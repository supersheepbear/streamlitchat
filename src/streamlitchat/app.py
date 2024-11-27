"""Main application entry point for StreamlitChat.

This module serves as the entry point for the Streamlit application.
It initializes the chat interface and handles the main application flow.
"""

import asyncio
import streamlit as st
from .ui import ChatUI
from .chat_interface import ChatInterface

async def main() -> None:
    """Main application entry point."""
    # Initialize chat interface with API key from environment
    chat_interface = ChatInterface()
    
    # Create and render UI
    ui = ChatUI(chat_interface)
    await ui.render()

if __name__ == "__main__":
    asyncio.run(main())
