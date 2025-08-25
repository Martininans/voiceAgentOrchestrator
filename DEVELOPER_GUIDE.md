# Voice Agent Orchestrator - Developer Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Project Architecture](#project-architecture)
4. [Development Workflow](#development-workflow)
5. [Testing Strategy](#testing-strategy)
6. [Code Standards](#code-standards)
7. [Adding Features](#adding-features)
8. [Debugging](#debugging)
9. [Performance Optimization](#performance-optimization)
10. [Contributing Guidelines](#contributing-guidelines)

## Getting Started

### Prerequisites

- **Node.js**: 18.x or higher
- **Python**: 3.9 or higher
- **Git**: Latest version
- **Docker**: 20.10 or higher (optional)
- **VS Code**: Recommended IDE with extensions

### Required VS Code Extensions

```json
{
  "recommendations": [
    "ms-vscode.vscode-typescript-next",
    "ms-python.python",
    "ms-python.black-formatter",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-eslint",
    "ms-vscode.vscode-json",
    "ms-vscode.vscode-yaml",
    "redhat.vscode-yaml",
    "ms-azuretools.vscode-docker"
  ]
}
```

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd voiceAgentOrchestrator

# Install Node.js dependencies
cd backend-node-realtime
npm install

# Install Python dependencies
cd ../backend-python-orchestrator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

# Setup environment variables
cd ../backend-node-realtime
node env-setup.js

cd ../backend-python-orchestrator
cp .env.example .env
# Edit .env with your configuration
```

## Development Environment

### Project Structure

```
voiceAgentOrchestrator/
├── backend-node-realtime/          # Node.js realtime backend
│   ├── src/
│   │   ├── voiceAgent/            # Voice provider drivers
│   │   │   ├── drivers/           # Provider implementations
│   │   │   │   ├── baseDriver.js  # Base driver interface
│   │   │   │   ├── twilioDriver.js
│   │   │   │   ├── vonageDriver.js
│   │   │   │   └── ...
│   │   │   └── index.js           # Driver registry
│   │   ├── routes/                # API routes
│   │   │   ├── voiceAgent.js      # Voice-related endpoints
│   │   │   └── supabase.js        # Database operations
│   │   ├── config.js              # Configuration management
│   │   └── index.js               # Main application
│   ├── __tests__/                 # Test files
│   ├── Dockerfile                 # Container configuration
│   └── package.json
├── backend-python-orchestrator/    # Python AI orchestrator
│   ├── app/
│   │   ├── agents/                # AI agent implementations
│   │   │   ├── input_agent.py     # Input processing agent
│   │   │   ├── memory_agent.py    # Memory management agent
│   │   │   ├── orchestrator_agent.py # Main orchestrator
│   │   │   └── tool_agent.py      # Tool integration agent
│   │   ├── auth.py                # Authentication logic
│   │   ├── config.py              # Configuration management
│   │   └── main.py                # FastAPI application
│   ├── tests/                     # Test files
│   ├── Dockerfile                 # Container configuration
│   └── requirements.txt
├── deploy/                        # Deployment configurations
├── docs/                          # Documentation
└── docker-compose.yml             # Local development
```

### Development Scripts

#### Node.js Backend

```json
{
  "scripts": {
    "dev": "nodemon src/index.js",
    "start": "node src/index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src/",
    "lint:fix": "eslint src/ --fix",
    "format": "prettier --write src/",
    "build": "npm run lint && npm test"
  }
}
```

#### Python Backend

```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Testing
pytest tests/
pytest tests/ --cov=app --cov-report=html

# Linting
black app/ tests/
flake8 app/ tests/

# Type checking
mypy app/
```

### Environment Configuration

#### Development Environment Variables

```env
# Node.js Backend (.env)
NODE_ENV=development
PORT=3000
HOST=0.0.0.0
DEBUG=true

# Voice Provider (use test credentials)
VOICE_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your-test-sid
TWILIO_AUTH_TOKEN=your-test-token
TWILIO_PHONE_NUMBER=+1234567890

# Supabase (use development project)
SUPABASE_URL=https://your-dev-project.supabase.co
SUPABASE_ANON_KEY=your-dev-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-dev-service-role-key

# Python Backend (.env)
DATABASE_URL=postgresql://user:password@localhost:5432/voice_agent_dev
CHROMA_HOST=localhost
CHROMA_PORT=8000
OPENAI_API_KEY=your-openai-key
```

## Project Architecture

### System Components

#### 1. Voice Provider Layer
- **Purpose**: Interface with voice communication services
- **Components**: Driver implementations, provider registry
- **Key Files**: `baseDriver.js`, `twilioDriver.js`, `vonageDriver.js`

#### 2. Real-time Communication Layer
- **Purpose**: Handle WebSocket connections and real-time updates
- **Components**: WebSocket server, connection management
- **Key Files**: `index.js` (WebSocket setup)

#### 3. API Gateway Layer
- **Purpose**: RESTful API endpoints for system management
- **Components**: Express routes, middleware, validation
- **Key Files**: `routes/voiceAgent.js`, `routes/supabase.js`

#### 4. AI Orchestration Layer
- **Purpose**: Manage AI agents and conversation flow
- **Components**: Agent implementations, conversation management
- **Key Files**: `agents/orchestrator_agent.py`, `agents/memory_agent.py`

#### 5. Data Layer
- **Purpose**: Persistent storage and data management
- **Components**: Supabase integration, ChromaDB
- **Key Files**: `routes/supabase.js`, `config.py`

### Data Flow

```
1. Voice Call → Voice Provider → Node.js Backend
2. Node.js Backend → WebSocket → Python Backend
3. Python Backend → AI Agents → Response Generation
4. Python Backend → Node.js Backend → Voice Provider
5. Voice Provider → User
```

## Development Workflow

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add new voice provider support"

# Push to remote
git push origin feature/your-feature-name

# Create pull request
# Merge after review
```

### Conventional Commits

```bash
# Commit message format
<type>(<scope>): <description>

# Examples
feat(voice): add Vonage provider support
fix(api): resolve authentication issue
docs(readme): update installation instructions
test(providers): add unit tests for Twilio driver
refactor(agents): improve memory management
```

### Development Commands

```bash
# Start development environment
docker-compose up -d

# Run tests
npm test --prefix backend-node-realtime
cd backend-python-orchestrator && pytest

# Check code quality
npm run lint --prefix backend-node-realtime
cd backend-python-orchestrator && black app/ && flake8 app/

# Build and test
npm run build --prefix backend-node-realtime
```

## Testing Strategy

### Test Structure

#### Node.js Tests

```
backend-node-realtime/
├── __tests__/
│   ├── unit/
│   │   ├── drivers/
│   │   │   ├── twilioDriver.test.js
│   │   │   └── vonageDriver.test.js
│   │   ├── routes/
│   │   │   ├── voiceAgent.test.js
│   │   │   └── supabase.test.js
│   │   └── utils/
│   │       └── helpers.test.js
│   ├── integration/
│   │   ├── api.test.js
│   │   └── websocket.test.js
│   └── e2e/
│       └── voice-call.test.js
```

#### Python Tests

```
backend-python-orchestrator/
├── tests/
│   ├── unit/
│   │   ├── test_agents/
│   │   │   ├── test_input_agent.py
│   │   │   ├── test_memory_agent.py
│   │   │   └── test_orchestrator_agent.py
│   │   ├── test_auth.py
│   │   └── test_config.py
│   ├── integration/
│   │   ├── test_api.py
│   │   └── test_database.py
│   └── e2e/
│       └── test_conversation_flow.py
```

### Writing Tests

#### Node.js Unit Tests

```javascript
// __tests__/unit/drivers/twilioDriver.test.js
const TwilioDriver = require('../../src/voiceAgent/drivers/twilioDriver');

describe('TwilioDriver', () => {
  let driver;

  beforeEach(() => {
    driver = new TwilioDriver();
  });

  describe('initialize', () => {
    it('should initialize with valid credentials', async () => {
      const result = await driver.initialize();
      expect(result).toBe(true);
    });

    it('should throw error with invalid credentials', async () => {
      process.env.TWILIO_ACCOUNT_SID = 'invalid';
      await expect(driver.initialize()).rejects.toThrow();
    });
  });

  describe('makeCall', () => {
    it('should initiate call successfully', async () => {
      const result = await driver.makeCall('+1234567890');
      expect(result.callId).toBeDefined();
      expect(result.status).toBe('initiating');
    });
  });
});
```

#### Python Unit Tests

```python
# tests/unit/test_agents/test_input_agent.py
import pytest
from unittest.mock import Mock, patch
from app.agents.input_agent import InputAgent

class TestInputAgent:
    @pytest.fixture
    def agent(self):
        return InputAgent()

    def test_process_input(self, agent):
        # Arrange
        input_text = "Hello, how can you help me?"
        
        # Act
        result = agent.process_input(input_text)
        
        # Assert
        assert result is not None
        assert "response" in result
        assert result["confidence"] > 0.5

    @patch('app.agents.input_agent.openai.ChatCompletion.create')
    def test_openai_integration(self, mock_openai, agent):
        # Arrange
        mock_openai.return_value = Mock(
            choices=[Mock(message=Mock(content="Test response"))]
        )
        
        # Act
        result = agent.process_input("Test input")
        
        # Assert
        assert result["response"] == "Test response"
        mock_openai.assert_called_once()
```

### Integration Tests

```javascript
// __tests__/integration/api.test.js
const request = require('supertest');
const app = require('../../src/index');

describe('API Integration Tests', () => {
  describe('POST /voice/calls/initiate', () => {
    it('should create a new call', async () => {
      const response = await request(app)
        .post('/voice/calls/initiate')
        .send({
          phone_number: '+1234567890',
          options: { recording: true }
        })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.call_id).toBeDefined();
    });
  });
});
```

### E2E Tests

```javascript
// __tests__/e2e/voice-call.test.js
const WebSocket = require('ws');

describe('Voice Call E2E', () => {
  let ws;

  beforeEach(() => {
    ws = new WebSocket('ws://localhost:3000/ws');
  });

  afterEach(() => {
    ws.close();
  });

  it('should handle complete voice call flow', (done) => {
    const events = [];

    ws.on('message', (data) => {
      const event = JSON.parse(data);
      events.push(event);

      if (event.type === 'call.completed') {
        expect(events).toHaveLength(4);
        expect(events[0].type).toBe('call.started');
        expect(events[1].type).toBe('message.received');
        expect(events[2].type).toBe('message.sent');
        expect(events[3].type).toBe('call.completed');
        done();
      }
    });

    // Simulate call initiation
    ws.send(JSON.stringify({
      type: 'initiate_call',
      phone_number: '+1234567890'
    }));
  });
});
```

## Code Standards

### JavaScript/Node.js Standards

#### ESLint Configuration

```json
{
  "extends": [
    "eslint:recommended",
    "@typescript-eslint/recommended"
  ],
  "rules": {
    "no-console": "warn",
    "prefer-const": "error",
    "no-var": "error",
    "object-shorthand": "error",
    "prefer-template": "error"
  }
}
```

#### Code Style Examples

```javascript
// Good
const makeCall = async (phoneNumber, options = {}) => {
  const { recording = false, transcription = false } = options;
  
  try {
    const result = await this.provider.calls.create({
      to: phoneNumber,
      from: this.config.phoneNumber,
      record: recording
    });
    
    return {
      success: true,
      callId: result.sid,
      status: 'initiating'
    };
  } catch (error) {
    logger.error('Call initiation failed', { error, phoneNumber });
    throw new Error('Failed to initiate call');
  }
};

// Bad
function makeCall(phoneNumber, options) {
  var result;
  try {
    result = this.provider.calls.create({
      to: phoneNumber,
      from: this.config.phoneNumber,
      record: options && options.recording
    });
    return { success: true, callId: result.sid, status: 'initiating' };
  } catch (error) {
    console.log('Error:', error);
    throw error;
  }
}
```

### Python Standards

#### Black Configuration

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

#### Code Style Examples

```python
# Good
class InputAgent:
    def __init__(self, model: str = "gpt-4", temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
        self.client = OpenAI()

    async def process_input(self, text: str, context: dict = None) -> dict:
        """Process user input and generate response."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=self.temperature
            )
            
            return {
                "response": response.choices[0].message.content,
                "confidence": 0.95,
                "tokens_used": response.usage.total_tokens
            }
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            raise ProcessingError(f"Failed to process input: {e}")

# Bad
class InputAgent:
    def __init__(self,model="gpt-4",temperature=0.7):
        self.model=model
        self.temperature=temperature
        self.client=OpenAI()
    
    def process_input(self,text,context=None):
        try:
            response=self.client.chat.completions.create(model=self.model,messages=[{"role":"system","content":self.system_prompt},{"role":"user","content":text}],temperature=self.temperature)
            return {"response":response.choices[0].message.content,"confidence":0.95,"tokens_used":response.usage.total_tokens}
        except Exception as e:
            print(f"Error: {e}")
            return None
```

## Adding Features

### Adding a New Voice Provider

#### 1. Create Driver Implementation

```javascript
// src/voiceAgent/drivers/newProviderDriver.js
const BaseDriver = require('./baseDriver');

class NewProviderDriver extends BaseDriver {
  constructor() {
    super();
    this.name = 'NewProvider';
    this.capabilities = ['voice', 'recording'];
  }

  async initialize() {
    // Validate configuration
    if (!process.env.NEW_PROVIDER_API_KEY) {
      throw new Error('NEW_PROVIDER_API_KEY is required');
    }

    // Initialize provider client
    this.client = new NewProviderClient(process.env.NEW_PROVIDER_API_KEY);
    
    return true;
  }

  async makeCall(phoneNumber, options = {}) {
    const { recording = false } = options;

    try {
      const call = await this.client.calls.create({
        to: phoneNumber,
        from: process.env.NEW_PROVIDER_PHONE_NUMBER,
        record: recording
      });

      return {
        success: true,
        callId: call.id,
        status: 'initiating'
      };
    } catch (error) {
      throw new Error(`Failed to initiate call: ${error.message}`);
    }
  }

  async handleWebhook(payload) {
    // Process incoming webhook
    const { callId, status, recordingUrl } = payload;

    return {
      callId,
      status,
      recordingUrl,
      timestamp: new Date().toISOString()
    };
  }

  async getCapabilities() {
    return {
      voice: {
        supported: true,
        features: ['call', 'record']
      },
      sms: {
        supported: false
      }
    };
  }
}

module.exports = NewProviderDriver;
```

#### 2. Add Configuration

```javascript
// env-setup.js
case 'new-provider':
  console.log('\n📞 New Provider Configuration:');
  envVars.NEW_PROVIDER_API_KEY = await question('New Provider API Key: ') || 'your-api-key-here';
  envVars.NEW_PROVIDER_PHONE_NUMBER = await question('New Provider Phone Number: ') || '+1234567890';
  envVars.NEW_PROVIDER_WEBHOOK_URL = await question('New Provider Webhook URL (default: http://localhost:3000/voice/webhook): ') || 'http://localhost:3000/voice/webhook';
  break;
```

#### 3. Register Driver

```javascript
// src/voiceAgent/index.js
const NewProviderDriver = require('./drivers/newProviderDriver');

// Add to provider registry
const providers = {
  twilio: TwilioDriver,
  vonage: VonageDriver,
  'new-provider': NewProviderDriver
};
```

#### 4. Add Tests

```javascript
// __tests__/unit/drivers/newProviderDriver.test.js
const NewProviderDriver = require('../../../src/voiceAgent/drivers/newProviderDriver');

describe('NewProviderDriver', () => {
  let driver;

  beforeEach(() => {
    driver = new NewProviderDriver();
  });

  describe('initialize', () => {
    it('should initialize with valid API key', async () => {
      process.env.NEW_PROVIDER_API_KEY = 'test-key';
      const result = await driver.initialize();
      expect(result).toBe(true);
    });
  });

  describe('makeCall', () => {
    it('should initiate call successfully', async () => {
      // Mock provider client
      driver.client = {
        calls: {
          create: jest.fn().mockResolvedValue({ id: 'call_123' })
        }
      };

      const result = await driver.makeCall('+1234567890');
      expect(result.success).toBe(true);
      expect(result.callId).toBe('call_123');
    });
  });
});
```

### Adding New AI Agent

#### 1. Create Agent Implementation

```python
# app/agents/custom_agent.py
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class CustomAgent(ABC):
    def __init__(self, name: str, model: str = "gpt-4"):
        self.name = name
        self.model = model
        self.logger = logger

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return response."""
        pass

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        required_fields = ['message', 'context']
        return all(field in input_data for field in required_fields)

class SentimentAnalysisAgent(CustomAgent):
    def __init__(self):
        super().__init__("sentiment_analysis", "gpt-3.5-turbo")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment of user input."""
        if not await self.validate_input(input_data):
            raise ValueError("Invalid input data")

        message = input_data['message']
        
        # Perform sentiment analysis
        sentiment = await self._analyze_sentiment(message)
        
        return {
            "sentiment": sentiment,
            "confidence": 0.85,
            "agent": self.name
        }

    async def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of text."""
        # Implementation here
        return "positive"
```

#### 2. Register Agent

```python
# app/agents/__init__.py
from .custom_agent import SentimentAnalysisAgent

AGENT_REGISTRY = {
    "input": InputAgent,
    "memory": MemoryAgent,
    "orchestrator": OrchestratorAgent,
    "tool": ToolAgent,
    "sentiment": SentimentAnalysisAgent
}
```

#### 3. Add Tests

```python
# tests/unit/test_agents/test_custom_agent.py
import pytest
from app.agents.custom_agent import SentimentAnalysisAgent

class TestSentimentAnalysisAgent:
    @pytest.fixture
    def agent(self):
        return SentimentAnalysisAgent()

    def test_validate_input(self, agent):
        valid_input = {"message": "Hello", "context": {}}
        assert agent.validate_input(valid_input) is True

        invalid_input = {"message": "Hello"}
        assert agent.validate_input(invalid_input) is False

    async def test_process_sentiment(self, agent):
        input_data = {
            "message": "I love this product!",
            "context": {"user_id": "123"}
        }
        
        result = await agent.process(input_data)
        
        assert "sentiment" in result
        assert "confidence" in result
        assert result["agent"] == "sentiment_analysis"
```

## Debugging

### Node.js Debugging

#### Debug Mode

```bash
# Start with debug logging
DEBUG=true npm run dev

# Use Node.js debugger
node --inspect src/index.js

# Debug specific files
node --inspect-brk src/index.js
```

#### Debug Configuration (VS Code)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Node.js Backend",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/backend-node-realtime/src/index.js",
      "env": {
        "NODE_ENV": "development",
        "DEBUG": "true"
      },
      "console": "integratedTerminal"
    }
  ]
}
```

### Python Debugging

#### Debug Mode

```bash
# Start with debug logging
DEBUG=true uvicorn app.main:app --reload --log-level debug

# Use Python debugger
python -m pdb -m uvicorn app.main:app
```

#### Debug Configuration (VS Code)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Python Backend",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
      "env": {
        "DEBUG": "true"
      },
      "console": "integratedTerminal"
    }
  ]
}
```

### Common Debugging Techniques

#### Logging

```javascript
// Node.js
const logger = require('./utils/logger');

logger.debug('Processing call', { callId, phoneNumber });
logger.info('Call initiated', { callId, status });
logger.error('Call failed', { error, callId });
```

```python
# Python
import logging

logger = logging.getLogger(__name__)

logger.debug("Processing input", extra={"input_data": input_data})
logger.info("Agent response generated", extra={"agent": agent_name})
logger.error("Processing failed", extra={"error": str(error)})
```

#### Breakpoints

```javascript
// Node.js
debugger; // Set breakpoint in code
console.log('Debug info:', { variable1, variable2 });
```

```python
# Python
import pdb; pdb.set_trace()  # Set breakpoint in code
print(f"Debug info: {variable1}, {variable2}")
```

## Performance Optimization

### Node.js Optimization

#### Memory Management

```javascript
// Use streams for large data
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

#### Connection Pooling

```javascript
// Database connection pooling
const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Use pool for queries
const result = await pool.query('SELECT * FROM calls WHERE id = $1', [callId]);
```

### Python Optimization

#### Async Operations

```python
import asyncio
from typing import List

async def process_multiple_calls(call_ids: List[str]) -> List[dict]:
    """Process multiple calls concurrently."""
    tasks = [process_single_call(call_id) for call_id in call_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

async def process_single_call(call_id: str) -> dict:
    """Process a single call."""
    # Async processing logic
    return {"call_id": call_id, "status": "processed"}
```

#### Caching

```python
import redis
import json
from functools import wraps

redis_client = redis.Redis.from_url(process.env.REDIS_URL)

def cache_result(expiry: int = 300):
    """Cache decorator for function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            redis_client.setex(cache_key, expiry, json.dumps(result))
            
            return result
        return wrapper
    return decorator

@cache_result(expiry=600)
async def get_user_preferences(user_id: str) -> dict:
    """Get user preferences with caching."""
    # Database query logic
    return {"language": "en", "timezone": "UTC"}
```

## Contributing Guidelines

### Pull Request Process

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Add tests** for new functionality
5. **Run the test suite**
   ```bash
   npm test --prefix backend-node-realtime
   cd backend-python-orchestrator && pytest
   ```
6. **Check code quality**
   ```bash
   npm run lint --prefix backend-node-realtime
   cd backend-python-orchestrator && black app/ && flake8 app/
   ```
7. **Submit a pull request**

### Code Review Checklist

- [ ] Code follows project standards
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance impact is considered
- [ ] Error handling is implemented
- [ ] Logging is appropriate

### Commit Message Guidelines

```bash
# Format
<type>(<scope>): <description>

# Types
feat: new feature
fix: bug fix
docs: documentation changes
style: formatting changes
refactor: code refactoring
test: adding tests
chore: maintenance tasks

# Examples
feat(voice): add Vonage provider support
fix(api): resolve authentication issue
docs(readme): update installation instructions
test(providers): add unit tests for Twilio driver
```

### Issue Reporting

When reporting issues, include:

1. **Environment details**
   - OS version
   - Node.js/Python versions
   - Docker version (if applicable)

2. **Steps to reproduce**
   - Clear, step-by-step instructions
   - Expected vs actual behavior

3. **Error messages**
   - Full error logs
   - Stack traces

4. **Additional context**
   - Screenshots (if applicable)
   - Configuration files (sanitized)

---

This developer guide provides comprehensive information for contributing to the Voice Agent Orchestrator project. For additional support, refer to the project's GitHub repository or contact the development team. 