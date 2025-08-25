# Voice Agent Orchestrator - Technical Documentation

## Table of Contents

1. [System Architecture](#system-architecture)
2. [API Reference](#api-reference)
3. [Voice Provider Integration](#voice-provider-integration)
4. [Deployment Guide](#deployment-guide)
5. [Development Guide](#development-guide)
6. [Troubleshooting](#troubleshooting)
7. [Security Considerations](#security-considerations)
8. [Performance Optimization](#performance-optimization)

## System Architecture

### Overview

The Voice Agent Orchestrator is a distributed system consisting of two main components:

1. **Node.js Realtime Backend** - Handles voice communication and real-time features
2. **Python Orchestrator Backend** - Manages AI agents and conversation intelligence

### Component Interaction

```
┌─────────────────┐    HTTP/WebSocket    ┌──────────────────┐
│   Voice Client  │◄────────────────────►│  Node.js Backend │
│   (Phone/Web)   │                      │  (Port 3000)     │
└─────────────────┘                      └──────────────────┘
                                                │
                                                │ HTTP
                                                ▼
                                       ┌──────────────────┐
                                       │ Python Backend   │
                                       │ (Port 8000)      │
                                       └──────────────────┘
                                                │
                                                ▼
                                       ┌──────────────────┐
                                       │   Databases      │
                                       │ Supabase/Chroma  │
                                       └──────────────────┘
```

### Data Flow

1. **Incoming Call**: Voice provider → Node.js Backend → WebSocket → Python Backend
2. **AI Processing**: Python Backend → AI Agents → Response Generation
3. **Response**: Python Backend → Node.js Backend → Voice Provider → Client

## API Reference

### Node.js Backend API

#### Base URL: `http://localhost:3000`

#### Health Endpoints

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "orchestrator": "connected",
    "voice_provider": "connected"
  }
}
```

#### Voice Provider Management

```http
GET /voice/providers
```

**Response:**
```json
{
  "available_providers": ["twilio", "vonage", "aws-connect", "generic-http"],
  "current_provider": "twilio",
  "providers": {
    "twilio": {
      "name": "Twilio",
      "capabilities": ["voice", "sms", "recording"],
      "status": "active"
    }
  }
}
```

```http
POST /voice/providers/switch
Content-Type: application/json

{
  "provider": "vonage"
}
```

```http
GET /voice/providers/{provider}/capabilities
```

#### Call Management

```http
POST /voice/calls/initiate
Content-Type: application/json

{
  "phone_number": "+1234567890",
  "options": {
    "recording": true,
    "transcription": true
  }
}
```

```http
GET /voice/calls/{callId}/status
```

```http
POST /voice/calls/{callId}/end
```

#### WebSocket Events

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:3000/ws');
```

**Event Types:**
- `call.started` - Call initiated
- `call.ended` - Call completed
- `message.received` - Incoming message
- `message.sent` - Outgoing message
- `error.occurred` - Error event

### Python Backend API

#### Base URL: `http://localhost:8000`

#### Health Check

```http
GET /health
```

#### Agent Management

```http
GET /agents
```

```http
POST /agents/create
Content-Type: application/json

{
  "agent_type": "input",
  "configuration": {
    "model": "gpt-4",
    "temperature": 0.7
  }
}
```

```http
GET /agents/{agentId}/status
```

#### Conversation Management

```http
POST /conversations/{conversationId}/messages
Content-Type: application/json

{
  "message": "Hello, how can I help you?",
  "context": {
    "user_id": "user123",
    "session_id": "session456"
  }
}
```

## Voice Provider Integration

### Provider Interface

All voice providers implement the `BaseDriver` interface:

```javascript
class BaseDriver {
  async initialize() {}
  async makeCall(phoneNumber, options) {}
  async handleWebhook(payload) {}
  async getCapabilities() {}
  async validateConfiguration() {}
}
```

### Provider Configuration

#### Twilio Configuration

```env
VOICE_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=http://localhost:3000/voice/webhook
```

#### Vonage Configuration

```env
VOICE_PROVIDER=vonage
VONAGE_API_KEY=your-api-key
VONAGE_API_SECRET=your-api-secret
VONAGE_APPLICATION_ID=your-application-id
VONAGE_PRIVATE_KEY=your-private-key
VONAGE_PHONE_NUMBER=+1234567890
VONAGE_WEBHOOK_URL=http://localhost:3000/voice/webhook
```

#### AWS Connect Configuration

```env
VOICE_PROVIDER=aws-connect
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_CONNECT_INSTANCE_ID=your-instance-id
AWS_CONNECT_PHONE_NUMBER=+1234567890
AWS_CONNECT_WEBHOOK_URL=http://localhost:3000/voice/webhook
```

### Adding New Providers

1. Create a new driver file in `backend-node-realtime/src/voiceAgent/drivers/`
2. Extend the `BaseDriver` class
3. Implement required methods
4. Add configuration to environment setup
5. Register in the provider registry

## Deployment Guide

### Local Development

```bash
# Clone repository
git clone <repository-url>
cd voiceAgentOrchestrator

# Setup environment
cd backend-node-realtime
node env-setup.js

cd ../backend-python-orchestrator
cp .env.example .env
# Edit .env with your configuration

# Start services
docker-compose up -d
```

### Production Deployment

#### Docker Deployment

```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### Cloud Deployment

##### AWS ECS

```bash
# Deploy to AWS ECS
./deploy.sh aws-ecs
```

**Requirements:**
- AWS CLI configured
- ECS cluster created
- Application Load Balancer configured

##### Google Cloud Run

```bash
# Deploy to Google Cloud Run
./deploy.sh google-cloud-run
```

**Requirements:**
- Google Cloud CLI configured
- Project with billing enabled
- Required APIs enabled

### Environment Variables

#### Production Environment Variables

```env
# Node.js Backend
NODE_ENV=production
PORT=3000
HOST=0.0.0.0

# Voice Provider (configure based on your choice)
VOICE_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your-production-sid
TWILIO_AUTH_TOKEN=your-production-token

# Database
SUPABASE_URL=https://your-production-project.supabase.co
SUPABASE_ANON_KEY=your-production-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-production-service-role-key

# Security
JWT_SECRET=your-production-jwt-secret
CORS_ORIGIN=https://your-domain.com

# Python Backend
DATABASE_URL=postgresql://user:password@host:port/database
OPENAI_API_KEY=your-production-openai-key
```

### SSL/TLS Configuration

For production, configure SSL certificates:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Development Guide

### Project Structure

```
voiceAgentOrchestrator/
├── backend-node-realtime/
│   ├── src/
│   │   ├── voiceAgent/
│   │   │   ├── drivers/           # Voice provider drivers
│   │   │   │   ├── baseDriver.js
│   │   │   │   ├── twilioDriver.js
│   │   │   │   ├── vonageDriver.js
│   │   │   │   └── ...
│   │   │   └── index.js
│   │   ├── routes/
│   │   │   ├── voiceAgent.js
│   │   │   └── supabase.js
│   │   ├── config.js
│   │   └── index.js
│   ├── Dockerfile
│   └── package.json
├── backend-python-orchestrator/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── input_agent.py
│   │   │   ├── memory_agent.py
│   │   │   ├── orchestrator_agent.py
│   │   │   └── tool_agent.py
│   │   ├── auth.py
│   │   ├── config.py
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
└── deploy/
    ├── aws-ecs/
    └── google-cloud-run/
```

### Development Workflow

1. **Setup Development Environment**
   ```bash
   # Install dependencies
   npm install --prefix backend-node-realtime
   pip install -r backend-python-orchestrator/requirements-dev.txt
   ```

2. **Run Development Servers**
   ```bash
   # Node.js backend with hot reload
   cd backend-node-realtime
   npm run dev

   # Python backend with hot reload
   cd backend-python-orchestrator
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Run Tests**
   ```bash
   # Node.js tests
   cd backend-node-realtime
   npm test

   # Python tests
   cd backend-python-orchestrator
   pytest
   ```

### Code Style Guidelines

#### JavaScript/Node.js
- Use ESLint and Prettier
- Follow Airbnb style guide
- Use async/await for asynchronous operations
- Implement proper error handling

#### Python
- Use Black for code formatting
- Follow PEP 8 style guide
- Use type hints
- Implement proper exception handling

### Testing Strategy

#### Unit Tests
- Test individual functions and methods
- Mock external dependencies
- Achieve >80% code coverage

#### Integration Tests
- Test component interactions
- Test API endpoints
- Test database operations

#### End-to-End Tests
- Test complete user workflows
- Test voice call scenarios
- Test error conditions

## Troubleshooting

### Common Issues

#### 1. Environment Variables Not Loading

**Symptoms:**
- Configuration errors on startup
- Missing API keys

**Solutions:**
```bash
# Check .env file location
ls -la backend-node-realtime/.env
ls -la backend-python-orchestrator/.env

# Verify file permissions
chmod 600 backend-node-realtime/.env

# Check environment variable loading
node -e "require('dotenv').config(); console.log(process.env.VOICE_PROVIDER)"
```

#### 2. Voice Provider Connection Issues

**Symptoms:**
- Cannot make calls
- Webhook failures

**Solutions:**
```bash
# Test provider configuration
curl http://localhost:3000/voice/providers/current

# Check provider status
curl http://localhost:3000/voice/providers/test

# Verify webhook URL
curl -X POST http://localhost:3000/voice/webhook/test
```

#### 3. Database Connection Issues

**Symptoms:**
- Database errors in logs
- Failed queries

**Solutions:**
```bash
# Test Supabase connection
curl http://localhost:3000/health/database

# Test ChromaDB connection
curl http://localhost:8000/health/database

# Check database credentials
echo $SUPABASE_URL
echo $DATABASE_URL
```

#### 4. WebSocket Connection Failures

**Symptoms:**
- Real-time updates not working
- Connection timeouts

**Solutions:**
```bash
# Check WebSocket configuration
grep WS_ backend-node-realtime/.env

# Monitor WebSocket connections
curl http://localhost:3000/ws/status

# Check firewall settings
netstat -an | grep 3000
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Node.js backend
DEBUG=true npm start

# Python backend
DEBUG=true uvicorn app.main:app --reload

# Docker with debug
docker-compose -f docker-compose.yml -f docker-compose.debug.yml up
```

### Log Analysis

```bash
# View real-time logs
docker-compose logs -f

# Filter by service
docker-compose logs -f node-backend
docker-compose logs -f python-backend

# Search for errors
docker-compose logs | grep ERROR

# Export logs for analysis
docker-compose logs > logs.txt
```

## Security Considerations

### Authentication & Authorization

1. **JWT Implementation**
   ```javascript
   // JWT middleware
   const jwt = require('jsonwebtoken');
   
   const authenticateToken = (req, res, next) => {
     const token = req.headers['authorization']?.split(' ')[1];
     if (!token) return res.sendStatus(401);
     
     jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
       if (err) return res.sendStatus(403);
       req.user = user;
       next();
     });
   };
   ```

2. **API Key Management**
   - Rotate keys regularly
   - Use environment variables
   - Implement key validation

3. **Rate Limiting**
   ```javascript
   const rateLimit = require('express-rate-limit');
   
   const limiter = rateLimit({
     windowMs: 15 * 60 * 1000, // 15 minutes
     max: 100 // limit each IP to 100 requests per windowMs
   });
   ```

### Data Protection

1. **Encryption**
   - Encrypt sensitive data at rest
   - Use TLS for data in transit
   - Implement secure key management

2. **Input Validation**
   ```javascript
   const { body, validationResult } = require('express-validator');
   
   const validatePhoneNumber = [
     body('phone_number').isMobilePhone(),
     (req, res, next) => {
       const errors = validationResult(req);
       if (!errors.isEmpty()) {
         return res.status(400).json({ errors: errors.array() });
       }
       next();
     }
   ];
   ```

3. **SQL Injection Prevention**
   - Use parameterized queries
   - Validate all inputs
   - Use ORM libraries

### Security Headers

```javascript
const helmet = require('helmet');
const cors = require('cors');

app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN,
  credentials: process.env.CORS_CREDENTIALS === 'true'
}));
```

## Performance Optimization

### Node.js Backend Optimization

1. **Connection Pooling**
   ```javascript
   const pool = new Pool({
     connectionString: process.env.DATABASE_URL,
     max: 20,
     idleTimeoutMillis: 30000,
     connectionTimeoutMillis: 2000,
   });
   ```

2. **Caching**
   ```javascript
   const Redis = require('ioredis');
   const redis = new Redis(process.env.REDIS_URL);
   
   const cacheMiddleware = async (req, res, next) => {
     const key = `cache:${req.originalUrl}`;
     const cached = await redis.get(key);
     if (cached) {
       return res.json(JSON.parse(cached));
     }
     next();
   };
   ```

3. **Load Balancing**
   ```nginx
   upstream node_backend {
     server 127.0.0.1:3001;
     server 127.0.0.1:3002;
     server 127.0.0.1:3003;
   }
   ```

### Python Backend Optimization

1. **Async Operations**
   ```python
   import asyncio
   from fastapi import FastAPI
   
   app = FastAPI()
   
   @app.get("/async-endpoint")
   async def async_endpoint():
       result = await asyncio.gather(
           database_query(),
           external_api_call(),
           cache_operation()
       )
       return result
   ```

2. **Database Optimization**
   ```python
   # Use connection pooling
   from sqlalchemy import create_engine
   
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=30,
       pool_pre_ping=True
   )
   ```

3. **Background Tasks**
   ```python
   from fastapi import BackgroundTasks
   
   @app.post("/process-call")
   async def process_call(background_tasks: BackgroundTasks):
       background_tasks.add_task(process_call_async)
       return {"status": "processing"}
   ```

### Monitoring and Metrics

1. **Application Metrics**
   ```javascript
   const prometheus = require('prom-client');
   
   const httpRequestDurationMicroseconds = new prometheus.Histogram({
     name: 'http_request_duration_seconds',
     help: 'Duration of HTTP requests in seconds',
     labelNames: ['method', 'route', 'code'],
     buckets: [0.1, 0.3, 0.5, 0.7, 1, 3, 5, 7, 10]
   });
   ```

2. **Health Checks**
   ```javascript
   app.get('/health', async (req, res) => {
     const health = {
       status: 'healthy',
       timestamp: new Date().toISOString(),
       uptime: process.uptime(),
       memory: process.memoryUsage(),
       cpu: process.cpuUsage()
     };
     res.json(health);
   });
   ```

3. **Error Tracking**
   ```javascript
   const Sentry = require('@sentry/node');
   
   Sentry.init({
     dsn: process.env.SENTRY_DSN,
     environment: process.env.NODE_ENV
   });
   ```

---

This documentation provides a comprehensive guide for developing, deploying, and maintaining the Voice Agent Orchestrator system. For additional support, refer to the project's GitHub repository or contact the development team. 