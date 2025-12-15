import pytest
from app import create_app, db

@pytest.fixture
def app():
    """Create and configure a test app instance"""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Test client for making requests"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """CLI runner for testing CLI commands"""
    return app.test_cli_runner()
