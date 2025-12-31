"""Noisett CLI - Command-line interface for AFD validation.

This CLI is the primary interface for testing commands before
any UI implementation, following Agent-First Development principles.

Usage:
    noisett <command> '<json_input>'
    noisett asset.generate '{"prompt": "cloud computing concept"}'
    noisett job.status '{"job_id": "abc-123"}'
    noisett model.list '{}'
"""

import asyncio
import json
import sys
from typing import Any, Callable, Coroutine

import click
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel

# Import commands
from src.commands.asset import (
    AssetGenerateInput,
    generate as asset_generate,
    types as asset_types,
)
from src.commands.job import (
    JobCancelInput,
    JobListInput,
    JobStatusInput,
    cancel as job_cancel,
    list_jobs as job_list,
    status as job_status,
)
from src.commands.lora import (
    CreateLoraInput,
    LoraActivateInput,
    LoraDeleteInput,
    LoraListInput,
    LoraStatusInput,
    TrainLoraInput,
    UploadImagesInput,
    activate as lora_activate,
    create as lora_create,
    delete as lora_delete,
    list_loras as lora_list,
    status as lora_status,
    train as lora_train,
    upload_images as lora_upload_images,
)
from src.commands.model import (
    ModelInfoInput,
    info as model_info,
    list_models as model_list,
)
from src.commands.quality import (
    PostProcessInput,
    QualityPresetsInput,
    RefineInput,
    UpscaleInput,
    VariationsInput,
    presets as quality_presets,
    refine as quality_refine,
    upscale as quality_upscale,
    variations as quality_variations,
    post_process as quality_post_process,
)
from src.commands.history import (
    HistoryGetInput,
    HistoryDeleteInput,
    HistoryListInput,
    history_list,
    history_get,
    history_delete,
)
from src.commands.favorites import (
    FavoritesAddInput,
    FavoritesListInput,
    FavoritesRemoveInput,
    favorites_add,
    favorites_list,
    favorites_remove,
)
from src.core.result import CommandResult
from src.core.auth import get_anonymous_user_id


# CLI user ID for local testing (in production, JWT provides user_id)
CLI_USER_ID = get_anonymous_user_id()


# ============================================================================
# Wrapper functions for commands that require user_id
# ============================================================================

async def cli_history_list(input_data: HistoryListInput | None = None) -> CommandResult:
    """CLI wrapper for history.list that provides user_id."""
    return history_list(user_id=CLI_USER_ID, input_data=input_data)


async def cli_history_get(input_data: HistoryGetInput) -> CommandResult:
    """CLI wrapper for history.get that provides user_id."""
    return history_get(user_id=CLI_USER_ID, input_data=input_data)


async def cli_history_delete(input_data: HistoryDeleteInput) -> CommandResult:
    """CLI wrapper for history.delete that provides user_id."""
    return history_delete(user_id=CLI_USER_ID, input_data=input_data)


async def cli_favorites_add(input_data: FavoritesAddInput) -> CommandResult:
    """CLI wrapper for favorites.add that provides user_id."""
    return favorites_add(user_id=CLI_USER_ID, input_data=input_data)


async def cli_favorites_list(input_data: FavoritesListInput | None = None) -> CommandResult:
    """CLI wrapper for favorites.list that provides user_id."""
    return favorites_list(user_id=CLI_USER_ID, input_data=input_data)


async def cli_favorites_remove(input_data: FavoritesRemoveInput) -> CommandResult:
    """CLI wrapper for favorites.remove that provides user_id."""
    return favorites_remove(user_id=CLI_USER_ID, input_data=input_data)

console = Console()

# Command registry mapping command names to handlers
COMMANDS: dict[str, tuple[Callable, type | None]] = {
    "asset.generate": (asset_generate, AssetGenerateInput),
    "asset.types": (asset_types, None),
    "job.status": (job_status, JobStatusInput),
    "job.cancel": (job_cancel, JobCancelInput),
    "job.list": (job_list, JobListInput),
    "model.list": (model_list, None),
    "model.info": (model_info, ModelInfoInput),
    # LoRA training commands (Phase 5)
    "lora.create": (lora_create, CreateLoraInput),
    "lora.upload-images": (lora_upload_images, UploadImagesInput),
    "lora.train": (lora_train, TrainLoraInput),
    "lora.status": (lora_status, LoraStatusInput),
    "lora.list": (lora_list, LoraListInput),
    "lora.activate": (lora_activate, LoraActivateInput),
    "lora.delete": (lora_delete, LoraDeleteInput),
    # Quality pipeline commands (Phase 6)
    "quality.presets": (quality_presets, QualityPresetsInput),
    "refine": (quality_refine, RefineInput),
    "upscale": (quality_upscale, UpscaleInput),
    "variations": (quality_variations, VariationsInput),
    "post-process": (quality_post_process, PostProcessInput),
    # History commands (Phase 8)
    "history.list": (cli_history_list, HistoryListInput),
    "history.get": (cli_history_get, HistoryGetInput),
    "history.delete": (cli_history_delete, HistoryDeleteInput),
    # Favorites commands (Phase 8)
    "favorites.add": (cli_favorites_add, FavoritesAddInput),
    "favorites.list": (cli_favorites_list, FavoritesListInput),
    "favorites.remove": (cli_favorites_remove, FavoritesRemoveInput),
}


