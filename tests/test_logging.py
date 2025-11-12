import logging
import threading

import pytest

from cenv.logging_config import get_logger, reset_logging_config, setup_logging


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration before each test"""
    reset_logging_config()
    yield
    reset_logging_config()


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


def test_setup_logging_is_thread_safe(tmp_path):
    """Test that concurrent logging setup doesn't corrupt state"""
    log_file = tmp_path / "test.log"
    errors = []

    def setup_concurrent():
        try:
            setup_logging(level=logging.INFO, log_file=log_file)
            logger = get_logger("test")
            logger.info("Test message")
        except Exception as e:
            errors.append(e)

    # Launch multiple threads setting up logging
    threads = [threading.Thread(target=setup_concurrent) for _ in range(10)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Should complete without errors
    assert len(errors) == 0, f"Got errors: {errors}"

    # Log file should exist and contain messages
    assert log_file.exists()
    content = log_file.read_text()
    assert "Test message" in content


def test_concurrent_logging_no_handler_duplication(tmp_path):
    """Test that concurrent setup doesn't duplicate handlers"""
    log_file = tmp_path / "test.log"

    def setup_and_count():
        setup_logging(level=logging.INFO, log_file=log_file)
        logger = logging.getLogger("cenv")
        return len(logger.handlers)

    # Setup multiple times concurrently
    threads = [threading.Thread(target=setup_and_count) for _ in range(5)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Check final handler count
    logger = logging.getLogger("cenv")
    # Should have exactly 2 handlers (console + file)
    assert len(logger.handlers) == 2, f"Expected 2 handlers, got {len(logger.handlers)}"
