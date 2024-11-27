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

    MAX_STORED_MESSAGES = 50  # Maximum number of messages to persist and load between sessions
    VALID_THEMES = {'light', 'dark'}  # Valid theme options
    MESSAGES_PER_PAGE = 10  # Number of messages to display per page

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
        
        # Add pagination controls if more than one page
        total_pages = self._get_total_pages()
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                if st.button("← Previous") and self.current_page > 0:
                    self._prev_page()
            with col2:
                st.write(f"Page {self.current_page + 1} of {total_pages}")
            with col3:
                if st.button("Next →") and self.current_page < total_pages - 1:
                    self._next_page()

    async def _handle_user_input(self) -> None:
        """Handle user input and generate AI response."""
        if prompt := st.chat_input("Type your message here..."):
            st.session_state.is_processing = True
            
            # Add user message to chat
            user_message = {"role": "user", "content": prompt}
            st.session_state.messages.append(user_message)
            # Enforce message limit
            if len(st.session_state.messages) > self.MAX_STORED_MESSAGES:
                st.session_state.messages = st.session_state.messages[-self.MAX_STORED_MESSAGES:]
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
                # Enforce message limit again after adding assistant response
                if len(st.session_state.messages) > self.MAX_STORED_MESSAGES:
                    st.session_state.messages = st.session_state.messages[-self.MAX_STORED_MESSAGES:]

            except Exception as e:
                st.error(f"Error: {str(e)}")
            
            finally:
                st.session_state.is_processing = False
                # Save conversation after each message
                self._save_conversation()

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
                # Theme Selection
                st.subheader("Theme")
                current_theme = st.session_state.settings.get('theme', 'light')
                theme = st.selectbox(
                    "Select Theme",
                    options=list(self.VALID_THEMES),
                    index=list(self.VALID_THEMES).index(current_theme)
                )
                if theme != current_theme:
                    self._update_theme(theme)

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
                
                # Apply theme if it exists
                theme = stored_settings.get('theme', 'light')
                if theme in self.VALID_THEMES:
                    self._update_theme(theme, save_settings=False)  # Avoid recursive save
                
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
