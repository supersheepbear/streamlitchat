"""Tests for logging and error handling functionality."""
import pytest
import logging
import os
from pathlib import Path
from streamlitchat.logging_config import configure_logging, LogConfig, LogContext
from streamlitchat.exceptions import ChatError, APIError, ValidationError

def test_logging_configuration():
    """Test basic logging configuration."""
    log_config = LogConfig()
    configure_logging(log_config)
    
    logger = logging.getLogger("streamlitchat")
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0
    
    # Test log levels are properly set
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

def test_log_rotation():
    """Test log rotation functionality."""
    log_dir = Path("logs")
    log_config = LogConfig(
        log_dir=log_dir,
        max_bytes=1024,  # Small size for testing
        backup_count=3
    )
    configure_logging(log_config)
    
    logger = logging.getLogger("streamlitchat")
    
    # Generate enough logs to trigger rotation
    for i in range(1000):
        logger.info("Test log message " * 10)
    
    # Check rotation occurred
    log_files = list(log_dir.glob("*.log*"))
    assert len(log_files) > 1
    assert len(log_files) <= 4  # main log + 3 backups

def test_request_id_tracking():
    """Test request ID is included in logs."""
    log_config = LogConfig()
    configure_logging(log_config)
    
    logger = logging.getLogger("streamlitchat")
    
    with LogContext(request_id="test-123"):
        logger.info("Test message")
        
    # Verify log contains request ID
    with open(log_config.log_file, 'r') as f:
        log_content = f.read()
        assert "test-123" in log_content

def test_custom_exceptions():
    """Test custom exception hierarchy."""
    # Base exception
    with pytest.raises(ChatError):
        raise ChatError("General chat error")
    
    # API error
    with pytest.raises(APIError):
        raise APIError("API call failed")
    
    # Validation error
    with pytest.raises(ValidationError):
        raise ValidationError("Invalid input") 