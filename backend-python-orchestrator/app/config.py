"""
Application Configuration Module
Supports .env files and mock fallback for local/dev environments
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

dotenv_path = Path(__file__).parent.parent / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)

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
    def azure_openai() -> dict:
        return {
            "api_key": Config.get_env("AZURE_OPENAI_API_KEY", "mock-azure-openai-key"),
            "endpoint": Config.get_env("AZURE_OPENAI_ENDPOINT", "https://mock-aoai.openai.azure.com"),
            "api_version": Config.get_env("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            "deployment_name": Config.get_env("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
        }

    @staticmethod
    def llm_provider() -> str:
        return Config.get_env("LLM_PROVIDER", "openai").lower()

    @staticmethod
    def vector_backend() -> str:
        return Config.get_env("VECTOR_BACKEND", "chroma").lower()

    @staticmethod
    def twilio() -> dict:
        return {
            "account_sid": Config.get_env("TWILIO_ACCOUNT_SID", "mock-twilio-account-sid"),
            "auth_token": Config.get_env("TWILIO_AUTH_TOKEN", "mock-twilio-auth-token"),
            "phone_number": Config.get_env("TWILIO_PHONE_NUMBER", "+1234567890")
        }

    @staticmethod
    def vonage() -> dict:
        return {
            "api_key": Config.get_env("VONAGE_API_KEY", "mock-vonage-api-key"),
            "api_secret": Config.get_env("VONAGE_API_SECRET", "mock-vonage-api-secret"),
            "application_id": Config.get_env("VONAGE_APPLICATION_ID", "mock-vonage-app-id"),
            "private_key": Config.get_env("VONAGE_PRIVATE_KEY", "mock-vonage-private-key"),
            "phone_number": Config.get_env("VONAGE_PHONE_NUMBER", "+2341234567890")
        }

    @staticmethod
    def aws_connect() -> dict:
        return {
            "access_key_id": Config.get_env("AWS_ACCESS_KEY_ID", "mock-aws-access-key"),
            "secret_access_key": Config.get_env("AWS_SECRET_ACCESS_KEY", "mock-aws-secret-key"),
            "region": Config.get_env("AWS_REGION", "us-east-1"),
            "instance_id": Config.get_env("AWS_CONNECT_INSTANCE_ID", "mock-aws-instance-id"),
            "phone_number": Config.get_env("AWS_CONNECT_PHONE_NUMBER", "+1234567890")
        }

    @staticmethod
    def generic_http() -> dict:
        return {
            "webhook_url": Config.get_env("GENERIC_HTTP_WEBHOOK_URL", "https://mock-service.com/webhook"),
            "api_key": Config.get_env("GENERIC_HTTP_API_KEY", "mock-generic-api-key"),
            "headers": Config.get_env("GENERIC_HTTP_HEADERS", "{}"),
            "timeout": Config.get_env("GENERIC_HTTP_TIMEOUT", "30000", cast_type=int)
        }

    @staticmethod
    def sarvam() -> dict:
        return {
            "api_key": Config.get_env("SARVAM_API_KEY", "mock-sarvam-api-key"),
            "api_secret": Config.get_env("SARVAM_API_SECRET", "mock-sarvam-api-secret"),
            "base_url": Config.get_env("SARVAM_BASE_URL", "https://api.sarvam.ai"),
            "model": Config.get_env("SARVAM_MODEL", "sarvam-tts-hindi"),
            "language": Config.get_env("SARVAM_LANGUAGE", "hi"),
            "voice": Config.get_env("SARVAM_VOICE", "female"),
            "webhook_url": Config.get_env("SARVAM_WEBHOOK_URL", "http://localhost:8000/voice/webhook")
        }

    @staticmethod
    def voice_provider() -> str:
        """Get the current voice provider from environment"""
        return Config.get_env("VOICE_PROVIDER", "twilio").lower()

    @staticmethod
    def voice_config() -> dict:
        """Get configuration for the current voice provider"""
        provider = Config.voice_provider()
        
        if provider == "twilio":
            return Config.twilio()
        elif provider == "vonage":
            return Config.vonage()
        elif provider == "aws-connect":
            return Config.aws_connect()
        elif provider == "generic-http":
            return Config.generic_http()
        elif provider == "sarvam":
            return Config.sarvam()
        else:
            logger.warning(f"Unknown voice provider: {provider}, falling back to twilio")
            return Config.twilio()

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