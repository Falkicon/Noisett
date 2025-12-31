# Deployment Guide

Azure infrastructure and CI/CD configuration for Noisett production deployment.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AZURE INFRASTRUCTURE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Azure Container Apps                          │    │
│  │                    (GPU Workload Profile)                        │    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │  Noisett Container                                       │    │    │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │    │    │
│  │  │  │  FastAPI    │  │  FastMCP    │  │  ML Pipeline    │  │    │    │
│  │  │  │  (REST)     │  │  (MCP/stdio)│  │  (HiDream)      │  │    │    │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────┘  │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│                              │                                          │
│  ┌─────────────────┐  ┌──────┴──────┐  ┌─────────────────────────────┐  │
│  │  Azure Blob     │  │  Azure CDN  │  │  Microsoft Entra ID         │  │
│  │  Storage        │  │  (optional) │  │  (Authentication)           │  │
│  │  - Images       │  │             │  │                             │  │
│  │  - Models       │  │             │  │                             │  │
│  │  - LoRAs        │  │             │  │                             │  │
│  └─────────────────┘  └─────────────┘  └─────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Resource Estimates

| Resource | SKU | Est. Monthly Cost | Notes |
|----------|-----|-------------------|-------|
| Container Apps (GPU) | NC-series workload | ~$20-50 | Scale-to-zero when idle |
| Blob Storage | Standard LRS | ~$1-5 | Generated images + models |
| Container Registry | Basic | ~$5 | Docker images |
| Entra ID | Included | $0 | Part of M365 |
| **Total** | | **~$30-60/month** | At 10-100 images/month |

---

## Prerequisites

### Azure Resources

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "Your-Subscription-Name"

# Create resource group
az group create \
  --name rg-noisett \
  --location westus2
```

### Container Registry

```bash
# Create container registry
az acr create \
  --name crnoisett \
  --resource-group rg-noisett \
  --sku Basic \
  --admin-enabled true

# Get login credentials
az acr credential show --name crnoisett
```

---

## Container Configuration

### Dockerfile

```dockerfile
# Dockerfile
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY web/ ./web/

# Download model weights at build time (optional, reduces cold start)
# Uncomment to bake models into image:
# RUN python -c "from diffusers import AutoPipelineForText2Image; AutoPipelineForText2Image.from_pretrained('HiDream/HiDream-I1-Full')"

