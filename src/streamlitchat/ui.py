"""Streamlit UI components for the chat interface.

This module contains the Streamlit-based user interface components for the chat application.
It handles the layout, message display, input fields, and other UI elements.
"""

import streamlit as st
from typing import Optional, List, Dict, Any, Set
from .chat_interface import ChatInterface
import logging
import time

# Add logger
logger = logging.getLogger(__name__)

class ChatUI:
    """Main UI class for the Streamlit chat interface."""

    MAX_STORED_MESSAGES = 50  # Maximum number of messages to persist and load between sessions
    VALID_THEMES = {'light', 'dark'}  # Valid theme options
    MESSAGES_PER_PAGE = 10  # Number of messages to display per page
    MESSAGES_PER_VIEW = 20  # Number of messages to render in viewport
    MAX_RECYCLED_COMPONENTS = 30  # Maximum number of recycled message components

    def __init__(self, chat_interface: Optional[ChatInterface] = None, test_mode: bool = False) -> None:
        """Initialize the ChatUI.

        Args:
            chat_interface: Optional ChatInterface instance. If not provided,
                          a new instance will be created.
            test_mode: If True, enables test mode which skips actual UI rendering.
        """
        self.chat_interface = chat_interface or ChatInterface()
        self.test_mode = test_mode
        self.current_page = 0  # Start at first page
        self.scroll_position = 0
        self.recycled_components: Dict[str, Any] = {}
        self._initialize_session_state()
        if not test_mode:
            self._setup_page()
            self._setup_keyboard_shortcuts()
            self._load_conversation()  # Load persisted conversation

    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state variables."""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "is_processing" not in st.session_state:
            st.session_state.is_processing = False
        if "keyboard_trigger" not in st.session_state:
            st.session_state.keyboard_trigger = None
        if "current_page" not in st.session_state:
            st.session_state.current_page = 0
        if "settings" not in st.session_state:
            st.session_state.settings = {
                'model': self.chat_interface.model_name,
                'api_params': {
                    'temperature': self.chat_interface.temperature,
                    'top_p': self.chat_interface.top_p,
                    'presence_penalty': self.chat_interface.presence_penalty,
                    'frequency_penalty': self.chat_interface.frequency_penalty
                },
                'theme': 'light'
            }
        
        # Load any persisted settings before applying theme
        self._load_settings()
        
        # Apply current theme
        current_theme = st.session_state.settings.get('theme', 'light')
        if current_theme in self.VALID_THEMES:
            self._update_theme(current_theme)

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
        """Display paginated messages in the chat interface."""
        messages = self._get_paginated_messages()
        for message in messages:
            self._display_message(message)
        
        # Add pagination controls if needed
        total_pages = max(1, len(st.session_state.messages) // self.MESSAGES_PER_PAGE)
        if total_pages > 1:
            cols = st.columns(3)
            with cols[0]:
                if st.button("← Previous", key="prev_btn") and st.session_state.current_page > 0:
                    st.session_state.current_page -= 1
            with cols[1]:
                st.write(f"Page {st.session_state.current_page + 1} of {total_pages}")
            with cols[2]:
                if st.button("Next →", key="next_btn") and st.session_state.current_page < total_pages - 1:
                    st.session_state.current_page += 1

    async def _handle_user_input(self) -> None:
        """Handle user input and generate AI response."""
        if prompt := st.chat_input("Type your message here...", key="main_chat_input"):
            st.session_state.is_processing = True
            response_placeholder = st.empty()  # Create placeholder for response
            
            try:
                # Add user message
                user_message = {"role": "user", "content": prompt}
                if "messages" not in st.session_state:
                    st.session_state.messages = []
                st.session_state.messages.append(user_message)
                self._display_message(user_message)

                # Get AI response
                full_response = ""
                async for chunk in self.chat_interface.send_message_stream(prompt):
                    full_response += chunk
                    with response_placeholder.container():  # Use placeholder
                        st.chat_message("assistant").write(full_response)
                
                # Add assistant message to history
                assistant_message = {"role": "assistant", "content": full_response}
                st.session_state.messages.append(assistant_message)
                
                # Force UI update
                st.rerun()
                
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                st.error(str(e))
                with st.chat_message("assistant"):
                    st.error(f"Error: {str(e)}")
            
            finally:
                st.session_state.is_processing = False

    def _render_sidebar(self) -> Dict[str, Any]:
        """Render the sidebar with settings and controls."""
        with st.sidebar:
            st.subheader("Settings")
            
            # Temperature slider
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=st.session_state.settings['api_params']['temperature'],
                help="Controls randomness in responses"
            )
            st.session_state.settings['api_params']['temperature'] = temperature
            self.chat_interface.temperature = temperature
            
            # Top P slider
            top_p = st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.settings['api_params']['top_p'],
                help="Controls diversity via nucleus sampling"
            )
            st.session_state.settings['api_params']['top_p'] = top_p
            self.chat_interface.top_p = top_p
            
            # Presence Penalty slider
            presence_penalty = st.slider(
                "Presence Penalty",
                min_value=0.0,
                max_value=2.0,
                value=st.session_state.settings['api_params']['presence_penalty'],
                help="Controls repetition penalty"
            )
            st.session_state.settings['api_params']['presence_penalty'] = presence_penalty
            self.chat_interface.presence_penalty = presence_penalty
            
            # Frequency Penalty slider
            frequency_penalty = st.slider(
                "Frequency Penalty",
                min_value=0.0,
                max_value=2.0,
                value=st.session_state.settings['api_params']['frequency_penalty'],
                help="Controls token frequency penalty"
            )
            st.session_state.settings['api_params']['frequency_penalty'] = frequency_penalty
            self.chat_interface.frequency_penalty = frequency_penalty
            
            # Theme selector
            theme = st.selectbox(
                "Select Theme",
                options=['light', 'dark'],
                index=0 if st.session_state.settings['theme'] == 'light' else 1
            )
            st.session_state.settings['theme'] = theme
            
            return {
                'temperature': temperature,
                'top_p': top_p,
                'presence_penalty': presence_penalty,
                'frequency_penalty': frequency_penalty,
                'theme': theme
            }

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
            if prompt := st.chat_input("Type your message here...", key=f"chat_input_{time.time()}"):
                if "messages" not in st.session_state:
                    st.session_state.messages = []
                st.session_state.messages.append({"role": "user", "content": prompt})
                await self._handle_user_input()
        elif st.session_state.keyboard_trigger == 'ctrl+l':
            st.session_state.messages = []
            self.chat_interface.clear_history()
        
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
        try:
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
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def _load_settings(self) -> None:
        """Load settings from persistent storage."""
        try:
            params = st.experimental_get_query_params()
            stored_settings = params.get('settings', [None])[0]
            
            if stored_settings and isinstance(stored_settings, dict):
                # Update chat interface settings
                if 'model' in stored_settings:
                    self.chat_interface.model_name = stored_settings['model']
                if 'api_params' in stored_settings:
                    params = stored_settings['api_params']
                    self.chat_interface.temperature = params.get('temperature', self.chat_interface.temperature)
                    self.chat_interface.top_p = params.get('top_p', self.chat_interface.top_p)
                    self.chat_interface.presence_penalty = params.get('presence_penalty', self.chat_interface.presence_penalty)
                    self.chat_interface.frequency_penalty = params.get('frequency_penalty', self.chat_interface.frequency_penalty)
                
                # Update session state settings
                st.session_state.settings.update(stored_settings)
                logger.info("Settings loaded from persistent storage")
            else:
                logger.info("No stored settings found, using defaults")
                
        except Exception as e:
            logger.warning(f"Error loading settings: {e}. Using defaults.")

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

    def _save_conversation(self) -> None:
        """Save current conversation to persistent storage."""
        try:
            # Get recent messages within limit
            messages_to_save = st.session_state.messages[-self.MAX_STORED_MESSAGES:]
            
            # Save to query parameters
            st.experimental_set_query_params(
                conversation=messages_to_save
            )
            logger.info(f"Saved {len(messages_to_save)} messages to persistent storage")
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")

    def _load_conversation(self) -> None:
        """Load conversation from persistent storage."""
        try:
            # Get stored conversation
            params = st.experimental_get_query_params()
            stored_messages = params.get('conversation', [])
            
            if stored_messages:
                # Ensure we only load up to MAX_STORED_MESSAGES
                messages_to_load = stored_messages[-self.MAX_STORED_MESSAGES:]
                # Update session state
                st.session_state.messages = messages_to_load
                logger.info(f"Loaded {len(messages_to_load)} messages from persistent storage")
            else:
                logger.info("No stored conversation found")
        except Exception as e:
            logger.error(f"Error loading conversation: {e}")
            st.session_state.messages = []

    def _enforce_message_limit(self) -> None:
        """Ensure messages don't exceed MAX_STORED_MESSAGES."""
        if len(st.session_state.messages) > self.MAX_STORED_MESSAGES:
            st.session_state.messages = st.session_state.messages[-self.MAX_STORED_MESSAGES:]
            logger.debug(f"Trimmed messages to {self.MAX_STORED_MESSAGES} most recent")

    def _get_theme_styles(self, theme: str) -> Dict[str, str]:
        """Get CSS styles for the specified theme.
        
        Args:
            theme: Theme name ('light' or 'dark')
            
        Returns:
            Dict[str, str]: Theme style definitions
            
        Raises:
            ValueError: If theme is invalid
        """
        if theme not in self.VALID_THEMES:
            raise ValueError(f"Invalid theme: {theme}. Must be one of {self.VALID_THEMES}")
            
        themes = {
            'light': {
                'background_color': '#ffffff',
                'text_color': '#000000',
                'sidebar_bg': '#f8f9fa',
                'input_bg': '#f0f2f6',
                'border_color': '#e6e6e6'
            },
            'dark': {
                'background_color': '#1E1E1E',
                'text_color': '#ffffff',
                'sidebar_bg': '#262626',
                'input_bg': '#2d2d2d',
                'border_color': '#404040'
            }
        }
        return themes[theme]
    
    def _update_theme(self, theme: str, save_settings: bool = True) -> None:
        """Update the UI theme.
        
        Args:
            theme: Theme name ('light' or 'dark')
            save_settings: Whether to save settings after updating theme
            
        Raises:
            ValueError: If theme is invalid
        """
        if theme not in self.VALID_THEMES:
            raise ValueError(f"Invalid theme: {theme}. Must be one of {self.VALID_THEMES}")
            
        st.session_state.settings['theme'] = theme
        styles = self._get_theme_styles(theme)
        
        # Apply theme using custom CSS
        css = f"""
        <style>
            .stApp {{
                background-color: {styles['background_color']};
                color: {styles['text_color']};
            }}
            .stSidebar {{
                background-color: {styles['sidebar_bg']};
            }}
            .stTextInput {{
                background-color: {styles['input_bg']};
                border-color: {styles['border_color']};
            }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
        logger.info(f"Updated theme to: {theme}")
        
        # Save settings to persist theme
        if save_settings:
            self._save_settings()

    def _get_total_pages(self) -> int:
        """Get total number of pages based on conversation count."""
        total_messages = len(st.session_state.messages)
        # Each conversation takes 2 messages (user + assistant)
        conversations = total_messages // 2
        conversations_per_page = self.MESSAGES_PER_PAGE // 2
        return max(1, (conversations + conversations_per_page - 1) // conversations_per_page)

    def _get_paginated_messages(self) -> List[Dict[str, str]]:
        """Get messages for current page.
        
        Returns:
            List[Dict[str, str]]: List of messages for the current page, newest conversations first.
            Each conversation consists of a user message followed by an assistant response.
        """
        total_messages = len(st.session_state.messages)
        # Calculate indices based on conversation pairs
        conversations_per_page = self.MESSAGES_PER_PAGE // 2
        
        # Calculate start and end indices for conversations
        start_conv = max(0, (total_messages // 2) - (self.current_page + 1) * conversations_per_page)
        end_conv = max(0, (total_messages // 2) - self.current_page * conversations_per_page)
        
        # Convert conversation indices to message indices and get messages
        messages = []
        for i in range(end_conv - 1, start_conv - 1, -1):  # Iterate in reverse
            if i * 2 + 1 < total_messages:  # Check if we have both user and assistant messages
                messages.extend([
                    st.session_state.messages[i * 2],      # User message
                    st.session_state.messages[i * 2 + 1]   # Assistant response
                ])
        
        return messages

    def _next_page(self) -> None:
        """Go to next page if available."""
        total_pages = self._get_total_pages()
        if self.current_page < total_pages - 1:
            self.current_page += 1
            logger.debug(f"Moved to page {self.current_page + 1} of {total_pages}")

    def _prev_page(self) -> None:
        """Go to previous page if available."""
        if self.current_page > 0:
            self.current_page -= 1
            logger.debug(f"Moved to page {self.current_page + 1} of {self._get_total_pages()}")

    def _get_visible_messages(self) -> List[Dict[str, str]]:
        """Get messages that should be visible in the current viewport.
        
        Returns:
            List[Dict[str, str]]: List of messages to render.
        """
        total_messages = len(st.session_state.messages)
        start_idx = max(0, min(
            self.scroll_position,
            total_messages - self.MESSAGES_PER_VIEW
        ))
        end_idx = min(start_idx + self.MESSAGES_PER_VIEW, total_messages)
        
        return st.session_state.messages[start_idx:end_idx]

    def _get_recycled_message_components(self) -> Dict[str, Any]:
        """Get recycled message components to improve rendering performance.
        
        Returns:
            Dict[str, Any]: Map of message keys to recycled components.
        """
        # Clean up old components if too many
        if len(self.recycled_components) > self.MAX_RECYCLED_COMPONENTS:
            # Keep most recently used components
            sorted_components = sorted(
                self.recycled_components.items(),
                key=lambda x: x[1].last_used,
                reverse=True
            )
            self.recycled_components = dict(
                sorted_components[:self.MAX_RECYCLED_COMPONENTS]
            )
        
        return self.recycled_components

    def _render_messages(self) -> None:
        """Render visible messages efficiently."""
        messages = self._get_visible_messages()
        recycled = self._get_recycled_message_components()
        
        for message in messages:
            key = f"{message['role']}:{message['content']}"
            
            # Try to reuse existing component
            if key in recycled:
                component = recycled[key]
                component.last_used = time.time()
            else:
                # Create new component if needed
                component = MessageComponent(message)
                recycled[key] = component
            
            # Render the message
            with st.chat_message(message["role"]):
                component.render()

class MessageComponent:
    """Reusable message component for efficient rendering."""
    
    def __init__(self, message: Dict[str, str]):
        """Initialize message component."""
        self.message = message
        self.last_used = time.time()
        
    def render(self) -> None:
        """Render the message content."""
        st.markdown(self.message["content"])
