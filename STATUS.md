# Noisett - Current Status

> Last Updated: 2026-01-14 12:30 PST

## Current State: ✅ WORKING!

**Replicate API integration is fully functional!** Real AI images generated via FLUX dev-lora.

### What's Working ✅
- **Image Generation** - `black-forest-labs/flux-dev-lora` on Replicate
- **Web UI** - `http://localhost:3000`
- **Backend API** - `http://localhost:8001` (run WITHOUT --reload)
- **Image Display** - Fixed URL handling for absolute Replicate URLs
- **Generation Count** - Fixed to 1 image per run across the entire stack

### Security Fixes (2026-01-14)
1. **JWT Bypass Fixed** - `auth.py` now fails closed when `AUTH_REQUIRED=true` but `pyjwt[crypto]` is missing
2. **Debug Endpoint Gated** - `/api/test-replicate` now requires `DEBUG=true` env var

### Root Causes Fixed
1. **Uvicorn `--reload` caching** - Hot-reload cached old code → Run WITHOUT `--reload`
2. **Python `__pycache__`** - Old bytecode persisted → Clear before restart
3. **Image URL bug** - Frontend prepended baseUrl to absolute URLs → Fixed
4. **Hardcoded Count** - Found and fixed in 5 files

## How to Start

```bash
# Terminal 1: Frontend
cd app && python -m http.server 3000

# Terminal 2: Backend (NO --reload!)
$env:CONVEX_URL = "https://neighborly-gazelle-692.convex.site"
$env:REPLICATE_API_TOKEN = "r8_..."
$env:ML_BACKEND = "replicate"
$env:DEBUG = "true"  # Optional: enables /api/test-replicate
python -m uvicorn src.server.api:app --port 8001
```

## TODO
- [ ] **Get LoRAs working** (priority)
- [ ] Persist completed jobs to history (review finding #2)
- [ ] Add cancellation check in process_job (review finding #3)
- [ ] Create centralized config file for settings
