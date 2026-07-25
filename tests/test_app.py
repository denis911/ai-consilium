import pytest


def test_app_imports_cleanly():
    """Verify that app.py imports without syntax or module import errors."""
    import app
    assert hasattr(app, "main")
    assert hasattr(app, "run_async")
