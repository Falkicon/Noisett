# API Specification

**Status:** Reference

**Base URL:** [`https://brand-assets-api.{domain}.com/api/v1`](https://brand-assets-api.{domain}.com/api/v1)

---

## Authentication

All endpoints require a valid Azure AD access token.

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOi...
```

---

## Endpoints

### Health Check

### `GET /health`

Check API availability. No authentication required.

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "gpu_available": true
}
```

---

### Generation

### `POST /generate`

Submit a new image generation request.

**Request:**

```json
{
  "prompt": "A person collaborating with AI on a creative project",
  "asset_type": "product",
  "model": "hidream",
  "quality": "standard",
  "count": 4
}
```

**Request Schema:**

| Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `prompt` | string | Yes | — | Image description, 1-500 chars |
| `asset_type` | enum | No | `product` | `icons`, `product`, `logo`, `premium` |
| `model` | enum | No | `hidream` | `hidream`, `flux`, `sd35` (v2.0+) |
| `quality` | enum | No | `standard` | `draft`, `standard`, `high`, `ultra` (v2.1+) |
| `count` | integer | No | `4` | Number of variations (1-4) |

**Response (202 Accepted):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "created_at": "2026-01-15T10:30:00Z",
  "estimated_seconds": 30
}
```

**Error Responses:**

| Code | Condition |
| --- | --- |
| 400 | Invalid prompt (too long, empty) |
| 401 | Missing or invalid token |
| 403 | User not authorized |
| 429 | Rate limit exceeded |
| 503 | GPU unavailable / queue full |

---

### Job Status

### `GET /jobs/{job_id}`

Get the status and results of a generation job.

**Response (Processing):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 65,
  "created_at": "2026-01-15T10:30:00Z",
  "started_at": "2026-01-15T10:30:02Z"
}
```

**Response (Complete):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "complete",
  "progress": 100,
  "created_at": "2026-01-15T10:30:00Z",
  "completed_at": "2026-01-15T10:30:32Z",
  "prompt": "A person collaborating with AI...",
  "images": [
    {
      "index": 0,
      "url": "[https://storage.blob.core.windows.net/](https://storage.blob.core.windows.net/)...",
      "width": 1024,
      "height": 1024
    },
    { "index": 1, "url": "...", "width": 1024, "height": 1024 },
    { "index": 2, "url": "...", "width": 1024, "height": 1024 },
    { "index": 3, "url": "...", "width": 1024, "height": 1024 }
  ]
}
```

**Job Status Values:**

| Status | Description |
| --- | --- |
| `queued` | Job is waiting in queue |
| `processing` | Generation in progress |
| `complete` | Success, images available |
| `failed` | Generation failed |
| `cancelled` | Job was cancelled |

---

### `DELETE /jobs/{job_id}`

Cancel a queued or processing job.

**Response (200 OK):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled"
}
```

---

### Image Download

### `GET /jobs/{job_id}/images/{index}`

Redirect to Blob Storage URL for download.

**Response (302 Found):**

```
Location: [https://storage.blob.core.windows.net/](https://storage.blob.core.windows.net/)...
```

---

### History (v2.1+)

### `GET /history`

Get user's generation history.

**Query Parameters:**

| Parameter | Type | Default |
| --- | --- | --- |
| `limit` | integer | 20 |
| `offset` | integer | 0 |
| `search` | string | — |

---

### Favorites (v2.1+)

### `POST /favorites`

Add image to favorites.

### `GET /favorites`

Get all favorites.

### `DELETE /favorites/{id}`

Remove favorite.

---

### Models (v2.0+)

### `GET /models`

Get available models.

**Response:**

```json
{
  "models": [
    {
      "id": "hidream",
      "name": "HiDream-I1",
      "license": "apache-2.0",
      "commercial_ok": true,
      "available": true
    },
    {
      "id": "flux",
      "name": "FLUX.1-dev",
      "license": "flux-dev",
      "commercial_ok": false,
      "available": true
    }
  ]
}
```

---

## Rate Limiting

| Endpoint | Limit | Window |
| --- | --- | --- |
| POST /generate | 10 requests | 1 minute |
| GET /jobs/{id} | 60 requests | 1 minute |
| All other | 100 requests | 1 minute |

**Rate Limit Headers:**

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1705315800
```

---

## OpenAPI Spec

```
GET /openapi.json
GET /docs  # Swagger UI
```