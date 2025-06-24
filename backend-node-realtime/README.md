# Voice Agent Orchestrator - Node.js Backend

This is the realtime layer of the Voice Agent Orchestrator, handling WebSocket connections, voice calls via Twilio, and communication with the Python orchestrator.

## Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Set Up Environment Variables
You have two options:

#### Option A: Interactive Setup (Recommended)
```bash
npm run setup-env
```
This will guide you through setting up all required environment variables interactively.

#### Option B: Manual Setup
1. Create a `.env` file in the `backend-node-realtime` directory
2. Copy the variables from `ENVIRONMENT_SETUP.md`
3. Update with your actual values

### 3. Start the Server
```bash
npm start
```

For development with auto-restart:
```bash
npm run dev
```

## Environment Variables

The application uses the following environment variables:

### Required Variables
- `TWILIO_ACCOUNT_SID` - Your Twilio Account SID
- `TWILIO_AUTH_TOKEN` - Your Twilio Auth Token
- `TWILIO_PHONE_NUMBER` - Your Twilio phone number
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Your Supabase anonymous key

### Optional Variables
- `PORT` - Server port (default: 3000)
- `HOST` - Server host (default: 0.0.0.0)
- `NODE_ENV` - Environment (default: development)
- `ORCHESTRATOR_URL` - Python orchestrator URL (default: http://localhost:8000)

See `ENVIRONMENT_SETUP.md` for the complete list of variables.

## Features

- **WebSocket Server**: Real-time communication with clients
- **Twilio Integration**: Voice calls, SMS, and TTS
- **Supabase Integration**: Database and authentication
- **Python Orchestrator Communication**: HTTP API calls to the Python backend
- **Health Checks**: Built-in health monitoring endpoints

## API Endpoints

- `GET /health` - Health check
- `POST /voice/webhook` - Twilio webhook endpoint
- `GET /voice/status` - Voice agent status
- `WS /ws` - WebSocket endpoint for real-time communication

## Configuration

All configuration is centralized in `src/config.js` and loaded from environment variables. The application will show warnings for missing required variables but will start with placeholder values for development.

## Development

### Running Tests
```bash
npm test
```

### Health Check
```bash
npm run health
```

### WebSocket Test
```bash
npm run test-ws
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client Apps   │    │  Node.js Backend │    │ Python Backend  │
│                 │◄──►│                  │◄──►│                 │
│ - Web App       │    │ - WebSocket      │    │ - AI Agents     │
│ - Mobile App    │    │ - Twilio Driver  │    │ - Orchestrator  │
│ - Voice Client  │    │ - Supabase       │    │ - Memory        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Troubleshooting

1. **Missing Environment Variables**: Check the console output for warnings about missing variables
2. **Twilio Issues**: Verify your Twilio credentials and phone number
3. **Supabase Issues**: Check your Supabase URL and API keys
4. **Python Orchestrator**: Ensure the Python backend is running on the configured URL

## License

ISC 