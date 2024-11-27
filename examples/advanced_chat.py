"""
Advanced chat example with custom configuration.
"""
import streamlitchat
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Custom settings
    settings = {
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

    # Initialize chat interface with custom settings
    chat = streamlitchat.ChatInterface(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4",
        settings=settings
    )
    
    # Run the interface
    chat.run()

if __name__ == "__main__":
    main() 