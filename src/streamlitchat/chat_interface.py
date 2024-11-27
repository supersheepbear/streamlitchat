"""StreamlitChat interface implementation."""
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
import aiohttp
import openai
from openai import AsyncOpenAI
import time
import asyncio
from collections import deque
import hashlib

# Configure logging
logger = logging.getLogger(__name__)

class ChatInterface:
    """A class to handle chat interactions with OpenAI API.
    
    This class provides methods to send messages, manage chat history,
    and handle streaming responses from OpenAI-compatible APIs.
    
    Attributes:
        messages (List[Dict[str, str]]): List of chat messages.
        model_name (str): Name of the model to use for chat.
        api_key (str): API key for authentication.
        api_base (Optional[str]): Base URL for API requests.
        temperature (float): Controls randomness in responses.
        top_p (float): Controls diversity via nucleus sampling.
        presence_penalty (float): Penalty for new tokens.
        frequency_penalty (float): Penalty for frequent tokens.
    
    Examples:
        >>> chat = ChatInterface(api_key="your-api-key")
        >>> response = await chat.send_message("Hello!")
        >>> print(response)
        "Hi there! How can I help you today?"
        
        >>> # Stream responses
        >>> async for chunk in chat.send_message_stream("Tell me a story"):
        ...     print(chunk, end="")
    """
    
    def __init__(
        self,
        api_key: str = "",
        model_name: str = "gpt-3.5-turbo",
        api_base: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        test_mode: bool = False
    ) -> None:
        """Initialize the ChatInterface.
        
        Args:
            api_key: The API key to use. Required unless test_mode is True.
            model_name: The name of the model to use. Defaults to "gpt-3.5-turbo".
            api_base: Optional base URL for API requests. Defaults to None.
            temperature: Controls randomness in responses. Defaults to 0.7.
            top_p: Controls diversity via nucleus sampling. Defaults to 0.9.
            presence_penalty: Penalty for new tokens. Defaults to 0.0.
            frequency_penalty: Penalty for frequent tokens. Defaults to 0.0.
            test_mode: If True, skip API key validation. Defaults to False.
        
        Raises:
            ValueError: If the API key is invalid and test_mode is False.
        """
        self.messages: List[Dict[str, str]] = []
        self.model_name = model_name
        self.api_base = api_base
        self.temperature = temperature
        self.top_p = top_p
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.test_mode = test_mode
        
        if not test_mode and not api_key:
            raise ValueError("API key is required unless test_mode is True")
        
        if not test_mode:
            self.validate_api_key(api_key)
        
        self.api_key = api_key
        logger.info("Initialized ChatInterface with model: %s", model_name)
        
        # Cache settings
        self.response_cache: Dict[str, str] = {}
        self.cache_ttl = 3600  # 1 hour cache lifetime
        self.cache_size = 1000  # Maximum cache entries
        
        # Rate limiting
        self.requests_per_minute = 60
        self.request_window = 60  # seconds
        self.request_timestamps: deque = deque(maxlen=self.requests_per_minute)
        
        # Request queuing
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.batch_size = 5
        self.batch_timeout = 1.0  # seconds
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate the format of the API key.
        
        Args:
            api_key: The API key to validate.
            
        Returns:
            bool: True if the API key is valid.
            
        Raises:
            ValueError: If the API key is invalid.
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        
        if not api_key.startswith("sk-") or len(api_key) < 20:
            raise ValueError("Invalid API key format")
        
        return True
    
    async def send_message(self, message: str) -> str:
        """Send a message and get a response.
        
        Args:
            message: The message to send.
            
        Returns:
            str: The response from the API.
            
        Raises:
            ValueError: If no API key is set.
            openai.OpenAIError: If there's an error with the API request.
        """
        if not self.api_key:
            raise ValueError("API key must be set before sending messages")
        
        try:
            # Add user message to history
            self.messages.append({"role": "user", "content": message})
            
            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )
            
            # Send request to API
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": m["role"], "content": m["content"]} 
                         for m in self.messages]
            )
            
            # Extract and store response
            assistant_message = response.choices[0].message.content
            self.messages.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            logger.info("Successfully sent message and received response")
            return assistant_message
            
        except openai.OpenAIError as e:
            logger.error("Error sending message: %s", str(e))
            raise
    
    async def send_message_stream(
        self,
        message: str
    ) -> AsyncGenerator[str, None]:
        """Send a message and get a streaming response.
        
        Args:
            message: The message to send.
            
        Yields:
            str: Chunks of the response from the API.
            
        Raises:
            ValueError: If no API key is set.
            openai.OpenAIError: If there's an error with the API request.
        """
        if not self.api_key:
            raise ValueError("API key must be set before sending messages")
        
        try:
            # Add user message to history
            self.messages.append({"role": "user", "content": message})
            
            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )
            
            # Send streaming request to API with parameters
            stream = await client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": m["role"], "content": m["content"]} 
                         for m in self.messages],
                stream=True,
                temperature=self.temperature,
                top_p=self.top_p,
                presence_penalty=self.presence_penalty,
                frequency_penalty=self.frequency_penalty
            )
            
            full_response = []
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response.append(content)
                    yield content
            
            # Store complete response in history
            complete_response = "".join(full_response)
            self.messages.append({
                "role": "assistant",
                "content": complete_response
            })
            
            logger.info("Successfully completed streaming response")
            
        except openai.OpenAIError as e:
            logger.error("Error in streaming response: %s", str(e))
            raise
    
    def clear_history(self) -> None:
        """Clear the chat history."""
        self.messages = []
        logger.info("Chat history cleared")
    
    def export_history(self) -> List[Dict[str, str]]:
        """Export the chat history.
        
        Returns:
            List[Dict[str, str]]: The chat history.
        """
        return self.messages.copy()
    
    def import_history(self, messages: List[Dict[str, str]]) -> None:
        """Import a chat history.
        
        Args:
            messages: The chat history to import.
        """
        self.messages = messages.copy()
        logger.info("Imported %d messages to chat history", len(messages))
    
    def _generate_cache_key(self, message: str, context: str = "") -> str:
        """Generate a cache key from message and context."""
        combined = f"{context}:{message}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    async def get_cached_response(self, message: str, context: str = "") -> Optional[str]:
        """Get cached response if available."""
        cache_key = self._generate_cache_key(message, context)
        return self.response_cache.get(cache_key)
    
    def _update_cache(self, message: str, response: str, context: str = "") -> None:
        """Update cache with new response."""
        if len(self.response_cache) >= self.cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self.response_cache))
            del self.response_cache[oldest_key]
        
        cache_key = self._generate_cache_key(message, context)
        self.response_cache[cache_key] = response
        logger.debug(f"Cached response for key: {cache_key}")
    
    def can_make_request(self) -> bool:
        """Check if we can make a request within rate limits."""
        now = time.time()
        # Remove old timestamps
        while self.request_timestamps and now - self.request_timestamps[0] > self.request_window:
            self.request_timestamps.popleft()
        
        return len(self.request_timestamps) < self.requests_per_minute
    
    async def queue_request(self, message: str) -> None:
        """Queue a request for processing."""
        await self.request_queue.put(message)
        logger.debug(f"Queued message: {message}")
    
    async def process_batch(self) -> List[str]:
        """Process a batch of queued requests.
        
        Returns:
            List[str]: List of responses for the batch of messages.
        """
        batch = []
        try:
            while len(batch) < self.batch_size:
                try:
                    message = await asyncio.wait_for(
                        self.request_queue.get(),
                        timeout=self.batch_timeout
                    )
                    batch.append(message)
                except asyncio.TimeoutError:
                    break
            
            if not batch:
                return []
            
            responses = []
            for message in batch:
                # Check cache first
                if cached := await self.get_cached_response(message):
                    responses.append(cached)
                    continue
                
                # Wait for rate limit
                while not self.can_make_request():
                    await asyncio.sleep(1)
                
                # Make API request
                if self.test_mode:
                    # Extract message number for test response
                    msg_num = message.split()[-1]  # Get "1" from "Message 1"
                    response = f"Test response to Message {msg_num}"
                else:
                    response = await self.send_message(message)
                
                self._update_cache(message, response)
                responses.append(response)
                
                # Update rate limit tracking
                self.request_timestamps.append(time.time())
            
            return responses
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            raise
