from app.main import app


def test_app_creates_fastapi_instance():
    assert app is not None
