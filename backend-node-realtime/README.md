# Voice Agent Orchestrator - Node.js Realtime Layer

A real-time WebSocket server that handles voice interactions and integrates with the Python orchestrator backend.

## Features

- 🔌 **WebSocket Support**: Real-time bidirectional communication
- 📞 **Voice Integration**: Twilio voice call handling
- 📱 **SMS Support**: Text message capabilities
- 🔊 **Text-to-Speech**: Voice response generation
- 🎤 **Speech Processing**: Audio input handling
- 🔗 **Orchestrator Integration**: Seamless connection to Python backend
- 📊 **Health Monitoring**: Built-in health checks and status endpoints
- 🛡️ **Error Handling**: Comprehensive error management

## Quick Start

### Prerequisites

- Node.js 16+ 
- Python orchestrator backend running on port 8000
- Twilio account (optional, for voice features)

### Installation

1. **Clone and navigate to the directory:**
   ```bash
   cd backend-node-realtime
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Start the server:**
   ```bash
   npm start
   ```

### Development

```bash
npm run dev  # Start with nodemon for auto-reload
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `3000` |
| `HOST` | Server host | `0.0.0.0` |
| `NODE_ENV` | Environment | `development` |
| `VOICE_PROVIDER` | Voice provider | `twilio` |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | - |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | - |
| `TWILIO_PHONE_NUMBER` | Twilio Phone Number | - |
| `ORCHESTRATOR_URL` | Python backend URL | `http://localhost:8000` |
| `ORCHESTRATOR_TIMEOUT` | Request timeout (ms) | `30000` |
| `MAX_WS_CONNECTIONS` | Max WebSocket connections | `100` |

## API Endpoints

### Health & Status

- `GET /health` - Health check
- `GET /` - Server info and endpoints

### Voice Agent Endpoints

- `POST /voice/inbound-call` - Handle incoming calls
- `POST /voice/outbound-call` - Initiate outbound calls
- `POST /voice/tts` - Text-to-speech conversion
- `POST /voice/sms` - Send SMS messages
- `POST /voice/process-speech` - Process speech input
- `POST /voice/webhook` - Twilio webhook handler
- `GET /voice/status` - Voice agent status
- `GET /voice/health` - Voice service health
- `GET /voice/config` - Configuration info

### WebSocket

- `WS /ws` - Real-time communication endpoint

## WebSocket Protocol

### Message Types

#### Client → Server

```javascript
// Audio message
{
  "type": "audio",
  "audio_data": "base64_encoded_audio",
  "user_id": "user123",
  "session_id": "session456",
  "context": { /* additional context */ }
}

// Text message
{
  "type": "text",
  "text": "Hello, how can you help me?",
  "user_id": "user123",
  "session_id": "session456",
  "context": { /* additional context */ }
}

// Ping
{
  "type": "ping"
}
```

#### Server → Client

```javascript
// Connection established
{
  "type": "connection",
  "message": "WebSocket connected successfully",
  "timestamp": "2024-01-01T00:00:00.000Z"
}

// Audio acknowledgment
{
  "type": "audio_ack",
  "message": "Audio received, processing...",
  "timestamp": "2024-01-01T00:00:00.000Z"
}

// Audio response
{
  "type": "audio_response",
  "success": true,
  "transcribed_text": "Hello, how can you help me?",
  "intent": "greeting",
  "response": "Hello! I'm here to help you.",
  "voice_url": "https://example.com/audio.mp3",
  "timestamp": "2024-01-01T00:00:00.000Z"
}

// Text response
{
  "type": "text_response",
  "success": true,
  "intent": "greeting",
  "response": "Hello! I'm here to help you.",
  "timestamp": "2024-01-01T00:00:00.000Z"
}

// Error
{
  "type": "error",
  "message": "Error description",
  "error": "Detailed error message",
  "timestamp": "2024-01-01T00:00:00.000Z"
}

// Pong
{
  "type": "pong",
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

## Usage Examples

### WebSocket Client Example

```javascript
const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:3000/ws');

ws.on('open', () => {
  console.log('Connected to WebSocket');
  
  // Send text message
  ws.send(JSON.stringify({
    type: 'text',
    text: 'Hello, how can you help me?',
    user_id: 'user123',
    session_id: 'session456'
  }));
});

ws.on('message', (data) => {
  const message = JSON.parse(data);
  console.log('Received:', message);
});

ws.on('error', (error) => {
  console.error('WebSocket error:', error);
});
```

### Voice Call Example

```bash
# Initiate outbound call
curl -X POST http://localhost:3000/voice/outbound-call \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+1234567890",
    "message": "Hello! This is a test call."
  }'
```

### SMS Example

```bash
# Send SMS
curl -X POST http://localhost:3000/voice/sms \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+1234567890",
    "message": "Hello from your AI assistant!"
  }'
```

## Architecture

```
┌─────────────────┐    WebSocket    ┌──────────────────┐
│   Web Client    │ ◄─────────────► │  Node.js Server  │
└─────────────────┘                 └──────────────────┘
                                              │
                                              │ HTTP
                                              ▼
                                    ┌──────────────────┐
                                    │ Python Backend   │
                                    │ (Orchestrator)   │
                                    └──────────────────┘
                                              │
                                              │ Twilio API
                                              ▼
                                    ┌──────────────────┐
                                    │   Twilio Cloud   │
                                    └──────────────────┘
```

## Testing

### Health Check

```bash
npm run health
```

### Manual Testing

1. **Start the server:**
   ```bash
   npm start
   ```

2. **Test health endpoint:**
   ```bash
   curl http://localhost:3000/health
   ```

3. **Test WebSocket connection:**
   ```bash
   # Use a WebSocket client or browser console
   const ws = new WebSocket('ws://localhost:3000/ws');
   ```

## Troubleshooting

### Common Issues

1. **Port already in use:**
   - Change `PORT` in `.env` file
   - Kill existing process: `lsof -ti:3000 | xargs kill`

2. **Orchestrator connection failed:**
   - Ensure Python backend is running on port 8000
   - Check `ORCHESTRATOR_URL` in `.env`

3. **Twilio errors:**
   - Verify Twilio credentials in `.env`
   - Check webhook URL configuration

### Logs

The server uses structured logging. Check console output for:
- `🚀` - Server startup
- `📞` - Voice operations
- `🔌` - WebSocket connections
- `❌` - Errors
- `✅` - Success operations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

ISC License 