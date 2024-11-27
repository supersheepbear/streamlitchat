"""Streamlit UI components for the chat interface.

This module contains the Streamlit-based user interface components for the chat application.
It handles the layout, message display, input fields, and other UI elements.
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from .chat_interface import ChatInterface

class ChatUI:
    """Main UI class for the Streamlit chat interface."""

    def __init__(self, chat_interface: Optional[ChatInterface] = None) -> None:
        """Initialize the ChatUI.

        Args:
            chat_interface: Optional ChatInterface instance. If not provided,
                          a new instance will be created.
        """
        self.chat_interface = chat_interface or ChatInterface()
        self._initialize_session_state()
        self._setup_page()

    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state variables."""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "is_processing" not in st.session_state:
            st.session_state.is_processing = False

    def _setup_page(self) -> None:
        """Configure the Streamlit page settings."""
        st.set_page_config(
            page_title="StreamlitChat",
            page_icon="💬",
            layout="wide",
            initial_sidebar_state="auto"
        )
        st.title("StreamlitChat")

    def _display_message(self, message: Dict[str, Any]) -> None:
        """Display a single message in the chat interface.

        Args:
            message: Message dictionary containing 'role' and 'content'.
        """
        role = message["role"]
        content = message["content"]
        
        with st.chat_message(role):
            st.markdown(content)

    def _display_messages(self) -> None:
        """Display all messages in the chat history."""
        for message in st.session_state.messages:
            self._display_message(message)

    async def _handle_user_input(self) -> None:
        """Handle user input and generate AI response."""
        if prompt := st.chat_input("Type your message here..."):
            st.session_state.is_processing = True
            
            # Add user message to chat
            user_message = {"role": "user", "content": prompt}
            st.session_state.messages.append(user_message)
            self._display_message(user_message)

            try:
                # Get AI response with streaming
                response_placeholder = st.empty()
                full_response = ""

                async for chunk in self.chat_interface.send_message_stream(prompt):
                    full_response += chunk
                    # Update response in real-time
                    with st.chat_message("assistant"):
                        response_placeholder.markdown(full_response + "▌")

                # Add final response to chat history
                assistant_message = {"role": "assistant", "content": full_response}
                st.session_state.messages.append(assistant_message)

            except Exception as e:
                st.error(f"Error: {str(e)}")
            
            finally:
                st.session_state.is_processing = False

    def _render_sidebar(self) -> None:
        """Render the sidebar with settings and controls."""
        with st.sidebar:
            st.header("Settings")
            
            # Model selection
            model = st.selectbox(
                "Model",
                ["gpt-3.5-turbo", "gpt-4"],
                index=0
            )
            if model != self.chat_interface.model_name:
                self.chat_interface.model_name = model

            # API Key input
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                value=self.chat_interface.api_key
            )
            if api_key != self.chat_interface.api_key:
                try:
                    self.chat_interface.api_key = api_key
                except ValueError as e:
                    st.error(str(e))

            # Chat controls
            st.header("Chat Controls")
            if st.button("Clear Chat"):
                st.session_state.messages = []
                self.chat_interface.clear_history()
                st.experimental_rerun()

            if st.button("Export Chat"):
                chat_history = self.chat_interface.export_history()
                st.download_button(
                    "Download Chat History",
                    data=str(chat_history),
                    file_name="chat_history.json",
                    mime="application/json"
                )

    async def render(self) -> None:
        """Render the complete chat interface."""
        self._render_sidebar()
        self._display_messages()
        await self._handle_user_input()
