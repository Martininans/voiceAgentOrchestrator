"""
Azure AD B2C with Google Federation Authentication Module
Complete enterprise-grade OAuth implementation supporting Google SSO
NO SUPABASE - Pure Azure AD B2C
"""

import os
import jwt
import httpx
import uuid
import time
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import logging
import redis
from app.config import Config

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Security scheme
security = HTTPBearer()

# Models
class User(BaseModel):
    id: str
    email: str
    name: str
    role: str = "user"
    organization: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    provider: str = "azure_ad_b2c"
    metadata: Dict[str, Any] = {}

class AuthResponse(BaseModel):
    user: User
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"

class AzureADB2CConfig:
    """Azure AD B2C Configuration with Google Federation"""

    def __init__(self):
        self.tenant_id = Config.get_env("AAD_B2C_TENANT_ID", required=True)
        self.client_id = Config.get_env("AAD_B2C_CLIENT_ID", required=True)
        self.client_secret = Config.get_env("AAD_B2C_CLIENT_SECRET", required=True)
        
        # Policies
        self.signup_signin_policy = Config.get_env("AAD_B2C_POLICY", "B2C_1_signupsignin")
        self.google_policy = Config.get_env("AAD_B2C_GOOGLE_POLICY", "B2C_1_GoogleSignIn")
        self.password_reset_policy = Config.get_env("AAD_B2C_PASSWORD_RESET_POLICY", "B2C_1_passwordreset")
        
        # Redirect URIs
        self.redirect_uri = Config.get_env("AAD_B2C_REDIRECT_URI", "http://localhost:8000/auth/callback")
        self.frontend_url = Config.get_env("FRONTEND_URL", "http://localhost:3000")
        
        # JWT Configuration
        self.jwt_secret = Config.get_env("JWT_SECRET", required=True)
        self.jwt_expires_in = int(Config.get_env("JWT_EXPIRES_IN", 3600, cast_type=int))  # 1 hour
        self.refresh_expires_in = int(Config.get_env("REFRESH_EXPIRES_IN", 86400, cast_type=int))  # 24 hours
        
        # Azure AD B2C endpoints
        self.authority = f"https://{self.tenant_id}.b2clogin.com/{self.tenant_id}.onmicrosoft.com"
        self.jwks_uri = f"{self.authority}/{self.signup_signin_policy}/discovery/v2.0/keys"
        
        # Google Federation endpoints
        self.google_auth_url = f"{self.authority}/{self.google_policy}/oauth2/v2.0/authorize"
        self.google_token_url = f"{self.authority}/{self.google_policy}/oauth2/v2.0/token"
        self.google_userinfo_url = f"{self.authority}/{self.google_policy}/openid/v2.0/userinfo"

