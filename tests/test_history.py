"""Tests for history commands and storage.

Phase 8: Test history.list, history.get, history.delete commands
and the underlying SQLite storage layer.
"""

import pytest
from datetime import datetime

from src.core.storage import (
    init_db,
    save_generation,
    get_generation,
    list_generations,
    delete_generation,
    get_db_path,
)
from src.core.types import AssetType, QualityPreset
from src.commands.history import (
    history_list,
    history_get,
    history_delete,
    HistoryGetInput,
    HistoryDeleteInput,
    HistoryListInput,
)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Set up fresh database for each test."""
    # Initialize fresh database (conftest handles cleanup)
    init_db()
    yield


class TestStorageLayer:
    """Test SQLite storage operations."""
    
    def test_save_generation(self):
        """Test saving a generation record."""
        record = save_generation(
            job_id="job_test_001",
            user_id="user_123",
            prompt="Test prompt",
            asset_type=AssetType.PRODUCT,
            images=["https://example.com/img1.jpg"],
            quality=QualityPreset.STANDARD,
            model="hidream",
        )
        
        assert record.job_id == "job_test_001"
        assert record.user_id == "user_123"
        assert record.prompt == "Test prompt"
        assert record.asset_type == AssetType.PRODUCT
        assert len(record.images) == 1
    
    def test_get_generation(self):
        """Test retrieving a generation record."""
        # Save first
        save_generation(
            job_id="job_test_002",
            user_id="user_123",
            prompt="Test prompt",
            asset_type=AssetType.ICONS,
            images=["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
        )
        
        # Retrieve
        record = get_generation(job_id="job_test_002")
        
        assert record is not None
        assert record.job_id == "job_test_002"
        assert record.asset_type == AssetType.ICONS
        assert len(record.images) == 2
    
    def test_get_generation_with_user_id(self):
        """Test retrieving a generation with user ownership check."""
        save_generation(
            job_id="job_test_003",
            user_id="user_123",
            prompt="Test",
            asset_type=AssetType.PRODUCT,
            images=[],
        )
        
        # Same user can retrieve
        record = get_generation(job_id="job_test_003", user_id="user_123")
        assert record is not None
        
        # Different user cannot retrieve
        record = get_generation(job_id="job_test_003", user_id="other_user")
        assert record is None
    
    def test_list_generations(self):
        """Test listing generations with pagination."""
        # Save multiple generations
        for i in range(5):
            save_generation(
                job_id=f"job_list_{i}",
                user_id="user_list",
                prompt=f"Prompt {i}",
                asset_type=AssetType.PRODUCT,
                images=[],
            )
        
        # List all
        records, total = list_generations(user_id="user_list")
        assert total == 5
        assert len(records) == 5
        
        # List with limit
        records, total = list_generations(user_id="user_list", limit=2)
        assert total == 5
        assert len(records) == 2
        
        # List with offset
        records, total = list_generations(user_id="user_list", limit=2, offset=3)
        assert total == 5
        assert len(records) == 2
    
    def test_delete_generation(self):
        """Test deleting a generation record."""
        save_generation(
            job_id="job_delete",
            user_id="user_del",
            prompt="Delete me",
            asset_type=AssetType.PRODUCT,
            images=[],
        )
        
        # Delete
        deleted = delete_generation(job_id="job_delete", user_id="user_del")
        assert deleted is True
        
        # Verify deleted
        record = get_generation(job_id="job_delete")
        assert record is None
    
    def test_delete_generation_wrong_user(self):
        """Test that users can only delete their own records."""
        save_generation(
            job_id="job_protected",
            user_id="user_owner",
            prompt="Protected",
            asset_type=AssetType.PRODUCT,
            images=[],
        )
        
        # Wrong user cannot delete
        deleted = delete_generation(job_id="job_protected", user_id="other_user")
        assert deleted is False
        
        # Record still exists
        record = get_generation(job_id="job_protected")
        assert record is not None


class TestHistoryCommands:
    """Test history command implementations."""
    
    def test_history_list_empty(self):
        """Test listing history when empty."""
        result = history_list(user_id="empty_user")
        
        assert result.success is True
        assert result.data.total_count == 0
        assert len(result.data.generations) == 0
        assert result.data.has_more is False
    
    def test_history_list_with_data(self):
        """Test listing history with records."""
        # Add some test data
        for i in range(3):
            save_generation(
                job_id=f"job_cmd_{i}",
                user_id="cmd_user",
                prompt=f"Command test {i}",
                asset_type=AssetType.ICONS,
                images=[f"https://example.com/img{i}.jpg"],
            )
        
        result = history_list(user_id="cmd_user")
        
        assert result.success is True
        assert result.data.total_count == 3
        assert len(result.data.generations) == 3
    
    def test_history_list_pagination(self):
        """Test history pagination."""
        for i in range(10):
            save_generation(
                job_id=f"job_page_{i}",
                user_id="page_user",
                prompt=f"Page test {i}",
                asset_type=AssetType.PRODUCT,
                images=[],
            )
        
        # First page
        input_data = HistoryListInput(limit=3, offset=0)
        result = history_list(user_id="page_user", input_data=input_data)
        
        assert result.success is True
        assert len(result.data.generations) == 3
        assert result.data.total_count == 10
        assert result.data.has_more is True
        
        # Last page
        input_data = HistoryListInput(limit=3, offset=9)
        result = history_list(user_id="page_user", input_data=input_data)
        
        assert result.success is True
        assert len(result.data.generations) == 1
        assert result.data.has_more is False
    
    def test_history_get_success(self):
        """Test getting a specific history record."""
        save_generation(
            job_id="job_get_test",
            user_id="get_user",
            prompt="Get this record",
            asset_type=AssetType.LOGO,
            images=["https://example.com/logo.png"],
            quality=QualityPreset.HIGH,
        )
        
        input_data = HistoryGetInput(job_id="job_get_test")
        result = history_get(user_id="get_user", input_data=input_data)
        
        assert result.success is True
        assert result.data.job_id == "job_get_test"
        assert result.data.prompt == "Get this record"
        assert result.data.asset_type == AssetType.LOGO
    
    def test_history_get_not_found(self):
        """Test getting a non-existent record."""
        input_data = HistoryGetInput(job_id="nonexistent")
        result = history_get(user_id="some_user", input_data=input_data)
        
        assert result.success is False
        assert result.error.code == "HISTORY_NOT_FOUND"
    
    def test_history_delete_success(self):
        """Test deleting a history record."""
        save_generation(
            job_id="job_to_delete",
            user_id="del_user",
            prompt="Delete me",
            asset_type=AssetType.PRODUCT,
            images=[],
        )
        
        input_data = HistoryDeleteInput(job_id="job_to_delete")
        result = history_delete(user_id="del_user", input_data=input_data)
        
        assert result.success is True
        assert result.data.deleted is True
        assert result.data.job_id == "job_to_delete"
    
    def test_history_delete_not_found(self):
        """Test deleting a non-existent record."""
        input_data = HistoryDeleteInput(job_id="nonexistent")
        result = history_delete(user_id="some_user", input_data=input_data)
        
        assert result.success is False
        assert result.error.code == "HISTORY_NOT_FOUND"
