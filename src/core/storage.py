"""SQLite storage layer for Noisett history and favorites.

Phase 8: Persistent storage for user generation history and favorites.

Database Tables:
    generation_history: Stores completed generation jobs
    favorites: Stores user-favorited images

Environment Variables:
    NOISETT_DB_PATH: Path to SQLite database (default: ./noisett.db)
"""

import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

from src.core.types import (
    AssetType,
    Favorite,
    GenerationRecord,
    QualityPreset,
)

# Database configuration
DB_PATH = os.getenv("NOISETT_DB_PATH", "./noisett.db")


def get_db_path() -> str:
    """Get the database file path."""
    return DB_PATH


@contextmanager
def get_db_connection():
    """Context manager for database connections.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM history")
            rows = cursor.fetchall()
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    try:
        yield conn
        conn.commit()
    except Exception:
        logger.exception("Database operation failed, rolling back transaction")
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initialize the database schema.
    
    Creates tables if they don't exist. Safe to call multiple times.
    """
    with get_db_connection() as conn:
        # Generation history table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS generation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                prompt TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                quality TEXT,
                model TEXT,
                images TEXT,  -- JSON array of image URLs
                created_at TEXT NOT NULL,
                
                -- Indexes for common queries
                UNIQUE(job_id)
            )
        """)
        
        # Create index on user_id for history queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_user_id 
            ON generation_history(user_id)
        """)
        
        # Create index on created_at for ordering
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_created_at 
            ON generation_history(created_at DESC)
        """)
        
        # Favorites table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                job_id TEXT NOT NULL,
                image_index INTEGER NOT NULL,
                image_url TEXT NOT NULL,
                prompt TEXT,
                created_at TEXT NOT NULL,
                
                -- Prevent duplicate favorites
                UNIQUE(user_id, job_id, image_index)
            )
        """)
        
        # Create index on user_id for favorites queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_favorites_user_id 
            ON favorites(user_id)
        """)


# ============================================================================
# Generation History Operations
# ============================================================================

def save_generation(
    job_id: str,
    user_id: str,
    prompt: str,
    asset_type: AssetType,
    images: list[str],
    quality: QualityPreset | None = None,
    model: str | None = None,
    created_at: datetime | None = None,
) -> GenerationRecord:
    """Save a completed generation to history.
    
    Args:
        job_id: Unique job identifier
        user_id: User who created the generation
        prompt: Original prompt text
        asset_type: Type of asset generated
        images: List of generated image URLs
        quality: Quality preset used
        model: Model ID used
        created_at: Timestamp (defaults to now)
        
    Returns:
        GenerationRecord with saved data
    """
    if created_at is None:
        created_at = datetime.now(UTC)
    
    # Ensure database is initialized
    init_db()
    
    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO generation_history 
            (job_id, user_id, prompt, asset_type, quality, model, images, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            user_id,
            prompt,
            asset_type.value if isinstance(asset_type, AssetType) else asset_type,
            quality.value if quality and isinstance(quality, QualityPreset) else quality,
            model,
            json.dumps(images),
            created_at.isoformat(),
        ))
    
    return GenerationRecord(
        job_id=job_id,
        user_id=user_id,
        prompt=prompt,
        asset_type=asset_type,
        quality=quality,
        model=model,
        images=images,
        created_at=created_at,
    )


def get_generation(job_id: str, user_id: str | None = None) -> GenerationRecord | None:
    """Get a specific generation by job ID.
    
    Args:
        job_id: Job identifier
        user_id: If provided, verify ownership
        
    Returns:
        GenerationRecord if found, None otherwise
    """
    init_db()
    
    with get_db_connection() as conn:
        if user_id:
            row = conn.execute(
                "SELECT * FROM generation_history WHERE job_id = ? AND user_id = ?",
                (job_id, user_id)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM generation_history WHERE job_id = ?",
                (job_id,)
            ).fetchone()
    
    if not row:
        return None
    
    return _row_to_generation_record(row)


def list_generations(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[GenerationRecord], int]:
    """List generation history for a user.
    
    Args:
        user_id: User identifier
        limit: Maximum records to return
        offset: Number of records to skip
        
    Returns:
        Tuple of (list of records, total count)
    """
    init_db()
    
    with get_db_connection() as conn:
        # Get total count
        total = conn.execute(
            "SELECT COUNT(*) FROM generation_history WHERE user_id = ?",
            (user_id,)
        ).fetchone()[0]
        
        # Get paginated results
        rows = conn.execute("""
            SELECT * FROM generation_history 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (user_id, limit, offset)).fetchall()
    
    records = [_row_to_generation_record(row) for row in rows]
    return records, total


