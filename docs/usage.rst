=====
Usage
=====

Basic Usage
----------

To use StreamlitChat in a project::

    import streamlitchat
    
    # Initialize the chat interface
    chat = streamlitchat.ChatInterface(
        api_key="your-api-key",  # Or use environment variable OPENAI_API_KEY
        model="gpt-3.5-turbo"    # Default model
    )
    
    # Run the chat interface
    chat.run()

Configuration
------------

You can customize the chat interface using settings::

    chat = streamlitchat.ChatInterface(
        api_key="your-api-key",
        model="gpt-3.5-turbo",
        settings={
            'temperature': 0.7,
            'top_p': 0.9,
            'presence_penalty': 0.0,
            'frequency_penalty': 0.0,
            'theme': 'light'
        }
    )

Environment Variables
-------------------

The following environment variables are supported:

- ``OPENAI_API_KEY``: Your OpenAI API key
- ``STREAMLIT_THEME``: UI theme ('light' or 'dark')
- ``LOG_LEVEL``: Logging level (DEBUG, INFO, WARNING, ERROR)

Example Configuration
-------------------

Here's a complete example with all available options::

    import streamlitchat
    import os
    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()

    # Initialize with custom settings
    chat = streamlitchat.ChatInterface(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4",
        settings={
            'temperature': 0.7,
            'top_p': 0.9,
            'presence_penalty': 0.0,
            'frequency_penalty': 0.0,
            'theme': 'dark',
            'max_tokens': 2000,
            'stream': True,
            'cache_enabled': True,
            'history_enabled': True
        }
    )

    # Run the interface
    chat.run()
