=====
Usage
=====

Basic Usage
----------

To use StreamlitChat in a project, create a Streamlit app file (e.g., ``app.py``)::

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
                page_title="StreamlitChat",
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
            st.title("StreamlitChat")
            
            # This will be called by Streamlit's async runtime
            st.write("Chat interface ready!")
            
        except Exception as e:
            logger.error(f"Error in main app: {e}", exc_info=True)
            st.error(f"Application error: {str(e)}")

    if __name__ == "__main__":
        main()

Configuration
------------

You can customize the chat interface with various parameters::

    chat_interface = ChatInterface(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model_name="gpt-3.5-turbo",
        temperature=0.7,
        top_p=0.9,
        presence_penalty=0.0,
        frequency_penalty=0.0,
        api_base=None  # Optional custom API endpoint
    )

Environment Variables
-------------------

The following environment variables are supported:

- ``OPENAI_API_KEY``: Your OpenAI API key
- ``STREAMLIT_THEME``: UI theme ('light' or 'dark')
- ``LOG_LEVEL``: Logging level (DEBUG, INFO, WARNING, ERROR)

Running the Application
---------------------

To run the application::

    streamlit run app.py

The application will start and open in your default web browser.

Chat History
-----------

StreamlitChat supports saving and loading chat histories::

    # Conversations are automatically saved to the chat_history directory
    # You can manage conversations through the sidebar:
    
    1. Click "💾 Save Current Conversation" to save the current chat
    2. Click on any saved conversation in the list to load it
    
    # Chat histories include:
    - All messages
    - Model settings
    - UI preferences
