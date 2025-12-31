"""Tests for job commands."""

import pytest
from src.commands.asset import AssetGenerateInput, generate
from src.commands.job import (
    JobCancelInput,
    JobListInput,
    JobStatusInput,
    cancel,
    list_jobs,
    status,
)
from src.core.types import AssetType, JobStatus


@pytest.fixture
async def created_job():
    """Create a job for testing."""
    input_data = AssetGenerateInput(
        prompt="Test job for status checks",
        asset_type=AssetType.PRODUCT,
    )
    result = await generate(input_data)
    return result.data.job


@pytest.mark.asyncio
async def test_job_status_success(created_job):
    """Test getting job status."""
    input_data = JobStatusInput(job_id=created_job.id)
    
    result = await status(input_data)
    
    assert result.success is True
    assert result.data is not None
    assert result.data.job.id == created_job.id
    assert result.reasoning is not None


@pytest.mark.asyncio
async def test_job_status_not_found():
    """Test status for non-existent job."""
    input_data = JobStatusInput(job_id="non-existent-job-id")
    
    result = await status(input_data)
    
    assert result.success is False
    assert result.error is not None
    assert result.error.code == "JOB_NOT_FOUND"


@pytest.mark.asyncio
async def test_job_cancel_success(created_job):
    """Test cancelling a queued job."""
    input_data = JobCancelInput(job_id=created_job.id)
    
    result = await cancel(input_data)
    
    assert result.success is True
    assert result.data is not None
    assert result.data.job.status == JobStatus.CANCELLED


@pytest.mark.asyncio
async def test_job_cancel_already_cancelled(created_job):
    """Test cancelling an already cancelled job."""
    # First cancel
    await cancel(JobCancelInput(job_id=created_job.id))
    
    # Try to cancel again
    result = await cancel(JobCancelInput(job_id=created_job.id))
    
    assert result.success is False
    assert result.error is not None
    assert result.error.code == "JOB_ALREADY_CANCELLED"


@pytest.mark.asyncio
async def test_job_list_success():
    """Test listing jobs."""
    # Create a few jobs first
    for i in range(3):
        await generate(
            AssetGenerateInput(
                prompt=f"Test job {i}",
                asset_type=AssetType.PRODUCT,
            )
        )
    
    input_data = JobListInput(limit=10)
    result = await list_jobs(input_data)
    
    assert result.success is True
    assert result.data is not None
    assert len(result.data.jobs) >= 3


@pytest.mark.asyncio
async def test_job_list_with_filter():
    """Test listing jobs with status filter."""
    input_data = JobListInput(limit=10, status_filter=JobStatus.QUEUED)
    result = await list_jobs(input_data)
    
    assert result.success is True
    assert result.data is not None
    # All returned jobs should be queued
    for job in result.data.jobs:
        assert job.status == JobStatus.QUEUED
