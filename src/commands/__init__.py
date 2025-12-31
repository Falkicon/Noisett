"""Noisett commands package.

All commands follow the AFD (Agent-First Development) pattern:
1. Commands are defined with Pydantic schemas
2. Commands are validated via CLI before UI implementation
3. Commands return CommandResult with UX-enabling metadata
"""

from src.commands.asset import generate as asset_generate
from src.commands.asset import types as asset_types
from src.commands.job import status as job_status
from src.commands.job import cancel as job_cancel
from src.commands.job import list_jobs as job_list
from src.commands.model import list_models as model_list
from src.commands.model import info as model_info

__all__ = [
    # Asset commands
    "asset_generate",
    "asset_types",
    # Job commands
    "job_status",
    "job_cancel",
    "job_list",
    # Model commands
    "model_list",
    "model_info",
]
