"""Noisett server package."""

from src.server.mcp import mcp
from src.server.api import app

__all__ = ["mcp", "app"]
