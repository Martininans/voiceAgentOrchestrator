import openai
import base64
import io
import os
from typing import Dict, Any
import logging

class InputAgent:
    """
    Input Agent: Transcribes audio to text using OpenAI Whisper
    """
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.logger = logging.getLogger(__name__)
        
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
            
            # Transcribe using OpenAI Whisper
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            
            self.logger.info(f"Transcription completed: {transcript[:100]}...")
            return transcript
            
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {str(e)}")
            raise Exception(f"Audio transcription failed: {str(e)}")
    
    async def transcribe_file(self, file_path: str) -> str:
        """
        Transcribe audio file to text
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            self.logger.info(f"Transcribing audio file: {file_path}")
            
            with open(file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            self.logger.info(f"File transcription completed: {transcript[:100]}...")
            return transcript
            
        except Exception as e:
            self.logger.error(f"Error transcribing file: {str(e)}")
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
            # This is a placeholder for audio metadata extraction
            # In a real implementation, you might use libraries like pydub
            return {
                "format": "wav",
                "duration": "estimated",
                "channels": 1,
                "sample_rate": 16000
            }
        except Exception as e:
            self.logger.error(f"Error extracting audio metadata: {str(e)}")
            return {} 