# Voice Agent Orchestrator - Deployment Guide

## 🚀 Quick Start

### 1. Local Development
```bash
# Start all services locally
docker-compose up -d

# Access services
# - Orchestrator: http://localhost:8000
# - Realtime: http://localhost:3000
# - ChromaDB: http://localhost:8001
```

### 2. Set Environment Variables
Create `.env` files in both backend directories with your credentials.

## ☁️ Cloud Deployment

### AWS ECS
1. Update `deploy/aws-ecs/task-definition.json`
2. Set up AWS Secrets Manager
3. Deploy with AWS CLI

### Google Cloud Run
1. Update `deploy/google-cloud-run/service.yaml`
2. Set up Google Secret Manager
3. Deploy with gcloud CLI

### GitHub Actions CI/CD
The workflow in `.github/workflows/ci-cd.yml` automatically:
- Runs tests and linting
- Builds Docker images
- Deploys to staging/production

## 🔧 Environment Variables

Required for both backends:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `JWT_SECRET`
- `OPENAI_API_KEY`
- `REDIS_URL`

## 🚨 Troubleshooting

Check container logs:
```bash
docker-compose logs orchestrator
docker-compose logs realtime
```

Health checks:
```bash
curl http://localhost:8000/health
curl http://localhost:3000/health
``` 