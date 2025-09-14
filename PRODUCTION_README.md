# Voice Agent Orchestrator - Production Deployment Guide

## 🚀 Production-Ready Features

This project has been cleaned up and optimized for production deployment with the following enhancements:

### ✅ Security Enhancements
- **Security Headers**: Helmet.js, CORS, CSP, HSTS
- **Rate Limiting**: Configurable rate limits for different endpoints
- **Input Validation**: Sanitization and validation middleware
- **Authentication**: JWT with Azure AD B2C support
- **Secrets Management**: Environment-based configuration
- **Non-root Containers**: Security-hardened Docker images

### ✅ Monitoring & Health Checks
- **Comprehensive Health Checks**: Database, Redis, Voice Provider, Memory
- **Prometheus Metrics**: Built-in metrics collection
- **Grafana Dashboards**: Pre-configured monitoring
- **Structured Logging**: JSON-formatted logs with rotation
- **Alerting**: Health check failures and performance issues

### ✅ Performance Optimizations
- **Connection Pooling**: Database and Redis connection optimization
- **Caching**: Redis-based caching for improved performance
- **Load Balancing**: Nginx reverse proxy with upstream configuration
- **Resource Limits**: Docker resource constraints
- **Gzip Compression**: Optimized response compression

### ✅ Production Infrastructure
- **Multi-stage Docker Builds**: Optimized production images
- **Health Checks**: Container health monitoring
- **Backup System**: Automated backup with retention policies
- **SSL/TLS**: HTTPS enforcement with security headers
- **Auto-scaling Ready**: Kubernetes and Docker Swarm compatible

## 📋 Prerequisites

### System Requirements
- **Docker**: 20.10+ with Docker Compose 2.0+
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 20GB free space
- **CPU**: 2+ cores recommended

### Required Services
- **Azure PostgreSQL**: For production database
- **Azure Blob Storage**: For file storage
- **Azure Redis Cache**: For caching and sessions
- **Azure OpenAI**: For AI/LLM services
- **Sarvam AI**: For voice services (or other voice provider)

## 🔧 Production Setup

### 1. Environment Configuration

Copy the production environment template:
```bash
cp env.prod .env.prod
```

Edit `.env.prod` with your production values:
```bash
# Voice Provider
VOICE_PROVIDER=sarvam
SARVAM_API_KEY=your_production_api_key
SARVAM_API_SECRET=your_production_api_secret

# Database
DATA_BACKEND=azure_postgres
AZURE_PG_CONNECTION_STRING=postgresql://user:pass@server.postgres.database.azure.com:5432/db?sslmode=require

# Storage
STORAGE_BACKEND=azure_blob
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=account;AccountKey=key;EndpointSuffix=core.windows.net

# Authentication
AUTH_PROVIDER=aad_b2c
AAD_B2C_TENANT_ID=your_tenant_id
AAD_B2C_CLIENT_ID=your_client_id

# AI Services
LLM_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Security
JWT_SECRET=your_super_secure_jwt_secret_key
CORS_ORIGIN=https://your-frontend-domain.com
```

### 2. SSL Certificate Setup

Generate SSL certificates for HTTPS:
```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"
```

### 3. Deploy to Production

Use the production deployment script:
```bash
chmod +x scripts/deploy-prod.sh
./scripts/deploy-prod.sh
```

Or deploy manually:
```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Check health
curl https://your-domain.com/health
```

## 📊 Monitoring Setup

### 1. Access Monitoring Dashboards

- **Grafana**: http://your-domain.com:3001
  - Username: `admin`
  - Password: Set in `GRAFANA_PASSWORD` environment variable

- **Prometheus**: http://your-domain.com:9090

### 2. Health Check Endpoints

- **Basic Health**: `GET /health`
- **Detailed Health**: `GET /health/detailed`
- **Readiness**: `GET /ready`
- **Liveness**: `GET /live`

### 3. Key Metrics to Monitor

- **Response Times**: API endpoint latency
- **Error Rates**: 4xx/5xx response rates
- **Memory Usage**: Container memory consumption
- **Database Connections**: Active connection count
- **Voice Provider Status**: Provider health and response times

## 🔒 Security Configuration

