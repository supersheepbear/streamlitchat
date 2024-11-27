"""Logging configuration for StreamlitChat."""
import logging
import logging.handlers
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os
from contextvars import ContextVar
import uuid

@dataclass
class LogConfig:
    """Configuration for logging setup.
    
    Args:
        log_dir: Directory for log files
        log_level: Logging level
        max_bytes: Maximum bytes per log file
        backup_count: Number of backup files to keep
        log_format: Format string for log messages
        
    Examples:
        >>> config = LogConfig(log_dir="logs", log_level=logging.DEBUG)
        >>> configure_logging(config)
    """
    log_dir: Path = Path("logs")
    log_level: int = logging.INFO
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    log_format: str = "%(asctime)s - %(name)s - [%(request_id)s] - %(levelname)s - %(message)s"
    
    @property
    def log_file(self) -> Path:
        """Get path to main log file."""
        return self.log_dir / "streamlitchat.log"

# Context variable for request ID
request_id: ContextVar[str] = ContextVar('request_id', default='')

class RequestIDFilter(logging.Filter):
    """Filter that adds request ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add request ID to record."""
        record.request_id = request_id.get() or 'no-request-id'
        return True

def configure_logging(config: LogConfig) -> None:
    """Configure logging with given settings.
    
    Args:
        config: Logging configuration
        
    Raises:
        OSError: If log directory cannot be created
    """
    # Create log directory
    os.makedirs(config.log_dir, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger("streamlitchat")
    logger.setLevel(config.log_level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add request ID filter
    logger.addFilter(RequestIDFilter())
    
    # Create formatters
    formatter = logging.Formatter(config.log_format)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        config.log_file,
        maxBytes=config.max_bytes,
        backupCount=config.backup_count
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

class LogContext:
    """Context manager for setting request ID.
    
    Examples:
        >>> with LogContext(request_id="123"):
        ...     logger.info("Processing request")
    """
    
    def __init__(self, request_id: Optional[str] = None):
        """Initialize context with optional request ID."""
        self.request_id = request_id or str(uuid.uuid4())
        self.token = None
    
    def __enter__(self):
        """Set request ID for context."""
        self.token = request_id.set(self.request_id)
        return self
    
    def __exit__(self, *args):
        """Reset request ID."""
        request_id.reset(self.token) 