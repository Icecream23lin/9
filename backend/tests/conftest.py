"""
Pytest configuration file for visualization testing
Contains shared fixtures and test configuration
"""

import pytest
import os
import tempfile
import shutil
from app import create_app


@pytest.fixture(scope='session')
def test_app():
    """Create test application instance"""
    app = create_app('testing')
    
    # Ensure test upload directory exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    yield app
    
    # Cleanup test upload directory after all tests
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        shutil.rmtree(app.config['UPLOAD_FOLDER'])


@pytest.fixture
def app(test_app):
    """Provide test app instance"""
    return test_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def temp_directory():
    """Create temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir)


@pytest.fixture(autouse=True)
def cleanup_matplotlib():
    """Cleanup matplotlib after each test to prevent memory leaks"""
    yield
    import matplotlib.pyplot as plt
    plt.close('all')
    plt.clf()


# Test configuration
def pytest_configure(config):
    """Configure pytest settings"""
    # Set up test markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests" 
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Mark API tests as integration tests
        if "test_visualization_api" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        # Mark service tests as unit tests
        elif "test_visualization_service" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Mark performance tests as slow
        if "performance" in item.name.lower() or "large" in item.name.lower():
            item.add_marker(pytest.mark.slow)