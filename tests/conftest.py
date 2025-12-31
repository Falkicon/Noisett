"""Test configuration for Noisett.

This conftest sets up isolated test databases for each test run.
"""

import os
import tempfile

import pytest

# Set test database paths BEFORE any imports touch storage
TEST_DB_DIR = tempfile.mkdtemp(prefix="noisett_test_")
os.environ["NOISETT_DB_PATH"] = os.path.join(TEST_DB_DIR, "test.db")


@pytest.fixture(autouse=True, scope="function")
def clean_db():
    """Reset database state before each test."""
    db_path = os.environ.get("NOISETT_DB_PATH")
    
    # Remove existing database before test
    if db_path and os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass  # File in use, will be overwritten
    
    yield
    
    # Cleanup after test
    if db_path and os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass


@pytest.fixture(autouse=True, scope="session")
def cleanup_test_dir():
    """Cleanup test directory after all tests."""
    yield
    
    # Try to remove test directory
    import shutil
    try:
        shutil.rmtree(TEST_DB_DIR, ignore_errors=True)
    except Exception:
        pass
