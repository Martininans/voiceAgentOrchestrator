# 🚀 Complete Azure Deployment Guide - Voice Agent Orchestrator

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Azure Infrastructure Setup](#azure-infrastructure-setup)
3. [Container Registry Setup](#container-registry-setup)
4. [Azure Services Configuration](#azure-services-configuration)
5. [Application Deployment](#application-deployment)
6. [Monitoring & Security](#monitoring--security)
7. [Production Optimization](#production-optimization)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### Required Tools
```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
```

### Azure Account Setup
1. **Create Azure Account**: https://azure.microsoft.com/free/
2. **Create Resource Group**:
```bash
az group create --name voice-agent-rg --location eastus
```

---

## 🏗️ Azure Infrastructure Setup

### 1. Create Core Infrastructure

```bash
# Set variables
RESOURCE_GROUP="voice-agent-rg"
LOCATION="eastus"
APP_NAME="voice-agent-orchestrator"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Log Analytics Workspace
az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name voice-agent-logs \
  --location $LOCATION

# Create Application Insights
az monitor app-insights component create \
  --app voice-agent-insights \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --workspace voice-agent-logs
```

### 2. Create Azure Container Registry

```bash
# Create ACR
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name voiceagentregistry \
  --sku Standard \
  --admin-enabled true

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name voiceagentregistry --query loginServer --output tsv)
echo "ACR Login Server: $ACR_LOGIN_SERVER"

# Enable admin user
az acr credential show --name voiceagentregistry
```

### 3. Create Azure Key Vault

```bash
# Create Key Vault
az keyvault create \
  --name voice-agent-kv \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku standard \
  --enable-rbac-authorization true

# Get Key Vault URI
KEY_VAULT_URI=$(az keyvault show --name voice-agent-kv --query properties.vaultUri --output tsv)
echo "Key Vault URI: $KEY_VAULT_URI"
```

---

## 🐳 Container Registry Setup

### 1. Build and Push Images

```bash
# Login to ACR
az acr login --name voiceagentregistry

# Build and push orchestrator
cd backend-python-orchestrator
docker build -t voiceagentregistry.azurecr.io/voice-agent-orchestrator:latest .
docker push voiceagentregistry.azurecr.io/voice-agent-orchestrator:latest

# Build and push realtime
cd ../backend-node-realtime
docker build -t voiceagentregistry.azurecr.io/voice-agent-realtime:latest .
docker push voiceagentregistry.azurecr.io/voice-agent-realtime:latest
```

### 2. Create Azure Container Instances

```bash
# Deploy Orchestrator
az container create \
  --resource-group $RESOURCE_GROUP \
  --name voice-agent-orchestrator \
  --image voiceagentregistry.azurecr.io/voice-agent-orchestrator:latest \
  --registry-login-server voiceagentregistry.azurecr.io \
  --registry-username voiceagentregistry \
  --registry-password $(az acr credential show --name voiceagentregistry --query passwords[0].value --output tsv) \
  --dns-name-label voice-agent-orchestrator \
  --ports 8000 \
  --cpu 2 \
  --memory 4 \
  --environment-variables \
    NODE_ENV=production \
    LOG_LEVEL=info \
    SECTOR=generic \
    CHROMA_PERSIST_DIRECTORY=/app/chroma_db \
    DISABLE_OPTIMIZATIONS=false \
  --secure-environment-variables \
    SUPABASE_URL="https://your-project.supabase.co" \
    JWT_SECRET="your-jwt-secret" \
    OPENAI_API_KEY="your-openai-key"

# Deploy Realtime Service
az container create \
  --resource-group $RESOURCE_GROUP \
  --name voice-agent-realtime \
  --image voiceagentregistry.azurecr.io/voice-agent-realtime:latest \
  --registry-login-server voiceagentregistry.azurecr.io \
  --registry-username voiceagentregistry \
  --registry-password $(az acr credential show --name voiceagentregistry --query passwords[0].value --output tsv) \
  --dns-name-label voice-agent-realtime \
  --ports 3000 \
  --cpu 1 \
  --memory 2 \
  --environment-variables \
    NODE_ENV=production \
    PORT=3000 \
    HOST=0.0.0.0 \
    VOICE_PROVIDER=twilio \
    ORCHESTRATOR_URL="http://voice-agent-orchestrator.eastus.azurecontainer.io:8000" \
    CORS_ORIGIN="*" \
  --secure-environment-variables \
    TWILIO_ACCOUNT_SID="your-twilio-sid" \
    TWILIO_AUTH_TOKEN="your-twilio-token" \
    JWT_SECRET="your-jwt-secret"
```

---

## 🔐 Azure Services Configuration

### 1. Azure Database for PostgreSQL

```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name voice-agent-postgres \
  --location $LOCATION \
  --admin-user voiceagentadmin \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --public-access 0.0.0.0 \
  --storage-size 32

# Create database
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name voice-agent-postgres \
  --database-name voiceagentdb

# Get connection string
CONNECTION_STRING="postgresql://voiceagentadmin:YourSecurePassword123!@voice-agent-postgres.postgres.database.azure.com:5432/voiceagentdb?sslmode=require"
```

### 2. Azure Redis Cache

```bash
# Create Redis Cache
az redis create \
  --resource-group $RESOURCE_GROUP \
  --name voice-agent-redis \
  --location $LOCATION \
  --sku Standard \
  --vm-size c1

# Get Redis connection string
REDIS_PRIMARY_KEY=$(az redis list-keys --resource-group $RESOURCE_GROUP --name voice-agent-redis --query primaryKey --output tsv)
REDIS_HOSTNAME=$(az redis show --resource-group $RESOURCE_GROUP --name voice-agent-redis --query hostName --output tsv)
REDIS_URL="redis://:$REDIS_PRIMARY_KEY@$REDIS_HOSTNAME:6380"
```

### 3. Azure Blob Storage

```bash
# Create storage account
az storage account create \
  --name voiceagentstorage \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2

# Create container
az storage container create \
  --name voice-agent-files \
  --account-name voiceagentstorage

# Get connection string
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string --name voiceagentstorage --resource-group $RESOURCE_GROUP --query connectionString --output tsv)
```

### 4. Azure OpenAI Service

```bash
# Create OpenAI resource
az cognitiveservices account create \
  --name voice-agent-openai \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --kind OpenAI \
  --sku S0

# Get API key
OPENAI_API_KEY=$(az cognitiveservices account keys list --name voice-agent-openai --resource-group $RESOURCE_GROUP --query key1 --output tsv)
OPENAI_ENDPOINT=$(az cognitiveservices account show --name voice-agent-openai --resource-group $RESOURCE_GROUP --query properties.endpoint --output tsv)
```

---

## 🔑 Secrets Management

### Store Secrets in Key Vault

```bash
# Store all secrets
az keyvault secret set --vault-name voice-agent-kv --name supabase-url --value "https://your-project.supabase.co"
az keyvault secret set --vault-name voice-agent-kv --name supabase-anon-key --value "your-supabase-anon-key"
az keyvault secret set --vault-name voice-agent-kv --name supabase-service-role-key --value "your-supabase-service-role-key"
az keyvault secret set --vault-name voice-agent-kv --name jwt-secret --value "your-super-secure-jwt-secret"
az keyvault secret set --vault-name voice-agent-kv --name openai-api-key --value "$OPENAI_API_KEY"
az keyvault secret set --vault-name voice-agent-kv --name openai-endpoint --value "$OPENAI_ENDPOINT"
az keyvault secret set --vault-name voice-agent-kv --name redis-url --value "$REDIS_URL"
az keyvault secret set --vault-name voice-agent-kv --name postgres-connection-string --value "$CONNECTION_STRING"
az keyvault secret set --vault-name voice-agent-kv --name storage-connection-string --value "$STORAGE_CONNECTION_STRING"
az keyvault secret set --vault-name voice-agent-kv --name twilio-account-sid --value "your-twilio-account-sid"
az keyvault secret set --vault-name voice-agent-kv --name twilio-auth-token --value "your-twilio-auth-token"
az keyvault secret set --vault-name voice-agent-kv --name twilio-phone-number --value "your-twilio-phone-number"
```

---

## 🚀 Application Deployment

### Option 1: Azure Container Instances (Recommended for Start)

```bash
# Create deployment script
cat > deploy-aci.sh << 'EOF'
#!/bin/bash

# Get secrets from Key Vault
SUPABASE_URL=$(az keyvault secret show --vault-name voice-agent-kv --name supabase-url --query value --output tsv)
SUPABASE_ANON_KEY=$(az keyvault secret show --vault-name voice-agent-kv --name supabase-anon-key --query value --output tsv)
JWT_SECRET=$(az keyvault secret show --vault-name voice-agent-kv --name jwt-secret --query value --output tsv)
OPENAI_API_KEY=$(az keyvault secret show --vault-name voice-agent-kv --name openai-api-key --query value --output tsv)
REDIS_URL=$(az keyvault secret show --vault-name voice-agent-kv --name redis-url --query value --output tsv)

# Deploy Orchestrator
az container create \
  --resource-group voice-agent-rg \
  --name voice-agent-orchestrator \
  --image voiceagentregistry.azurecr.io/voice-agent-orchestrator:latest \
  --registry-login-server voiceagentregistry.azurecr.io \
  --registry-username voiceagentregistry \
  --registry-password $(az acr credential show --name voiceagentregistry --query passwords[0].value --output tsv) \
  --dns-name-label voice-agent-orchestrator \
  --ports 8000 \
  --cpu 2 \
  --memory 4 \
  --environment-variables \
    NODE_ENV=production \
    LOG_LEVEL=info \
    SECTOR=generic \
    CHROMA_PERSIST_DIRECTORY=/app/chroma_db \
    DISABLE_OPTIMIZATIONS=false \
    SUPABASE_URL="$SUPABASE_URL" \
    REDIS_URL="$REDIS_URL" \
  --secure-environment-variables \
    SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
    JWT_SECRET="$JWT_SECRET" \
    OPENAI_API_KEY="$OPENAI_API_KEY"

# Deploy Realtime
az container create \
  --resource-group voice-agent-rg \
  --name voice-agent-realtime \
  --image voiceagentregistry.azurecr.io/voice-agent-realtime:latest \
  --registry-login-server voiceagentregistry.azurecr.io \
  --registry-username voiceagentregistry \
  --registry-password $(az acr credential show --name voiceagentregistry --query passwords[0].value --output tsv) \
  --dns-name-label voice-agent-realtime \
  --ports 3000 \
  --cpu 1 \
  --memory 2 \
  --environment-variables \
    NODE_ENV=production \
    PORT=3000 \
    HOST=0.0.0.0 \
    VOICE_PROVIDER=twilio \
    ORCHESTRATOR_URL="http://voice-agent-orchestrator.eastus.azurecontainer.io:8000" \
    CORS_ORIGIN="*"

echo "Deployment completed!"
echo "Orchestrator URL: http://voice-agent-orchestrator.eastus.azurecontainer.io:8000"
echo "Realtime URL: http://voice-agent-realtime.eastus.azurecontainer.io:3000"
EOF

chmod +x deploy-aci.sh
./deploy-aci.sh
```

### Option 2: Azure Kubernetes Service (For Production Scale)

```bash
# Create AKS cluster
az aks create \
  --resource-group $RESOURCE_GROUP \
  --name voice-agent-aks \
  --node-count 3 \
  --node-vm-size Standard_D2s_v3 \
  --enable-addons monitoring \
  --generate-ssh-keys \
  --attach-acr voiceagentregistry

# Get credentials
az aks get-credentials --resource-group $RESOURCE_GROUP --name voice-agent-aks

# Create Kubernetes manifests
cat > k8s-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voice-agent-orchestrator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: voice-agent-orchestrator
  template:
    metadata:
      labels:
        app: voice-agent-orchestrator
    spec:
      containers:
      - name: orchestrator
        image: voiceagentregistry.azurecr.io/voice-agent-orchestrator:latest
        ports:
        - containerPort: 8000
        env:
        - name: NODE_ENV
          value: "production"
        - name: SUPABASE_URL
          valueFrom:
            secretKeyRef:
              name: voice-agent-secrets
              key: supabase-url
        - name: SUPABASE_ANON_KEY
          valueFrom:
            secretKeyRef:
              name: voice-agent-secrets
              key: supabase-anon-key
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: voice-agent-secrets
              key: jwt-secret
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: voice-agent-secrets
              key: openai-api-key
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: voice-agent-secrets
              key: redis-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: voice-agent-orchestrator-service
spec:
  selector:
    app: voice-agent-orchestrator
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voice-agent-realtime
spec:
  replicas: 2
  selector:
    matchLabels:
      app: voice-agent-realtime
  template:
    metadata:
      labels:
        app: voice-agent-realtime
    spec:
      containers:
      - name: realtime
        image: voiceagentregistry.azurecr.io/voice-agent-realtime:latest
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "production"
        - name: PORT
          value: "3000"
        - name: HOST
          value: "0.0.0.0"
        - name: VOICE_PROVIDER
          value: "twilio"
        - name: ORCHESTRATOR_URL
          value: "http://voice-agent-orchestrator-service:80"
        - name: CORS_ORIGIN
          value: "*"
        - name: TWILIO_ACCOUNT_SID
          valueFrom:
            secretKeyRef:
              name: voice-agent-secrets
              key: twilio-account-sid
        - name: TWILIO_AUTH_TOKEN
          valueFrom:
            secretKeyRef:
              name: voice-agent-secrets
              key: twilio-auth-token
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: voice-agent-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: voice-agent-realtime-service
spec:
  selector:
    app: voice-agent-realtime
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: LoadBalancer
EOF

# Create secrets in Kubernetes
kubectl create secret generic voice-agent-secrets \
  --from-literal=supabase-url="$(az keyvault secret show --vault-name voice-agent-kv --name supabase-url --query value --output tsv)" \
  --from-literal=supabase-anon-key="$(az keyvault secret show --vault-name voice-agent-kv --name supabase-anon-key --query value --output tsv)" \
  --from-literal=jwt-secret="$(az keyvault secret show --vault-name voice-agent-kv --name jwt-secret --query value --output tsv)" \
  --from-literal=openai-api-key="$(az keyvault secret show --vault-name voice-agent-kv --name openai-api-key --query value --output tsv)" \
  --from-literal=redis-url="$(az keyvault secret show --vault-name voice-agent-kv --name redis-url --query value --output tsv)" \
  --from-literal=twilio-account-sid="$(az keyvault secret show --vault-name voice-agent-kv --name twilio-account-sid --query value --output tsv)" \
  --from-literal=twilio-auth-token="$(az keyvault secret show --vault-name voice-agent-kv --name twilio-auth-token --query value --output tsv)"

# Deploy to Kubernetes
kubectl apply -f k8s-deployment.yaml
```

---

## 📊 Monitoring & Security

### 1. Application Insights Integration

```bash
# Get Application Insights connection string
APP_INSIGHTS_CONNECTION_STRING=$(az monitor app-insights component show --app voice-agent-insights --resource-group $RESOURCE_GROUP --query connectionString --output tsv)

# Update container deployments with Application Insights
az container create \
  --resource-group $RESOURCE_GROUP \
  --name voice-agent-orchestrator \
  --image voiceagentregistry.azurecr.io/voice-agent-orchestrator:latest \
  --environment-variables \
    APPLICATIONINSIGHTS_CONNECTION_STRING="$APP_INSIGHTS_CONNECTION_STRING" \
    # ... other environment variables
```

### 2. Azure Monitor Alerts

```bash
# Create action group for alerts
az monitor action-group create \
  --name voice-agent-alerts \
  --resource-group $RESOURCE_GROUP \
  --short-name voice-alerts

# Create CPU alert
az monitor metrics alert create \
  --name "High CPU Usage" \
  --resource-group $RESOURCE_GROUP \
  --scopes $(az container show --name voice-agent-orchestrator --resource-group $RESOURCE_GROUP --query id --output tsv) \
  --condition "avg Percentage CPU > 80" \
  --description "Alert when CPU usage is high" \
  --evaluation-frequency 1m \
  --window-size 5m \
  --severity 2
```

### 3. Security Configuration

```bash
# Enable Azure Security Center
az security pricing create --name "VirtualMachines" --tier "Standard"

# Create Network Security Group
az network nsg create \
  --resource-group $RESOURCE_GROUP \
  --name voice-agent-nsg \
  --location $LOCATION

# Add security rules
az network nsg rule create \
  --resource-group $RESOURCE_GROUP \
  --nsg-name voice-agent-nsg \
  --name allow-http \
  --priority 1000 \
  --source-address-prefixes '*' \
  --source-port-ranges '*' \
  --destination-address-prefixes '*' \
  --destination-port-ranges 80 443 \
  --access Allow \
  --protocol Tcp \
  --description "Allow HTTP/HTTPS traffic"
```

---

## 🔧 Production Optimization

### 1. Auto-scaling Configuration

```bash
# Create auto-scaling profile for ACI
az monitor autoscale create \
  --resource-group $RESOURCE_GROUP \
  --resource voice-agent-orchestrator \
  --resource-type Microsoft.ContainerInstance/containerGroups \
  --name voice-agent-autoscale \
  --min-count 1 \
  --max-count 10 \
  --count 2
```

### 2. CDN Configuration

```bash
# Create CDN profile
az cdn profile create \
  --resource-group $RESOURCE_GROUP \
  --name voice-agent-cdn \
  --sku Standard_Microsoft

# Create CDN endpoint
az cdn endpoint create \
  --resource-group $RESOURCE_GROUP \
  --profile-name voice-agent-cdn \
  --name voice-agent-endpoint \
  --origin voice-agent-orchestrator.eastus.azurecontainer.io \
  --origin-host-header voice-agent-orchestrator.eastus.azurecontainer.io
```

### 3. Backup Configuration

```bash
# Create backup vault
az backup vault create \
  --resource-group $RESOURCE_GROUP \
  --name voice-agent-backup-vault \
  --location $LOCATION

# Create backup policy
az backup policy create \
  --resource-group $RESOURCE_GROUP \
  --vault-name voice-agent-backup-vault \
  --name daily-backup-policy \
  --policy policy.json
```

---

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. Container Startup Issues
```bash
# Check container logs
az container logs --name voice-agent-orchestrator --resource-group $RESOURCE_GROUP

# Check container status
az container show --name voice-agent-orchestrator --resource-group $RESOURCE_GROUP --query instanceView.state
```

#### 2. Network Connectivity Issues
```bash
# Test connectivity
az container exec --name voice-agent-orchestrator --resource-group $RESOURCE_GROUP --exec-command "curl -f http://localhost:8000/health"

# Check DNS resolution
az container exec --name voice-agent-orchestrator --resource-group $RESOURCE_GROUP --exec-command "nslookup voice-agent-realtime.eastus.azurecontainer.io"
```

#### 3. Secret Access Issues
```bash
# Verify Key Vault access
az keyvault secret show --vault-name voice-agent-kv --name jwt-secret

# Check container environment variables
az container show --name voice-agent-orchestrator --resource-group $RESOURCE_GROUP --query containers[0].environmentVariables
```

### Health Check Commands

```bash
# Check orchestrator health
curl http://voice-agent-orchestrator.eastus.azurecontainer.io:8000/health

# Check realtime health
curl http://voice-agent-realtime.eastus.azurecontainer.io:3000/health

# Check metrics endpoint
curl http://voice-agent-orchestrator.eastus.azurecontainer.io:8000/metrics
```

---

## 📈 Cost Optimization

### 1. Resource Sizing
- **Development**: Use B1ms for PostgreSQL, Standard_B1s for containers
- **Production**: Use Standard_D2s_v3 for AKS nodes, Standard_F2s_v2 for containers

### 2. Reserved Instances
```bash
# Purchase reserved instances for cost savings
az reservations reservation-order purchase \
  --reserved-resource-type VirtualMachines \
  --billing-scope-id "/subscriptions/your-subscription-id" \
  --term P1Y \
  --billing-plan Monthly \
  --quantity 1 \
  --display-name "Voice Agent Reserved Instance"
```

### 3. Auto-shutdown for Development
```bash
# Create auto-shutdown schedule
az vm auto-shutdown \
  --resource-group $RESOURCE_GROUP \
  --name voice-agent-dev-vm \
  --time 1900 \
  --email "your-email@domain.com"
```

---

## 🎯 Next Steps

1. **Set up CI/CD pipeline** with Azure DevOps
2. **Configure custom domain** with Azure DNS
3. **Implement disaster recovery** with Azure Site Recovery
4. **Add performance testing** with Azure Load Testing
5. **Set up compliance monitoring** with Azure Policy

---

## 📞 Support

- **Azure Documentation**: https://docs.microsoft.com/azure/
- **Azure Support**: https://azure.microsoft.com/support/
- **Community Forums**: https://docs.microsoft.com/answers/topics/azure.html

---

**🎉 Congratulations! Your Voice Agent Orchestrator is now deployed on Azure with enterprise-grade infrastructure, monitoring, and security!**
