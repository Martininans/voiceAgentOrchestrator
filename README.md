# Voice Agent Orchestrator

A comprehensive, production-ready voice agent system with multi-provider support, real-time orchestration, and scalable architecture.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Voice Providers](#voice-providers)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Development](#development)
- [Testing](#testing)
- [Monitoring & Logging](#monitoring--logging)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

Voice Agent Orchestrator is a sophisticated system that enables intelligent voice interactions through multiple voice providers. It consists of two main components:

- **Node.js Realtime Backend**: Handles real-time voice communication, WebSocket connections, and voice provider integrations
- **Python Orchestrator Backend**: Manages AI agents, conversation flow, and intelligent response generation

The system supports multiple voice providers (Twilio, Vonage, AWS Connect, Generic HTTP) with runtime switching capabilities, making it highly flexible and vendor-agnostic.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Voice Client  │    │  Node.js Backend │    │ Python Backend  │
│   (Phone/Web)   │◄──►│  (Realtime)      │◄──►│  (Orchestrator) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Supabase DB   │    │   ChromaDB      │
                       │   (PostgreSQL)  │    │   (Vector DB)   │
                       └─────────────────┘    └─────────────────┘
```

### Core Components

1. **Voice Provider Drivers**: Pluggable drivers for different voice services
2. **WebSocket Manager**: Real-time communication layer
3. **Agent Orchestrator**: AI agent management and conversation flow
4. **Database Layer**: Supabase for structured data, ChromaDB for vector storage
5. **API Gateway**: RESTful endpoints for system management

## ✨ Features

### 🎙️ Voice Capabilities
- **Multi-Provider Support**: Twilio, Vonage, AWS Connect, Generic HTTP
- **Runtime Provider Switching**: Change providers without restart
- **Real-time Communication**: WebSocket-based real-time updates
- **Voice Quality Optimization**: Adaptive audio processing
- **Call Recording**: Automatic call recording and storage

### 🤖 AI & Intelligence
- **Multi-Agent Architecture**: Input, Memory, Tool, and Orchestrator agents
- **Conversation Memory**: Persistent conversation history
- **Context Awareness**: Intelligent context management
- **Tool Integration**: Extensible tool system for external integrations
- **Response Optimization**: Intelligent response generation and optimization

### 🔧 System Features
- **Scalable Architecture**: Microservices-based design
- **High Availability**: Load balancing and failover support
- **Security**: JWT authentication, CORS protection, rate limiting
- **Monitoring**: Comprehensive logging and metrics
- **CI/CD Ready**: Automated deployment pipelines

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- Docker and Docker Compose
- Supabase account
- Voice provider account (Twilio, Vonage, etc.)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd voiceAgentOrchestrator
```

### 2. Environment Configuration

```bash
# Node.js Backend
cd backend-node-realtime
node env-setup.js

# Python Backend
cd ../backend-python-orchestrator
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Services

```bash
# Using Docker Compose (Recommended)
docker-compose up -d

# Or manually
# Terminal 1: Node.js Backend
cd backend-node-realtime
npm install
npm start

# Terminal 2: Python Backend
cd backend-python-orchestrator
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Verify Installation

```bash
# Check Node.js Backend
curl http://localhost:3000/health

# Check Python Backend
curl http://localhost:8000/health

# Check available voice providers
curl http://localhost:3000/voice/providers
```

## 📦 Installation

### Manual Installation

#### Node.js Backend

```bash
cd backend-node-realtime
npm install
npm run build  # If using TypeScript
```

#### Python Backend

```bash
cd backend-python-orchestrator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Docker Installation

```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## ⚙️ Configuration

### Environment Variables

#### Node.js Backend (`.env`)

```env
# Server Configuration
PORT=3000
HOST=0.0.0.0
NODE_ENV=development

# Voice Provider
VOICE_PROVIDER=twilio

# Twilio Configuration
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Python Orchestrator
ORCHESTRATOR_URL=http://localhost:8000
```

#### Python Backend (`.env`)

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/database
CHROMA_HOST=localhost
CHROMA_PORT=8000

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Security
JWT_SECRET=your-jwt-secret
```

### Voice Provider Configuration

See [VOICE_PROVIDERS.md](./VOICE_PROVIDERS.md) for detailed provider-specific configuration.

## 🎙️ Voice Providers

The system supports multiple voice providers with a unified interface:

### Supported Providers

1. **Twilio** - Most popular, extensive features
2. **Vonage** - Global reach, competitive pricing
3. **AWS Connect** - Enterprise-grade, AWS integration
4. **Generic HTTP** - Custom provider integration

### Provider Switching

```bash
# Switch to Vonage
curl -X POST http://localhost:3000/voice/providers/switch \
  -H "Content-Type: application/json" \
  -d '{"provider": "vonage"}'

# Check current provider
curl http://localhost:3000/voice/providers/current
```

## 📚 API Documentation

### Core Endpoints

#### Health Check
```http
GET /health
```

#### Voice Provider Management
```http
GET /voice/providers
GET /voice/providers/current
POST /voice/providers/switch
GET /voice/providers/{provider}/capabilities
```

#### Call Management
```http
POST /voice/calls/initiate
POST /voice/calls/{callId}/end
GET /voice/calls/{callId}/status
```

#### WebSocket Events
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:3000/ws');

// Listen for events
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.payload);
};
```

### Python Orchestrator API

#### Agent Management
```http
GET /agents
POST /agents/create
GET /agents/{agentId}/status
POST /agents/{agentId}/message
```

#### Conversation Management
```http
GET /conversations
GET /conversations/{conversationId}
POST /conversations/{conversationId}/messages
```

## 🚀 Deployment

### Production Deployment

#### Using Docker Compose

```bash
# Production environment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### Cloud Deployment

##### AWS ECS
```bash
# Deploy to AWS ECS
./deploy.sh aws-ecs
```

##### Google Cloud Run
```bash
# Deploy to Google Cloud Run
./deploy.sh google-cloud-run
```

### CI/CD Pipeline

The project includes GitHub Actions workflows for:

- Automated testing
- Security scanning
- Docker image building
- Deployment to staging/production

See [CI_CD_SETUP.md](./CI_CD_SETUP.md) for detailed setup instructions.

## 🛠️ Development

### Project Structure

```
voiceAgentOrchestrator/
├── backend-node-realtime/          # Node.js realtime backend
│   ├── src/
│   │   ├── voiceAgent/            # Voice provider drivers
│   │   ├── routes/                # API routes
│   │   └── config.js              # Configuration
│   ├── Dockerfile
│   └── package.json
├── backend-python-orchestrator/    # Python AI orchestrator
│   ├── app/
│   │   ├── agents/                # AI agents
│   │   ├── auth.py                # Authentication
│   │   └── main.py                # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── deploy/                        # Deployment configurations
├── docker-compose.yml             # Local development
└── README.md                      # This file
```

### Development Workflow

1. **Fork and Clone**
   ```bash
   git clone <your-fork-url>
   cd voiceAgentOrchestrator
   ```

2. **Setup Development Environment**
   ```bash
   # Install dependencies
   npm install --prefix backend-node-realtime
   pip install -r backend-python-orchestrator/requirements-dev.txt
   ```

3. **Run Development Servers**
   ```bash
   # Node.js backend with hot reload
   cd backend-node-realtime
   npm run dev

   # Python backend with hot reload
   cd backend-python-orchestrator
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Run Tests**
   ```bash
   # Node.js tests
   cd backend-node-realtime
   npm test

   # Python tests
   cd backend-python-orchestrator
   pytest
   ```

### Adding New Voice Providers

1. Create a new driver in `backend-node-realtime/src/voiceAgent/drivers/`
2. Extend the `BaseDriver` class
3. Implement required methods
4. Add configuration to `env-setup.js`
5. Update provider registry in `voiceAgent/index.js`

Example:
```javascript
// newProviderDriver.js
const BaseDriver = require('./baseDriver');

class NewProviderDriver extends BaseDriver {
  async initialize() {
    // Provider-specific initialization
  }
  
  async makeCall(phoneNumber, options) {
    // Implement call logic
  }
  
  async handleWebhook(payload) {
    // Handle incoming webhooks
  }
}

module.exports = NewProviderDriver;
```

## 🧪 Testing

### Test Structure

```
├── backend-node-realtime/
│   ├── __tests__/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   └── test/
├── backend-python-orchestrator/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   └── test_*.py
```

### Running Tests

```bash
# All tests
npm run test:all

# Specific test suites
npm run test:unit
npm run test:integration
npm run test:e2e

# Python tests
cd backend-python-orchestrator
pytest tests/
pytest tests/unit/
pytest tests/integration/
```

### Test Coverage

```bash
# Node.js coverage
npm run test:coverage

# Python coverage
cd backend-python-orchestrator
pytest --cov=app tests/
```

## 📊 Monitoring & Logging

### Logging Configuration

The system uses structured logging with multiple levels:

- **ERROR**: System errors and failures
- **WARN**: Warning conditions
- **INFO**: General information
- **DEBUG**: Detailed debugging information

### Metrics and Monitoring

#### Health Checks
```bash
# System health
curl http://localhost:3000/health
curl http://localhost:8000/health

# Detailed health
curl http://localhost:3000/health/detailed
```

#### Performance Metrics
- Call duration and quality
- Response times
- Error rates
- Resource usage

### Log Aggregation

For production environments, configure log aggregation:

```yaml
# docker-compose.prod.yml
services:
  node-backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🔒 Security

### Authentication & Authorization

- **JWT-based authentication** for API access
- **WebSocket authentication** for real-time connections
- **Role-based access control** (RBAC)
- **API key management** for voice providers

### Data Protection

- **Encryption at rest** for sensitive data
- **TLS/SSL** for data in transit
- **Secure environment variables** management
- **Regular security audits**

### Security Best Practices

1. **Environment Variables**: Never commit secrets to version control
2. **API Keys**: Rotate keys regularly
3. **Access Control**: Implement least privilege principle
4. **Monitoring**: Monitor for suspicious activities
5. **Updates**: Keep dependencies updated

### Security Headers

```javascript
// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN,
  credentials: process.env.CORS_CREDENTIALS === 'true'
}));
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Environment Variables Not Loading

