"""
Optimized Supabase JWT Authentication Module
"""

import os
import jwt
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import logging
from supabase import create_client, Client
from dotenv import load_dotenv
import time
from app.config import Config

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Init Supabase client using Config
supabase_url = Config.get_env("SUPABASE_URL", required=True)
supabase_anon_key = Config.get_env("SUPABASE_ANON_KEY", required=True)
supabase_service_key = Config.get_env("SUPABASE_SERVICE_ROLE_KEY")
jwt_secret = Config.get_env("JWT_SECRET", required=True)
jwt_expires_in = int(Config.get_env("JWT_EXPIRES_IN", 86400, cast_type=int))  # default: 24h

if not supabase_url or not supabase_anon_key:
    logger.warning("⚠️ Supabase config missing. Auth will be disabled.")
    supabase: Optional[Client] = None
else:
    try:
        supabase = create_client(supabase_url, supabase_anon_key)
        logger.info("✅ Supabase client initialized")
    except Exception as e:
        logger.error(f"❌ Failed to init Supabase client: {e}")
        supabase = None

# Security scheme
security = HTTPBearer()

# Models
class User(BaseModel):
    id: str
    email: str
    role: str = "user"
    metadata: Dict[str, Any] = {}

class AuthResponse(BaseModel):
    user: User
    access_token: str
    refresh_token: str
    expires_in: int

# Service
class SupabaseAuth:
    def __init__(self):
        self.client = supabase
        self.jwt_secret = jwt_secret

        if not self.jwt_secret:
            logger.error("❌ JWT_SECRET not set. Exiting.")
            raise RuntimeError("JWT_SECRET is required")

    def _create_jwt_token(self, user_id: str, email: str, role: str = "user") -> str:
        expire = datetime.utcnow() + timedelta(seconds=jwt_expires_in)
        to_encode = {
            "sub": user_id,
            "email": email,
            "role": role,
            "exp": int(expire.timestamp())
        }
        return jwt.encode(to_encode, self.jwt_secret, algorithm="HS256")

    def _verify_jwt_token(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    def _retry(self, func, *args, retries=3, delay=1, **kwargs):
        """Simple retry wrapper"""
        for attempt in range(retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Retry {attempt + 1}/{retries} failed: {e}")
                time.sleep(delay)
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

    async def sign_up(self, email: str, password: str, metadata: Optional[Dict] = None) -> AuthResponse:
        if not self.client:
            raise HTTPException(status_code=503, detail="Auth service unavailable")

        try:
            response = self._retry(
                self.client.auth.sign_up,
                {
                    "email": email,
                    "password": password,
                    "options": {"data": metadata or {}}
                }
            )

            if response.user:
                user = User(
                    id=response.user.id,
                    email=response.user.email,
                    role=metadata.get("role", "user") if metadata else "user",
                    metadata=metadata or {}
                )
                access_token = self._create_jwt_token(user.id, user.email, user.role)

                return AuthResponse(
                    user=user,
                    access_token=access_token,
                    refresh_token=response.session.refresh_token if response.session else "",
                    expires_in=jwt_expires_in
                )
            else:
                raise HTTPException(status_code=400, detail="Failed to create user")

        except Exception as e:
            logger.error(f"Sign up error for {email}: {e}")
            raise HTTPException(status_code=400, detail="Sign up failed")

    async def sign_in(self, email: str, password: str) -> AuthResponse:
        if not self.client:
            raise HTTPException(status_code=503, detail="Auth service unavailable")

        try:
            response = self._retry(
                self.client.auth.sign_in_with_password,
                {
                    "email": email,
                    "password": password
                }
            )

            if response.user and response.session:
                user_metadata = response.user.user_metadata or {}
                user = User(
                    id=response.user.id,
                    email=response.user.email,
                    role=user_metadata.get("role", "user"),
                    metadata=user_metadata
                )
                access_token = self._create_jwt_token(user.id, user.email, user.role)

                return AuthResponse(
                    user=user,
                    access_token=access_token,
                    refresh_token=response.session.refresh_token,
                    expires_in=jwt_expires_in
                )
            else:
                raise HTTPException(status_code=401, detail="Invalid credentials")

        except Exception as e:
            logger.error(f"Sign in error for {email}: {e}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

    async def refresh_token(self, refresh_token: str) -> AuthResponse:
        if not self.client:
            raise HTTPException(status_code=503, detail="Auth service unavailable")

        try:
            response = self._retry(
                self.client.auth.refresh_session,
                refresh_token
            )

            if response.user and response.session:
                user_metadata = response.user.user_metadata or {}
                user = User(
                    id=response.user.id,
                    email=response.user.email,
                    role=user_metadata.get("role", "user"),
                    metadata=user_metadata
                )
                access_token = self._create_jwt_token(user.id, user.email, user.role)

                return AuthResponse(
                    user=user,
                    access_token=access_token,
                    refresh_token=response.session.refresh_token,
                    expires_in=jwt_expires_in
                )
            else:
                raise HTTPException(status_code=401, detail="Invalid refresh token")

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise HTTPException(status_code=401, detail="Invalid refresh token")

    def get_user_from_token(self, token: str) -> User:
        payload = self._verify_jwt_token(token)
        return User(
            id=payload.get("sub"),
            email=payload.get("email"),
            role=payload.get("role", "user"),
            metadata={}
        )

# Create auth instance
supabase_auth = SupabaseAuth()

# FastAPI dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    if not supabase_auth.client:
        raise HTTPException(status_code=503, detail="Auth service unavailable")
    try:
        return supabase_auth.get_user_from_token(credentials.credentials)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid auth credentials")

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

async def require_roles(allowed_roles: list, current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions. Required roles: {allowed_roles}"
        )
    return current_user

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    return await require_roles(["admin"], current_user) 