def print_result(result: CommandResult) -> None:
    """Print a CommandResult with rich formatting."""
    # Convert to dict for JSON output
    result_dict = result.model_dump(exclude_none=True, mode="json")
    
    # Determine style based on success
    if result.success:
        title = "✓ Success"
        border_style = "green"
    else:
        title = "✗ Error"
        border_style = "red"
    
    # Print formatted JSON
    panel = Panel(
        JSON.from_data(result_dict),
        title=title,
        border_style=border_style,
    )
    console.print(panel)


async def run_command(command_name: str, input_json: str) -> CommandResult:
    """Run a command with JSON input."""
    if command_name not in COMMANDS:
        from src.core.result import error
        return error(
            code="COMMAND_NOT_FOUND",
            message=f"Unknown command: {command_name}",
            suggestion=f"Available commands: {', '.join(COMMANDS.keys())}",
        )
    
    handler, input_class = COMMANDS[command_name]
    
    try:
        # Parse JSON input
        input_data = json.loads(input_json) if input_json else {}
        
        # Validate and create input object if schema exists
        if input_class:
            validated_input = input_class(**input_data)
            result = await handler(validated_input)
        else:
            result = await handler()
        
        return result
        
    except json.JSONDecodeError as e:
        from src.core.result import error
        return error(
            code="INVALID_JSON",
            message=f"Invalid JSON input: {e}",
            suggestion="Ensure input is valid JSON, e.g., '{\"key\": \"value\"}'",
        )
    except Exception as e:
        from src.core.result import error
        return error(
            code="VALIDATION_ERROR",
            message=str(e),
            suggestion="Check the command schema with 'noisett schema <command>'",
        )


@click.group(invoke_without_command=True)
@click.pass_context
@click.argument("command_name", required=False)
@click.argument("input_json", required=False, default="{}")
def main(ctx: click.Context, command_name: str | None, input_json: str) -> None:
    """Noisett CLI - AI Brand Asset Generator.
    
    Run commands with JSON input:
    
        noisett asset.generate '{"prompt": "cloud computing concept"}'
        
        noisett job.status '{"job_id": "abc-123"}'
        
        noisett model.list '{}'
    
    List available commands:
    
        noisett commands
    """
    if ctx.invoked_subcommand is not None:
        return
        
    if command_name is None:
        # Show help if no command provided
        click.echo(ctx.get_help())
        return
    
    # Special command: list all commands
    if command_name == "commands":
        console.print("\n[bold]Available Commands[/bold]\n")
        for name in sorted(COMMANDS.keys()):
            console.print(f"  • {name}")
        console.print()
        return
    
    # Run the command
    result = asyncio.run(run_command(command_name, input_json))
    print_result(result)
    
    # Exit with error code if command failed
    if not result.success:
        sys.exit(1)


@main.command()
@click.argument("command_name")
def schema(command_name: str) -> None:
    """Show the JSON schema for a command's input."""
    if command_name not in COMMANDS:
        console.print(f"[red]Unknown command: {command_name}[/red]")
        console.print(f"Available: {', '.join(COMMANDS.keys())}")
        sys.exit(1)
    
    _, input_class = COMMANDS[command_name]
    
    if input_class is None:
        console.print(f"[yellow]{command_name}[/yellow] takes no input parameters")
        return
    
    # Get JSON schema from Pydantic model
    schema_dict = input_class.model_json_schema()
    
    panel = Panel(
        JSON.from_data(schema_dict),
        title=f"Schema: {command_name}",
        border_style="blue",
    )
    console.print(panel)


@main.command()
def doctor() -> None:
    """Check system health and dependencies."""
    console.print("\n[bold]Noisett System Check[/bold]\n")
    
    checks = []
    
    # Check Python version
    import sys
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 11)
    checks.append(("Python ≥3.11", py_ok, py_version))
    
    # Check required packages
    packages = [
        ("pydantic", "Pydantic"),
        ("click", "Click"),
        ("rich", "Rich"),
    ]
    
    for pkg_name, display_name in packages:
        try:
            pkg = __import__(pkg_name)
            version = getattr(pkg, "__version__", "unknown")
            checks.append((display_name, True, version))
        except ImportError:
            checks.append((display_name, False, "not installed"))
    
    # Check optional ML packages
    ml_packages = [
        ("torch", "PyTorch"),
        ("diffusers", "Diffusers"),
    ]
    
    console.print("[bold]Core Dependencies[/bold]")
    for name, ok, version in checks:
        status = "[green]✓[/green]" if ok else "[red]✗[/red]"
        console.print(f"  {status} {name}: {version}")
    
    console.print("\n[bold]ML Dependencies (optional)[/bold]")
    for pkg_name, display_name in ml_packages:
        try:
            pkg = __import__(pkg_name)
            version = getattr(pkg, "__version__", "unknown")
            console.print(f"  [green]✓[/green] {display_name}: {version}")
        except ImportError:
            console.print(f"  [yellow]○[/yellow] {display_name}: not installed")
    
    console.print()


if __name__ == "__main__":
    main()
