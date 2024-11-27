"""
Basic chat example using StreamlitChat.
"""
import streamlit as st
from streamlitchat.chat_interface import ChatInterface
from streamlitchat.ui import ChatUI
import os
from dotenv import load_dotenv
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Main application entry point."""
    try:
        # Set page config
        st.set_page_config(
            page_title="StreamlitChat Basic Example",
            page_icon="💬",
            layout="wide"
        )
        
        # Initialize chat interface
        chat_interface = ChatInterface(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model_name="gpt-3.5-turbo"
        )
        
        # Create and render UI
        ui = ChatUI(chat_interface)
        st.title("StreamlitChat Basic Example")
        
        # This will be called by Streamlit's async runtime
        st.write("Chat interface ready!")
        
    except Exception as e:
        logger.error(f"Error in main app: {e}", exc_info=True)
        st.error(f"Application error: {str(e)}")

if __name__ == "__main__":
    main() 