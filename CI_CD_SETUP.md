# Voice Agent Orchestrator - CI/CD Setup Guide

This guide covers setting up continuous integration and deployment for your Voice Agent Orchestrator project.

## 🏗️ Architecture Overview

Your application consists of:
- **Python FastAPI Backend** (Orchestrator) - Port 8000
- **Node.js Fastify Backend** (Realtime) - Port 3000
- **Supabase** (Database/Auth)
- **Redis** (Caching/Sessions)
- **ChromaDB** (Vector Storage)

## 🚀 Quick Start with Docker Compose

For local development and testing:

```bash
# 1. Set up environment variables
cp backend-python-orchestrator/.env.example backend-python-orchestrator/.env
cp backend-node-realtime/env-template.txt backend-node-realtime/.env

# 2. Update the .env files with your actual credentials

# 3. Start all services
docker-compose up -d

# 4. Check services
docker-compose ps
```

## ☁️ Cloud Deployment Options

### Option 1: AWS ECS (Recommended for Production)

#### Prerequisites
- AWS CLI configured
- Docker images pushed to ECR or GitHub Container Registry
- AWS Secrets Manager set up

#### Setup Steps

1. **Create AWS Secrets**
```bash
aws secretsmanager create-secret --name supabase-anon-key --secret-string "your-supabase-anon-key"
aws secretsmanager create-secret --name supabase-service-role-key --secret-string "your-supabase-service-role-key"
aws secretsmanager create-secret --name jwt-secret --secret-string "your-jwt-secret"
aws secretsmanager create-secret --name openai-api-key --secret-string "your-openai-api-key"
aws secretsmanager create-secret --name twilio-account-sid --secret-string "your-twilio-account-sid"
aws secretsmanager create-secret --name twilio-auth-token --secret-string "your-twilio-auth-token"
aws secretsmanager create-secret --name twilio-phone-number --secret-string "your-twilio-phone-number"
aws secretsmanager create-secret --name redis-url --secret-string "redis://your-redis-endpoint:6379"
```

2. **Update Task Definition**
Edit `deploy/aws-ecs/task-definition.json`:
- Replace `YOUR_ACCOUNT_ID` with your AWS account ID
- Replace `YOUR_USERNAME` with your GitHub username
- Update image URLs to match your registry

3. **Deploy to ECS**
```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://deploy/aws-ecs/task-definition.json

# Create ECS service
aws ecs create-service \
  --cluster your-cluster-name \
  --service-name voice-agent-orchestrator \
  --task-definition voice-agent-orchestrator:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

### Option 2: Google Cloud Run

#### Prerequisites
- Google Cloud SDK installed
- Docker images pushed to Google Container Registry
- Google Cloud Secrets Manager set up

#### Setup Steps

1. **Create Google Cloud Secrets**
```bash
echo -n "your-supabase-anon-key" | gcloud secrets create supabase-anon-key --data-file=-
echo -n "your-jwt-secret" | gcloud secrets create jwt-secret --data-file=-
echo -n "your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-
# ... repeat for other secrets
```

2. **Create Secret Manager Secret**
```bash
gcloud secrets create voice-agent-secrets --replication-policy="automatic"
gcloud secrets versions add voice-agent-secrets --data-file=secrets.yaml
```

3. **Deploy Services**
```bash
# Update service.yaml with your project ID
sed -i 's/YOUR_PROJECT_ID/your-actual-project-id/g' deploy/google-cloud-run/service.yaml

# Deploy orchestrator
gcloud run services replace deploy/google-cloud-run/service.yaml

# Deploy realtime service
gcloud run services replace deploy/google-cloud-run/service.yaml
```

### Option 3: Azure Container Instances

#### Prerequisites
- Azure CLI installed
- Docker images pushed to Azure Container Registry

#### Setup Steps

1. **Create Azure Key Vault**
```bash
az keyvault create --name voice-agent-kv --resource-group your-rg --location eastus
az keyvault secret set --vault-name voice-agent-kv --name supabase-anon-key --value "your-supabase-anon-key"
# ... repeat for other secrets
```

2. **Deploy Containers**
```bash
# Deploy orchestrator
az container create \
  --resource-group your-rg \
  --name voice-agent-orchestrator \
  --image your-registry.azurecr.io/voice-agent-orchestrator:latest \
  --dns-name-label voice-agent-orchestrator \
  --ports 8000 \
  --environment-variables SUPABASE_URL=https://your-project.supabase.co

# Deploy realtime
az container create \
  --resource-group your-rg \
  --name voice-agent-realtime \
  --image your-registry.azurecr.io/voice-agent-realtime:latest \
  --dns-name-label voice-agent-realtime \
  --ports 3000 \
  --environment-variables ORCHESTRATOR_URL=http://voice-agent-orchestrator.eastus.azurecontainer.io:8000
