from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
import os
from enum import Enum

class ChannelType(Enum):
    """Supported communication channels"""
    VOICE = "voice"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"

class VoiceAgentBase(ABC):
    """
    Base VoiceAgent interface for loosely coupled voice communication
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.supported_channels = []
        self._initialize()
    
    @abstractmethod
    def _initialize(self):
        """Initialize the voice agent with configuration"""
        pass
    
    @abstractmethod
    async def send_message(
        self, 
        to: str, 
        message: str, 
        channel: ChannelType = ChannelType.SMS,
        context: Dict = None
    ) -> Dict[str, Any]:
        """
        Send a message via specified channel
        
        Args:
            to: Recipient identifier (phone number, email, etc.)
            message: Message content
            channel: Communication channel
            context: Additional context
            
        Returns:
            Response with message_id, status, etc.
        """
        pass
    
    @abstractmethod
    async def make_call(
        self, 
        to: str, 
        message: str,
        context: Dict = None
    ) -> Dict[str, Any]:
        """
        Make a voice call
        
        Args:
            to: Recipient phone number
            message: Message to speak or play
            context: Additional context
            
        Returns:
            Response with call_id, status, etc.
        """
        pass
    
    @abstractmethod
    async def text_to_speech(
        self, 
        text: str,
        voice_config: Dict = None
    ) -> Dict[str, Any]:
        """
        Convert text to speech
        
        Args:
            text: Text to convert
            voice_config: Voice configuration (voice, speed, etc.)
            
        Returns:
            Response with audio_url, duration, etc.
        """
        pass
    
    @abstractmethod
    async def speech_to_text(
        self, 
        audio_data: bytes,
        audio_config: Dict = None
    ) -> Dict[str, Any]:
        """
        Convert speech to text
        
        Args:
            audio_data: Audio data bytes
            audio_config: Audio configuration (format, language, etc.)
            
        Returns:
            Response with text, confidence, etc.
        """
        pass
    
    def get_supported_channels(self) -> List[ChannelType]:
        """Get list of supported communication channels"""
        return self.supported_channels
    
    def is_channel_supported(self, channel: ChannelType) -> bool:
        """Check if a channel is supported"""
        return channel in self.supported_channels
    
    async def handle_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """
        Handle incoming webhook data
        
        Args:
            webhook_data: Webhook payload
            
        Returns:
            Response to webhook
        """
        self.logger.info(f"Received webhook: {webhook_data}")
        return {"status": "received", "processed": True}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get voice agent status and health"""
        return {
            "status": "healthy",
            "provider": self.__class__.__name__,
            "supported_channels": [channel.value for channel in self.supported_channels],
            "config": self.config
        }

