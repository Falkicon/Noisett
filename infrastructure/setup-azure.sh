#!/bin/bash
# Noisett Azure Infrastructure Setup Script
# Prerequisites: az cli logged in, subscription selected

set -e

# Configuration
RESOURCE_GROUP="rg-noisett"
LOCATION="eastus"
ACR_NAME="crnoisett"
STORAGE_ACCOUNT="stnoisett"
CONTAINER_APP_ENV="cae-noisett"
CONTAINER_APP_NAME="ca-noisett"
APP_INSIGHTS="ai-noisett"

echo "🚀 Setting up Noisett Azure infrastructure..."

# Create Resource Group
echo "📦 Creating resource group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Create Container Registry
echo "📦 Creating container registry..."
az acr create \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --sku Basic \
  --admin-enabled true

# Create Storage Account
echo "📦 Creating storage account..."
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Get storage account key
STORAGE_KEY=$(az storage account keys list \
  --account-name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query '[0].value' -o tsv)

# Create storage containers
echo "📦 Creating storage containers..."
az storage container create \
  --name generated-images \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY

az storage container create \
  --name models \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY

az storage container create \
  --name loras \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY

# Create Application Insights
echo "📊 Creating Application Insights..."
az monitor app-insights component create \
  --app $APP_INSIGHTS \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --kind web \
  --application-type web

# Create Container Apps Environment with GPU workload profile
echo "🐳 Creating Container Apps environment with GPU..."
az containerapp env create \
  --name $CONTAINER_APP_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --enable-workload-profiles

# Add GPU workload profile (NC24-A100)
echo "🎮 Adding GPU workload profile..."
az containerapp env workload-profile add \
  --name $CONTAINER_APP_ENV \
  --resource-group $RESOURCE_GROUP \
  --workload-profile-name "gpu" \
  --workload-profile-type "NC24-A100" \
  --min-nodes 0 \
  --max-nodes 1

# Get connection strings
echo "📝 Retrieving connection strings..."

ACR_PASSWORD=$(az acr credential show \
  --name $ACR_NAME \
  --query 'passwords[0].value' -o tsv)

STORAGE_CONNECTION=$(az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query connectionString -o tsv)

APP_INSIGHTS_KEY=$(az monitor app-insights component show \
  --app $APP_INSIGHTS \
  --resource-group $RESOURCE_GROUP \
  --query connectionString -o tsv)

echo ""
echo "✅ Azure infrastructure created successfully!"
echo ""
echo "🔑 Save these values for GitHub Secrets:"
echo "================================================"
echo "ACR_PASSWORD: $ACR_PASSWORD"
echo "AZURE_STORAGE_CONNECTION_STRING: $STORAGE_CONNECTION"
echo "APPLICATIONINSIGHTS_CONNECTION_STRING: $APP_INSIGHTS_KEY"
echo "================================================"
echo ""
echo "📋 Next steps:"
echo "1. Create Entra ID app registration (see 04-deployment.md)"
echo "2. Add GitHub secrets: AZURE_CREDENTIALS, AZURE_AD_CLIENT_ID, AZURE_AD_TENANT_ID"
echo "3. Build and push initial image:"
echo "   docker build -t $ACR_NAME.azurecr.io/noisett:v1.0.0 ."
echo "   az acr login --name $ACR_NAME"
echo "   docker push $ACR_NAME.azurecr.io/noisett:v1.0.0"
echo "4. Create container app (update container-app.yaml with secrets first)"
