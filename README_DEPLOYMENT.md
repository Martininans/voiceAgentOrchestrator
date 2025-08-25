# Voice Agent Orchestrator - CI/CD & Deployment Guide

This guide will help you set up continuous integration and deployment for your Voice Agent Orchestrator project, allowing you to take it live while continuing development.

## 🚀 Quick Start

### 1. Local Development with Docker Compose

```bash
# Make the deployment script executable
chmod +x deploy.sh

# Deploy locally
./deploy.sh local
```

### 2. Set Up GitHub Actions CI/CD

The CI/CD pipeline is already configured in `.github/workflows/ci-cd.yml`. It will:

- ✅ Run linting and tests on both Python and Node.js backends
- 🔒 Scan for security vulnerabilities
- 🐳 Build and push Docker images to GitHub Container Registry
- 🚀 Deploy to staging (develop branch) and production (main branch)

## 📋 What's Been Set Up

### 1. GitHub Actions Workflow (`.github/workflows/ci-cd.yml`)
- **Linting & Testing**: Runs flake8, black, and tests for both backends
- **Security Scanning**: Uses Trivy to scan for vulnerabilities
- **Docker Builds**: Builds and pushes images to GitHub Container Registry
- **Multi-Environment Deployment**: Staging (develop) and Production (main)

### 2. Docker Configuration
- **Python Orchestrator** (`backend-python-orchestrator/Dockerfile`)
  - Python 3.11 slim image
  - Non-root user for security
  - Health checks included
  - Optimized for production

- **Node.js Realtime** (`backend-node-realtime/Dockerfile`)
  - Node.js 18 Alpine image
  - Non-root user for security
  - Health checks included
  - Signal handling with dumb-init

### 3. Docker Compose (`docker-compose.yml`)
- Complete local development stack
- Includes Redis and ChromaDB
- Environment variable configuration
- Network isolation

### 4. Cloud Deployment Configurations
- **AWS ECS**: Task definition for Fargate deployment
- **Google Cloud Run**: Service configurations
- **Azure Container Instances**: Ready for deployment
- **DigitalOcean App Platform**: App specification

### 5. Deployment Script (`deploy.sh`)
- Automated deployment to multiple platforms
- Prerequisites checking
- Error handling and colored output
- Support for local, AWS, and GCP deployments

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Node.js        │    │  Python         │
│   (Future)      │◄──►│  Realtime       │◄──►│  Orchestrator   │
│                 │    │  (Port 3000)    │    │  (Port 8000)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Redis       │    │    ChromaDB     │
                       │   (Caching)     │    │  (Vector DB)    │
                       └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────────────────────────────┐
                       │              Supabase                   │
                       │         (Database & Auth)               │
                       └─────────────────────────────────────────┘
```

## 🔧 Environment Setup

### Required Environment Variables

#### Python Orchestrator (`.env`)
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
JWT_SECRET=your-jwt-secret
OPENAI_API_KEY=your-openai-api-key
REDIS_URL=redis://localhost:6379
CHROMA_HOST=localhost
CHROMA_PORT=8000
SECTOR=generic
NODE_ENV=production
```

#### Node.js Realtime (`.env`)
```bash
PORT=3000
HOST=0.0.0.0
VOICE_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=your-twilio-phone-number
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
ORCHESTRATOR_URL=http://localhost:8000
JWT_SECRET=your-jwt-secret
REDIS_URL=redis://localhost:6379
CORS_ORIGIN=*
NODE_ENV=production
```

## 🚀 Deployment Options

### Option 1: Local Development
```bash
# Start all services locally
./deploy.sh local

# Access services
# - Orchestrator: http://localhost:8000
# - Realtime: http://localhost:3000
# - ChromaDB: http://localhost:8001
```

### Option 2: AWS ECS (Recommended for Production)
```bash
# Prerequisites
# 1. Install AWS CLI
# 2. Configure AWS credentials
# 3. Create ECS cluster
# 4. Set up secrets in AWS Secrets Manager

# Deploy
./deploy.sh aws
```

### Option 3: Google Cloud Run
```bash
# Prerequisites
# 1. Install Google Cloud SDK
# 2. Authenticate with gcloud
# 3. Set up secrets in Secret Manager

# Deploy
./deploy.sh gcp
```

### Option 4: Manual Deployment
```bash
# Build images
./deploy.sh build

# Push to registry
./deploy.sh push

# Deploy using your preferred method
```

## 🔄 CI/CD Pipeline Flow

```
┌─────────────────┐
│   Push to Git   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  GitHub Actions │
│   (Automated)   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   Lint & Test   │
│   (Python +     │
│    Node.js)     │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ Security Scan   │
│   (Trivy)       │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ Build & Push    │
│ Docker Images   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   Deploy to     │
│   Environment   │
└─────────────────┘
```

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

## 🔒 Security Features

1. **Container Security**
   - Non-root users in containers
   - Minimal base images
   - Security scanning in CI/CD

2. **Secrets Management**
   - Environment variables for local development
   - Cloud secrets managers for production
   - No secrets in version control

3. **Network Security**
   - Docker network isolation
   - Health checks
   - CORS configuration

## 🚨 Troubleshooting

### Common Issues

1. **Environment Variables Not Loading**
   ```bash
   # Check if .env files exist
   ls -la backend-python-orchestrator/.env
   ls -la backend-node-realtime/.env
   
   # Check environment variables in container
   docker exec <container-name> env
   ```

2. **Container Startup Failures**
   ```bash
   # Check container logs
   docker logs <container-name>
   
   # Check health endpoints
   curl http://localhost:8000/health
   curl http://localhost:3000/health
   ```

3. **Network Connectivity Issues**
   ```bash
   # Check if services can communicate
   docker-compose exec orchestrator ping realtime
   docker-compose exec realtime ping orchestrator
   ```

### Debug Commands

```bash
# View all running containers
docker-compose ps

# View logs for specific service
docker-compose logs orchestrator
docker-compose logs realtime

# Access container shell
docker-compose exec orchestrator bash
docker-compose exec realtime sh

# Check resource usage
docker stats
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

## 🆘 Getting Help

1. **Check the troubleshooting section above**
2. **Review cloud provider documentation**
3. **Check application logs for errors**
4. **Verify environment configuration**

## 🎯 Next Steps

1. **Set up your environment variables**
2. **Choose your deployment platform**
3. **Configure secrets in your cloud provider**
4. **Test the deployment locally first**
5. **Deploy to staging environment**
6. **Monitor and test thoroughly**
7. **Deploy to production**

---

**Remember**: Always test deployments in a staging environment before going to production!

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Supabase Documentation](https://supabase.com/docs) 