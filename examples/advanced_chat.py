"""
Advanced chat example with custom configuration.
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
            page_title="StreamlitChat Advanced Example",
            page_icon="💬",
            layout="wide"
        )
        
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
        
        # Create and render UI
        ui = ChatUI(chat_interface)
        st.title("StreamlitChat Advanced Example")
        
        # This will be called by Streamlit's async runtime
        st.write("Chat interface ready!")
        
    except Exception as e:
        logger.error(f"Error in main app: {e}", exc_info=True)
        st.error(f"Application error: {str(e)}")

if __name__ == "__main__":
    main() 