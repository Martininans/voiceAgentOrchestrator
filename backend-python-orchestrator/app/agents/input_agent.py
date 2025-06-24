import openai
import base64
import io
import structlog
import asyncio
from typing import Dict, Any
from app.config import Config
from app.optimization_implementations import (
    circuit_breaker,
    retry_on_exception,
    track_metrics
)

class InputAgent:
    """
    Input Agent: Transcribes audio to text using OpenAI Whisper
    """
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.openai()["api_key"])
        self.logger = structlog.get_logger(__name__)
        
    @track_metrics("transcribe_audio")
    @retry_on_exception(max_attempts=3, delay=2)
    @circuit_breaker
    async def transcribe_audio(self, audio_data: str) -> str:
        """
        Transcribe audio data to text using OpenAI Whisper
        
        Args:
            audio_data: Base64 encoded audio data or audio file path
            
        Returns:
            Transcribed text
        """
        try:
            self.logger.info("Starting audio transcription")
            
            # Handle base64 encoded audio data
            if audio_data.startswith('data:audio'):
                # Extract base64 data from data URL
                audio_data = audio_data.split(',')[1]
            
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Create a file-like object for OpenAI API
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"  # Give it a filename
            
            def sync_call():
                return self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )

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
        Transcribe audio file to text
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            self.logger.info("Transcribing file", file_path=file_path)
            
            def sync_call():
                with open(file_path, "rb") as audio_file:
                    return self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )

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