**Problem**: Configuration not being read
**Solution**: 
```bash
# Check .env file location
ls -la backend-node-realtime/.env
ls -la backend-python-orchestrator/.env

# Verify file permissions
chmod 600 backend-node-realtime/.env
```

#### 2. Voice Provider Connection Issues

**Problem**: Cannot connect to voice provider
**Solution**:
```bash
# Check provider configuration
curl http://localhost:3000/voice/providers/current

# Test provider connectivity
curl http://localhost:3000/voice/providers/test
```

#### 3. WebSocket Connection Failures

**Problem**: WebSocket connections dropping
**Solution**:
```bash
# Check WebSocket configuration
grep WS_ backend-node-realtime/.env

# Monitor WebSocket connections
curl http://localhost:3000/ws/status
```

#### 4. Database Connection Issues

**Problem**: Cannot connect to Supabase/ChromaDB
**Solution**:
```bash
# Test Supabase connection
curl http://localhost:3000/health/database

# Test ChromaDB connection
curl http://localhost:8000/health/database
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Node.js backend
DEBUG=true npm start

# Python backend
DEBUG=true uvicorn app.main:app --reload
```

### Log Analysis

```bash
# View real-time logs
docker-compose logs -f

# Filter logs by service
docker-compose logs -f node-backend
docker-compose logs -f python-backend

# Search for errors
docker-compose logs | grep ERROR
```

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Contribution Process

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Add tests** for new functionality
5. **Run the test suite**
   ```bash
   npm run test:all
   pytest
   ```
6. **Submit a pull request**

### Code Style

- **Node.js**: ESLint + Prettier
- **Python**: Black + Flake8
- **Commit messages**: Conventional Commits format

### Development Setup

```bash
# Install development dependencies
npm install --prefix backend-node-realtime
pip install -r backend-python-orchestrator/requirements-dev.txt

# Setup pre-commit hooks
npm run setup:dev
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

### Getting Help

- **Documentation**: Check this README and other docs in the project
- **Issues**: Create an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact the maintainers

### Community

- **GitHub**: [Project Repository](https://github.com/your-username/voiceAgentOrchestrator)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/voiceAgentOrchestrator/discussions)
- **Issues**: [GitHub Issues](https://github.com/your-username/voiceAgentOrchestrator/issues)

---

**Voice Agent Orchestrator** - Empowering intelligent voice interactions with multi-provider support and scalable architecture.

*Built with ❤️ for the voice AI community* 