# Copy LoRA weights
COPY loras/ ./loras/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
  CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["uvicorn", "src.server.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### requirements.txt

```text
# Core
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
python-multipart>=0.0.6

# MCP
fastmcp>=0.1.0

# ML
torch>=2.1.0
diffusers>=0.25.0
transformers>=4.36.0
accelerate>=0.25.0
peft>=0.7.0
safetensors>=0.4.0

# Azure
azure-storage-blob>=12.19.0
azure-identity>=1.15.0

# Auth
python-jose[cryptography]>=3.3.0
httpx>=0.26.0
```

---

## Container Apps Setup

### Create Environment with GPU

```bash
# Create Container Apps environment
az containerapp env create \
  --name cae-noisett \
  --resource-group rg-noisett \
  --location westus2 \
  --enable-workload-profiles

# Add GPU workload profile
az containerapp env workload-profile add \
  --name cae-noisett \
  --resource-group rg-noisett \
  --workload-profile-name gpu-profile \
  --workload-profile-type NC24-A100 \
  --min-nodes 0 \
  --max-nodes 1
```

### Deploy Container App

```yaml
# container-app.yaml
properties:
  managedEnvironmentId: /subscriptions/{sub}/resourceGroups/rg-noisett/providers/Microsoft.App/managedEnvironments/cae-noisett
  workloadProfileName: gpu-profile
  configuration:
    ingress:
      external: true
      targetPort: 8000
      transport: http
      corsPolicy:
        allowedOrigins:
          - "https://noisett.internal.company.com"
        allowedMethods:
          - GET
          - POST
          - DELETE
        allowedHeaders:
          - "*"
    secrets:
      - name: azure-storage-connection
        value: ${AZURE_STORAGE_CONNECTION_STRING}
      - name: azure-ad-client-id
        value: ${AZURE_AD_CLIENT_ID}
      - name: azure-ad-tenant-id
        value: ${AZURE_AD_TENANT_ID}
    registries:
      - server: crnoisett.azurecr.io
        username: crnoisett
        passwordSecretRef: acr-password
  template:
    containers:
      - name: noisett
        image: crnoisett.azurecr.io/noisett:latest
        resources:
          cpu: 4
          memory: 16Gi
          gpu: 1
        env:
          - name: AZURE_STORAGE_CONNECTION_STRING
            secretRef: azure-storage-connection
          - name: AZURE_AD_CLIENT_ID
            secretRef: azure-ad-client-id
          - name: AZURE_AD_TENANT_ID
            secretRef: azure-ad-tenant-id
          - name: MODEL_CACHE_DIR
            value: /app/models
        volumeMounts:
          - volumeName: model-cache
            mountPath: /app/models
    volumes:
      - name: model-cache
        storageType: AzureFile
        storageName: noisett-models
    scale:
      minReplicas: 0
      maxReplicas: 2
      rules:
        - name: http-scale
          http:
            metadata:
              concurrentRequests: "5"
```

```bash
# Deploy
az containerapp create \
  --name ca-noisett \
  --resource-group rg-noisett \
  --yaml container-app.yaml
```

---

## Blob Storage Setup

### Create Storage Account

```bash
# Create storage account
az storage account create \
  --name stnoisett \
  --resource-group rg-noisett \
  --location westus2 \
  --sku Standard_LRS

# Create containers
az storage container create \
  --name generated-images \
  --account-name stnoisett \
  --public-access off

az storage container create \
  --name models \
  --account-name stnoisett \
  --public-access off

az storage container create \
  --name loras \
  --account-name stnoisett \
  --public-access off
```

### Lifecycle Policy (Auto-delete old images)

```json
{
  "rules": [
    {
      "name": "delete-old-images",
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["generated-images/"]
        },
        "actions": {
          "baseBlob": {
            "delete": {
              "daysAfterCreationGreaterThan": 30
            }
          }
        }
      }
    }
  ]
}
```

```bash
az storage account management-policy create \
  --account-name stnoisett \
  --policy @lifecycle-policy.json
```

---

## Entra ID Configuration

### App Registration

1. Go to Azure Portal → Entra ID → App registrations
2. Click "New registration"
   - Name: `Noisett`
   - Supported account types: Single tenant
3. Configure authentication:
   - Add platform: Single-page application
   - Redirect URIs:
     - `http://localhost:8000` (dev)
     - `https://ca-noisett.{region}.azurecontainerapps.io` (prod)
4. API permissions:
   - Microsoft Graph → User.Read
5. Expose an API:
   - Set Application ID URI: `api://{client-id}`
   - Add scope: `access_as_user`
6. (Optional) Token configuration:
   - Add groups claim for access control

### Environment Variables

```bash
# Required environment variables
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_TENANT_ID=your-tenant-id
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=stnoisett;...
```

---

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy Noisett

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  AZURE_CONTAINER_REGISTRY: crnoisett.azurecr.io
  IMAGE_NAME: noisett
  RESOURCE_GROUP: rg-noisett
  CONTAINER_APP_NAME: ca-noisett

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run tests
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio
          pytest tests/ -v

      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Login to ACR
        run: |
          az acr login --name crnoisett

      - name: Build and push image
        run: |
          docker build -t ${{ env.AZURE_CONTAINER_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} .
          docker push ${{ env.AZURE_CONTAINER_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          
          # Tag as latest
          docker tag ${{ env.AZURE_CONTAINER_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
                     ${{ env.AZURE_CONTAINER_REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          docker push ${{ env.AZURE_CONTAINER_REGISTRY }}/${{ env.IMAGE_NAME }}:latest

      - name: Deploy to Container Apps
        run: |
          az containerapp update \
            --name ${{ env.CONTAINER_APP_NAME }} \
            --resource-group ${{ env.RESOURCE_GROUP }} \
            --image ${{ env.AZURE_CONTAINER_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

      - name: Verify deployment
        run: |
          # Wait for deployment
          sleep 30
          
          # Health check
          FQDN=$(az containerapp show \
            --name ${{ env.CONTAINER_APP_NAME }} \
            --resource-group ${{ env.RESOURCE_GROUP }} \
            --query properties.configuration.ingress.fqdn -o tsv)
          
          curl -f "https://${FQDN}/health" || exit 1
```

### Secrets Required

| Secret | Description |
|--------|-------------|
| `AZURE_CREDENTIALS` | Service principal JSON for Azure login |
| `AZURE_AD_CLIENT_ID` | Entra ID app client ID |
| `AZURE_AD_TENANT_ID` | Entra ID tenant ID |
| `AZURE_STORAGE_CONNECTION_STRING` | Blob storage connection string |

---

## Monitoring

### Application Insights

```python
# src/core/logging.py
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
import os

def setup_logging():
    """Configure Azure Application Insights logging."""
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    
    if connection_string:
        logger = logging.getLogger(__name__)
        logger.addHandler(AzureLogHandler(connection_string=connection_string))
        logger.setLevel(logging.INFO)
        return logger
    
    # Fallback to console logging
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)
```

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Generation latency | <60 sec | >90 sec |
| Error rate | <5% | >10% |
| GPU utilization | Monitor | >90% sustained |
| Cold start time | <90 sec | >120 sec |

### Health Check Endpoint

```python
# In src/server/api.py
@app.get("/health")
async def health():
    """Health check endpoint for Container Apps."""
    gpu_available = torch.cuda.is_available()
    
    return {
        "status": "healthy" if gpu_available else "degraded",
        "version": "1.0.0",
        "gpu_available": gpu_available,
        "model_loaded": ml_pipeline.is_loaded(),
    }
```

---

## Cost Optimization

### Scale-to-Zero

Container Apps automatically scales to zero when idle. Cold start takes ~60-90 seconds (acceptable for internal tool).

### Model Caching

Store model weights in Azure Blob and mount as volume to avoid re-downloading on container restart:

```bash
# Upload models to blob storage
az storage blob upload-batch \
  --account-name stnoisett \
  --destination models \
  --source ./models/
```

### Right-Size GPU

- **T4 (16GB)**: Sufficient for HiDream inference
- **A10G (24GB)**: For FLUX or multiple models
- **A100**: Overkill for this use case

---

## Runbook

### Deploy New Version

```bash
# 1. Build and push
docker build -t crnoisett.azurecr.io/noisett:v1.2.0 .
docker push crnoisett.azurecr.io/noisett:v1.2.0

# 2. Update container app
az containerapp update \
  --name ca-noisett \
  --resource-group rg-noisett \
  --image crnoisett.azurecr.io/noisett:v1.2.0

# 3. Verify
curl https://ca-noisett.{region}.azurecontainerapps.io/health
```

### Rollback

```bash
az containerapp revision list \
  --name ca-noisett \
  --resource-group rg-noisett

az containerapp revision activate \
  --name ca-noisett \
  --resource-group rg-noisett \
  --revision ca-noisett--{previous-revision}
```

### View Logs

```bash
az containerapp logs show \
  --name ca-noisett \
  --resource-group rg-noisett \
  --follow
```

### Update LoRA Weights

```bash
# Upload new LoRA
az storage blob upload \
  --account-name stnoisett \
  --container-name loras \
  --name brand-style-v2.safetensors \
  --file ./loras/brand-style-v2.safetensors

# Restart container to pick up new weights
az containerapp revision restart \
  --name ca-noisett \
  --resource-group rg-noisett
```
