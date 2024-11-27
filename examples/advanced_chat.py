"""
Advanced chat example with custom configuration.
"""
import streamlit as st
from streamlitchat.chat_interface import ChatInterface
from streamlitchat.ui import ChatUI
import os
from dotenv import load_dotenv
import logging
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

# Set page config first, before any other Streamlit commands
st.set_page_config(
    page_title="StreamlitChat Advanced Example",
    page_icon="💬",
    layout="wide"
)

# Load environment variables
load_dotenv()

async def main():
    """Main application entry point."""
    try:
        # Initialize chat interface with custom settings
        chat_interface = ChatInterface(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model_name="gpt-4",
            temperature=0.7,
            top_p=0.9,
            presence_penalty=0.0,
            frequency_penalty=0.0,
            api_base=None
        )
        
        # Create UI instance
        ui = ChatUI(chat_interface)
        
        # Display title
        st.title("StreamlitChat Advanced Example")
        
        # Render the chat interface
        ui.render_sidebar()  # Show settings sidebar
        ui.display_messages()  # Show message history
        await ui.handle_user_input()  # Show chat input
        
    except Exception as e:
        logger.error(f"Error in main app: {e}", exc_info=True)
        st.error(f"Application error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 