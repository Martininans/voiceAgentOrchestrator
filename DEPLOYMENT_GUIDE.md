# Voice Agent Orchestrator - Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Cloud Platform Deployment](#cloud-platform-deployment)
5. [Monitoring & Logging](#monitoring--logging)
6. [Scaling & Performance](#scaling--performance)
7. [Security Configuration](#security-configuration)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Node.js**: 18.x or higher
- **Python**: 3.9 or higher
- **Docker**: 20.10 or higher
- **Docker Compose**: 2.0 or higher
- **Git**: Latest version

### Cloud Requirements

- **AWS Account** (for ECS deployment)
- **Google Cloud Account** (for Cloud Run deployment)
- **Supabase Account** (for database)
- **Voice Provider Account** (Twilio, Vonage, etc.)

### Network Requirements

- **Ports**: 3000 (Node.js), 8000 (Python), 5432 (PostgreSQL), 8000 (ChromaDB)
- **SSL Certificate**: For production HTTPS
- **Domain Name**: For production deployment

## Local Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd voiceAgentOrchestrator
```

### 2. Environment Configuration

#### Node.js Backend Setup

```bash
cd backend-node-realtime

# Run interactive setup
node env-setup.js

# Or manually create .env file
cp .env.example .env
# Edit .env with your configuration
```

#### Python Backend Setup

```bash
cd backend-python-orchestrator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your configuration
```

### 3. Database Setup

#### Supabase Setup

1. Create a new project at [supabase.com](https://supabase.com)
2. Get your project URL and API keys
3. Update your `.env` files with Supabase credentials

#### ChromaDB Setup

```bash
# Start ChromaDB locally
docker run -p 8000:8000 chromadb/chroma:latest

# Or use the provided docker-compose
docker-compose up chromadb -d
```

### 4. Start Development Environment

#### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Manual Startup

```bash
# Terminal 1: Node.js Backend
cd backend-node-realtime
npm install
npm run dev

# Terminal 2: Python Backend
cd backend-python-orchestrator
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: ChromaDB (if not using Docker)
docker run -p 8000:8000 chromadb/chroma:latest
```

### 5. Verify Installation

```bash
# Test Node.js Backend
curl http://localhost:3000/health

# Test Python Backend
curl http://localhost:8000/health

# Test voice providers
curl http://localhost:3000/voice/providers
```

## Production Deployment

### 1. Production Environment Variables

#### Node.js Backend (`.env`)

```env
# Server Configuration
NODE_ENV=production
PORT=3000
HOST=0.0.0.0

# Voice Provider Configuration
VOICE_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your-production-sid
TWILIO_AUTH_TOKEN=your-production-token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=https://your-domain.com/voice/webhook

# Supabase Configuration
SUPABASE_URL=https://your-production-project.supabase.co
SUPABASE_ANON_KEY=your-production-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-production-service-role-key

# Python Orchestrator Configuration
ORCHESTRATOR_URL=https://your-domain.com:8000
ORCHESTRATOR_TIMEOUT=30000
ORCHESTRATOR_RETRIES=3

# Security Configuration
JWT_SECRET=your-production-jwt-secret
CORS_ORIGIN=https://your-domain.com
CORS_CREDENTIALS=true

# Logging Configuration
LOG_LEVEL=info
LOG_FORMAT=json

# Performance Configuration
MAX_WS_CONNECTIONS=1000
WS_HEARTBEAT_INTERVAL=30000
```

#### Python Backend (`.env`)

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database
CHROMA_HOST=your-chromadb-host
CHROMA_PORT=8000

# OpenAI Configuration
OPENAI_API_KEY=your-production-openai-key

# Security Configuration
JWT_SECRET=your-production-jwt-secret
SECRET_KEY=your-production-secret-key

# Performance Configuration
WORKERS=4
MAX_CONNECTIONS=100
```

### 2. Docker Production Build

```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

### 3. SSL/TLS Configuration

#### Using Let's Encrypt

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot

# Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com

# Configure Nginx
sudo nano /etc/nginx/sites-available/voice-agent
```

#### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Node.js Backend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Python Backend
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:3000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Systemd Service Configuration

#### Node.js Service

```ini
# /etc/systemd/system/voice-agent-node.service
[Unit]
Description=Voice Agent Node.js Backend
After=network.target

[Service]
Type=simple
User=voice-agent
WorkingDirectory=/opt/voice-agent/backend-node-realtime
Environment=NODE_ENV=production
ExecStart=/usr/bin/node src/index.js
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Python Service

```ini
# /etc/systemd/system/voice-agent-python.service
[Unit]
Description=Voice Agent Python Backend
After=network.target

[Service]
Type=simple
User=voice-agent
WorkingDirectory=/opt/voice-agent/backend-python-orchestrator
Environment=PATH=/opt/voice-agent/backend-python-orchestrator/venv/bin
ExecStart=/opt/voice-agent/backend-python-orchestrator/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Enable Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable voice-agent-node
sudo systemctl enable voice-agent-python
sudo systemctl start voice-agent-node
sudo systemctl start voice-agent-python
```

## Cloud Platform Deployment

### AWS ECS Deployment

#### 1. Prerequisites

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS CLI
aws configure
```

#### 2. Create ECS Cluster

```bash
# Create cluster
aws ecs create-cluster --cluster-name voice-agent-cluster

# Create task definition
aws ecs register-task-definition --cli-input-json file://deploy/aws-ecs/task-definition.json

# Create service
aws ecs create-service --cli-input-json file://deploy/aws-ecs/service-definition.json
```

#### 3. Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer --cli-input-json file://deploy/aws-ecs/alb-definition.json

# Create target group
aws elbv2 create-target-group --cli-input-json file://deploy/aws-ecs/target-group-definition.json
```

#### 4. Deploy Using Script

```bash
# Run deployment script
./deploy.sh aws-ecs
```

### Google Cloud Run Deployment

#### 1. Prerequisites

```bash
# Install Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize and authenticate
gcloud init
gcloud auth login
```

#### 2. Enable Required APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### 3. Build and Deploy

```bash
# Build and push images
gcloud builds submit --tag gcr.io/PROJECT_ID/voice-agent-node
gcloud builds submit --tag gcr.io/PROJECT_ID/voice-agent-python

# Deploy to Cloud Run
gcloud run deploy voice-agent-node --image gcr.io/PROJECT_ID/voice-agent-node --platform managed --region us-central1 --allow-unauthenticated

gcloud run deploy voice-agent-python --image gcr.io/PROJECT_ID/voice-agent-python --platform managed --region us-central1 --allow-unauthenticated
```

#### 4. Deploy Using Script

```bash
# Run deployment script
./deploy.sh google-cloud-run
```

### Kubernetes Deployment

#### 1. Create Namespace

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: voice-agent
```

#### 2. Deploy Services

```bash
# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

## Monitoring & Logging

### Application Monitoring

#### Health Checks

```bash
# Automated health checks
curl -f http://localhost:3000/health || exit 1
curl -f http://localhost:8000/health || exit 1
```

#### Prometheus Metrics

```javascript
// Node.js metrics
const prometheus = require('prom-client');

const httpRequestDurationMicroseconds = new prometheus.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'code'],
  buckets: [0.1, 0.3, 0.5, 0.7, 1, 3, 5, 7, 10]
});

