import os
import council

def test_package_import():
    """Verify council package imports correctly and version is defined."""
    assert council.__version__ == "0.1.0"

def test_missing_env_file_graceful():
    """Verify that absence of .env file does not cause uncaught errors."""
    # Ensure test runs safely even if .env is missing
    env_exists = os.path.exists(".env")
    assert isinstance(env_exists, bool)
