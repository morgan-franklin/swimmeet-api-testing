"""
Pytest configuration and fixtures
"""

import pytest
import shutil
import os


@pytest.fixture(scope="session", autouse=True)
def reset_test_data():
    """
    Reset mock API data files before test session
    This ensures clean state for tests
    """
    # Backup original data
    data_dir = "mock_api/data"
    backup_dir = "mock_api/data_backup"

    # Create backup if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        for file in ['swimmers.json', 'race_results.json', 'events.json']:
            src = os.path.join(data_dir, file)
            dst = os.path.join(backup_dir, file)
            if os.path.exists(src):
                shutil.copy(src, dst)

    # Restore from backup before tests
    for file in ['swimmers.json', 'race_results.json', 'events.json']:
        src = os.path.join(backup_dir, file)
        dst = os.path.join(data_dir, file)
        if os.path.exists(src):
            shutil.copy(src, dst)

    yield

    # Optionally restore after tests too
    for file in ['swimmers.json', 'race_results.json', 'events.json']:
        src = os.path.join(backup_dir, file)
        dst = os.path.join(data_dir, file)
        if os.path.exists(src):
            shutil.copy(src, dst)


@pytest.fixture(scope="function")
def api_base_url():
    """Base URL for API requests"""
    return "http://localhost:5001/api"