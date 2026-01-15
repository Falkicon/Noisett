# Deployment Reference

Azure Container Apps deployment for Noisett.

## Live Deployment

| Resource | Value |
|----------|-------|
| **Live URL** | https://noisett.thankfulplant-c547bdac.eastus.azurecontainerapps.io/ |
| **Container App** | noisett (East US) |
| **Registry** | noisettacr.azurecr.io |
| **Resource Group** | noisett-rg |
| **Backend** | ML_BACKEND=fireworks |

## Infrastructure Files

```
infrastructure/
├── container-app.yaml    # Container Apps config
└── setup-azure.sh        # Provisioning script

.github/workflows/
└── deploy.yml            # CI/CD pipeline
```

## Container Apps Configuration

```yaml
# infrastructure/container-app.yaml
properties:
  configuration:
    ingress:
      external: true
      targetPort: 8000
    secrets:
      - name: fireworks-api-key
        value: ${FIREWORKS_API_KEY}
  template:
    containers:
      - name: noisett
        image: noisettacr.azurecr.io/noisett:latest
        env:
          - name: ML_BACKEND
            value: fireworks
          - name: FIREWORKS_API_KEY
            secretRef: fireworks-api-key
        resources:
          cpu: 0.5
          memory: 1Gi
```

## CI/CD Pipeline

Triggered on push to `main`:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Build and push image
        run: |
          az acr build --registry noisettacr \
            --image noisett:${{ github.sha }} .

      - name: Deploy to Container Apps
        run: |
          az containerapp update --name noisett \
            --resource-group noisett-rg \
            --image noisettacr.azurecr.io/noisett:${{ github.sha }}
```

## Manual Deployment

```bash
# 1. Build and push image
az acr build --registry noisettacr --image noisett:latest .

# 2. Update container app
az containerapp update --name noisett \
  --resource-group noisett-rg \
  --image noisettacr.azurecr.io/noisett:latest

# 3. Check logs
az containerapp logs show --name noisett \
  --resource-group noisett-rg --follow
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ML_BACKEND` | ML inference backend | Yes |
| `FIREWORKS_API_KEY` | Fireworks.ai API key | If using Fireworks |
| `PORT` | Server port (default 8000) | No |

## Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY web/ web/

ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "src.server.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Health Checks

The `/health` endpoint returns:

```json
{
  "status": "healthy",
  "version": "0.9.1",
  "backend": "fireworks",
  "timestamp": "2026-01-13T12:00:00Z"
}
```

## Scaling

Container Apps auto-scales based on HTTP traffic:

```yaml
scale:
  minReplicas: 0
  maxReplicas: 3
  rules:
    - name: http-scaling
      http:
        metadata:
          concurrentRequests: "10"
```

## Troubleshooting

| Issue | Check |
|-------|-------|
| 502 errors | Container startup logs, health endpoint |
| Slow responses | ML backend status, network latency |
| Auth failures | JWT middleware, Entra ID config |
| Missing images | Fireworks API key, rate limits |