class VoiceAgentFactory:
    """
    Factory for creating voice agent instances
    """
    
    _providers = {}
    
    @classmethod
    def register_provider(cls, name: str, provider_class):
        """Register a voice agent provider"""
        cls._providers[name] = provider_class
        logging.getLogger(__name__).info(f"Registered voice agent provider: {name}")
    
    @classmethod
    def create(cls, provider_name: str, config: Dict = None) -> VoiceAgentBase:
        """
        Create a voice agent instance
        
        Args:
            provider_name: Name of the provider (twilio, aws, etc.)
            config: Provider-specific configuration
            
        Returns:
            VoiceAgent instance
        """
        if provider_name not in cls._providers:
            raise ValueError(f"Unknown voice agent provider: {provider_name}")
        
        provider_class = cls._providers[provider_name]
        return provider_class(config)
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available providers"""
        return list(cls._providers.keys())

# Example Twilio implementation
class TwilioVoiceAgent(VoiceAgentBase):
    """
    Twilio implementation of VoiceAgent
    """
    
    def _initialize(self):
        """Initialize Twilio client"""
        try:
            from twilio.rest import Client
            from twilio.twiml import VoiceResponse
            
            account_sid = self.config.get("account_sid") or os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = self.config.get("auth_token") or os.getenv("TWILIO_AUTH_TOKEN")
            
            if not account_sid or not auth_token:
                raise ValueError("Twilio credentials not found in config or environment")
            
            self.client = Client(account_sid, auth_token)
            self.supported_channels = [ChannelType.VOICE, ChannelType.SMS, ChannelType.WHATSAPP]
            
            self.logger.info("Twilio VoiceAgent initialized successfully")
            
        except ImportError:
            self.logger.error("Twilio library not installed. Install with: pip install twilio")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize Twilio: {str(e)}")
            raise
    
    async def send_message(
        self, 
        to: str, 
        message: str, 
        channel: ChannelType = ChannelType.SMS,
        context: Dict = None
    ) -> Dict[str, Any]:
        """Send message via Twilio"""
        try:
            from_number = self.config.get("from_number") or os.getenv("TWILIO_FROM_NUMBER")
            
            if channel == ChannelType.SMS:
                message_obj = self.client.messages.create(
                    body=message,
                    from_=from_number,
                    to=to
                )
                return {
                    "message_id": message_obj.sid,
                    "status": message_obj.status,
                    "provider": "twilio",
                    "channel": "sms"
                }
            
            elif channel == ChannelType.WHATSAPP:
                # Twilio WhatsApp requires special formatting
                from_whatsapp = f"whatsapp:{from_number}"
                to_whatsapp = f"whatsapp:{to}"
                
                message_obj = self.client.messages.create(
                    body=message,
                    from_=from_whatsapp,
                    to=to_whatsapp
                )
                return {
                    "message_id": message_obj.sid,
                    "status": message_obj.status,
                    "provider": "twilio",
                    "channel": "whatsapp"
                }
            
            else:
                raise ValueError(f"Channel {channel} not supported by Twilio")
                
        except Exception as e:
            self.logger.error(f"Error sending message via Twilio: {str(e)}")
            return {
                "error": str(e),
                "status": "failed",
                "provider": "twilio"
            }
    
    async def make_call(
        self, 
        to: str, 
        message: str,
        context: Dict = None
    ) -> Dict[str, Any]:
        """Make voice call via Twilio"""
        try:
            from_number = self.config.get("from_number") or os.getenv("TWILIO_FROM_NUMBER")
            webhook_url = self.config.get("webhook_url") or os.getenv("TWILIO_WEBHOOK_URL")
            
            call = self.client.calls.create(
                twiml=f'<Response><Say>{message}</Say></Response>',
                from_=from_number,
                to=to,
                webhook_url=webhook_url
            )
            
            return {
                "call_id": call.sid,
                "status": call.status,
                "provider": "twilio",
                "channel": "voice"
            }
            
        except Exception as e:
            self.logger.error(f"Error making call via Twilio: {str(e)}")
            return {
                "error": str(e),
                "status": "failed",
                "provider": "twilio"
            }
    
    async def text_to_speech(
        self, 
        text: str,
        voice_config: Dict = None
    ) -> Dict[str, Any]:
        """Convert text to speech using Twilio"""
        try:
            from twilio.twiml import VoiceResponse
            
            # Create TwiML response
            response = VoiceResponse()
            voice_params = voice_config or {}
            
            response.say(
                text,
                voice=voice_params.get("voice", "alice"),
                language=voice_params.get("language", "en-US")
            )
            
            # In a real implementation, you might save this to a file or return TwiML
            return {
                "twiml": str(response),
                "duration": len(text) * 0.06,  # Rough estimate
                "provider": "twilio",
                "format": "twiml"
            }
            
        except Exception as e:
            self.logger.error(f"Error in text-to-speech via Twilio: {str(e)}")
            return {
                "error": str(e),
                "status": "failed",
                "provider": "twilio"
            }
    
    async def speech_to_text(
        self, 
        audio_data: bytes,
        audio_config: Dict = None
    ) -> Dict[str, Any]:
        """Convert speech to text using Twilio"""
        # Twilio doesn't provide direct STT, would need to use another service
        # This is a placeholder implementation
        return {
            "error": "Speech-to-text not directly supported by Twilio",
            "status": "not_supported",
            "provider": "twilio"
        }

# Example AWS Polly implementation
class AWSPollyVoiceAgent(VoiceAgentBase):
    """
    AWS Polly implementation of VoiceAgent
    """
    
    def _initialize(self):
        """Initialize AWS Polly client"""
        try:
            import boto3
            
            self.polly_client = boto3.client('polly')
            self.supported_channels = [ChannelType.VOICE]
            
            self.logger.info("AWS Polly VoiceAgent initialized successfully")
            
        except ImportError:
            self.logger.error("AWS boto3 library not installed. Install with: pip install boto3")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize AWS Polly: {str(e)}")
            raise
    
    async def send_message(self, to: str, message: str, channel: ChannelType = ChannelType.SMS, context: Dict = None) -> Dict[str, Any]:
        """AWS Polly doesn't support direct messaging"""
        return {
            "error": "Direct messaging not supported by AWS Polly",
            "status": "not_supported",
            "provider": "aws_polly"
        }
    
    async def make_call(self, to: str, message: str, context: Dict = None) -> Dict[str, Any]:
        """AWS Polly doesn't support direct calling"""
        return {
            "error": "Direct calling not supported by AWS Polly",
            "status": "not_supported",
            "provider": "aws_polly"
        }
    
    async def text_to_speech(self, text: str, voice_config: Dict = None) -> Dict[str, Any]:
        """Convert text to speech using AWS Polly"""
        try:
            voice_params = voice_config or {}
            
            response = self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_params.get("voice", "Joanna"),
                Engine=voice_params.get("engine", "standard")
            )
            
            # In a real implementation, you'd save the audio to a file or S3
            audio_data = response['AudioStream'].read()
            
            return {
                "audio_data": audio_data,
                "duration": len(text) * 0.06,  # Rough estimate
                "provider": "aws_polly",
                "format": "mp3"
            }
            
        except Exception as e:
            self.logger.error(f"Error in text-to-speech via AWS Polly: {str(e)}")
            return {
                "error": str(e),
                "status": "failed",
                "provider": "aws_polly"
            }
    
    async def speech_to_text(self, audio_data: bytes, audio_config: Dict = None) -> Dict[str, Any]:
        """AWS Polly doesn't support STT, would need AWS Transcribe"""
        return {
            "error": "Speech-to-text not supported by AWS Polly (use AWS Transcribe)",
            "status": "not_supported",
            "provider": "aws_polly"
        }

# Register providers
VoiceAgentFactory.register_provider("twilio", TwilioVoiceAgent)
VoiceAgentFactory.register_provider("aws_polly", AWSPollyVoiceAgent)

# Convenience function
def create_voice_agent(provider: str = None, config: Dict = None) -> VoiceAgentBase:
    """
    Create a voice agent instance
    
    Args:
        provider: Provider name (defaults to environment variable)
        config: Provider configuration
        
    Returns:
        VoiceAgent instance
    """
    if not provider:
        provider = os.getenv("VOICE_PROVIDER", "twilio")
    
    return VoiceAgentFactory.create(provider, config) 