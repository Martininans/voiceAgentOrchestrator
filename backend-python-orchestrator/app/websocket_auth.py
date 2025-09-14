"""
WebSocket Authentication Middleware
Validates JWT token during WebSocket handshake
"""

from fastapi import WebSocket, HTTPException, status
from typing import Optional
import logging
import jwt
import os

from app.auth import azure_auth, User  # Import your Azure AD B2C auth instance
from app.config import Config

logger = logging.getLogger(__name__)

# Load JWT secret from config (fallback to mock if needed)
JWT_SECRET = Config.get_env("JWT_SECRET", "mock-jwt-secret-key-for-development-only")

__all__ = ["websocket_auth", "require_admin_ws", "WSUser"]

class WSUser(User):
    """Extended User model for WebSocket session"""
    def __init__(self, user_id: str, email: str, role: str, metadata: dict = {}):
        super().__init__(id=user_id, email=email, role=role, metadata=metadata)

async def websocket_auth(websocket: WebSocket) -> WSUser:
    """
    Authenticate WebSocket connection and return WSUser
    
    Supports token via:
    - Query param ?token=xxx
    - Header Authorization: Bearer xxx
    """
    token: Optional[str] = None

    # 1️⃣ Try query param
    token = websocket.query_params.get("token")

    # 2️⃣ Try header if no query param
    if not token:
        auth_header = websocket.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

    # 3️⃣ Reject if no token
    if not token:
        logger.warning("WebSocket connection rejected: no token provided")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token in WebSocket connection"
        )

    # 4️⃣ Verify token via SupabaseAuth or fallback
    try:
        # Prefer using your SupabaseAuth logic
        payload = azure_auth._verify_jwt_token(token)
        
        user = WSUser(
            user_id=payload.get("sub"),
            email=payload.get("email"),
            role=payload.get("role", "user"),
            metadata={}  # You can extract more from payload if needed
        )

        logger.info(f"✅ WebSocket auth success: user={user.email}, role={user.role}")
        return user

    except jwt.ExpiredSignatureError:
        logger.error("WebSocket token expired")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )

    except jwt.PyJWTError as e:
        logger.error(f"WebSocket token invalid: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"WebSocket auth error: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication"
        )

async def require_admin_ws(websocket: WebSocket) -> WSUser:
    """Require admin role for WebSocket"""
    user = await websocket_auth(websocket)
    
    if user.role != "admin":
        logger.warning(f"WebSocket rejected: user {user.email} is not admin")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin required."
        )
    
    return user