// Expose metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', prometheus.register.contentType);
  res.end(await prometheus.register.metrics());
});
```

#### Grafana Dashboards

```json
{
  "dashboard": {
    "title": "Voice Agent Orchestrator",
    "panels": [
      {
        "title": "Active Calls",
        "type": "stat",
        "targets": [
          {
            "expr": "voice_calls_active",
            "legendFormat": "Active Calls"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_request_duration_seconds_sum[5m])",
            "legendFormat": "Response Time"
          }
        ]
      }
    ]
  }
}
```

### Logging Configuration

#### Structured Logging

```javascript
// Node.js logging
const winston = require('winston');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'voice-agent-node' },
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});

if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.simple()
  }));
}
```

#### Log Aggregation

```yaml
# docker-compose.prod.yml
services:
  node-backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        tag: "{{.Name}}"
  
  python-backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        tag: "{{.Name}}"
```

### Alerting

#### Prometheus Alert Rules

```yaml
# prometheus/alerts.yml
groups:
  - name: voice-agent
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "Service {{ $labels.instance }} is down"
```

## Scaling & Performance

### Horizontal Scaling

#### Load Balancer Configuration

```nginx
upstream node_backend {
    least_conn;
    server 127.0.0.1:3001;
    server 127.0.0.1:3002;
    server 127.0.0.1:3003;
    server 127.0.0.1:3004;
}