### 1. Network Security
- All services run in isolated Docker network
- Nginx acts as reverse proxy with SSL termination
- Internal service communication over private network

### 2. Authentication
- JWT tokens for API authentication
- Azure AD B2C for user authentication
- WebSocket authentication for real-time connections

### 3. Data Protection
- All data encrypted in transit (TLS 1.2+)
- Sensitive data encrypted at rest
- Regular security updates and patches

## 🗄️ Backup & Recovery

### 1. Automated Backups

Set up automated backups:
```bash
# Add to crontab
0 2 * * * /path/to/scripts/backup.sh --upload-cloud
```

### 2. Backup Contents
- Database snapshots
- Redis data
- ChromaDB vector data
- Configuration files
- Application logs

### 3. Recovery Process
```bash
# Restore from backup
./scripts/restore.sh --backup-name backup-20240101-020000
```

## 🧪 Testing

### 1. Run Health Check Tests
```bash
cd tests
npm install
npm test test_health_checks.js
```

### 2. Run Integration Tests
```bash
cd tests
python -m pytest test_sarvam_integration.py -v
```

### 3. Load Testing
```bash
# Install k6
curl https://github.com/grafana/k6/releases/download/v0.47.0/k6-v0.47.0-linux-amd64.tar.gz -L | tar xvz --strip-components 1

# Run load test
k6 run load-test.js
```

## 📈 Scaling

### 1. Horizontal Scaling
```bash
# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale realtime=3 --scale orchestrator=2
```

### 2. Load Balancer Configuration
Update nginx configuration for multiple backend instances:
```nginx
upstream realtime_backend {
    server realtime_1:3000;
    server realtime_2:3000;
    server realtime_3:3000;
}
```

### 3. Database Scaling
- Use Azure PostgreSQL read replicas
- Implement connection pooling
- Monitor query performance

## 🚨 Troubleshooting

### 1. Common Issues

**Service Not Starting**:
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs realtime
docker-compose -f docker-compose.prod.yml logs orchestrator

# Check health
curl http://localhost:3000/health
curl http://localhost:8000/health
```

**Database Connection Issues**:
```bash
# Test database connection
docker-compose -f docker-compose.prod.yml exec orchestrator python -c "from app.config import Config; print(Config.database())"
```

**Voice Provider Issues**:
```bash
# Test voice provider
curl http://localhost:3000/voice/providers/current
curl http://localhost:3000/voice/providers/test
```

### 2. Performance Issues

**High Memory Usage**:
- Check for memory leaks in logs
- Monitor container resource usage
- Scale services horizontally

**Slow Response Times**:
- Check database query performance
- Monitor Redis cache hit rates
- Review nginx access logs

### 3. Security Issues

**Rate Limiting**:
- Check rate limit configuration
- Monitor for DDoS attacks
- Adjust limits based on usage patterns

**Authentication Failures**:
- Verify JWT secret configuration
- Check Azure AD B2C settings
- Review authentication logs

## 📞 Support

### 1. Logs Location
- **Application Logs**: `/app/logs/` in containers
- **Nginx Logs**: `/var/log/nginx/` in nginx container
- **Docker Logs**: `docker-compose logs [service]`

### 2. Monitoring Alerts
- Set up alerts for health check failures
- Monitor error rates and response times
- Track resource usage trends

### 3. Maintenance
- Regular security updates
- Database maintenance and optimization
- Log rotation and cleanup
- Backup verification

## 🔄 Updates & Maintenance

### 1. Rolling Updates
```bash
# Deploy new version
./scripts/deploy-prod.sh

# Rollback if needed
./scripts/rollback.sh
```

### 2. Database Migrations
```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec orchestrator python -m alembic upgrade head
```

### 3. Configuration Updates
```bash
# Update configuration
docker-compose -f docker-compose.prod.yml down
# Edit configuration files
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🎯 Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database connections tested
- [ ] Voice provider configured
- [ ] Monitoring dashboards accessible
- [ ] Health checks passing
- [ ] Backup system configured
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] Log aggregation working
- [ ] Performance benchmarks met
- [ ] Disaster recovery tested

Your Voice Agent Orchestrator is now production-ready! 🚀












