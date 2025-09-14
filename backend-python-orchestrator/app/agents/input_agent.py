import base64
import io
import structlog
import asyncio
import requests
from typing import Dict, Any
from app.config import Config
from app.optimization_implementations import (
    circuit_breaker,
    retry_on_exception,
    track_metrics
)

class InputAgent:
    """
    Input Agent: Transcribes audio to text using Sarvam AI
    """
    
    def __init__(self):
        self.api_key = Config.sarvam()["api_key"]
        self.base_url = "https://api.sarvam.ai"
        self.logger = structlog.get_logger(__name__)
        
    @track_metrics("transcribe_audio")
    @retry_on_exception(max_attempts=3, delay=2)
    @circuit_breaker
    async def transcribe_audio(self, audio_data: str) -> str:
        """
        Transcribe audio data to text using Sarvam AI Speech-to-Text
        
        Args:
            audio_data: Base64 encoded audio data or audio file path
            
        Returns:
            Transcribed text
        """
        try:
            self.logger.info("Starting audio transcription with Sarvam AI")
            
            # Handle base64 encoded audio data
            if audio_data.startswith('data:audio'):
                # Extract base64 data from data URL
                audio_data = audio_data.split(',')[1]
            
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            def sync_call():
                # Prepare the request for Sarvam AI Speech-to-Text API
                url = f"{self.base_url}/v1/speech/transcribe"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "audio/wav"
                }
                
                response = requests.post(
                    url,
                    headers=headers,
                    data=audio_bytes,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("text", "")
                else:
                    raise Exception(f"Sarvam AI API error: {response.status_code} - {response.text}")

            transcript = await asyncio.to_thread(sync_call)
            
            self.logger.info("Transcription complete", preview=transcript[:100])
            return transcript
            
        except Exception as e:
            self.logger.error("Error in transcribe_audio", error=str(e))
            raise Exception(f"Audio transcription failed: {str(e)}")
    
    @track_metrics("transcribe_file")
    @retry_on_exception(max_attempts=3, delay=2)
    @circuit_breaker
    async def transcribe_file(self, file_path: str) -> str:
        """
        Transcribe audio file to text using Sarvam AI
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            self.logger.info("Transcribing file with Sarvam AI", file_path=file_path)
            
            def sync_call():
                with open(file_path, "rb") as audio_file:
                    # Prepare the request for Sarvam AI Speech-to-Text API
                    url = f"{self.base_url}/v1/speech/transcribe"
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "audio/wav"
                    }
                    
                    response = requests.post(
                        url,
                        headers=headers,
                        data=audio_file.read(),
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return result.get("text", "")
                    else:
                        raise Exception(f"Sarvam AI API error: {response.status_code} - {response.text}")

            transcript = await asyncio.to_thread(sync_call)
            
            self.logger.info("File transcription complete", preview=transcript[:100])
            return transcript
            
        except Exception as e:
            self.logger.error("Error in transcribe_file", error=str(e))
            raise Exception(f"File transcription failed: {str(e)}")
    
    async def get_audio_metadata(self, audio_data: str) -> Dict[str, Any]:
        """
        Extract metadata from audio data
        
        Args:
            audio_data: Base64 encoded audio data
            
        Returns:
            Audio metadata (duration, format, etc.)
        """
        try:
            self.logger.info("Extracting audio metadata")

            # Placeholder metadata - future: pydub or ffmpeg-python
            return {
                "format": "wav",
                "duration": "unknown",
                "channels": 1,
                "sample_rate": 16000
            }
        except Exception as e:
            self.logger.error("Error in get_audio_metadata", error=str(e))
            return {} 