upstream python_backend {
    least_conn;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
    server 127.0.0.1:8004;
}
```

#### Auto Scaling

```yaml
# AWS ECS Auto Scaling
{
  "AutoScalingTarget": {
    "MinCapacity": 2,
    "MaxCapacity": 10,
    "TargetCapacity": 5
  },
  "ScalingPolicies": [
    {
      "PolicyName": "ScaleUp",
      "ScalingAdjustment": 1,
      "AdjustmentType": "ChangeInCapacity",
      "Cooldown": 300
    }
  ]
}
```

### Performance Optimization

#### Database Optimization

```sql
-- PostgreSQL optimization
CREATE INDEX idx_calls_phone_number ON calls(phone_number);
CREATE INDEX idx_calls_status ON calls(status);
CREATE INDEX idx_calls_created_at ON calls(created_at);

-- Connection pooling
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
```

#### Caching Strategy

```javascript
// Redis caching
const Redis = require('ioredis');
const redis = new Redis(process.env.REDIS_URL);

const cacheMiddleware = async (req, res, next) => {
  const key = `cache:${req.originalUrl}`;
  const cached = await redis.get(key);
  
  if (cached) {
    return res.json(JSON.parse(cached));
  }
  
  res.sendResponse = res.json;
  res.json = (body) => {
    redis.setex(key, 300, JSON.stringify(body)); // Cache for 5 minutes
    res.sendResponse(body);
  };
  
  next();
};
```

## Security Configuration

### Network Security

#### Firewall Configuration

```bash
# UFW firewall rules
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 3000/tcp
sudo ufw deny 8000/tcp
sudo ufw enable
```

#### VPN Configuration

```bash
# WireGuard VPN setup
sudo apt-get install wireguard

# Generate keys
wg genkey | sudo tee /etc/wireguard/private.key
sudo cat /etc/wireguard/private.key | wg pubkey | sudo tee /etc/wireguard/public.key

# Configure WireGuard
sudo nano /etc/wireguard/wg0.conf
```

### Application Security

#### Security Headers

```javascript
// Security middleware
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP'
});

app.use('/api/', limiter);
```

#### Input Validation

```javascript
// Joi validation
const Joi = require('joi');

const callSchema = Joi.object({
  phone_number: Joi.string().pattern(/^\+[1-9]\d{1,14}$/).required(),
  options: Joi.object({
    recording: Joi.boolean().default(false),
    transcription: Joi.boolean().default(false),
    timeout: Joi.number().integer().min(1).max(300).default(30)
  }).default({})
});

const validateCall = (req, res, next) => {
  const { error, value } = callSchema.validate(req.body);
  if (error) {
    return res.status(400).json({
      error: {
        code: 'VALIDATION_ERROR',
        message: error.details[0].message
      }
    });
  }
  req.validatedBody = value;
  next();
};
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check service status
sudo systemctl status voice-agent-node
sudo systemctl status voice-agent-python

# Check logs
sudo journalctl -u voice-agent-node -f
sudo journalctl -u voice-agent-python -f

# Check port availability
sudo netstat -tulpn | grep :3000
sudo netstat -tulpn | grep :8000
```

#### 2. Database Connection Issues

```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1;"

# Check connection pool
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### 3. Memory Issues

```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Check for memory leaks
node --inspect src/index.js

# Monitor with htop
htop
```

#### 4. Network Issues

```bash
# Test connectivity
curl -v http://localhost:3000/health
curl -v http://localhost:8000/health

# Check DNS resolution
nslookup your-domain.com

# Test SSL certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=debug

# Start services in debug mode
npm run dev
uvicorn app.main:app --reload --log-level debug
```

### Performance Profiling

```bash
# Node.js profiling
node --prof src/index.js

# Python profiling
python -m cProfile -o profile.stats app/main.py

# Analyze profiles
node --prof-process isolate-*.log > profile.txt
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"
```

---

This deployment guide provides comprehensive instructions for deploying the Voice Agent Orchestrator in various environments. For additional support, refer to the project's GitHub repository or contact the development team. 