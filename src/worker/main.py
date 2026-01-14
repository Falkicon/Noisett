"""Noisett Cloudflare Worker Entry Point.

This is the edge worker that handles HTTP requests.
It wraps the existing FastAPI app for Cloudflare Workers runtime.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Edge-optimized app instance
app = FastAPI(
    title="Noisett API (Edge)",
    description="AI Brand Asset Generation - Cloudflare Workers",
    version="1.0.0",
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "noisett",
        "status": "healthy",
        "runtime": "cloudflare-workers",
    }


@app.get("/api/health")
async def health():
    """Detailed health check."""
    return {
        "status": "ok",
        "components": {
            "worker": "healthy",
            "convex": "pending",  # TODO: Check Convex connection
            "fireworks": "pending",  # TODO: Check Fireworks connection
        }
    }


# TODO: Import and mount existing Noisett routes once migrated
# from src.server.api import create_app
# app.mount("/api", create_app())


# Cloudflare Workers handler
async def on_fetch(request, env):
    """Cloudflare Workers fetch handler.
    
    This is called by the Workers runtime for each request.
    """
    import json
    from urllib.parse import urlparse
    
    # Convert CF Request to ASGI
    url = urlparse(request.url)
    scope = {
        "type": "http",
        "method": request.method,
        "path": url.path,
        "query_string": (url.query or "").encode(),
        "headers": [(k.lower().encode(), v.encode()) for k, v in request.headers.items()],
    }
    
    # Simple routing for now
    if url.path == "/" or url.path == "":
        return Response(
            json.dumps({"service": "noisett", "status": "healthy", "runtime": "cloudflare-workers"}),
            headers={"Content-Type": "application/json"}
        )
    
    if url.path == "/api/health":
        return Response(
            json.dumps({"status": "ok"}),
            headers={"Content-Type": "application/json"}
        )
    
    return Response("Not Found", status=404)
