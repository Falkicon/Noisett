"""Tests for favorites commands and storage.

Phase 8: Test favorites.add, favorites.list, favorites.remove commands
and the underlying SQLite storage layer.
"""

import pytest

from src.core.storage import (
    init_db,
    add_favorite,
    get_favorite,
    list_favorites,
    remove_favorite,
    is_favorite,
)
from src.commands.favorites import (
    favorites_add,
    favorites_list,
    favorites_remove,
    FavoritesAddInput,
    FavoritesListInput,
    FavoritesRemoveInput,
)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Set up fresh database for each test."""
    # Initialize fresh database (conftest handles cleanup)
    init_db()
    yield


class TestFavoritesStorage:
    """Test SQLite favorites storage operations."""
    
    def test_add_favorite(self):
        """Test adding a favorite."""
        favorite = add_favorite(
            user_id="user_fav",
            job_id="job_001",
            image_index=0,
            image_url="https://example.com/img.jpg",
            prompt="Test prompt",
        )
        
        assert favorite.user_id == "user_fav"
        assert favorite.job_id == "job_001"
        assert favorite.image_index == 0
        assert favorite.image_url == "https://example.com/img.jpg"
        assert favorite.prompt == "Test prompt"
    
    def test_add_duplicate_favorite(self):
        """Test that duplicate favorites raise an error."""
        add_favorite(
            user_id="user_dup",
            job_id="job_dup",
            image_index=0,
            image_url="https://example.com/img.jpg",
            prompt="Test",
        )
        
        # Adding same favorite again should raise IntegrityError
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError):
            add_favorite(
                user_id="user_dup",
                job_id="job_dup",
                image_index=0,
                image_url="https://example.com/img.jpg",
                prompt="Test",
            )
    
    def test_get_favorite(self):
        """Test retrieving a favorite."""
        add_favorite(
            user_id="user_get",
            job_id="job_get",
            image_index=1,
            image_url="https://example.com/get.jpg",
            prompt="Get test",
        )
        
        favorite = get_favorite(
            user_id="user_get",
            job_id="job_get",
            image_index=1,
        )
        
        assert favorite is not None
        assert favorite.job_id == "job_get"
        assert favorite.image_index == 1
    
    def test_get_favorite_not_found(self):
        """Test getting a non-existent favorite."""
        favorite = get_favorite(
            user_id="nobody",
            job_id="nothing",
            image_index=0,
        )
        
        assert favorite is None
    
    def test_list_favorites(self):
        """Test listing favorites with pagination."""
        # Add multiple favorites
        for i in range(5):
            add_favorite(
                user_id="user_list",
                job_id=f"job_{i}",
                image_index=0,
                image_url=f"https://example.com/img{i}.jpg",
                prompt=f"Test {i}",
            )
        
        # List all
        favorites, total = list_favorites(user_id="user_list")
        assert total == 5
        assert len(favorites) == 5
        
        # List with limit
        favorites, total = list_favorites(user_id="user_list", limit=2)
        assert total == 5
        assert len(favorites) == 2
        
        # List with offset
        favorites, total = list_favorites(user_id="user_list", limit=2, offset=4)
        assert total == 5
        assert len(favorites) == 1
    
    def test_remove_favorite(self):
        """Test removing a favorite."""
        add_favorite(
            user_id="user_rem",
            job_id="job_rem",
            image_index=0,
            image_url="https://example.com/rem.jpg",
            prompt="Remove test",
        )
        
        # Remove
        removed = remove_favorite(
            user_id="user_rem",
            job_id="job_rem",
            image_index=0,
        )
        assert removed is True
        
        # Verify removed
        favorite = get_favorite(
            user_id="user_rem",
            job_id="job_rem",
            image_index=0,
        )
        assert favorite is None
    
    def test_remove_favorite_not_found(self):
        """Test removing a non-existent favorite."""
        removed = remove_favorite(
            user_id="nobody",
            job_id="nothing",
            image_index=0,
        )
        assert removed is False
    
    def test_is_favorite(self):
        """Test checking if image is favorited."""
        add_favorite(
            user_id="user_check",
            job_id="job_check",
            image_index=2,
            image_url="https://example.com/check.jpg",
            prompt="Check test",
        )
        
        # Is favorited
        assert is_favorite(user_id="user_check", job_id="job_check", image_index=2) is True
        
        # Not favorited
        assert is_favorite(user_id="user_check", job_id="job_check", image_index=0) is False
        assert is_favorite(user_id="other_user", job_id="job_check", image_index=2) is False


class TestFavoritesCommands:
    """Test favorites command implementations."""
    
    def test_favorites_add_success(self):
        """Test adding a favorite via command."""
        input_data = FavoritesAddInput(
            job_id="job_cmd_add",
            image_index=0,
            image_url="https://example.com/add.jpg",
            prompt="Test add",
        )
        
        result = favorites_add(user_id="cmd_user", input_data=input_data)
        
        assert result.success is True
        assert result.data.job_id == "job_cmd_add"
        assert result.data.image_index == 0
    
    def test_favorites_add_duplicate(self):
        """Test adding a duplicate favorite."""
        input_data = FavoritesAddInput(
            job_id="job_dup_cmd",
            image_index=0,
            image_url="https://example.com/dup.jpg",
            prompt="Dup test",
        )
        
        # First add succeeds
        result = favorites_add(user_id="dup_user", input_data=input_data)
        assert result.success is True
        
        # Second add fails
        result = favorites_add(user_id="dup_user", input_data=input_data)
        assert result.success is False
        assert result.error.code == "FAVORITE_ALREADY_EXISTS"
    
    def test_favorites_list_empty(self):
        """Test listing favorites when empty."""
        result = favorites_list(user_id="empty_fav_user")
        
        assert result.success is True
        assert result.data.total_count == 0
        assert len(result.data.favorites) == 0
    
    def test_favorites_list_with_data(self):
        """Test listing favorites with data."""
        # Add test favorites
        for i in range(3):
            add_favorite(
                user_id="list_fav_user",
                job_id=f"job_list_{i}",
                image_index=0,
                image_url=f"https://example.com/list{i}.jpg",
                prompt=f"List test {i}",
            )
        
        result = favorites_list(user_id="list_fav_user")
        
        assert result.success is True
        assert result.data.total_count == 3
        assert len(result.data.favorites) == 3
    
    def test_favorites_list_pagination(self):
        """Test favorites pagination."""
        for i in range(10):
            add_favorite(
                user_id="page_fav_user",
                job_id=f"job_page_{i}",
                image_index=0,
                image_url=f"https://example.com/page{i}.jpg",
                prompt=f"Page test {i}",
            )
        
        # First page
        input_data = FavoritesListInput(limit=3, offset=0)
        result = favorites_list(user_id="page_fav_user", input_data=input_data)
        
        assert result.success is True
        assert len(result.data.favorites) == 3
        assert result.data.total_count == 10
    
    def test_favorites_remove_success(self):
        """Test removing a favorite via command."""
        # Add a favorite
        add_favorite(
            user_id="rem_cmd_user",
            job_id="job_rem_cmd",
            image_index=1,
            image_url="https://example.com/rem.jpg",
            prompt="Remove cmd test",
        )
        
        input_data = FavoritesRemoveInput(job_id="job_rem_cmd", image_index=1)
        result = favorites_remove(user_id="rem_cmd_user", input_data=input_data)
        
        assert result.success is True
        assert result.data.removed is True
        assert result.data.job_id == "job_rem_cmd"
        assert result.data.image_index == 1
    
    def test_favorites_remove_not_found(self):
        """Test removing a non-existent favorite."""
        input_data = FavoritesRemoveInput(job_id="nonexistent", image_index=0)
        result = favorites_remove(user_id="some_user", input_data=input_data)
        
        assert result.success is False
        assert result.error.code == "FAVORITE_NOT_FOUND"
