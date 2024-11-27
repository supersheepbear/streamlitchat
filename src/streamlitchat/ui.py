"""Streamlit UI components for the chat interface.

This module contains the Streamlit-based user interface components for the chat application.
It handles the layout, message display, input fields, and other UI elements.
"""

import streamlit as st
from typing import Optional, List, Dict, Any, Set
from .chat_interface import ChatInterface
import logging

# Add logger
logger = logging.getLogger(__name__)

class ChatUI:
    """Main UI class for the Streamlit chat interface."""

    def __init__(self, chat_interface: Optional[ChatInterface] = None, test_mode: bool = False) -> None:
        """Initialize the ChatUI.

        Args:
            chat_interface: Optional ChatInterface instance. If not provided,
                          a new instance will be created.
            test_mode: If True, enables test mode which skips actual UI rendering.
        """
        self.chat_interface = chat_interface or ChatInterface()
        self.test_mode = test_mode
        self._initialize_session_state()
        if not test_mode:
            self._setup_page()
            self._setup_keyboard_shortcuts()

    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state variables."""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "is_processing" not in st.session_state:
            st.session_state.is_processing = False
        if "keyboard_trigger" not in st.session_state:
            st.session_state.keyboard_trigger = None
        if "settings" not in st.session_state:
            st.session_state.settings = {
                'model': 'gpt-3.5-turbo',
                'api_params': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'presence_penalty': 0.0,
                    'frequency_penalty': 0.0
                },
                'theme': 'light'
            }
        
        # Load any persisted settings
        self._load_settings()

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

    def _render_sidebar(self) -> Dict[str, Any]:
        """Render the sidebar with settings and controls.
        
        Returns:
            Dict[str, Any]: Current settings values (useful for testing)
        """
        settings = {
            'temperature': st.session_state.settings['api_params']['temperature'],
            'top_p': st.session_state.settings['api_params']['top_p'],
            'presence_penalty': st.session_state.settings['api_params']['presence_penalty'],
            'frequency_penalty': st.session_state.settings['api_params']['frequency_penalty']
        }
        
        # Update chat interface with current settings
        self.chat_interface.temperature = settings['temperature']
        self.chat_interface.top_p = settings['top_p']
        self.chat_interface.presence_penalty = settings['presence_penalty']
        self.chat_interface.frequency_penalty = settings['frequency_penalty']

        # Always render sliders but skip other UI elements in test mode
        with st.sidebar:
            # API Parameters
            st.subheader("API Parameters")
            
            # Temperature
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=settings['temperature'],
                help="Controls randomness in responses"
            )
            self.chat_interface.temperature = temperature
            settings['temperature'] = temperature
            
            # Top P
            top_p = st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=settings['top_p'],
                help="Controls diversity via nucleus sampling"
            )
            self.chat_interface.top_p = top_p
            settings['top_p'] = top_p

            if not self.test_mode:
                # Rest of the sidebar UI...
                pass

        return settings

    def _setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts using Streamlit components."""
        st.markdown("""
            <script>
                document.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        window.streamlitKeyboardTrigger('enter');
                    }
                    if (e.key === 'l' && e.ctrlKey) {
                        e.preventDefault();
                        window.streamlitKeyboardTrigger('ctrl+l');
                    }
                });
            </script>
        """, unsafe_allow_html=True)

    async def _handle_keyboard_shortcuts(self) -> None:
        """Handle keyboard shortcut events."""
        if st.session_state.keyboard_trigger == 'enter' and not st.session_state.is_processing:
            await self._handle_user_input()
            logger.debug("Enter key pressed - handling message input")
        elif st.session_state.keyboard_trigger == 'ctrl+l':
            self.chat_interface.clear_history()
            st.session_state.messages = []
            logger.info("Chat cleared via Ctrl+L shortcut")
        
        # Reset keyboard trigger
        st.session_state.keyboard_trigger = None

    async def render(self) -> None:
        """Render the complete chat interface."""
        settings = self._render_sidebar()
        self._display_messages()
        await self._handle_keyboard_shortcuts()
        await self._handle_user_input()

    def _save_settings(self) -> None:
        """Save current settings to persistent storage."""
        # Get current settings from chat interface
        current_settings = {
            'model': self.chat_interface.model_name,
            'api_params': {
                'temperature': self.chat_interface.temperature,
                'top_p': self.chat_interface.top_p,
                'presence_penalty': self.chat_interface.presence_penalty,
                'frequency_penalty': self.chat_interface.frequency_penalty
            },
            'theme': st.session_state.settings.get('theme', 'light')
        }
        
        # Update session state
        st.session_state.settings = current_settings
        
        # Save to URL parameters for persistence
        st.experimental_set_query_params(settings=current_settings)
        logger.info("Settings saved to persistent storage")

    def _load_settings(self) -> None:
        """Load settings from persistent storage."""
        # Try to load settings from URL parameters
        params = st.experimental_get_query_params()
        stored_settings = params.get('settings', None)
        
        if stored_settings:
            try:
                # Update chat interface with stored settings
                self.chat_interface.model_name = stored_settings['model']
                api_params = stored_settings['api_params']
                self.chat_interface.temperature = api_params['temperature']
                self.chat_interface.top_p = api_params['top_p']
                self.chat_interface.presence_penalty = api_params['presence_penalty']
                self.chat_interface.frequency_penalty = api_params['frequency_penalty']
                
                # Update session state
                st.session_state.settings = stored_settings
                logger.info("Settings loaded from persistent storage")
            except (KeyError, TypeError) as e:
                logger.warning(f"Error loading settings: {e}. Using defaults.")
                self._initialize_default_settings()
        else:
            logger.info("No stored settings found, using defaults")
            self._initialize_default_settings()

    def _initialize_default_settings(self) -> None:
        """Initialize default settings."""
        default_settings = {
            'model': 'gpt-3.5-turbo',
            'api_params': {
                'temperature': 0.7,
                'top_p': 0.9,
                'presence_penalty': 0.0,
                'frequency_penalty': 0.0
            },
            'theme': 'light'
        }
        
        # Update chat interface
        self.chat_interface.model_name = default_settings['model']
        self.chat_interface.temperature = default_settings['api_params']['temperature']
        self.chat_interface.top_p = default_settings['api_params']['top_p']
        self.chat_interface.presence_penalty = default_settings['api_params']['presence_penalty']
        self.chat_interface.frequency_penalty = default_settings['api_params']['frequency_penalty']
        
        # Update session state
        st.session_state['settings'] = default_settings
