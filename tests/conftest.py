"""
Pytest configuration and shared fixtures for XScraper tests
"""
import os
import sys
import pytest
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables for all tests"""
    load_dotenv()

@pytest.fixture
def x_credentials():
    """Provide X.com credentials from environment"""
    return {
        'email': os.getenv('X_EMAIL'),
        'password': os.getenv('X_PASSWORD'),
        'backup_email': os.getenv('X_EMAIL_BACKUP'),
        'backup_password': os.getenv('X_PASSWORD_BACKUP')
    }

@pytest.fixture
def decodo_config():
    """Provide Decodo proxy configuration"""
    return {
        'username': os.getenv('DECODO_USERNAME'),
        'password': os.getenv('DECODO_PASSWORD'),
        'host': os.getenv('DECODO_HOST'),
        'ports': [int(p.strip()) for p in os.getenv('DECODO_PORTS', '10001,10002,10003').split(',')]
    }