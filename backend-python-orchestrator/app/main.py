from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import json
import os
from dotenv import load_dotenv
import logging
import time
import uuid
import redis
from prometheus_client import Counter, Histogram, CollectorRegistry, CONTENT_TYPE_LATEST, generate_latest

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

# LangGraph wiring
from app.graphs.conversation_graph import build_graph
from app.tools.router import route_to_tool as simple_route
from app.auth import azure_auth, AuthResponse, User, get_current_user, get_optional_user, require_admin, require_roles
from fastapi import Request


# Initialize FastAPI app
app = FastAPI(
    title="AIVoice Agent Orchestrator",
    description="Sector-Agnostic AI Voice Agent Orchestrator with Supabase JWT Authentication",
    version="1.0.0"
)

# CORS middleware - Production ready configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://your-frontend-domain.com",  # Replace with actual frontend domain
        "https://your-app-domain.com"        # Replace with actual app domain
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
)

# Optimization: Initialize on startup
@app.on_event("startup")
async def startup_event():
    # Allow disabling optimizations (e.g., when Redis is not running)
    disable_opt = os.getenv("DISABLE_OPTIMIZATIONS", "false").lower()
    if disable_opt == "true":
        logger.warning("Starting without optimizations (DISABLE_OPTIMIZATIONS=true)")
        return
    
    try:
        await initialize_optimizations()
    except Exception as e:
        logger.warning(f"Failed to initialize optimizations: {e}")
        logger.warning("Continuing without optimizations...")

# --- Observability: Correlation IDs & Metrics ---
registry = CollectorRegistry()
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=("method", "path", "status"),
    registry=registry,
)
http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=("method", "path"),
    registry=registry,
)

@app.middleware("http")
async def metrics_and_correlation_middleware(request: Request, call_next):
    start_time = time.time()
    # Correlation ID
    req_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    # Process request
    response: Response
    try:
        response = await call_next(request)
    finally:
        duration = time.time() - start_time
        path_template = request.scope.get("path") or request.url.path
        http_request_duration.labels(request.method, path_template).observe(duration)
    # Count after response determined
    http_requests_total.labels(request.method, path_template, str(response.status_code)).inc()
    # Propagate header
    response.headers["x-request-id"] = req_id
    return response

@app.get("/metrics")
def metrics():
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

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

# Build minimal graph using LangChain-based classifier and simple router

def classify_node(state: Dict) -> Dict:
    # No-op: intent is precomputed in the endpoint and included in state
    return state


def act_node(state: Dict) -> Dict:
    tool_response = simple_route(
        intent=state.get("intent", "fallback"),
        text=state["text"],
        context=state.get("context", {})
    )
    state.update({"response": tool_response})
    return state

conversation_graph = build_graph(classify_node, act_node)

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

@app.get("/ready")
def readiness_check():
    # Optionally verify Redis connectivity if configured
    redis_url = os.getenv("REDIS_URL")
    redis_ok = None
    if redis_url:
        try:
            r = redis.from_url(redis_url, socket_connect_timeout=1, socket_timeout=1)
            r.ping()
            redis_ok = True
        except Exception:
            redis_ok = False
    return {
        "ready": True if (redis_ok is not False) else False,
        "redis": redis_ok,
        "sector": sector_config["sector"],
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
    # Compute intent first (async), then run graph for action only
    intent_result = await orchestrator_agent.determine_intent(
        text=request.text,
        context={
            "user_id": request.user_id,
            "session_id": request.session_id,
            "sector": request.sector
        }
    )

    initial_state = {
        "text": request.text,
        "context": {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "sector": request.sector
        },
        "intent": intent_result.get("intent"),
        "confidence": intent_result.get("confidence", 0.0)
    }
    result_state = conversation_graph.invoke(initial_state)

    await memory_agent.store_interaction(
        user_id=request.user_id,
        session_id=request.session_id,
        input_type="text",
        content=request.text,
        intent=result_state.get("intent"),
        response=result_state.get("response")
    )
    return {
        "success": True,
        "intent": result_state.get("intent"),
        "response": result_state.get("response"),
        "confidence": result_state.get("confidence", 0.0)
    }

# =============================================================================
# AZURE AD B2C AUTHENTICATION ENDPOINTS
# =============================================================================

@app.get("/auth/google", response_model=Dict[str, str])
async def get_google_auth_url(request: Request):
    """Get Google SSO authorization URL through Azure AD B2C"""
    try:
        return await azure_auth.get_google_auth_url(request)
    except Exception as e:
        logger.error(f"Google auth URL error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate Google auth URL")

@app.get("/auth/azure", response_model=Dict[str, str])
async def get_azure_auth_url(request: Request):
    """Get Azure AD B2C authorization URL"""
    try:
        return await azure_auth.get_regular_auth_url(request)
    except Exception as e:
        logger.error(f"Azure auth URL error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate Azure auth URL")

@app.post("/auth/callback", response_model=AuthResponse)
async def oauth_callback(
    code: str,
    state: str,
    request: Request
):
    """Handle OAuth callback from Azure AD B2C (Google or regular)"""
    try:
        return await azure_auth.exchange_code_for_token(code, state, request)
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail="OAuth authentication failed")

@app.post("/auth/refresh", response_model=AuthResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    try:
        return await azure_auth.refresh_access_token(refresh_token)
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=401, detail="Token refresh failed")

@app.post("/auth/logout")
async def logout(
    user_id: str,
    refresh_token: str,
    current_user: User = Depends(get_current_user)
):
    """Logout user and invalidate tokens"""
    try:
        return await azure_auth.logout(user_id, refresh_token)
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@app.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.get("/auth/providers")
async def get_auth_providers():
    """Get available authentication providers"""
    return {
        "providers": [
            {
                "name": "google",
                "display_name": "Google",
                "auth_url_endpoint": "/auth/google",
                "icon": "https://developers.google.com/identity/images/g-logo.png"
            },
            {
                "name": "azure_ad",
                "display_name": "Microsoft Account",
                "auth_url_endpoint": "/auth/azure",
                "icon": "https://img.icons8.com/color/48/000000/microsoft.png"
            }
        ]
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
    # Compute intent first (async), then run graph for action only
    intent_result = await orchestrator_agent.determine_intent(
        text=message["text"],
        context={**message.get("context", {}), "user_id": user.email}
    )
    state = {
        "text": message["text"],
        "context": {**message.get("context", {}), "user_id": user.email},
        "intent": intent_result.get("intent"),
        "confidence": intent_result.get("confidence", 0.0)
    }
    result = conversation_graph.invoke(state)
    await websocket.send_text(json.dumps({
        "type": "text_response",
        "intent": result.get("intent"),
        "response": result.get("response"),
        "user": user.email,
        "confidence": result.get("confidence", 0.0)
    }))

# --- MAIN ENTRYPOINT ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
