"""Tests for REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.server.api import app


@pytest.fixture
def client():
    """Create test client for API."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self, client):
        """Health endpoint returns status (healthy or degraded in mock mode)."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert data["service"] == "noisett-api"


class TestGenerateEndpoint:
    """Tests for POST /api/generate endpoint."""

    def test_generate_success(self, client):
        """Generate endpoint accepts valid request."""
        response = client.post("/api/generate", json={
            "prompt": "A robot waving hello",
            "asset_type": "product",
            "quality": "standard",
            "count": 2,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "job" in data["data"]
        assert "id" in data["data"]["job"]

    def test_generate_empty_prompt(self, client):
        """Generate endpoint rejects empty prompt."""
        response = client.post("/api/generate", json={
            "prompt": "",
        })
        assert response.status_code == 422  # Validation error

    def test_generate_missing_prompt(self, client):
        """Generate endpoint requires prompt field."""
        response = client.post("/api/generate", json={})
        assert response.status_code == 422

    def test_generate_with_defaults(self, client):
        """Generate endpoint uses defaults for optional fields."""
        response = client.post("/api/generate", json={
            "prompt": "A simple test image",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAssetTypesEndpoint:
    """Tests for GET /api/asset-types endpoint."""

    def test_asset_types_returns_list(self, client):
        """Asset types endpoint returns available types."""
        response = client.get("/api/asset-types")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "types" in data["data"]
        assert len(data["data"]["types"]) > 0


class TestJobStatusEndpoint:
    """Tests for GET /api/jobs/{job_id} endpoint."""

    def test_job_status_not_found(self, client):
        """Job status returns 404 for unknown job."""
        response = client.get("/api/jobs/unknown-job-id")
        assert response.status_code == 404

    def test_job_status_after_generate(self, client):
        """Job status works for generated job."""
        # First create a job
        gen_response = client.post("/api/generate", json={
            "prompt": "Test image for status check",
        })
        assert gen_response.status_code == 200
        job_id = gen_response.json()["data"]["job"]["id"]
        
        # Then check its status
        status_response = client.get(f"/api/jobs/{job_id}")
        assert status_response.status_code == 200
        data = status_response.json()
        assert data["success"] is True


class TestCancelJobEndpoint:
    """Tests for DELETE /api/jobs/{job_id} endpoint."""

    def test_cancel_unknown_job(self, client):
        """Cancel returns 404 for unknown job."""
        response = client.delete("/api/jobs/unknown-job-id")
        assert response.status_code == 404


class TestListJobsEndpoint:
    """Tests for GET /api/jobs endpoint."""

    def test_list_jobs_returns_list(self, client):
        """List jobs endpoint returns job list."""
        response = client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "jobs" in data["data"]

    def test_list_jobs_with_limit(self, client):
        """List jobs respects limit parameter."""
        response = client.get("/api/jobs?limit=5")
        assert response.status_code == 200


class TestModelsEndpoint:
    """Tests for GET /api/models endpoint."""

    def test_models_returns_list(self, client):
        """Models endpoint returns available models."""
        response = client.get("/api/models")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "models" in data["data"]
        assert len(data["data"]["models"]) > 0

    def test_model_info_hidream(self, client):
        """Model info returns details for hidream."""
        response = client.get("/api/models/hidream")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["model"]["id"] == "hidream"

    def test_model_info_invalid(self, client):
        """Model info returns 400 for invalid model."""
        response = client.get("/api/models/invalid-model")
        assert response.status_code == 400
