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
from src.commands.lora import activate as lora_activate
from src.commands.lora import create as lora_create
from src.commands.lora import delete as lora_delete
from src.commands.lora import list_loras as lora_list
from src.commands.lora import status as lora_status
from src.commands.lora import train as lora_train
from src.commands.lora import upload_images as lora_upload_images
from src.commands.model import list_models as model_list
from src.commands.model import info as model_info
from src.commands.quality import presets as quality_presets
from src.commands.quality import refine as quality_refine
from src.commands.quality import upscale as quality_upscale
from src.commands.quality import variations as quality_variations
from src.commands.quality import post_process as quality_post_process
from src.commands.history import history_list, history_get, history_delete
from src.commands.favorites import favorites_add, favorites_list, favorites_remove

__all__ = [
    # Asset commands
    "asset_generate",
    "asset_types",
    # Job commands
    "job_status",
    "job_cancel",
    "job_list",
    # LoRA training commands (Phase 5)
    "lora_create",
    "lora_upload_images",
    "lora_train",
    "lora_status",
    "lora_list",
    "lora_activate",
    "lora_delete",
    # Quality pipeline commands (Phase 6)
    "quality_presets",
    "quality_refine",
    "quality_upscale",
    "quality_variations",
    "quality_post_process",
    # History commands (Phase 8)
    "history_list",
    "history_get",
    "history_delete",
    # Favorites commands (Phase 8)
    "favorites_add",
    "favorites_list",
    "favorites_remove",
    # Model commands
    "model_list",
    "model_info",
]
