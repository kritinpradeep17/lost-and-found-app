from app import create_app
import pytest

def test_app_creation():
    app = create_app()
    assert app is not None