```

### Option 4: DigitalOcean App Platform

#### Prerequisites
- DigitalOcean account
- Docker images pushed to DigitalOcean Container Registry

#### Setup Steps

1. **Create App Specification**
```yaml
# .do/app.yaml
name: voice-agent-orchestrator
services:
- name: orchestrator
  source_dir: /backend-python-orchestrator
  github:
    repo: your-username/voiceAgentOrchestrator
    branch: main
  run_command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
  environment_slug: python
  instance_count: 2
  instance_size_slug: basic-xxs
  envs:
  - key: SUPABASE_URL
    value: https://your-project.supabase.co
  - key: SUPABASE_ANON_KEY
    value: ${SUPABASE_ANON_KEY}
  - key: JWT_SECRET
    value: ${JWT_SECRET}
  - key: OPENAI_API_KEY
    value: ${OPENAI_API_KEY}

- name: realtime
  source_dir: /backend-node-realtime
  github:
    repo: your-username/voiceAgentOrchestrator
    branch: main
  run_command: node src/index.js
  environment_slug: node-js
  instance_count: 2
  instance_size_slug: basic-xxs
  envs:
  - key: PORT
    value: "3000"
  - key: ORCHESTRATOR_URL
    value: ${ORCHESTRATOR_URL}
  - key: SUPABASE_ANON_KEY
    value: ${SUPABASE_ANON_KEY}
  - key: JWT_SECRET
    value: ${JWT_SECRET}
```

2. **Deploy**
```bash
doctl apps create --spec .do/app.yaml
```

## 🔧 Environment Configuration

### Required Environment Variables

#### Python Orchestrator
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
JWT_SECRET=your-jwt-secret
OPENAI_API_KEY=your-openai-api-key
REDIS_URL=redis://your-redis-endpoint:6379
CHROMA_HOST=your-chromadb-host
CHROMA_PORT=8000
SECTOR=generic
NODE_ENV=production
```

#### Node.js Realtime
```bash
PORT=3000
HOST=0.0.0.0
VOICE_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=your-twilio-phone-number
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
ORCHESTRATOR_URL=http://orchestrator:8000
JWT_SECRET=your-jwt-secret
REDIS_URL=redis://your-redis-endpoint:6379
CORS_ORIGIN=*
NODE_ENV=production
```

## 🔒 Security Best Practices

1. **Secrets Management**
   - Use cloud provider's secrets manager (AWS Secrets Manager, Google Secret Manager, Azure Key Vault)
   - Never commit secrets to version control
   - Rotate secrets regularly

2. **Network Security**
   - Use VPC/private subnets where possible
   - Configure security groups/firewall rules
   - Enable HTTPS/TLS encryption

3. **Container Security**
   - Use non-root users in containers
   - Scan images for vulnerabilities
   - Keep base images updated

4. **Monitoring & Logging**
   - Set up centralized logging (CloudWatch, Stackdriver, etc.)
   - Configure health checks
   - Set up alerts for critical metrics

## 📊 Monitoring & Health Checks

### Health Check Endpoints
- **Orchestrator**: `GET /health`
- **Realtime**: `GET /health`

### Key Metrics to Monitor
- Response times
- Error rates
- Memory usage
- CPU usage
- Database connections
- WebSocket connections

## 🚨 Troubleshooting

### Common Issues

1. **Environment Variables Not Loading**
   - Check secret names match exactly
   - Verify secret values are not empty
   - Ensure proper permissions for secret access

2. **Container Startup Failures**
   - Check container logs
   - Verify health check endpoints
   - Ensure all dependencies are available

3. **Network Connectivity Issues**
   - Verify security group rules
   - Check VPC/subnet configuration
   - Test service-to-service communication

### Debug Commands

```bash
# Check container logs
docker logs <container-name>

# Check service health
curl http://localhost:8000/health
curl http://localhost:3000/health

# Check environment variables
docker exec <container-name> env

# Test database connectivity
docker exec <container-name> python -c "import redis; r = redis.Redis.from_url('$REDIS_URL'); print(r.ping())"
```

## 🔄 CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) automatically:
1. Runs linting and tests
2. Scans for security vulnerabilities
3. Builds and pushes Docker images
4. Deploys to staging (develop branch)
5. Deploys to production (main branch)

### Manual Deployment

```bash
# Build and push images
docker build -t your-registry/voice-agent-orchestrator:latest ./backend-python-orchestrator
docker build -t your-registry/voice-agent-realtime:latest ./backend-node-realtime
docker push your-registry/voice-agent-orchestrator:latest
docker push your-registry/voice-agent-realtime:latest

# Deploy using your cloud provider's CLI
```

## 📈 Scaling Considerations

1. **Horizontal Scaling**
   - Use load balancers
   - Configure auto-scaling policies
   - Distribute traffic across multiple instances

2. **Database Scaling**
   - Use managed database services
   - Configure read replicas
   - Implement connection pooling

3. **Caching Strategy**
   - Use Redis for session storage
   - Implement API response caching
   - Cache frequently accessed data

## 🆘 Support

For deployment issues:
1. Check the troubleshooting section above
2. Review cloud provider documentation
3. Check application logs for errors
4. Verify environment configuration

---

**Remember**: Always test deployments in a staging environment before going to production! 