# Voice Agent Orchestrator - Refactored (Sector-Agnostic & Loosely Coupled)

## 🚀 **Overview**

This is a **sector-agnostic** and **loosely coupled** voice agent orchestrator that can be used by any industry or sector. The system is designed to be:

- **Sector-Agnostic**: Works for hotels, hospitals, retail, education, logistics, or any other sector
- **Loosely Coupled**: VoiceAgent is abstracted and supports multiple providers (Twilio, AWS, etc.)
- **Configurable**: Easy to add new sectors and tools without code changes
- **Scalable**: Microservice architecture with clear separation of concerns

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Node.js        │    │   Python        │
│   (Web Audio)   │◄──►│   (WebSocket)    │◄──►│   (Orchestrator)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Supabase       │    │   VoiceAgent    │
                       │   (Database)     │    │   (Abstracted)  │
                       └──────────────────┘    └─────────────────┘
```

## 🔧 **Key Components**

### 1. **Sector-Agnostic Tool Agents**
- **BaseTool**: Abstract base class for all tools
- **ToolAgents**: Registry that loads tools based on sector configuration
- **GenericTool**: Fallback tool that works for any sector
- **Sector-Specific Tools**: Can be added dynamically

### 2. **Loosely Coupled VoiceAgent**
- **VoiceAgentBase**: Abstract interface for voice communication
- **VoiceAgentFactory**: Factory pattern for creating voice agents
- **Provider Implementations**: Twilio, AWS Polly, etc.
- **Channel Support**: Voice, SMS, WhatsApp, Email, etc.

### 3. **Configurable Sectors**
- **Generic**: Basic tools for any sector
- **Hotel**: Room booking, amenities, concierge
- **Hospital**: Appointments, triage, emergency
- **Custom**: Easy to add new sectors

## 🚀 **Quick Start**

### 1. **Environment Setup**

```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies
cd backend-node-realtime
npm install

# Environment variables
cp .env.example .env
```

### 2. **Environment Variables**

```env
# OpenAI
OPENAI_API_KEY=your_openai_key

# Voice Provider (default: twilio)
VOICE_PROVIDER=twilio

# Sector (default: generic)
SECTOR=generic

# Twilio (if using Twilio)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=your_phone_number

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 3. **Start Services**

```bash
# Start Python orchestrator
cd backend-python-orchestrator/app
python main_refactored.py

# Start Node.js realtime layer
cd backend-node-realtime
npm start
```

## 📋 **API Endpoints**

### **Core Endpoints**

```http
GET  /                    # System status
GET  /health             # Health check
GET  /sector             # Current sector info
POST /sector/configure   # Configure sector
GET  /tools              # Available tools
GET  /voice/status       # Voice agent status
```

### **Processing Endpoints**

```http
POST /process-audio      # Transcribe audio
POST /process-intent     # Determine intent
POST /generate-voice-response  # Text to speech
POST /send-message       # Send message
GET  /memory/{user_id}   # User memory
```

### **WebSocket**

```http
WS   /ws                 # Real-time communication
```

## 🎯 **Sector Configuration**

### **Generic Sector (Default)**

```json
{
  "sector": "generic",
  "available_tools": [
    "booking", "information", "reminder", "support", 
    "notification", "search", "help", "greeting", "goodbye"
  ],
  "intent_mapping": {
    "booking": ["book", "reserve", "schedule", "appointment"],
    "information": ["info", "details", "hours", "location", "contact"],
    "reminder": ["remind", "reminder", "alert", "notify"],
    "support": ["help", "support", "assist", "issue"]
  }
}
```

### **Hotel Sector**

```json
{
  "sector": "hotel",
  "available_tools": [
    "booking", "information", "reminder", "support", 
    "notification", "search", "help", "greeting", "goodbye",
    "room_service", "housekeeping", "concierge"
  ],
  "intent_mapping": {
    "booking": ["book", "reserve", "room", "check-in", "check-out"],
    "room_service": ["food", "order", "room service", "dining"],
    "housekeeping": ["clean", "towel", "housekeeping", "maintenance"],
    "concierge": ["concierge", "assist", "recommendation"]
  }
}
```

### **Hospital Sector**

```json
{
  "sector": "hospital",
  "available_tools": [
    "booking", "information", "reminder", "support", 
    "notification", "search", "help", "greeting", "goodbye",
    "appointment", "triage", "emergency"
  ],
  "intent_mapping": {
    "booking": ["book", "schedule", "appointment", "visit"],
    "appointment": ["appointment", "schedule", "doctor", "visit"],
    "triage": ["symptom", "health", "assessment", "triage"],
    "emergency": ["emergency", "urgent", "critical", "ambulance"]
  }
}
```

## 🔌 **Adding New Sectors**

### 1. **Create Sector Configuration**

```python
# Add to load_sector_config() in main_refactored.py
"retail": {
    "sector": "retail",
    "available_tools": [
        "booking", "information", "reminder", "support", 
        "notification", "search", "help", "greeting", "goodbye",
        "inventory", "pricing", "returns"
    ],
    "intent_mapping": {
        "booking": ["book", "reserve", "appointment", "consultation"],
        "inventory": ["stock", "availability", "inventory", "check"],
        "pricing": ["price", "cost", "discount", "offer"],
        "returns": ["return", "refund", "exchange", "warranty"]
    }
}
```