def delete_generation(job_id: str, user_id: str) -> bool:
    """Delete a generation from history.
    
    Args:
        job_id: Job identifier
        user_id: User identifier (must own the record)
        
    Returns:
        True if deleted, False if not found
    """
    init_db()
    
    with get_db_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM generation_history WHERE job_id = ? AND user_id = ?",
            (job_id, user_id)
        )
        return cursor.rowcount > 0


def _row_to_generation_record(row: sqlite3.Row) -> GenerationRecord:
    """Convert a database row to GenerationRecord."""
    return GenerationRecord(
        job_id=row["job_id"],
        user_id=row["user_id"],
        prompt=row["prompt"],
        asset_type=AssetType(row["asset_type"]),
        quality=QualityPreset(row["quality"]) if row["quality"] else None,
        model=row["model"],
        images=json.loads(row["images"]) if row["images"] else [],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


# ============================================================================
# Favorites Operations
# ============================================================================

def add_favorite(
    user_id: str,
    job_id: str,
    image_index: int,
    image_url: str,
    prompt: str | None = None,
) -> Favorite:
    """Add an image to favorites.
    
    Args:
        user_id: User identifier
        job_id: Job that generated the image
        image_index: Index of image in job results
        image_url: URL of the image
        prompt: Optional prompt that generated it
        
    Returns:
        Favorite object
        
    Raises:
        sqlite3.IntegrityError: If already favorited
    """
    init_db()
    created_at = datetime.now(UTC)
    
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO favorites 
            (user_id, job_id, image_index, image_url, prompt, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            job_id,
            image_index,
            image_url,
            prompt,
            created_at.isoformat(),
        ))
    
    return Favorite(
        user_id=user_id,
        job_id=job_id,
        image_index=image_index,
        image_url=image_url,
        prompt=prompt,
        created_at=created_at,
    )


def get_favorite(
    user_id: str,
    job_id: str,
    image_index: int,
) -> Favorite | None:
    """Get a specific favorite.
    
    Args:
        user_id: User identifier
        job_id: Job identifier
        image_index: Image index
        
    Returns:
        Favorite if found, None otherwise
    """
    init_db()
    
    with get_db_connection() as conn:
        row = conn.execute("""
            SELECT * FROM favorites 
            WHERE user_id = ? AND job_id = ? AND image_index = ?
        """, (user_id, job_id, image_index)).fetchone()
    
    if not row:
        return None
    
    return _row_to_favorite(row)


