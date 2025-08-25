# Voice Agent Orchestrator - Troubleshooting Guide

## Table of Contents

1. [Common Issues](#common-issues)
2. [Error Messages](#error-messages)
3. [Debugging Techniques](#debugging-techniques)
4. [Performance Issues](#performance-issues)
5. [Voice Provider Issues](#voice-provider-issues)
6. [Database Issues](#database-issues)
7. [Network Issues](#network-issues)
8. [Deployment Issues](#deployment-issues)
9. [Getting Help](#getting-help)

## Common Issues

### 1. Environment Variables Not Loading

**Symptoms:**
- Configuration errors on startup
- Missing API keys
- Default values being used instead of configured values

**Solutions:**

#### Check .env File Location
```bash
# Node.js Backend
ls -la backend-node-realtime/.env

# Python Backend
ls -la backend-python-orchestrator/.env
```

#### Verify File Permissions
```bash
# Set correct permissions
chmod 600 backend-node-realtime/.env
chmod 600 backend-python-orchestrator/.env
```

#### Test Environment Loading
```bash
# Node.js
node -e "require('dotenv').config(); console.log('VOICE_PROVIDER:', process.env.VOICE_PROVIDER)"

# Python
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('VOICE_PROVIDER:', os.getenv('VOICE_PROVIDER'))"
```

#### Check for Syntax Errors
```bash
# Validate .env file syntax
grep -E "^[A-Z_]+=" backend-node-realtime/.env
grep -E "^[A-Z_]+=" backend-python-orchestrator/.env
```

### 2. Voice Provider Connection Issues

**Symptoms:**
- Cannot make calls
- Webhook failures
- Authentication errors

**Solutions:**

#### Test Provider Configuration
```bash
# Check current provider
curl http://localhost:3000/voice/providers/current

# Test provider connectivity
curl http://localhost:3000/voice/providers/test
```

#### Verify Credentials
```bash
# Check environment variables
echo $TWILIO_ACCOUNT_SID
echo $TWILIO_AUTH_TOKEN
echo $VONAGE_API_KEY
echo $VONAGE_API_SECRET
```

#### Test Provider API Directly
```bash
# Twilio
curl -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN" \
  https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/Calls.json

# Vonage
curl -X GET "https://rest.nexmo.com/account/numbers" \
  -H "Authorization: Bearer $VONAGE_API_KEY"
```

### 3. WebSocket Connection Failures

**Symptoms:**
- Real-time updates not working
- Connection timeouts
- WebSocket errors in browser console

**Solutions:**

#### Check WebSocket Configuration
```bash
# Verify WebSocket settings
grep WS_ backend-node-realtime/.env

# Check WebSocket status
curl http://localhost:3000/ws/status
```

#### Test WebSocket Connection
```javascript
// Browser console or Node.js
const ws = new WebSocket('ws://localhost:3000/ws');

ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => console.log('Message:', event.data);
ws.onerror = (error) => console.error('Error:', error);
ws.onclose = () => console.log('Disconnected');
```

#### Check Firewall Settings
```bash
# Check if port is open
netstat -an | grep 3000
lsof -i :3000

# Test port connectivity
telnet localhost 3000
```

### 4. Database Connection Issues

**Symptoms:**
- Database errors in logs
- Failed queries
- Connection timeouts

**Solutions:**

#### Test Database Connections
```bash
# Test Supabase connection
curl http://localhost:3000/health/database

# Test ChromaDB connection
curl http://localhost:8000/health/database
```

#### Verify Database Credentials
```bash
# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY
echo $DATABASE_URL
echo $CHROMA_HOST
echo $CHROMA_PORT
```

#### Test Direct Database Access
```bash
# PostgreSQL (Supabase)
psql $DATABASE_URL -c "SELECT version();"

# ChromaDB
curl http://$CHROMA_HOST:$CHROMA_PORT/api/v1/heartbeat
```

## Error Messages

### Node.js Backend Errors

#### "Provider not found"
```
Error: Provider 'unknown-provider' not found
```

**Solution:**
```bash
# Check available providers
curl http://localhost:3000/voice/providers

# Verify provider configuration
echo $VOICE_PROVIDER
```

#### "Authentication failed"
```
Error: Authentication failed for provider 'twilio'
```

**Solution:**
```bash
# Verify credentials
echo $TWILIO_ACCOUNT_SID
echo $TWILIO_AUTH_TOKEN

# Test authentication
curl -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN" \
  https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID.json
```

#### "WebSocket connection failed"
```
Error: WebSocket connection failed: ECONNREFUSED
```

**Solution:**
```bash
# Check if WebSocket server is running
ps aux | grep node

# Restart WebSocket server
npm restart --prefix backend-node-realtime
```

### Python Backend Errors

#### "Database connection failed"
```
Error: Could not connect to database
```

**Solution:**
```bash
# Check database URL
echo $DATABASE_URL

# Test database connection
python -c "
import psycopg2
try:
    conn = psycopg2.connect('$DATABASE_URL')
    print('Database connected successfully')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

#### "OpenAI API error"
```
Error: OpenAI API request failed
```

**Solution:**
```bash
# Verify API key
echo $OPENAI_API_KEY

# Test OpenAI API
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

#### "ChromaDB connection failed"
```
Error: Could not connect to ChromaDB
```

**Solution:**
```bash
# Check ChromaDB status
curl http://$CHROMA_HOST:$CHROMA_PORT/api/v1/heartbeat

# Restart ChromaDB
docker-compose restart chromadb
```

### Docker Errors

#### "Container failed to start"
```
Error: Container exited with code 1
```

**Solution:**
```bash
# Check container logs
docker-compose logs node-backend
docker-compose logs python-backend

# Check container status
docker-compose ps

# Restart containers
docker-compose down
docker-compose up -d
```

#### "Port already in use"
```
Error: Port 3000 is already in use
```

**Solution:**
```bash
# Find process using port
lsof -i :3000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different ports
PORT=3001 docker-compose up -d
```

## Debugging Techniques

### Enable Debug Mode

#### Node.js Backend
```bash
# Set debug environment variable
DEBUG=true npm start

# Or use Node.js debugger
node --inspect src/index.js

# Debug specific modules
DEBUG=voice-agent:* npm start
```

#### Python Backend
```bash
# Set debug environment variable
DEBUG=true uvicorn app.main:app --reload

# Use Python debugger
python -m pdb -m uvicorn app.main:app

# Increase log level
uvicorn app.main:app --log-level debug
```

### Log Analysis

#### View Real-time Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f node-backend
docker-compose logs -f python-backend

# Filter by log level
docker-compose logs | grep ERROR
docker-compose logs | grep WARN
```

#### Export Logs for Analysis
```bash
# Export all logs
docker-compose logs > logs.txt

# Export specific service logs
docker-compose logs node-backend > node-logs.txt
docker-compose logs python-backend > python-logs.txt

# Export logs with timestamps
docker-compose logs -t > logs-with-timestamps.txt
```

### Network Debugging

#### Check Network Connectivity
```bash
# Test local connections
curl http://localhost:3000/health
curl http://localhost:8000/health

# Test external connections
curl https://api.twilio.com/2010-04-01/Accounts.json
curl https://api.openai.com/v1/models

# Check DNS resolution
nslookup api.twilio.com
nslookup api.openai.com
```

#### Monitor Network Traffic
```bash
# Monitor HTTP requests
curl -v http://localhost:3000/health

# Use tcpdump for network analysis
sudo tcpdump -i lo0 port 3000
sudo tcpdump -i lo0 port 8000
```

### Performance Debugging

#### Monitor Resource Usage
```bash
# Check CPU and memory usage
top
htop

# Check disk usage
df -h
du -sh *

# Check network usage
iftop
nethogs
```

#### Profile Application Performance
```bash
# Node.js profiling
node --prof src/index.js

# Python profiling
python -m cProfile -o profile.stats app/main.py

# Analyze profiles
node --prof-process isolate-*.log > profile.txt
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"
```

## Performance Issues

### High Memory Usage

**Symptoms:**
- Application crashes
- Slow response times
- Memory leaks

**Solutions:**

#### Check Memory Usage
```bash
# Node.js memory usage
node -e "console.log(process.memoryUsage())"

# Python memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(process.memory_info())
"
```

#### Optimize Memory Usage
```javascript
// Node.js - Use streams for large data
const fs = require('fs');
const { Transform } = require('stream');

const processStream = new Transform({
  transform(chunk, encoding, callback) {
    // Process chunk
    this.push(processedChunk);
    callback();
  }
});

fs.createReadStream('large-file.json')
  .pipe(processStream)
  .pipe(fs.createWriteStream('output.json'));
```

```python
# Python - Use generators for large datasets
def process_large_dataset(data):
    for item in data:
        yield process_item(item)

# Use instead of list comprehension
results = list(process_large_dataset(large_dataset))
```

### Slow Response Times

**Symptoms:**
- API timeouts
- Slow call initiation
- Delayed responses

**Solutions:**

#### Database Optimization
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_calls_phone_number ON calls(phone_number);
CREATE INDEX idx_calls_status ON calls(status);
CREATE INDEX idx_calls_created_at ON calls(created_at);

-- Optimize queries
EXPLAIN ANALYZE SELECT * FROM calls WHERE phone_number = '+1234567890';
```

#### Caching Implementation
```javascript
// Node.js - Redis caching
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

```python
# Python - Redis caching
import redis
import json

redis_client = redis.Redis.from_url(os.getenv('REDIS_URL'))

def cache_result(func):
    def wrapper(*args, **kwargs):
        cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        result = func(*args, **kwargs)
        redis_client.setex(cache_key, 300, json.dumps(result))
        return result
    return wrapper
```

### Connection Pool Exhaustion

**Symptoms:**
- Database connection errors
- Timeout errors
- Resource exhaustion

**Solutions:**

#### Optimize Connection Pools
```javascript
// Node.js - PostgreSQL connection pooling
const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});
```

```python
# Python - Database connection pooling
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

## Voice Provider Issues

### Twilio Issues

#### "Invalid Account SID"
```
Error: Invalid Account SID
```

**Solution:**
```bash
# Verify Account SID format
echo $TWILIO_ACCOUNT_SID
# Should be 34 characters starting with 'AC'

# Test with Twilio API
curl -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN" \
  https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID.json
```

#### "Phone number not verified"
```
Error: Phone number not verified
```

**Solution:**
1. Verify phone number in Twilio console
2. Check phone number format (E.164)
3. Ensure number is active and not suspended

#### "Webhook URL not accessible"
```
Error: Webhook URL not accessible
```

**Solution:**
```bash
# Test webhook URL accessibility
curl -X POST http://localhost:3000/voice/webhook/twilio \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "CallSid=test&CallStatus=ringing"

# Check if server is accessible from internet
# Use ngrok for local development
ngrok http 3000
```

### Vonage Issues

#### "Invalid API credentials"
```
Error: Invalid API credentials
```

**Solution:**
```bash
# Verify API credentials
echo $VONAGE_API_KEY
echo $VONAGE_API_SECRET

# Test with Vonage API
curl -X GET "https://rest.nexmo.com/account/numbers" \
  -H "Authorization: Bearer $VONAGE_API_KEY"
```

#### "Application not found"
```
Error: Application not found
```

**Solution:**
1. Verify Application ID in Vonage console
2. Check Application configuration
3. Ensure Application is active

### AWS Connect Issues

#### "Invalid AWS credentials"
```
Error: Invalid AWS credentials
```

**Solution:**
```bash
# Verify AWS credentials
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
echo $AWS_REGION

# Test AWS credentials
aws sts get-caller-identity
```

#### "Instance not found"
```
Error: Instance not found
```

**Solution:**
1. Verify Instance ID in AWS Console
2. Check Instance status
3. Ensure proper permissions

## Database Issues

### Supabase Issues

#### "Connection timeout"
```
Error: Connection timeout
```

**Solution:**
```bash
# Check Supabase status
curl https://status.supabase.com/api/v2/status.json

# Test connection
psql $DATABASE_URL -c "SELECT version();"

# Check connection pool settings
echo $DATABASE_URL
```

#### "Authentication failed"
```
Error: Authentication failed
```

**Solution:**
```bash
# Verify Supabase credentials
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY
echo $SUPABASE_SERVICE_ROLE_KEY

# Test with Supabase client
node -e "
const { createClient } = require('@supabase/supabase-js');
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_ANON_KEY);
supabase.from('calls').select('*').limit(1).then(console.log);
"
```

### ChromaDB Issues

#### "Connection refused"
```
Error: Connection refused
```

**Solution:**
```bash
# Check ChromaDB status
curl http://$CHROMA_HOST:$CHROMA_PORT/api/v1/heartbeat

# Restart ChromaDB
docker-compose restart chromadb

# Check ChromaDB logs
docker-compose logs chromadb
```

#### "Collection not found"
```
Error: Collection not found
```

**Solution:**
```python
# Create collection if it doesn't exist
import chromadb

client = chromadb.Client()
try:
    collection = client.get_collection("conversations")
except:
    collection = client.create_collection("conversations")
```

## Network Issues

### CORS Issues

**Symptoms:**
- Browser console errors
- API requests blocked
- WebSocket connection failures

**Solutions:**

#### Configure CORS
```javascript
// Node.js - CORS configuration
const cors = require('cors');

app.use(cors({
  origin: process.env.CORS_ORIGIN || '*',
  credentials: process.env.CORS_CREDENTIALS === 'true'
}));
```

#### Test CORS
```bash
# Test CORS headers
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS http://localhost:8000/agents
```

### SSL/TLS Issues

**Symptoms:**
- HTTPS connection errors
- Certificate validation failures
- Mixed content warnings

**Solutions:**

#### Check SSL Certificate
```bash
# Check certificate validity
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Test HTTPS connection
curl -I https://your-domain.com/health
```

#### Configure SSL
```nginx
# Nginx SSL configuration
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

## Deployment Issues

### Docker Deployment Issues

#### "Image build failed"
```
Error: Image build failed
```

**Solution:**
```bash
# Check Dockerfile syntax
docker build --no-cache -t voice-agent .

# Check build context
docker build --progress=plain -t voice-agent .

# Check Docker daemon
docker system info
```

#### "Container health check failed"
```
Error: Container health check failed
```

**Solution:**
```bash
# Check container logs
docker logs <container-id>

# Check health endpoint
curl http://localhost:3000/health

# Restart container
docker restart <container-id>
```

### Cloud Deployment Issues

#### AWS ECS Issues

**Symptoms:**
- Service not starting
- Task definition errors
- Load balancer issues

**Solutions:**
```bash
# Check ECS service status
aws ecs describe-services --cluster your-cluster --services your-service

# Check task definition
aws ecs describe-task-definition --task-definition your-task-definition

# Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix /ecs/voice-agent
```

#### Google Cloud Run Issues

**Symptoms:**
- Service not deploying
- Container startup errors
- Scaling issues

**Solutions:**
```bash
# Check service status
gcloud run services describe voice-agent --region=us-central1

# Check logs
gcloud logs read "resource.type=cloud_run_revision" --limit=50

# Redeploy service
gcloud run deploy voice-agent --source . --region=us-central1
```

## Getting Help

### Self-Service Resources

1. **Documentation**: Check project documentation
2. **GitHub Issues**: Search existing issues
3. **Stack Overflow**: Search for similar problems
4. **Provider Documentation**: Check voice provider docs

### Reporting Issues

When reporting issues, include:

1. **Environment Details**
   - OS version
   - Node.js/Python versions
   - Docker version
   - Deployment environment

2. **Error Information**
   - Full error message
   - Stack trace
   - Log files

3. **Steps to Reproduce**
   - Clear, step-by-step instructions
   - Expected vs actual behavior

4. **Additional Context**
   - Configuration files (sanitized)
   - Screenshots (if applicable)
   - Recent changes

### Contact Information

- **GitHub Issues**: [Project Repository](https://github.com/your-username/voiceAgentOrchestrator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/voiceAgentOrchestrator/discussions)
- **Email**: Contact maintainers

### Emergency Contacts

For critical production issues:

1. **Immediate**: Check system status page
2. **Escalation**: Contact on-call engineer
3. **Provider Support**: Contact voice provider support

---

This troubleshooting guide covers the most common issues and their solutions. For additional support, refer to the project's GitHub repository or contact the development team. 