### 2. **Create Sector-Specific Tools (Optional)**

```python
# tools/retail/inventory_tool.py
from agents.tool_agents_refactored import BaseTool

class InventoryTool(BaseTool):
    async def execute(self, text: str, context: Dict = None) -> Dict[str, Any]:
        # Custom inventory logic
        return {"response": "Inventory check completed", "success": True}
    
    def get_description(self) -> str:
        return "Check product inventory and availability"
```

### 3. **Set Environment Variable**

```bash
export SECTOR=retail
```

## 🔌 **Adding New Voice Providers**

### 1. **Create Provider Implementation**

```python
# voice_agent_base.py
class CustomVoiceAgent(VoiceAgentBase):
    def _initialize(self):
        # Initialize your provider
        self.supported_channels = [ChannelType.VOICE, ChannelType.SMS]
    
    async def send_message(self, to: str, message: str, channel: ChannelType, context: Dict = None):
        # Your implementation
        pass
    
    async def make_call(self, to: str, message: str, context: Dict = None):
        # Your implementation
        pass
    
    async def text_to_speech(self, text: str, voice_config: Dict = None):
        # Your implementation
        pass
    
    async def speech_to_text(self, audio_data: bytes, audio_config: Dict = None):
        # Your implementation
        pass
```

### 2. **Register Provider**

```python
# Register in voice_agent_base.py
VoiceAgentFactory.register_provider("custom", CustomVoiceAgent)
```

### 3. **Use Provider**

```bash
export VOICE_PROVIDER=custom
```

## 📊 **Usage Examples**

### **Basic Text Processing**

```python
import requests

# Process text intent
response = requests.post("http://localhost:8000/process-intent", json={
    "text": "I need to book a room for tomorrow",
    "context": {"user_id": "user123", "sector": "hotel"}
})

print(response.json())
# Output: {"intent": "booking", "response": {...}, "sector": "hotel"}
```

### **Audio Processing**

```python
# Process audio
response = requests.post("http://localhost:8000/process-audio", json={
    "audio_data": "base64_encoded_audio",
    "user_id": "user123"
})

print(response.json())
# Output: {"transcribed_text": "Hello, I need help", "sector": "generic"}
```

### **WebSocket Communication**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'text',
        text: 'What services do you offer?',
        context: { user_id: 'user123' }
    }));
};

ws.onmessage = (event) => {
    const response = JSON.parse(event.data);
    console.log(response);
};
```

### **Sector Configuration**

```python
# Change sector dynamically
response = requests.post("http://localhost:8000/sector/configure", json={
    "sector": "hospital",
    "config": {
        "sector": "hospital",
        "available_tools": ["booking", "information", "appointment"],
        "intent_mapping": {...}
    }
})
```

## 🧪 **Testing**

### **Health Check**

```bash
curl http://localhost:8000/health
```

### **Sector Info**

```bash
curl http://localhost:8000/sector
```

### **Available Tools**

```bash
curl http://localhost:8000/tools
```

### **Voice Agent Status**

```bash
curl http://localhost:8000/voice/status
```

## 🔧 **Development**

### **Project Structure**

```
backend-python-orchestrator/
├── app/
│   ├── agents/
│   │   ├── input_agent.py
│   │   ├── orchestrator_agent.py
│   │   ├── memory_agent.py
│   │   ├── tool_agents_refactored.py
│   │   └── voice_agent_base.py
│   ├── main_refactored.py
│   └── tools/
│       ├── hotel/
│       ├── hospital/
│       └── retail/
└── requirements.txt

backend-node-realtime/
├── src/
│   ├── index.js
│   ├── routes/
│   └── voiceAgent/
└── package.json
```

### **Adding New Tools**

1. Create tool class extending `BaseTool`
2. Implement `execute()` and `get_description()` methods
3. Add to sector configuration
4. Register in tool registry

### **Adding New Voice Providers**

1. Create provider class extending `VoiceAgentBase`
2. Implement all abstract methods
3. Register with `VoiceAgentFactory`
4. Set environment variable

## 🚀 **Deployment**

### **Docker**

```dockerfile
# Python orchestrator
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main_refactored.py"]
```

### **Environment Variables**

```bash
# Production environment variables
export OPENAI_API_KEY=your_key
export VOICE_PROVIDER=twilio
export SECTOR=hotel
export TWILIO_ACCOUNT_SID=your_sid
export TWILIO_AUTH_TOKEN=your_token
```

## 📈 **Monitoring & Metrics**

- **Health Checks**: `/health` endpoint
- **Sector Status**: `/sector` endpoint
- **Tool Availability**: `/tools` endpoint
- **Voice Agent Status**: `/voice/status` endpoint

## 🔒 **Security**

- **Environment Variables**: All sensitive data in env vars
- **CORS**: Configured for cross-origin requests
- **Input Validation**: Pydantic models for request validation
- **Error Handling**: Comprehensive error handling and logging

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## 📄 **License**

MIT License - see LICENSE file for details

---

**🎉 You now have a fully sector-agnostic and loosely coupled voice agent orchestrator!** 