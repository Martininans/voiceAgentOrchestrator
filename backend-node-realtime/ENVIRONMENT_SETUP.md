# Environment Setup for Node.js Backend

This document explains how to configure environment variables for the Voice Agent Orchestrator Node.js backend.

## Quick Setup

1. Create a `.env` file in the `backend-node-realtime` directory
2. Copy the variables below and update with your actual values
3. The application will automatically load the `.env` file on startup

## Required Environment Variables

### Server Configuration
```env
PORT=3000
HOST=0.0.0.0
NODE_ENV=development
```

### Voice Provider Configuration
```env
VOICE_PROVIDER=twilio
```

### Twilio Configuration (Required for voice functionality)
```env
TWILIO_ACCOUNT_SID=your-twilio-account-sid-here
TWILIO_AUTH_TOKEN=your-twilio-auth-token-here
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=http://localhost:3000/voice/webhook
```

### Supabase Configuration (Required for database)
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key-here
```

### Python Orchestrator Configuration
```env
ORCHESTRATOR_URL=http://localhost:8000
ORCHESTRATOR_TIMEOUT=30000
ORCHESTRATOR_RETRIES=3
```

### WebSocket Configuration
```env
MAX_WS_CONNECTIONS=100
WS_HEARTBEAT_INTERVAL=30000
```

### Logging Configuration
```env
LOG_LEVEL=info
LOG_FORMAT=json
```

### Security Configuration
```env
CORS_ORIGIN=*
CORS_CREDENTIALS=false
```

### Optional Configuration

#### JWT Secret (if needed for authentication)
```env
JWT_SECRET=your-jwt-secret-key-here
```

#### OpenAI Configuration (if needed)
```env
OPENAI_API_KEY=your-openai-api-key-here
```

#### Redis Configuration (if needed)
```env
REDIS_URL=redis://localhost:6379
```

#### Database Configuration (if needed)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/database
```

#### ChromaDB Configuration (if needed)
```env
CHROMA_HOST=localhost
CHROMA_PORT=8000
```

#### Sector Configuration
```env
SECTOR=generic
```

#### Debug Mode
```env
DEBUG=true
```

## Complete .env File Example

Create a file named `.env` in the `backend-node-realtime` directory with the following content:

```env
# Server Configuration
PORT=3000
HOST=0.0.0.0
NODE_ENV=development

# Voice Provider Configuration
VOICE_PROVIDER=twilio

# Twilio Configuration
TWILIO_ACCOUNT_SID=your-twilio-account-sid-here
TWILIO_AUTH_TOKEN=your-twilio-auth-token-here
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=http://localhost:3000/voice/webhook

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key-here

# Python Orchestrator Configuration
ORCHESTRATOR_URL=http://localhost:8000
ORCHESTRATOR_TIMEOUT=30000
ORCHESTRATOR_RETRIES=3

# WebSocket Configuration
MAX_WS_CONNECTIONS=100
WS_HEARTBEAT_INTERVAL=30000

# Logging Configuration
LOG_LEVEL=info
LOG_FORMAT=json

# Security Configuration
CORS_ORIGIN=*
CORS_CREDENTIALS=false

# JWT Secret
JWT_SECRET=your-jwt-secret-key-here

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/database

# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Sector Configuration
SECTOR=generic

# Debug Mode
DEBUG=true
```

## Validation

The application will automatically validate your environment variables on startup and show warnings for missing required variables.

## Notes

- The `.env` file is already in `.gitignore` to prevent committing sensitive data
- The application uses `dotenv` package to automatically load environment variables
- All configuration is centralized in `src/config.js`
- Missing required variables will show warnings but won't prevent the application from starting (it will use placeholder values) 