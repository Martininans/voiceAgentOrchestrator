# Voice Agent Orchestrator - API Reference

## Table of Contents

1. [Authentication](#authentication)
2. [Node.js Backend API](#nodejs-backend-api)
3. [Python Backend API](#python-backend-api)
4. [WebSocket API](#websocket-api)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)

## Authentication

### JWT Authentication

All API endpoints require JWT authentication unless specified otherwise.

```http
Authorization: Bearer <jwt_token>
```

### API Key Authentication

For voice provider webhooks and public endpoints:

```http
X-API-Key: <api_key>
```

## Node.js Backend API

### Base URL
```
http://localhost:3000
```

### Health & Status Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "version": "1.0.0",
  "uptime": 3600,
  "services": {
    "database": "connected",
    "orchestrator": "connected",
    "voice_provider": "connected"
  }
}
```

#### Detailed Health Check
```http
GET /health/detailed
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "version": "1.0.0",
  "uptime": 3600,
  "memory": {
    "rss": 52428800,
    "heapTotal": 20971520,
    "heapUsed": 10485760,
    "external": 1048576
  },
  "cpu": {
    "user": 1000000,
    "system": 500000
  },
  "services": {
    "database": {
      "status": "connected",
      "response_time": 15
    },
    "orchestrator": {
      "status": "connected",
      "response_time": 25
    },
    "voice_provider": {
      "status": "connected",
      "provider": "twilio",
      "response_time": 50
    }
  }
}
```

### Voice Provider Management

#### Get Available Providers
```http
GET /voice/providers
```

**Response:**
```json
{
  "available_providers": [
    "twilio",
    "vonage", 
    "aws-connect",
    "generic-http"
  ],
  "current_provider": "twilio",
  "providers": {
    "twilio": {
      "name": "Twilio",
      "capabilities": ["voice", "sms", "recording"],
      "status": "active",
      "phone_number": "+1234567890"
    },
    "vonage": {
      "name": "Vonage",
      "capabilities": ["voice", "sms"],
      "status": "inactive",
      "phone_number": null
    }
  }
}
```

#### Get Current Provider
```http
GET /voice/providers/current
```

**Response:**
```json
{
  "provider": "twilio",
  "name": "Twilio",
  "status": "active",
  "capabilities": ["voice", "sms", "recording"],
  "phone_number": "+1234567890"
}
```

#### Switch Provider
```http
POST /voice/providers/switch
Content-Type: application/json

{
  "provider": "vonage"
}
```

**Response:**
```json
{
  "success": true,
  "previous_provider": "twilio",
  "current_provider": "vonage",
  "message": "Provider switched successfully"
}
```

#### Get Provider Capabilities
```http
GET /voice/providers/{provider}/capabilities
```

**Response:**
```json
{
  "provider": "twilio",
  "capabilities": {
    "voice": {
      "supported": true,
      "features": ["call", "record", "transcribe"]
    },
    "sms": {
      "supported": true,
      "features": ["send", "receive"]
    },
    "recording": {
      "supported": true,
      "formats": ["mp3", "wav"]
    }
  }
}
```

#### Test Provider Connection
```http
POST /voice/providers/test
```

**Response:**
```json
{
  "success": true,
  "provider": "twilio",
  "test_results": {
    "authentication": "passed",
    "api_access": "passed",
    "webhook_url": "passed"
  },
  "response_time": 150
}
```

### Call Management

#### Initiate Call
```http
POST /voice/calls/initiate
Content-Type: application/json

{
  "phone_number": "+1234567890",
  "options": {
    "recording": true,
    "transcription": true,
    "timeout": 30,
    "caller_id": "+1987654321"
  }
}
```

**Response:**
```json
{
  "success": true,
  "call_id": "call_123456789",
  "status": "initiating",
  "phone_number": "+1234567890",
  "provider": "twilio",
  "estimated_duration": 30
}
```

#### Get Call Status
```http
GET /voice/calls/{callId}/status
```

**Response:**
```json
{
  "call_id": "call_123456789",
  "status": "in-progress",
  "phone_number": "+1234567890",
  "start_time": "2024-01-01T00:00:00.000Z",
  "duration": 45,
  "recording_url": "https://api.twilio.com/recordings/rec_123",
  "transcription": "Hello, how can I help you today?"
}
```

#### End Call
```http
POST /voice/calls/{callId}/end
```

**Response:**
```json
{
  "success": true,
  "call_id": "call_123456789",
  "status": "completed",
  "duration": 120,
  "recording_url": "https://api.twilio.com/recordings/rec_123"
}
```

#### Get Call History
```http
GET /voice/calls
```

**Query Parameters:**
- `limit` (optional): Number of calls to return (default: 10)
- `offset` (optional): Number of calls to skip (default: 0)
- `status` (optional): Filter by status (initiated, in-progress, completed, failed)
- `phone_number` (optional): Filter by phone number

**Response:**
```json
{
  "calls": [
    {
      "call_id": "call_123456789",
      "phone_number": "+1234567890",
      "status": "completed",
      "start_time": "2024-01-01T00:00:00.000Z",
      "end_time": "2024-01-01T00:02:00.000Z",
      "duration": 120,
      "provider": "twilio"
    }
  ],
  "pagination": {
    "total": 100,
    "limit": 10,
    "offset": 0,
    "has_more": true
  }
}
```

### WebSocket Management

#### Get WebSocket Status
```http
GET /ws/status
```

**Response:**
```json
{
  "active_connections": 5,
  "max_connections": 100,
  "uptime": 3600,
  "connections": [
    {
      "id": "ws_123",
      "connected_at": "2024-01-01T00:00:00.000Z",
      "last_activity": "2024-01-01T00:01:00.000Z"
    }
  ]
}
```

### Voice Provider Webhooks

#### Twilio Webhook
```http
POST /voice/webhook/twilio
Content-Type: application/x-www-form-urlencoded

CallSid=call_123&CallStatus=ringing&From=%2B1234567890&To=%2B1987654321
```

#### Vonage Webhook
```http
POST /voice/webhook/vonage
Content-Type: application/json

{
  "uuid": "call_123",
  "status": "ringing",
  "from": "+1234567890",
  "to": "+1987654321"
}
```

#### Generic Webhook
```http
POST /voice/webhook/generic
Content-Type: application/json

{
  "provider": "custom-provider",
  "event_type": "call.started",
  "call_id": "call_123",
  "data": {
    "from": "+1234567890",
    "to": "+1987654321"
  }
}
```

## Python Backend API

### Base URL
```
http://localhost:8000
```

### Health & Status Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "chromadb": "connected",
    "openai": "connected"
  }
}
```

#### Detailed Health Check
```http
GET /health/detailed
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "version": "1.0.0",
  "memory_usage": {
    "rss": 52428800,
    "vms": 104857600
  },
  "services": {
    "database": {
      "status": "connected",
      "response_time": 10
    },
    "chromadb": {
      "status": "connected",
      "collections": 5
    },
    "openai": {
      "status": "connected",
      "models": ["gpt-4", "gpt-3.5-turbo"]
    }
  }
}
```

### Agent Management

#### Get Available Agents
```http
GET /agents
```

**Response:**
```json
{
  "agents": [
    {
      "id": "agent_123",
      "type": "input",
      "name": "Input Agent",
      "status": "active",
      "model": "gpt-4",
      "created_at": "2024-01-01T00:00:00.000Z"
    },
    {
      "id": "agent_456",
      "type": "memory",
      "name": "Memory Agent",
      "status": "active",
      "model": "gpt-3.5-turbo",
      "created_at": "2024-01-01T00:00:00.000Z"
    }
  ]
}
```

#### Create Agent
```http
POST /agents/create
Content-Type: application/json

{
  "agent_type": "input",
  "name": "Custom Input Agent",
  "configuration": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

**Response:**
```json
{
  "success": true,
  "agent": {
    "id": "agent_789",
    "type": "input",
    "name": "Custom Input Agent",
    "status": "active",
    "model": "gpt-4",
    "configuration": {
      "temperature": 0.7,
      "max_tokens": 1000
    },
    "created_at": "2024-01-01T00:00:00.000Z"
  }
}
```

#### Get Agent Status
```http
GET /agents/{agentId}/status
```

**Response:**
```json
{
  "agent_id": "agent_123",
  "status": "active",
  "type": "input",
  "model": "gpt-4",
  "last_activity": "2024-01-01T00:01:00.000Z",
  "total_requests": 150,
  "average_response_time": 250
}
```

#### Send Message to Agent
```http
POST /agents/{agentId}/message
Content-Type: application/json

{
  "message": "Hello, how can you help me?",
  "context": {
    "user_id": "user_123",
    "session_id": "session_456",
    "conversation_id": "conv_789"
  },
  "options": {
    "stream": false,
    "temperature": 0.7
  }
}
```

**Response:**
```json
{
  "success": true,
  "response": {
    "message": "Hello! I'm here to help you with any questions or tasks you might have. What can I assist you with today?",
    "agent_id": "agent_123",
    "model": "gpt-4",
    "tokens_used": 25,
    "response_time": 250
  }
}
```

### Conversation Management

#### Get Conversations
```http
GET /conversations
```

**Query Parameters:**
- `limit` (optional): Number of conversations to return (default: 10)
- `offset` (optional): Number of conversations to skip (default: 0)
- `user_id` (optional): Filter by user ID
- `status` (optional): Filter by status (active, completed, archived)

**Response:**
```json
{
  "conversations": [
    {
      "id": "conv_123",
      "user_id": "user_123",
      "status": "active",
      "created_at": "2024-01-01T00:00:00.000Z",
      "last_message_at": "2024-01-01T00:05:00.000Z",
      "message_count": 10
    }
  ],
  "pagination": {
    "total": 50,
    "limit": 10,
    "offset": 0,
    "has_more": true
  }
}
```

#### Get Conversation Details
```http
GET /conversations/{conversationId}
```

**Response:**
```json
{
  "id": "conv_123",
  "user_id": "user_123",
  "status": "active",
  "created_at": "2024-01-01T00:00:00.000Z",
  "last_message_at": "2024-01-01T00:05:00.000Z",
  "messages": [
    {
      "id": "msg_123",
      "role": "user",
      "content": "Hello, how can you help me?",
      "timestamp": "2024-01-01T00:00:00.000Z"
    },
    {
      "id": "msg_124",
      "role": "assistant",
      "content": "Hello! I'm here to help you with any questions or tasks you might have.",
      "timestamp": "2024-01-01T00:00:05.000Z"
    }
  ],
  "metadata": {
    "agent_type": "input",
    "model": "gpt-4",
    "total_tokens": 150
  }
}
```

#### Add Message to Conversation
```http
POST /conversations/{conversationId}/messages
Content-Type: application/json

{
  "role": "user",
  "content": "What's the weather like today?",
  "metadata": {
    "source": "voice",
    "confidence": 0.95
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": {
    "id": "msg_125",
    "role": "user",
    "content": "What's the weather like today?",
    "timestamp": "2024-01-01T00:06:00.000Z",
    "metadata": {
      "source": "voice",
      "confidence": 0.95
    }
  },
  "conversation_updated": true
}
```

### Memory Management

#### Get Memory Context
```http
GET /memory/{userId}/context
```

**Response:**
```json
{
  "user_id": "user_123",
  "context": {
    "recent_conversations": [
      {
        "conversation_id": "conv_123",
        "summary": "User asked about weather and received information",
        "timestamp": "2024-01-01T00:05:00.000Z"
      }
    ],
    "preferences": {
      "language": "en",
      "timezone": "UTC",
      "communication_style": "friendly"
    },
    "knowledge_base": {
      "topics": ["weather", "general_inquiry"],
      "last_updated": "2024-01-01T00:05:00.000Z"
    }
  }
}
```

#### Update Memory Context
```http
POST /memory/{userId}/context
Content-Type: application/json

{
  "preferences": {
    "language": "es",
    "timezone": "America/New_York"
  },
  "knowledge": {
    "topics": ["weather", "general_inquiry", "scheduling"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "user_id": "user_123",
  "context_updated": true,
  "timestamp": "2024-01-01T00:07:00.000Z"
}
```

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:3000/ws');

ws.onopen = () => {
  console.log('Connected to WebSocket');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

ws.onclose = () => {
  console.log('Disconnected from WebSocket');
};
```

### Authentication

```javascript
// Send authentication message
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your-jwt-token'
}));
```

### Event Types

#### Call Events

```json
{
  "type": "call.started",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "data": {
    "call_id": "call_123",
    "phone_number": "+1234567890",
    "provider": "twilio"
  }
}
```

```json
{
  "type": "call.ended",
  "timestamp": "2024-01-01T00:02:00.000Z",
  "data": {
    "call_id": "call_123",
    "duration": 120,
    "status": "completed"
  }
}
```

#### Message Events

```json
{
  "type": "message.received",
  "timestamp": "2024-01-01T00:00:30.000Z",
  "data": {
    "call_id": "call_123",
    "message": "Hello, how can I help you?",
    "confidence": 0.95
  }
}
```

```json
{
  "type": "message.sent",
  "timestamp": "2024-01-01T00:00:35.000Z",
  "data": {
    "call_id": "call_123",
    "message": "Hello! I'm here to help you with any questions.",
    "agent_id": "agent_123"
  }
}
```

#### Error Events

```json
{
  "type": "error.occurred",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "data": {
    "error_code": "PROVIDER_ERROR",
    "message": "Failed to connect to voice provider",
    "call_id": "call_123"
  }
}
```

#### System Events

```json
{
  "type": "system.status",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "data": {
    "status": "healthy",
    "active_connections": 5,
    "uptime": 3600
  }
}
```

### Sending Messages

```javascript
// Send a message to the server
ws.send(JSON.stringify({
  type: 'message',
  data: {
    call_id: 'call_123',
    content: 'Hello, server!'
  }
}));

// Subscribe to specific events
ws.send(JSON.stringify({
  type: 'subscribe',
  events: ['call.started', 'call.ended']
}));

// Unsubscribe from events
ws.send(JSON.stringify({
  type: 'unsubscribe',
  events: ['call.started']
}));
```

## Error Handling

### Error Response Format

All API endpoints return errors in a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid phone number format",
    "details": {
      "field": "phone_number",
      "value": "1234567890",
      "expected": "E.164 format (+1234567890)"
    },
    "timestamp": "2024-01-01T00:00:00.000Z",
    "request_id": "req_123456789"
  }
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `AUTHENTICATION_ERROR` | Invalid or missing authentication | 401 |
| `AUTHORIZATION_ERROR` | Insufficient permissions | 403 |
| `VALIDATION_ERROR` | Invalid request data | 400 |
| `NOT_FOUND` | Resource not found | 404 |
| `PROVIDER_ERROR` | Voice provider error | 502 |
| `RATE_LIMIT_EXCEEDED` | Too many requests | 429 |
| `INTERNAL_ERROR` | Server error | 500 |

### Error Handling Examples

#### JavaScript
```javascript
async function makeApiCall() {
  try {
    const response = await fetch('/voice/calls/initiate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        phone_number: '+1234567890'
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error.message);
    }

    return await response.json();
  } catch (error) {
    console.error('API Error:', error.message);
    throw error;
  }
}
```

#### Python
```python
import requests

def make_api_call():
    try:
        response = requests.post(
            'http://localhost:3000/voice/calls/initiate',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            },
            json={
                'phone_number': '+1234567890'
            }
        )
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, 'json'):
            error = e.response.json()
            raise Exception(error['error']['message'])
        raise e
```

## Rate Limiting

### Rate Limit Headers

API responses include rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### Rate Limit Exceeded Response

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "details": {
      "limit": 100,
      "remaining": 0,
      "reset_time": "2024-01-01T01:00:00.000Z"
    }
  }
}
```

### Rate Limit Categories

| Endpoint Category | Limit | Window |
|------------------|-------|--------|
| Health checks | 1000 | 1 minute |
| Voice provider management | 100 | 1 minute |
| Call management | 50 | 1 minute |
| Agent management | 200 | 1 minute |
| Conversation management | 500 | 1 minute |

### Handling Rate Limits

```javascript
async function handleRateLimit(response) {
  if (response.status === 429) {
    const error = await response.json();
    const resetTime = new Date(error.error.details.reset_time);
    const waitTime = resetTime.getTime() - Date.now();
    
    console.log(`Rate limit exceeded. Waiting ${waitTime}ms`);
    await new Promise(resolve => setTimeout(resolve, waitTime));
    
    // Retry the request
    return makeApiCall();
  }
  
  return response;
}
```

---

This API reference provides comprehensive documentation for all endpoints and features of the Voice Agent Orchestrator system. For additional examples and use cases, refer to the project's GitHub repository or contact the development team. 