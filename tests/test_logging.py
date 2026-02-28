import os
import logging
from app.core.logging_config import setup_logging
from app.core.settings import settings

def test_logging_configuration():
    # Clear existing log file if exists
    if os.path.exists(settings.LOG_FILE):
        os.remove(settings.LOG_FILE)
    
    # Run setup
    setup_logging()
    
    # Get a logger and log something
    logger = logging.getLogger("test_logger")
    test_message = "This is a test log message"
    logger.info(test_message)
    
    # Check if log file was created
    assert os.path.exists(settings.LOG_FILE)
    
    # Check if message is in the file
    with open(settings.LOG_FILE, "r") as f:
        content = f.read()
        assert test_message in content
        assert "INFO" in content

def test_logging_levels():
    # Change log level in settings (mocking or temporarily changing)
    original_level = settings.LOG_LEVEL
    settings.LOG_LEVEL = "ERROR"
    
    setup_logging()
    logger = logging.getLogger("test_error_logger")
    
    info_msg = "Should not be in log"
    error_msg = "Should be in log"
    
    logger.info(info_msg)
    logger.error(error_msg)
    
    with open(settings.LOG_FILE, "r") as f:
        content = f.read()
        assert error_msg in content
        assert info_msg not in content
    
    # Restore
    settings.LOG_LEVEL = original_level
    setup_logging()
