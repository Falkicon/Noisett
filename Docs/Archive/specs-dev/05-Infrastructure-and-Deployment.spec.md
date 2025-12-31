# Infrastructure & Deployment

**Status:** Reference

**Cloud:** Microsoft Azure

**Region:** West US 2 (or nearest GPU availability)

---

## Azure Resources

### Resource Overview

| Resource | Service | SKU/Tier | Est. Cost |
| --- | --- | --- | --- |
| Frontend | Static Web Apps | Free | $0/month |
| Backend + ML | Container Apps | GPU workload profile | ~$20-50/month* |
| Image Storage | Blob Storage | Hot tier | ~$1-5/month |
| Auth | Entra ID | Included | $0 |
| Database (v2+) | PostgreSQL Flexible | Burstable B1ms | ~$15/month |

*GPU cost depends on usage; scales to zero when idle

---

## Container Apps Configuration

### Environment Setup

```bash
# Create resource group
az group create \
  --name rg-brand-assets \
  --location westus2

# Create Container Apps environment with GPU
az containerapp env create \
  --name cae-brand-assets \
  --resource-group rg-brand-assets \
  --location westus2 \
  --enable-workload-profiles

# Add GPU workload profile
az containerapp env workload-profile add \
  --name cae-brand-assets \
  --resource-group rg-brand-assets \
  --workload-profile-name gpu-profile \
  --workload-profile-type NC24-A100 \
  --min-nodes 0 \
  --max-nodes 1
```

### Container App Deployment

```yaml
# container-app.yaml
properties:
  managedEnvironmentId: /subscriptions/.../cae-brand-assets
  workloadProfileName: gpu-profile
  configuration:
    ingress:
      external: true
      targetPort: 8000
      transport: http
    secrets:
      - name: azure-storage-connection
        value: ${AZURE_STORAGE_CONNECTION}
      - name: azure-ad-client-secret
        value: ${AZURE_AD_CLIENT_SECRET}
  template:
    containers:
      - name: api
        image: [your-registry.azurecr.io/brand-asset-api:latest](http://your-registry.azurecr.io/brand-asset-api:latest)
        resources:
          cpu: 4
          memory: 16Gi
          gpu: 1
        env:
          - name: AZURE_STORAGE_CONNECTION
            secretRef: azure-storage-connection
          - name: AZURE_AD_CLIENT_ID
            value: your-client-id
          - name: AZURE_AD_TENANT_ID
            value: your-tenant-id
    scale:
      minReplicas: 0
      maxReplicas: 2
      rules:
        - name: http-rule
          http:
            metadata:
              concurrentRequests: "5"
```

---

## Dockerfile

```docker
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
COPY app/ ./app/
COPY ml/ ./ml/

# Download model weights at build time (optional, faster cold start)
# RUN python -c "from diffusers import AutoPipelineForText2Image; AutoPipelineForText2Image.from_pretrained('HiDream/HiDream-I1-Full')"

# Copy LoRA weights
COPY loras/ ./loras/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Blob Storage Setup

```bash
# Create storage account
az storage account create \
  --name stbrandassets \
  --resource-group rg-brand-assets \
  --location westus2 \
  --sku Standard_LRS

# Create container for generated images
az storage container create \
  --name generated-images \
  --account-name stbrandassets \
  --public-access off

# Set lifecycle policy (auto-delete after 30 days)
az storage account management-policy create \
  --account-name stbrandassets \
  --policy @lifecycle-policy.json
```

**lifecycle-policy.json:**

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
            "delete": { "daysAfterCreationGreaterThan": 30 }
          }
        }
      }
    }
  ]
}
```

---

## Azure AD App Registration

### Setup Steps

1. **Register Application**
    - Go to Azure Portal → Entra ID → App registrations
    - New registration: "Brand Asset Generator"
    - Supported account types: Single tenant
2. **Configure Authentication**
    - Add platform: Single-page application
    - Redirect URIs:
        - [`http://localhost:5173`](http://localhost:5173) (dev)
        - [`https://your-app.azurestaticapps.net`](https://your-app.azurestaticapps.net) (prod)
3. **API Permissions**
    - Add permission: Microsoft Graph → [User.Read](http://User.Read)
4. **Expose an API**
    - Set Application ID URI: `api://{client-id}`
    - Add scope: `access_as_user`
5. **Configure Groups (Optional)**
    - Token configuration → Add groups claim
    - Create security group for authorized users

---

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          
      - name: Install and Build
        working-directory: frontend
        run: |
          npm ci
          npm run build
        env:
          VITE_API_URL: $ vars.API_URL 
          VITE_AZURE_CLIENT_ID: $ [vars.AZURE](http://vars.AZURE)_CLIENT_ID 
          VITE_AZURE_TENANT_ID: $ [vars.AZURE](http://vars.AZURE)_TENANT_ID 
          
      - name: Deploy to Static Web Apps
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: $ [secrets.AZURE](http://secrets.AZURE)_SWA_TOKEN 
          action: upload
          app_location: frontend/dist

  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: $ [secrets.AZURE](http://secrets.AZURE)_CREDENTIALS 
          
      - name: Login to ACR
        run: |
          az acr login --name $ vars.ACR_NAME 
          
      - name: Build and Push
        working-directory: backend
        run: |
          docker build -t $ vars.ACR_NAME .[azurecr.io/brand-asset-api:$](http://azurecr.io/brand-asset-api:$) github.sha  .
          docker push $ vars.ACR_NAME .[azurecr.io/brand-asset-api:$](http://azurecr.io/brand-asset-api:$) github.sha 
          
      - name: Deploy to Container Apps
        run: |
          az containerapp update \
            --name ca-brand-assets \
            --resource-group rg-brand-assets \
            --image $ vars.ACR_NAME .[azurecr.io/brand-asset-api:$](http://azurecr.io/brand-asset-api:$) github.sha 
```

---

## Monitoring

### Application Insights

```python
# app/core/[logging.py](http://logging.py)
from [opencensus.ext.azure](http://opencensus.ext.azure).log_exporter import AzureLogHandler
from [opencensus.ext.azure](http://opencensus.ext.azure).trace_exporter import AzureExporter
import logging

def setup_logging():
    logger = logging.getLogger(__name__)
    logger.addHandler(AzureLogHandler(
        connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    ))
    return logger
```

### Key Metrics to Track

| Metric | Target | Alert Threshold |
| --- | --- | --- |
| Generation latency | <60 sec | >90 sec |
| Error rate | <5% | >10% |
| GPU utilization | Monitor only | >90% sustained |
| Queue depth | <10 | >20 |