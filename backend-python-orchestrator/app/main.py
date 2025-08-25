from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import json
import os
from dotenv import load_dotenv
import logging

# Setup logging
logger = logging.getLogger(__name__)
# Import agents
from app.agents.input_agent import InputAgent
from app.agents.orchestrator_agent import OrchestratorAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.tool_agent import ToolAgents
from app.voice_agent_base import create_voice_agent, ChannelType
# Import websocket_auth
from app.websocket_auth import websocket_auth, require_admin_ws, WSUser
# Import optimization implementations
from app.optimization_implementations import initialize_optimizations, cache_manager, rate_limiter, db_manager, concurrent_processor, api_optimizer, memory_monitor
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)


# Initialize FastAPI app
app = FastAPI(
    title="AIVoice Agent Orchestrator",
    description="Sector-Agnostic AI Voice Agent Orchestrator with Supabase JWT Authentication",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optimization: Initialize on startup
@app.on_event("startup")
async def startup_event():
    await initialize_optimizations()

# Load sector configuration
def load_sector_config() -> Dict:
    sector = os.getenv("SECTOR", "generic")
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
        }
    }
    return sector_configs.get(sector, sector_configs["generic"])

# Initialize agents
sector_config = load_sector_config()
input_agent = InputAgent()
orchestrator_agent = OrchestratorAgent()
memory_agent = MemoryAgent()
tool_agents = ToolAgents(sector_config)
voice_agent = create_voice_agent()

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
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

# --- ROUTES ---

@app.get("/")
def read_root():
    return {
        "message": "Voice Agent Orchestrator is running",
        "version": "2.0.0",
        "sector": sector_config["sector"],
        "available_tools": tool_agents.get_available_tools()
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "sector": sector_config["sector"]
    }

@app.post("/process-audio")
async def process_audio(request: AudioRequest):
    transcribed_text = await input_agent.transcribe_audio(request.audio_data)
    await memory_agent.store_interaction(
        user_id=request.user_id,
        session_id=request.session_id,
        input_type="audio",
        content=transcribed_text
    )
    return {
        "success": True,
        "transcribed_text": transcribed_text
    }

@app.post("/process-intent")
async def process_intent(request: TextRequest):
    intent_result = await orchestrator_agent.determine_intent(
        text=request.text,
        context={}
    )
    tool_response = await tool_agents.route_to_tool(
        intent=intent_result["intent"],
        text=request.text,
        context={}
    )
    await memory_agent.store_interaction(
        user_id=request.user_id,
        session_id=request.session_id,
        input_type="text",
        content=request.text,
        intent=intent_result["intent"],
        response=tool_response
    )
    return {
        "success": True,
        "intent": intent_result["intent"],
        "response": tool_response
    }

# --- VONAGE WEBHOOK ENDPOINTS ---

@app.post("/webhook/vonage/answer")
async def vonage_answer_webhook(request: Request):
    """Handle incoming call answer webhook from Vonage"""
    try:
        form_data = await request.form()
        
        # Log the webhook data
        logger.info(f"Vonage answer webhook received: {dict(form_data)}")
        
        # Extract call details
        call_uuid = form_data.get("uuid")
        from_number = form_data.get("from")
        to_number = form_data.get("to")
        
        # Create NCCO (Nexmo Call Control Object) response
        ncco = [
            {
                "action": "talk",
                "text": "Hello! Welcome to the AI Voice Agent. How can I help you today?",
                "voiceName": "Amy"
            },
            {
                "action": "input",
                "type": ["speech"],
                "speech": {
                    "endOnSilence": 3,
                    "language": "en-US"
                },
                "eventUrl": [f"{request.base_url}webhook/vonage/speech"]
            }
        ]
        
        return {"ncco": ncco}
        
    except Exception as e:
        logger.error(f"Error in Vonage answer webhook: {e}")
        return {"error": str(e)}

@app.post("/webhook/vonage/speech")
async def vonage_speech_webhook(request: Request):
    """Handle speech input from Vonage"""
    try:
        form_data = await request.form()
        
        # Log the speech data
        logger.info(f"Vonage speech webhook received: {dict(form_data)}")
        
        # Extract speech details
        speech_results = form_data.get("speech", {})
        text = speech_results.get("results", [{}])[0].get("text", "")
        
        if text:
            # Process the speech through your AI agents
            intent_result = await orchestrator_agent.determine_intent(
                text=text,
                context={}
            )
            tool_response = await tool_agents.route_to_tool(
                intent=intent_result["intent"],
                text=text,
                context={}
            )
            
            # Create response NCCO
            ncco = [
                {
                    "action": "talk",
                    "text": tool_response,
                    "voiceName": "Amy"
                },
                {
                    "action": "input",
                    "type": ["speech"],
                    "speech": {
                        "endOnSilence": 3,
                        "language": "en-US"
                    },
                    "eventUrl": [f"{request.base_url}webhook/vonage/speech"]
                }
            ]
        else:
            # No speech detected, ask again
            ncco = [
                {
                    "action": "talk",
                    "text": "I didn't catch that. Could you please repeat?",
                    "voiceName": "Amy"
                },
                {
                    "action": "input",
                    "type": ["speech"],
                    "speech": {
                        "endOnSilence": 3,
                        "language": "en-US"
                    },
                    "eventUrl": [f"{request.base_url}webhook/vonage/speech"]
                }
            ]
        
        return {"ncco": ncco}
        
    except Exception as e:
        logger.error(f"Error in Vonage speech webhook: {e}")
        return {"error": str(e)}

@app.post("/webhook/vonage/event")
async def vonage_event_webhook(request: Request):
    """Handle general events from Vonage (call status, etc.)"""
    try:
        form_data = await request.form()
        
        # Log the event
        logger.info(f"Vonage event webhook received: {dict(form_data)}")
        
        # Handle different event types
        event_type = form_data.get("status")
        
        if event_type == "completed":
            logger.info("Call completed")
        elif event_type == "answered":
            logger.info("Call answered")
        elif event_type == "busy":
            logger.info("Call busy")
        elif event_type == "failed":
            logger.info("Call failed")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error in Vonage event webhook: {e}")
        return {"error": str(e)}

# --- WEBSOCKET (SECURED) ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Authenticate user
    user: WSUser = await websocket_auth(websocket)

    # Accept connection after auth
    await manager.connect(websocket)
    print(f"✅ WebSocket connected: {user.email}")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "text":
                await process_text_websocket(message, websocket, user)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"🔌 WebSocket disconnected: {user.email}")

# --- ADMIN WEBSOCKET (SECURED, ROLE=ADMIN) ---

@app.websocket("/ws/admin")
async def admin_websocket_endpoint(websocket: WebSocket):
    # Require admin user
    admin_user: WSUser = await require_admin_ws(websocket)

    # Accept connection after auth
    await manager.connect(websocket)
    print(f"✅ ADMIN WebSocket connected: {admin_user.email}")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "text":
                await process_text_websocket(message, websocket, admin_user)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"🔌 ADMIN WebSocket disconnected: {admin_user.email}")

# --- TEXT PROCESSOR (WS) ---

async def process_text_websocket(message: Dict, websocket: WebSocket, user: WSUser):
    intent_result = await orchestrator_agent.determine_intent(
        text=message["text"],
        context=message.get("context", {})
    )
    tool_response = await tool_agents.route_to_tool(
        intent=intent_result["intent"],
        text=message["text"],
        context=message.get("context", {})
    )
    await websocket.send_text(json.dumps({
        "type": "text_response",
        "intent": intent_result["intent"],
        "response": tool_response,
        "user": user.email
    }))

# --- MAIN ENTRYPOINT ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