def list_favorites(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Favorite], int]:
    """List favorites for a user.
    
    Args:
        user_id: User identifier
        limit: Maximum records to return
        offset: Number of records to skip
        
    Returns:
        Tuple of (list of favorites, total count)
    """
    init_db()
    
    with get_db_connection() as conn:
        # Get total count
        total = conn.execute(
            "SELECT COUNT(*) FROM favorites WHERE user_id = ?",
            (user_id,)
        ).fetchone()[0]
        
        # Get paginated results
        rows = conn.execute("""
            SELECT * FROM favorites 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (user_id, limit, offset)).fetchall()
    
    favorites = [_row_to_favorite(row) for row in rows]
    return favorites, total


def remove_favorite(
    user_id: str,
    job_id: str,
    image_index: int,
) -> bool:
    """Remove an image from favorites.
    
    Args:
        user_id: User identifier
        job_id: Job identifier
        image_index: Image index
        
    Returns:
        True if removed, False if not found
    """
    init_db()
    
    with get_db_connection() as conn:
        cursor = conn.execute("""
            DELETE FROM favorites 
            WHERE user_id = ? AND job_id = ? AND image_index = ?
        """, (user_id, job_id, image_index))
        return cursor.rowcount > 0


def is_favorite(
    user_id: str,
    job_id: str,
    image_index: int,
) -> bool:
    """Check if an image is favorited.
    
    Args:
        user_id: User identifier
        job_id: Job identifier
        image_index: Image index
        
    Returns:
        True if favorited, False otherwise
    """
    init_db()
    
    with get_db_connection() as conn:
        row = conn.execute("""
            SELECT 1 FROM favorites 
            WHERE user_id = ? AND job_id = ? AND image_index = ?
        """, (user_id, job_id, image_index)).fetchone()
    
    return row is not None


def _row_to_favorite(row: sqlite3.Row) -> Favorite:
    """Convert a database row to Favorite."""
    return Favorite(
        user_id=row["user_id"],
        job_id=row["job_id"],
        image_index=row["image_index"],
        image_url=row["image_url"],
        prompt=row["prompt"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


# ============================================================================
# Database Utilities
# ============================================================================

def clear_user_data(user_id: str) -> dict:
    """Clear all data for a user (GDPR compliance).
    
    Args:
        user_id: User identifier
        
    Returns:
        Dict with counts of deleted records
    """
    init_db()
    
    with get_db_connection() as conn:
        history_count = conn.execute(
            "DELETE FROM generation_history WHERE user_id = ?",
            (user_id,)
        ).rowcount
        
        favorites_count = conn.execute(
            "DELETE FROM favorites WHERE user_id = ?",
            (user_id,)
        ).rowcount
    
    return {
        "history_deleted": history_count,
        "favorites_deleted": favorites_count,
    }


def get_stats(user_id: str) -> dict:
    """Get usage statistics for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Dict with usage statistics
    """
    init_db()
    
    with get_db_connection() as conn:
        # Total generations
        total_generations = conn.execute(
            "SELECT COUNT(*) FROM generation_history WHERE user_id = ?",
            (user_id,)
        ).fetchone()[0]
        
        # Total images generated
        rows = conn.execute(
            "SELECT images FROM generation_history WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        total_images = sum(len(json.loads(row[0] or "[]")) for row in rows)
        
        # Total favorites
        total_favorites = conn.execute(
            "SELECT COUNT(*) FROM favorites WHERE user_id = ?",
            (user_id,)
        ).fetchone()[0]
        
        # Most used asset type
        most_used = conn.execute("""
            SELECT asset_type, COUNT(*) as count 
            FROM generation_history 
            WHERE user_id = ?
            GROUP BY asset_type 
            ORDER BY count DESC 
            LIMIT 1
        """, (user_id,)).fetchone()
    
    return {
        "total_generations": total_generations,
        "total_images": total_images,
        "total_favorites": total_favorites,
        "most_used_asset_type": most_used[0] if most_used else None,
    }


# Initialize on import (creates tables if needed)
if os.path.exists(os.path.dirname(DB_PATH) or "."):
    init_db()


# Export for easy imports
__all__ = [
    "init_db",
    "get_db_connection",
    "get_db_path",
    # History operations
    "save_generation",
    "get_generation",
    "list_generations",
    "delete_generation",
    # Favorites operations
    "add_favorite",
    "get_favorite",
    "list_favorites",
    "remove_favorite",
    "is_favorite",
    # Utilities
    "clear_user_data",
    "get_stats",
]
