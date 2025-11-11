import logging
from pathlib import Path
import pytest
from cenv.logging_config import setup_logging, get_logger


def test_setup_logging_creates_logger():
    """Test that setup_logging creates configured logger"""
    setup_logging(level=logging.DEBUG)
    logger = get_logger("test")

    assert logger is not None
    # Check the parent cenv logger is configured with DEBUG level
    cenv_logger = logging.getLogger("cenv")
    assert cenv_logger.level == logging.DEBUG


def test_get_logger_returns_logger_with_name():
    """Test that get_logger returns properly named logger"""
    logger = get_logger("cenv.test")
    assert logger.name == "cenv.test"


def test_logging_to_file(tmp_path):
    """Test that logs can be written to file"""
    log_file = tmp_path / "cenv.log"
    setup_logging(level=logging.INFO, log_file=log_file)

    logger = get_logger("test")
    logger.info("Test message")

    assert log_file.exists()
    content = log_file.read_text()
    assert "Test message" in content


def test_logging_respects_level():
    """Test that logging level is respected"""
    setup_logging(level=logging.WARNING)
    logger = get_logger("test")

    # Debug and info should not be logged at WARNING level
    assert not logger.isEnabledFor(logging.DEBUG)
    assert not logger.isEnabledFor(logging.INFO)
    assert logger.isEnabledFor(logging.WARNING)