class AzureADB2CAuth:
    """Azure AD B2C Authentication Service with Google Federation"""
    
    def __init__(self):
        self.config = AzureADB2CConfig()
        self.redis_client = self._init_redis()
        self.active_sessions = {}  # Fallback if Redis unavailable
        
    def _init_redis(self):
        """Initialize Redis client for session management"""
        try:
            redis_url = Config.get_env("REDIS_URL", "redis://localhost:6379")
            return redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.warning(f"Redis not available: {e}. Using in-memory storage.")
            return None
    
    def _store_session(self, key: str, data: Dict[str, Any], expire_seconds: int = 300):
        """Store session data"""
        try:
            if self.redis_client:
                self.redis_client.setex(key, expire_seconds, json.dumps(data))
            else:
                self.active_sessions[key] = {
                    **data,
                    "expires_at": time.time() + expire_seconds
                }
        except Exception as e:
            logger.error(f"Failed to store session: {e}")
    
    def _get_session(self, key: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        try:
            if self.redis_client:
                data = self.redis_client.get(key)
                return json.loads(data) if data else None
            else:
                session = self.active_sessions.get(key)
                if session and session["expires_at"] > time.time():
                    return {k: v for k, v in session.items() if k != "expires_at"}
                return None
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    def _delete_session(self, key: str):
        """Delete session data"""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                self.active_sessions.pop(key, None)
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
    
    async def get_google_auth_url(self, request: Request) -> Dict[str, str]:
        """Generate Google SSO authorization URL through Azure AD B2C"""
        # Generate state parameter for security
        state = str(uuid.uuid4())
        
        # Store state in session
        session_data = {
            "state": state,
            "timestamp": time.time(),
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
            "provider": "google"
        }
        self._store_session(f"oauth_state:{state}", session_data, 600)  # 10 minutes
        
        # Build Google SSO authorization URL
        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "redirect_uri": self.config.redirect_uri,
            "scope": "openid profile email",
            "state": state,
            "response_mode": "query"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        authorization_url = f"{self.config.google_auth_url}?{query_string}"
        
        return {
            "authorization_url": authorization_url,
            "state": state,
            "provider": "google"
        }
    
    async def get_regular_auth_url(self, request: Request) -> Dict[str, str]:
        """Generate regular Azure AD B2C authorization URL"""
        state = str(uuid.uuid4())
        
        session_data = {
            "state": state,
            "timestamp": time.time(),
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
            "provider": "azure_ad"
        }
        self._store_session(f"oauth_state:{state}", session_data, 600)
        
        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "redirect_uri": self.config.redirect_uri,
            "scope": "openid profile email",
            "state": state,
            "response_mode": "query"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{self.config.authority}/{self.config.signup_signin_policy}/oauth2/v2.0/authorize"
        authorization_url = f"{auth_url}?{query_string}"
        
        return {
            "authorization_url": authorization_url,
            "state": state,
            "provider": "azure_ad"
        }
    
    async def exchange_code_for_token(self, code: str, state: str, request: Request) -> AuthResponse:
        """Exchange authorization code for tokens"""
        # Verify state parameter
        session_data = self._get_session(f"oauth_state:{state}")
        if not session_data:
            raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
        
        # Verify IP address (optional security check)
        if session_data.get("ip_address") != request.client.host:
            logger.warning(f"IP mismatch for OAuth callback: {request.client.host}")
        
        provider = session_data.get("provider", "azure_ad")
        
        # Clean up state
        self._delete_session(f"oauth_state:{state}")
        
        try:
            # Determine token endpoint based on provider
            if provider == "google":
                token_endpoint = self.config.google_token_url
            else:
                token_endpoint = f"{self.config.authority}/{self.config.signup_signin_policy}/oauth2/v2.0/token"
            
            # Exchange code for tokens
            token_data = {
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "code": code,
                "redirect_uri": self.config.redirect_uri,
                "grant_type": "authorization_code",
                "scope": "openid profile email"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_endpoint,
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                token_response = response.json()
            
            # Get user information
            user_info = await self._get_user_info(token_response["access_token"], provider)
            
            # Create or update user
            user = await self._create_or_update_user(user_info, provider)
            
            # Generate application tokens
            access_token = self._generate_access_token(user)
            refresh_token = self._generate_refresh_token(user)
            
            # Store refresh token
            self._store_session(
                f"refresh_token:{user.id}",
                {"refresh_token": refresh_token, "user_id": user.id},
                self.config.refresh_expires_in
            )

            return AuthResponse(
                user=user,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.config.jwt_expires_in,
                token_type="Bearer"
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"Token exchange failed: {e.response.text}")
            raise HTTPException(status_code=400, detail="Token exchange failed")
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            raise HTTPException(status_code=400, detail="OAuth authentication failed")
    
    async def _get_user_info(self, access_token: str, provider: str) -> Dict[str, Any]:
        """Get user information from Azure AD B2C"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Determine userinfo endpoint based on provider
        if provider == "google":
            userinfo_endpoint = self.config.google_userinfo_url
        else:
            userinfo_endpoint = f"{self.config.authority}/{self.config.signup_signin_policy}/openid/v2.0/userinfo"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(userinfo_endpoint, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def _create_or_update_user(self, user_info: Dict[str, Any], provider: str) -> User:
        """Create or update user in your system"""
        # Extract user information from Azure AD B2C response
        user_data = {
            "id": user_info.get("sub") or user_info.get("oid"),
            "email": user_info.get("email") or user_info.get("emails", [{}])[0].get("value"),
            "name": user_info.get("name") or f"{user_info.get('given_name', '')} {user_info.get('family_name', '')}".strip(),
            "role": self._determine_user_role(user_info),
            "organization": user_info.get("extension_Organization"),
            "department": user_info.get("extension_Department"),
            "job_title": user_info.get("extension_JobTitle"),
            "provider": f"azure_ad_b2c_{provider}",
            "metadata": {
                "given_name": user_info.get("given_name"),
                "family_name": user_info.get("family_name"),
                "tenant_id": user_info.get("tid"),
                "object_id": user_info.get("oid"),
                "provider": provider,
                "last_login": datetime.utcnow().isoformat(),
                "auth_method": "oauth"
            }
        }
        
        # In production, save to your database
        # For now, return the user object
        return User(**user_data)
    
    def _determine_user_role(self, user_info: Dict[str, Any]) -> str:
        """Determine user role based on Azure AD B2C claims"""
        # Check for admin role in claims
        roles = user_info.get("extension_Roles", [])
        if isinstance(roles, str):
            roles = [roles]
        
        if "admin" in roles or "administrator" in roles:
            return "admin"
        elif "manager" in roles:
            return "manager"
        else:
            return "user"
    
    def _generate_access_token(self, user: User) -> str:
        """Generate application access token"""
        payload = {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "organization": user.organization,
            "provider": user.provider,
            "exp": datetime.utcnow() + timedelta(seconds=self.config.jwt_expires_in),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(payload, self.config.jwt_secret, algorithm="HS256")
    
    def _generate_refresh_token(self, user: User) -> str:
        """Generate refresh token"""
        payload = {
            "sub": user.id,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(seconds=self.config.refresh_expires_in),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.config.jwt_secret, algorithm="HS256")
    
    def _verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.config.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def refresh_access_token(self, refresh_token: str) -> AuthResponse:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = self._verify_token(refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            
            user_id = payload.get("sub")
            
            # Get stored refresh token
            stored_token = self._get_session(f"refresh_token:{user_id}")
            if not stored_token or stored_token.get("refresh_token") != refresh_token:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            
            # Get user information (in production, fetch from database)
            # For now, we'll need to reconstruct user from token
            user = User(
                id=user_id,
                email=payload.get("email", ""),
                name=payload.get("name", ""),
                role=payload.get("role", "user"),
                provider=payload.get("provider", "azure_ad_b2c")
            )
            
            # Generate new tokens
            new_access_token = self._generate_access_token(user)
            new_refresh_token = self._generate_refresh_token(user)
            
            # Update stored refresh token
            self._store_session(
                f"refresh_token:{user_id}",
                {"refresh_token": new_refresh_token, "user_id": user_id},
                self.config.refresh_expires_in
            )

            return AuthResponse(
                user=user,
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_in=self.config.jwt_expires_in,
                token_type="Bearer"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise HTTPException(status_code=401, detail="Token refresh failed")
    
    async def logout(self, user_id: str, refresh_token: str):
        """Logout user and invalidate tokens"""
        try:
            # Remove refresh token from storage
            self._delete_session(f"refresh_token:{user_id}")
            
            # In production, you might want to add the access token to a blacklist
            # For now, we rely on short token expiration
            
            return {"message": "Logged out successfully"}
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            raise HTTPException(status_code=500, detail="Logout failed")

# Create auth instance
azure_auth = AzureADB2CAuth()

# FastAPI dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    try:
        payload = azure_auth._verify_token(credentials.credentials)
        
        # Check if token is expired
        if payload.get("exp", 0) < time.time():
            raise HTTPException(status_code=401, detail="Token expired")
        
        # Return user object
        return User(
            id=payload.get("sub"),
            email=payload.get("email"),
            name=payload.get("name"),
            role=payload.get("role", "user"),
            organization=payload.get("organization"),
            provider=payload.get("provider", "azure_ad_b2c"),
            metadata={}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_roles(allowed_roles: list, current_user: User = Depends(get_current_user)) -> User:
    """Require specific roles"""
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions. Required roles: {allowed_roles}"
        )
    return current_user