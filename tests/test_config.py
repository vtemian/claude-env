import os
import pytest
import threading
from pathlib import Path
from cenv.config import load_config, Config, DEFAULT_GIT_TIMEOUT, get_config, _reset_config_for_testing


@pytest.fixture(autouse=True)
def reset_config():
    """Reset config before and after each test"""
    _reset_config_for_testing()
    yield
    _reset_config_for_testing()


def test_default_config():
    """Test that default config has sensible values"""
    config = Config()

    assert config.git_timeout > 0
    assert config.git_timeout == DEFAULT_GIT_TIMEOUT
    assert isinstance(config.trash_dir_name, str)


def test_config_from_environment_variables(monkeypatch):
    """Test loading config from environment variables"""
    monkeypatch.setenv("CENV_GIT_TIMEOUT", "600")
    monkeypatch.setenv("CENV_LOG_LEVEL", "DEBUG")

    config = load_config()

    assert config.git_timeout == 600


def test_invalid_config_values_use_defaults(monkeypatch):
    """Test that invalid values fall back to defaults"""
    monkeypatch.setenv("CENV_GIT_TIMEOUT", "invalid")

    config = load_config()

    # Should use default, not crash
    assert config.git_timeout == DEFAULT_GIT_TIMEOUT


def test_config_file_loading(tmp_path):
    """Test loading config from file"""
    config_file = tmp_path / ".cenvrc"
    config_file.write_text("""
git_timeout = 600
log_level = DEBUG
    """)

    config = load_config(config_file=config_file)

    assert config.git_timeout == 600


def test_get_config_is_thread_safe():
    """Test that concurrent get_config calls don't create multiple instances"""
    # Fixture handles reset
    configs = []

    def get_and_store():
        config = get_config()
        configs.append(id(config))

    # Launch 10 concurrent threads
    threads = []
    for _ in range(10):
        thread = threading.Thread(target=get_and_store)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # All threads should get the SAME instance (same id)
    assert len(set(configs)) == 1, (
        f"Expected singleton, got {len(set(configs))} different instances"
    )


def test_concurrent_config_loading():
    """Test that concurrent config loading doesn't cause errors"""
    # Fixture handles reset
    errors = []

    def load_config_safely():
        try:
            config = get_config()
            assert config.git_timeout == 300
        except Exception as e:
            errors.append(str(e))

    threads = []
    for _ in range(20):
        thread = threading.Thread(target=load_config_safely)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    assert not errors, f"Config loading errors: {errors}"
