"""
Application Configuration Module
Supports .env files and mock fallback for local/dev environments
"""

import os
import logging
from typing import Optional

from dotenv import load_dotenv

load_dotenv()
print("DEBUG: SUPABASE_URL =", os.getenv("SUPABASE_URL"))
print("DEBUG: REDIS_URL =", os.getenv("REDIS_URL"))
print("DEBUG: OPENAI_API_KEY =", os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger(__name__)

class Config:
    """Application configuration"""

    @staticmethod
    def get_env(key: str, default: Optional[str] = None, required: bool = False, cast_type: Optional[type] = None):
        value = os.getenv(key, default)

        if not value and required:
            value = f"mock-{key.lower()}-1234567890abcdef"
            logger.warning(f"⚠️  Missing required env var {key}, using mock value: {value}")

        if cast_type:
            try:
                if cast_type == bool:
                    return value.lower() in ("true", "1", "yes")
                return cast_type(value)
            except Exception as e:
                logger.error(f"Failed to cast {key} to {cast_type}: {e}")
                return default

        return value

    @staticmethod
    def is_mock_mode() -> bool:
        return Config.get_env("MOCK_MODE", "false", cast_type=bool)

    @staticmethod
    def supabase() -> dict:
        return {
            "url": Config.get_env("SUPABASE_URL", "https://mock-project.supabase.co"),
            "anon_key": Config.get_env("SUPABASE_ANON_KEY", "mock-anon-key"),
            "service_role_key": Config.get_env("SUPABASE_SERVICE_ROLE_KEY", "mock-service-role-key"),
            "jwt_secret": Config.get_env("JWT_SECRET", "mock-jwt-secret")
        }

    @staticmethod
    def openai() -> dict:
        return {
            "api_key": Config.get_env("OPENAI_API_KEY", "sk-mock-openai-api-key")
        }

    @staticmethod
    def twilio() -> dict:
        return {
            "account_sid": Config.get_env("TWILIO_ACCOUNT_SID", "mock-twilio-account-sid"),
            "auth_token": Config.get_env("TWILIO_AUTH_TOKEN", "mock-twilio-auth-token"),
            "phone_number": Config.get_env("TWILIO_PHONE_NUMBER", "+1234567890")
        }

    @staticmethod
    def database() -> dict:
        return {
            "url": Config.get_env("DATABASE_URL", "postgresql://mock_user:mock_password@localhost:5432/mock_db")
        }

    @staticmethod
    def redis() -> dict:
        return {
            "url": Config.get_env("REDIS_URL", "redis://localhost:6379")
        }

    @staticmethod
    def chroma() -> dict:
        return {
            "host": Config.get_env("CHROMA_HOST", "localhost"),
            "port": Config.get_env("CHROMA_PORT", "8000", cast_type=int)
        }

    @staticmethod
    def app() -> dict:
        return {
            "sector": Config.get_env("SECTOR", "generic"),
            "port": Config.get_env("PORT", "8000", cast_type=int),
            "host": Config.get_env("HOST", "0.0.0.0"),
            "log_level": Config.get_env("LOG_LEVEL", "info"),
            "cors_origin": Config.get_env("CORS_ORIGIN", "*"),
            "debug": Config.get_env("DEBUG", "true", cast_type=bool)
        }

    @staticmethod
    def print_mock_warning():
        if Config.is_mock_mode():
            logger.warning("🚨 RUNNING IN MOCK MODE - Using placeholder values for all external services")
            logger.warning("📋 This is for development/testing only.")
            logger.warning("🔧 To use real services, copy .env.example → .env and update values")

# Initialize
app_config = Config() 