# Voice Provider System - Documentation

This document explains how to use and configure different voice providers in the Voice Agent Orchestrator.

## 🎯 Overview

The Voice Agent Orchestrator supports multiple voice providers through a pluggable driver system. This allows you to easily switch between different voice services without changing your application code.

## 📞 Supported Providers

### 1. Twilio (Default)
- **Provider ID**: `twilio`
- **Features**: Voice calls, SMS, TTS, Speech recognition
- **Best for**: Global coverage, reliable service
- **Documentation**: [Twilio Voice API](https://www.twilio.com/voice)

### 2. Vonage (formerly Nexmo)
- **Provider ID**: `vonage`
- **Features**: Voice calls, SMS, TTS, Speech recognition
- **Best for**: European markets, competitive pricing
- **Documentation**: [Vonage Voice API](https://developer.vonage.com/voice)

### 3. AWS Connect
- **Provider ID**: `aws-connect`
- **Features**: Voice calls, TTS, Speech recognition
- **Best for**: AWS ecosystem integration
- **Documentation**: [AWS Connect](https://aws.amazon.com/connect/)

### 4. Generic HTTP
- **Provider ID**: `generic-http`
- **Features**: Custom voice provider integration
- **Best for**: Custom or regional voice providers
- **Documentation**: See configuration section below

## 🔧 Configuration

### Environment Variables

Set the `VOICE_PROVIDER` environment variable to choose your provider:

```bash
# For Twilio
VOICE_PROVIDER=twilio

# For Vonage
VOICE_PROVIDER=vonage

# For AWS Connect
VOICE_PROVIDER=aws-connect

# For Generic HTTP
VOICE_PROVIDER=generic-http
```

### Provider-Specific Configuration

#### Twilio Configuration
```bash
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=http://localhost:3000/voice/webhook
```

#### Vonage Configuration
```bash
VONAGE_API_KEY=your-api-key
VONAGE_API_SECRET=your-api-secret
VONAGE_APPLICATION_ID=your-application-id
VONAGE_PRIVATE_KEY=your-private-key
VONAGE_PHONE_NUMBER=+1234567890
VONAGE_WEBHOOK_URL=http://localhost:3000/voice/webhook
```

#### AWS Connect Configuration
```bash
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-1
AWS_CONNECT_INSTANCE_ID=your-instance-id
AWS_CONNECT_PHONE_NUMBER=+1234567890
AWS_CONNECT_WEBHOOK_URL=http://localhost:3000/voice/webhook
```

#### Generic HTTP Configuration
```bash
GENERIC_HTTP_WEBHOOK_URL=https://your-voice-provider.com/api
GENERIC_HTTP_API_KEY=your-api-key
GENERIC_HTTP_TIMEOUT=30000
GENERIC_HTTP_HEADERS={"Custom-Header": "value"}
```

## 🚀 Quick Setup

### 1. Interactive Setup
```bash
cd backend-node-realtime
npm run setup-env
```

This will guide you through selecting a provider and configuring it.

### 2. Manual Setup
1. Create a `.env` file in `backend-node-realtime/`
2. Set `VOICE_PROVIDER` to your chosen provider
3. Add the required environment variables for your provider
4. Start the server: `npm start`

## 🔄 Dynamic Provider Switching

You can switch providers at runtime using the API:

### List Available Providers
```bash
curl http://localhost:3000/voice/providers
```

### Switch Provider
```bash
curl -X POST http://localhost:3000/voice/providers/switch \
  -H "Content-Type: application/json" \
  -d '{"provider": "vonage"}'
```

### Get Provider Capabilities
```bash
curl http://localhost:3000/voice/providers/vonage/capabilities
```

## 📡 Webhook Endpoints

Each provider has its own webhook endpoint:

- **Twilio**: `POST /voice/webhook`
- **Vonage**: `POST /voice/webhooks/vonage`
- **AWS Connect**: `POST /voice/webhooks/aws-connect`
- **Generic HTTP**: `POST /voice/webhooks/generic`

## 🔌 Generic HTTP Provider

The Generic HTTP provider allows you to integrate with any voice service that provides HTTP webhooks.

### Configuration
```bash
GENERIC_HTTP_WEBHOOK_URL=https://your-voice-provider.com/api
GENERIC_HTTP_API_KEY=your-api-key
GENERIC_HTTP_TIMEOUT=30000
GENERIC_HTTP_HEADERS={"Authorization": "Bearer your-token"}
```

### Expected API Endpoints

Your voice provider should implement these endpoints:

#### 1. Inbound Call
```
POST /inbound-call
Content-Type: application/json

{
  "callId": "unique-call-id",
  "from": "+1234567890",
  "to": "+0987654321",
  "status": "ringing"
}
```

#### 2. Outbound Call
```
POST /outbound-call
Content-Type: application/json

{
  "to": "+1234567890",
  "message": "Hello from AI assistant",
  "callbackUrl": "http://localhost:3000/voice/webhook"
}
```

#### 3. Text-to-Speech
```
POST /tts
Content-Type: application/json

{
  "text": "Hello, how can I help you?",
  "voice": "en-US",
  "language": "en-US"
}
```

#### 4. SMS
```
POST /sms
Content-Type: application/json

{
  "to": "+1234567890",
  "message": "Your appointment is confirmed",
  "from": "+0987654321"
}
```

#### 5. Speech Processing
```
POST /process-speech
Content-Type: application/json

{
  "speechResult": "I need help with my order",
  "confidence": 0.95,
  "callId": "unique-call-id"
}
```

#### 6. Status
```
GET /status
```

Response:
```json
{
  "status": "operational",
  "capabilities": ["inbound_calls", "outbound_calls", "tts", "sms", "speech_processing"]
}
```

## 🧪 Testing

### Test Provider Status
```bash
curl http://localhost:3000/voice/status
```

### Test Health Check
```bash
curl http://localhost:3000/voice/health
```

### Test Configuration
```bash
curl http://localhost:3000/voice/config
```

## 🔍 Troubleshooting

### Common Issues

1. **Provider Not Found**
   ```
   ❌ VoiceAgent Driver "unknown-provider" not found!
   Available drivers: twilio, vonage, aws-connect, generic-http
   ```
   **Solution**: Check your `VOICE_PROVIDER` environment variable

2. **Missing Configuration**
   ```
   ⚠️  Missing twilio environment variables: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
   ```
   **Solution**: Add the required environment variables for your provider

3. **Initialization Failed**
   ```
   ⚠️  VoiceAgent initialization failed for provider: twilio
   ```
   **Solution**: Check your credentials and network connectivity

4. **Webhook Not Working**
   ```
   ❌ Error processing webhook: Failed to process webhook
   ```
   **Solution**: Check webhook URL configuration and network access

### Debug Commands

```bash
# Check environment variables
node -e "console.log(process.env.VOICE_PROVIDER)"

# Test provider initialization
node -e "const VoiceAgent = require('./src/voiceAgent'); VoiceAgent.initialize().then(console.log)"

# Check provider status
curl http://localhost:3000/voice/status
```

## 📊 Provider Comparison

| Feature | Twilio | Vonage | AWS Connect | Generic HTTP |
|---------|--------|--------|-------------|--------------|
| Voice Calls | ✅ | ✅ | ✅ | ✅ |
| SMS | ✅ | ✅ | ❌ | ✅ |
| TTS | ✅ | ✅ | ✅ | ✅ |
| Speech Recognition | ✅ | ✅ | ✅ | ✅ |
| Global Coverage | ✅ | ✅ | ✅ | Depends |
| Pricing | High | Medium | Low | Depends |
| Setup Complexity | Low | Medium | High | Medium |

## 🔄 Migration Guide

### From Twilio to Vonage

1. **Update Environment Variables**
   ```bash
   VOICE_PROVIDER=vonage
   VONAGE_API_KEY=your-vonage-api-key
   VONAGE_API_SECRET=your-vonage-api-secret
   VONAGE_PHONE_NUMBER=your-vonage-number
   ```

2. **Update Webhook URLs**
   - Change Twilio webhook URLs to Vonage webhook URLs
   - Update your Vonage application settings

3. **Test the Migration**
   ```bash
   curl -X POST http://localhost:3000/voice/providers/switch \
     -H "Content-Type: application/json" \
     -d '{"provider": "vonage"}'
   ```

### From Any Provider to Generic HTTP

1. **Set up your voice provider's HTTP API**
2. **Configure Generic HTTP**
   ```bash
   VOICE_PROVIDER=generic-http
   GENERIC_HTTP_WEBHOOK_URL=https://your-provider.com/api
   GENERIC_HTTP_API_KEY=your-api-key
   ```
3. **Test the integration**

## 🆘 Support

### Getting Help

1. **Check the troubleshooting section above**
2. **Review provider-specific documentation**
3. **Check application logs for errors**
4. **Verify environment configuration**

### Provider-Specific Resources

- **Twilio**: [Twilio Support](https://support.twilio.com/)
- **Vonage**: [Vonage Support](https://help.nexmo.com/)
- **AWS Connect**: [AWS Support](https://aws.amazon.com/support/)
- **Generic HTTP**: Depends on your voice provider

---

**Remember**: Always test your voice provider configuration in a development environment before deploying to production! 