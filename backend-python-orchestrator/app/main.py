from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import json
import os
from dotenv import load_dotenv

# Import our agents
from agents.input_agent import InputAgent
from agents.orchestrator_agent import OrchestratorAgent
from agents.memory_agent import MemoryAgent
from agents.tool_agents_refactored import ToolAgents
from voice_agent_base import create_voice_agent, ChannelType

load_dotenv()

app = FastAPI(
    title="Voice Agent Orchestrator",
    description="Sector-Agnostic AI Voice Agent Orchestrator",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load sector configuration
def load_sector_config() -> Dict:
    """Load sector configuration from environment or config file"""
    sector = os.getenv("SECTOR", "generic")
    
    # Default configurations for different sectors
    sector_configs = {
        "generic": {
            "sector": "generic",
            "available_tools": [
                "booking", "information", "reminder", "support", 
                "notification", "search", "help", "greeting", "goodbye"
            ],
            "intent_mapping": {
                "booking": ["book", "reserve", "schedule", "appointment"],
                "information": ["info", "details", "hours", "location", "contact"],
                "reminder": ["remind", "reminder", "alert", "notify"],
                "support": ["help", "support", "assist", "issue"],
                "notification": ["notify", "alert", "message", "sms"],
                "search": ["find", "search", "lookup", "locate"],
                "help": ["help", "assist", "guide", "support"],
                "greeting": ["hello", "hi", "good morning", "good afternoon"],
                "goodbye": ["bye", "goodbye", "see you", "thank you"]
            }
        },
        "hotel": {
            "sector": "hotel",
            "available_tools": [
                "booking", "information", "reminder", "support", 
                "notification", "search", "help", "greeting", "goodbye",
                "room_service", "housekeeping", "concierge"
            ],
            "intent_mapping": {
                "booking": ["book", "reserve", "room", "check-in", "check-out"],
                "information": ["info", "details", "wifi", "amenities", "hours"],
                "room_service": ["food", "order", "room service", "dining"],
                "housekeeping": ["clean", "towel", "housekeeping", "maintenance"],
                "concierge": ["concierge", "assist", "recommendation"],
                "reminder": ["remind", "reminder", "wake-up", "call"],
                "support": ["help", "support", "assist", "issue"],
                "notification": ["notify", "alert", "message", "sms"],
                "search": ["find", "search", "lookup", "locate"],
                "help": ["help", "assist", "guide", "support"],
                "greeting": ["hello", "hi", "good morning", "good afternoon"],
                "goodbye": ["bye", "goodbye", "see you", "thank you"]
            }
        },
        "hospital": {
            "sector": "hospital",
            "available_tools": [
                "booking", "information", "reminder", "support", 
                "notification", "search", "help", "greeting", "goodbye",
                "appointment", "triage", "emergency"
            ],
            "intent_mapping": {
                "booking": ["book", "schedule", "appointment", "visit"],
                "information": ["info", "details", "hours", "department", "location"],
                "appointment": ["appointment", "schedule", "doctor", "visit"],
                "triage": ["symptom", "health", "assessment", "triage"],
                "emergency": ["emergency", "urgent", "critical", "ambulance"],
                "reminder": ["remind", "reminder", "appointment", "follow-up"],
                "support": ["help", "support", "assist", "issue"],
                "notification": ["notify", "alert", "message", "sms"],
                "search": ["find", "search", "lookup", "locate"],
                "help": ["help", "assist", "guide", "support"],
                "greeting": ["hello", "hi", "good morning", "good afternoon"],
                "goodbye": ["bye", "goodbye", "see you", "thank you"]
            }
        }
    }
    
    return sector_configs.get(sector, sector_configs["generic"])

# Initialize agents with sector configuration
sector_config = load_sector_config()
input_agent = InputAgent()
orchestrator_agent = OrchestratorAgent()
memory_agent = MemoryAgent()
tool_agents = ToolAgents(sector_config)
voice_agent = create_voice_agent({"provider": "twilio"})

# WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Pydantic models
class AudioRequest(BaseModel):
    audio_data: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    sector: Optional[str] = None

class TextRequest(BaseModel):
    text: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    sector: Optional[str] = None

class IntentRequest(BaseModel):
    text: str
    context: Optional[Dict] = None
    sector: Optional[str] = None

class SectorConfigRequest(BaseModel):
    sector: str
    config: Dict

@app.get("/")
def read_root():
    return {
        "message": "Sector-Agnostic Voice Agent Orchestrator is running",
        "version": "2.0.0",
        "current_sector": sector_config["sector"],
        "agents": ["input", "orchestrator", "memory", "tools", "voice"],
        "available_tools": tool_agents.get_available_tools()
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "agents": "all_operational",
        "sector": sector_config["sector"],
        "voice_provider": voice_agent.__class__.__name__
    }

@app.get("/sector")
def get_sector_info():
    """Get current sector configuration"""
    return {
        "current_sector": sector_config["sector"],
        "available_tools": tool_agents.get_available_tools(),
        "intent_mapping": sector_config.get("intent_mapping", {})
    }

@app.post("/sector/configure")
async def configure_sector(request: SectorConfigRequest):
    """Configure sector-specific settings"""
    global sector_config, tool_agents
    
    # Update sector configuration
    sector_config = request.config
    sector_config["sector"] = request.sector
    
    # Reinitialize tool agents with new configuration
    tool_agents = ToolAgents(sector_config)
    
    return {
        "success": True,
        "message": f"Sector configured to {request.sector}",
        "sector": request.sector,
        "available_tools": tool_agents.get_available_tools()
    }

@app.post("/process-audio")
async def process_audio(request: AudioRequest):
    """Process audio input and return text transcription"""
    try:
        # Step 1: Transcribe audio to text
        transcribed_text = await input_agent.transcribe_audio(request.audio_data)
        
        # Step 2: Store in memory
        await memory_agent.store_interaction(
            user_id=request.user_id,
            session_id=request.session_id,
            input_type="audio",
            content=transcribed_text
        )
        
        return {
            "success": True,
            "transcribed_text": transcribed_text,
            "next_step": "process_intent",
            "sector": sector_config["sector"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-intent")
async def process_intent(request: IntentRequest):
    """Determine intent and route to appropriate agent"""
    try:
        # Step 1: Determine intent using GPT-4
        intent_result = await orchestrator_agent.determine_intent(
            text=request.text,
            context=request.context
        )
        
        # Step 2: Route to appropriate tool agent
        tool_response = await tool_agents.route_to_tool(
            intent=intent_result["intent"],
            text=request.text,
            context=request.context
        )
        
        # Step 3: Store interaction in memory
        await memory_agent.store_interaction(
            user_id=request.context.get("user_id") if request.context else None,
            session_id=request.context.get("session_id") if request.context else None,
            input_type="text",
            content=request.text,
            intent=intent_result["intent"],
            response=tool_response
        )
        
        return {
            "success": True,
            "intent": intent_result["intent"],
            "confidence": intent_result["confidence"],
            "response": tool_response,
            "next_step": "voice_response",
            "sector": sector_config["sector"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-voice-response")
async def generate_voice_response(request: TextRequest):
    """Generate voice response from text"""
    try:
        # Generate TTS response
        voice_response = await voice_agent.text_to_speech(request.text)
        
        return {
            "success": True,
            "voice_url": voice_response.get("url"),
            "duration": voice_response.get("duration"),
            "provider": voice_response.get("provider"),
            "format": voice_response.get("format")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-message")
async def send_message(request: TextRequest):
    """Send message via configured channel"""
    try:
        # Determine channel from context or use default
        channel = ChannelType.SMS  # Default
        if request.context and "channel" in request.context:
            channel = ChannelType(request.context["channel"])
        
        # Send via VoiceAgent
        message_result = await voice_agent.send_message(
            to=request.context.get("recipient") if request.context else "",
            message=request.text,
            channel=channel,
            context=request.context
        )
        
        return {
            "success": True,
            "message_id": message_result.get("message_id"),
            "status": message_result.get("status"),
            "provider": message_result.get("provider"),
            "channel": message_result.get("channel")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/{user_id}")
async def get_user_memory(user_id: str):
    """Retrieve user interaction history"""
    try:
        memory = await memory_agent.get_user_memory(user_id)
        return {
            "success": True,
            "user_id": user_id,
            "memory": memory,
            "sector": sector_config["sector"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools")
async def get_available_tools():
    """Get list of available tools for current sector"""
    tools = {}
    for tool_name in tool_agents.get_available_tools():
        tools[tool_name] = tool_agents.get_tool_description(tool_name)
    
    return {
        "sector": sector_config["sector"],
        "available_tools": tools
    }

@app.get("/voice/status")
async def get_voice_agent_status():
    """Get voice agent status and capabilities"""
    status = await voice_agent.get_status()
    return {
        "voice_agent": status,
        "sector": sector_config["sector"]
    }

# WebSocket endpoint for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process based on message type
            if message["type"] == "audio":
                # Process audio
                result = await process_audio_websocket(message, websocket)
                await manager.send_personal_message(json.dumps(result), websocket)
                
            elif message["type"] == "text":
                # Process text
                result = await process_text_websocket(message, websocket)
                await manager.send_personal_message(json.dumps(result), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def process_audio_websocket(message: Dict, websocket: WebSocket):
    """Process audio via WebSocket"""
    try:
        # Transcribe audio
        transcribed_text = await input_agent.transcribe_audio(message["audio_data"])
        
        # Determine intent
        intent_result = await orchestrator_agent.determine_intent(
            text=transcribed_text,
            context=message.get("context")
        )
        
        # Get tool response
        tool_response = await tool_agents.route_to_tool(
            intent=intent_result["intent"],
            text=transcribed_text,
            context=message.get("context")
        )
        
        # Generate voice response
        voice_response = await voice_agent.text_to_speech(tool_response["response"])
        
        return {
            "type": "response",
            "transcribed_text": transcribed_text,
            "intent": intent_result["intent"],
            "response": tool_response["response"],
            "voice_url": voice_response.get("url"),
            "sector": sector_config["sector"]
        }
    except Exception as e:
        return {
            "type": "error",
            "message": str(e)
        }

async def process_text_websocket(message: Dict, websocket: WebSocket):
    """Process text via WebSocket"""
    try:
        # Determine intent
        intent_result = await orchestrator_agent.determine_intent(
            text=message["text"],
            context=message.get("context")
        )
        
        # Get tool response
        tool_response = await tool_agents.route_to_tool(
            intent=intent_result["intent"],
            text=message["text"],
            context=message.get("context")
        )
        
        return {
            "type": "response",
            "intent": intent_result["intent"],
            "response": tool_response["response"],
            "sector": sector_config["sector"]
        }
    except Exception as e:
        return {
            "type": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)