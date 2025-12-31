"""Job management commands.

Commands:
- job.status: Get the current status of a generation job
- job.cancel: Cancel a queued or in-progress job
- job.list: List recent generation jobs
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field

from src.core.errors import ErrorCode, get_error_template
from src.core.result import CommandResult, error, success
from src.core.types import Job, JobStatus


# --- Input/Output Schemas ---


class JobStatusInput(BaseModel):
    """Input for job.status command."""

    job_id: str = Field(..., description="Job ID to check")


class JobStatusOutput(BaseModel):
    """Output for job.status command."""

    job: Job


class JobCancelInput(BaseModel):
    """Input for job.cancel command."""

    job_id: str = Field(..., description="Job ID to cancel")


class JobCancelOutput(BaseModel):
    """Output for job.cancel command."""

    job: Job


class JobListInput(BaseModel):
    """Input for job.list command."""

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of jobs to return",
    )
    status_filter: Optional[JobStatus] = Field(
        default=None,
        description="Optional filter by status",
    )


class JobListOutput(BaseModel):
    """Output for job.list command."""

    jobs: List[Job]
    total: int


# --- Command Implementations ---


async def status(input: JobStatusInput) -> CommandResult[JobStatusOutput]:
    """Get the current status of a generation job.
    
    Returns job details including status, progress, and generated images.
    
    Args:
        input: Job ID to check
        
    Returns:
        CommandResult with job details
    """
    # Import here to avoid circular imports
    from src.commands.asset import get_job

    job = get_job(input.job_id)

    if not job:
        template = get_error_template(ErrorCode.JOB_NOT_FOUND)
        return error(
            code=ErrorCode.JOB_NOT_FOUND,
            message=f"Job '{input.job_id}' not found",
            suggestion=template["suggestion"],
        )

    output = JobStatusOutput(job=job)

    # Build status-specific reasoning
    if job.status == JobStatus.QUEUED:
        reasoning = f"Job is queued, waiting to start"
    elif job.status == JobStatus.PROCESSING:
        reasoning = f"Job is processing ({job.progress:.0f}% complete)"
    elif job.status == JobStatus.COMPLETE:
        reasoning = f"Job complete with {len(job.images)} images"
    elif job.status == JobStatus.FAILED:
        reasoning = f"Job failed: {job.error_message or 'Unknown error'}"
    elif job.status == JobStatus.CANCELLED:
        reasoning = "Job was cancelled"
    else:
        reasoning = f"Job status: {job.status.value}"

    return success(data=output, reasoning=reasoning)


async def cancel(input: JobCancelInput) -> CommandResult[JobCancelOutput]:
    """Cancel a queued or in-progress generation job.
    
    Jobs that are already complete or cancelled cannot be cancelled.
    
    Args:
        input: Job ID to cancel
        
    Returns:
        CommandResult with updated job status
    """
    from src.commands.asset import get_job, update_job

    job = get_job(input.job_id)

    if not job:
        template = get_error_template(ErrorCode.JOB_NOT_FOUND)
        return error(
            code=ErrorCode.JOB_NOT_FOUND,
            message=f"Job '{input.job_id}' not found",
            suggestion=template["suggestion"],
        )

    # Check if job can be cancelled
    if job.status == JobStatus.COMPLETE:
        template = get_error_template(ErrorCode.JOB_ALREADY_COMPLETE)
        return error(
            code=ErrorCode.JOB_ALREADY_COMPLETE,
            message=template["message"],
            suggestion=template["suggestion"],
        )

    if job.status == JobStatus.CANCELLED:
        template = get_error_template(ErrorCode.JOB_ALREADY_CANCELLED)
        return error(
            code=ErrorCode.JOB_ALREADY_CANCELLED,
            message=template["message"],
            suggestion=template["suggestion"],
        )

    if job.status == JobStatus.FAILED:
        return error(
            code="JOB_ALREADY_FAILED",
            message="Job has already failed",
            suggestion="Start a new generation instead",
        )

    # Cancel the job
    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.now(timezone.utc)
    update_job(job)

    output = JobCancelOutput(job=job)

    return success(
        data=output,
        reasoning=f"Job cancelled (was {job.progress:.0f}% complete)",
    )


async def list_jobs(input: JobListInput) -> CommandResult[JobListOutput]:
    """List recent generation jobs.
    
    Returns jobs sorted by creation time (newest first).
    Optionally filter by status.
    
    Args:
        input: Limit and optional status filter
        
    Returns:
        CommandResult with list of jobs
    """
    from src.commands.asset import list_all_jobs

    all_jobs = list_all_jobs()

    # Apply status filter if provided
    if input.status_filter:
        filtered_jobs = [j for j in all_jobs if j.status == input.status_filter]
    else:
        filtered_jobs = all_jobs

    # Apply limit
    limited_jobs = filtered_jobs[: input.limit]

    output = JobListOutput(jobs=limited_jobs, total=len(filtered_jobs))

    # Build reasoning
    if input.status_filter:
        reasoning = f"Found {len(filtered_jobs)} {input.status_filter.value} jobs"
    else:
        reasoning = f"Found {len(filtered_jobs)} jobs"

    if len(filtered_jobs) > input.limit:
        reasoning += f" (showing first {input.limit})"

    return success(data=output, reasoning=reasoning)
