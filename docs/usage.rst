=====
Usage
=====

Basic Usage
----------

To use StreamlitChat in a project::

    import streamlitchat
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Initialize the chat interface
    chat = streamlitchat.ChatInterface(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model_name="gpt-3.5-turbo"  # Default model
    )
    
    # Run the chat interface
    chat.run()

Configuration
------------

You can customize the chat interface with various parameters::

    chat = streamlitchat.ChatInterface(
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
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model_name="gpt-4",
        temperature=0.7,
        top_p=0.9,
        presence_penalty=0.0,
        frequency_penalty=0.0,
        api_base=None  # Optional custom API endpoint
    )

    # Run the interface
    chat.run()
