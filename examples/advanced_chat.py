"""
Advanced chat example with custom configuration.
"""
import streamlitchat
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Initialize chat interface with custom settings
    chat = streamlitchat.ChatInterface(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model_name="gpt-4",
        temperature=0.7,
        top_p=0.9,
        presence_penalty=0.0,
        frequency_penalty=0.0,
        api_base=None
    )
    
    # Run the interface
    chat.run()

if __name__ == "__main__":
    main() 