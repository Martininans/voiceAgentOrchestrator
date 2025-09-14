"""
Security middleware for the Python orchestrator
"""
import logging
import time
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import re
import asyncio
from collections import defaultdict, deque
import os

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
    
    async def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed for the given IP"""
        now = time.time()
        client_requests = self.requests[client_ip]
        
        # Remove old requests outside the window
        while client_requests and client_requests[0] <= now - self.window_seconds:
            client_requests.popleft()
        
        # Check if under limit
        if len(client_requests) >= self.max_requests:
            return False
        
        # Add current request
        client_requests.append(now)
        return True

# Rate limiters for different endpoints
general_limiter = RateLimiter(max_requests=100, window_seconds=900)  # 100 requests per 15 minutes
strict_limiter = RateLimiter(max_requests=20, window_seconds=900)    # 20 requests per 15 minutes
voice_limiter = RateLimiter(max_requests=10, window_seconds=60)      # 10 requests per minute

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    # Check for forwarded headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    if hasattr(request.client, 'host'):
        return request.client.host
    
    return "unknown"

def sanitize_input(data: Any) -> Any:
    """Sanitize input data to prevent injection attacks"""
    if isinstance(data, str):
        # Remove potentially dangerous characters
        return re.sub(r'[<>"\'%;()&+]', '', data)
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    else:
        return data

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    client_ip = get_client_ip(request)
    
    # Choose limiter based on endpoint
    if request.url.path.startswith("/voice/"):
        limiter = voice_limiter
    elif request.url.path.startswith("/process-intent"):
        limiter = strict_limiter
    else:
        limiter = general_limiter
    
    if not await limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Too many requests from this IP, please try again later",
                "retry_after": limiter.window_seconds,
                "timestamp": time.time()
            }
        )
    
    response = await call_next(request)
    return response

async def request_logging_middleware(request: Request, call_next):
    """Request logging middleware"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path} from {get_client_ip(request)}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    duration = time.time() - start_time
    logger.info(f"Response: {response.status_code} in {duration:.3f}s")
    
    return response

async def input_validation_middleware(request: Request, call_next):
    """Input validation and sanitization middleware"""
    # Sanitize query parameters
    if request.query_params:
        sanitized_params = sanitize_input(dict(request.query_params))
        # Note: FastAPI doesn't allow direct modification of query_params
        # This is more of a logging/validation step
    
    # For POST requests, sanitize body will be handled in the endpoint
    response = await call_next(request)
    return response

async def security_headers_middleware(request: Request, call_next):
    """Add security headers to responses"""
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # Add HSTS header in production
    if os.getenv("NODE_ENV") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    return response

def get_cors_middleware():
    """Get CORS middleware configuration"""
    allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
    
    return CORSMiddleware(
        app=None,  # Will be set when added to FastAPI app
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        max_age=86400  # 24 hours
    )

def get_trusted_host_middleware():
    """Get trusted host middleware configuration"""
    trusted_hosts = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1").split(",")
    
    return TrustedHostMiddleware(
        allowed_hosts=trusted_hosts
    )

class SecurityError(Exception):
    """Custom security exception"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def validate_phone_number(phone: str) -> bool:
    """Validate phone number format"""
    # Basic phone number validation
    phone_pattern = r'^\+?[1-9]\d{1,14}$'
    return bool(re.match(phone_pattern, phone))

def validate_email(email: str) -> bool:
    """Validate email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

def validate_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Validate webhook signature"""
    import hmac
    import hashlib
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal"""
    # Remove directory traversal attempts
    filename = re.sub(r'[./\\]', '', filename)
    # Remove non-alphanumeric characters except dots and hyphens
    filename = re.sub(r'[^a-zA-Z0-9.-]', '', filename)
    return filename

# Security configuration
SECURITY_CONFIG = {
    "max_request_size": int(os.getenv("MAX_REQUEST_SIZE", "10485760")),  # 10MB
    "session_timeout": int(os.getenv("SESSION_TIMEOUT", "3600")),        # 1 hour
    "max_file_size": int(os.getenv("MAX_FILE_SIZE", "5242880")),         # 5MB
    "allowed_file_types": os.getenv("ALLOWED_FILE_TYPES", "wav,mp3,mp4").split(","),
    "enable_csrf": os.getenv("ENABLE_CSRF", "true").lower() == "true",
    "enable_rate_limiting": os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
}












