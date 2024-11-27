"""
Basic chat example using StreamlitChat.
"""
import streamlitchat
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Initialize chat interface
    chat = streamlitchat.ChatInterface(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model_name="gpt-3.5-turbo"
    )
    
    # Run the interface
    chat.run()

if __name__ == "__main__":
    main() 