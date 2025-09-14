"""
Integration tests for Sarvam AI voice provider
"""
import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend-python-orchestrator'))

from app.voice_agent_base import SarvamVoiceAgent
from app.config import Config

class TestSarvamIntegration:
    """Test class for Sarvam AI integration"""
    
    @pytest.fixture
    def sarvam_config(self):
        """Mock Sarvam configuration"""
        return {
            'api_key': 'test-api-key',
            'api_secret': 'test-api-secret',
            'base_url': 'https://api.sarvam.ai',
            'model': 'sarvam-tts-hindi',
            'language': 'hi',
            'voice': 'female',
            'webhook_url': 'http://localhost:8000/voice/webhook'
        }
    
    @pytest.fixture
    def sarvam_agent(self, sarvam_config):
        """Create Sarvam voice agent instance"""
        return SarvamVoiceAgent(sarvam_config)
    
    @pytest.mark.asyncio
    async def test_text_to_speech_success(self, sarvam_agent):
        """Test successful TTS conversion"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'audio_url': 'https://api.sarvam.ai/audio/test.wav',
            'audio_data': 'base64_encoded_audio_data'
        })
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response):
            result = await sarvam_agent.text_to_speech("नमस्ते, यह एक परीक्षण है")
            
            assert result['success'] is True
            assert result['provider'] == 'sarvam'
            assert result['language'] == 'hi'
            assert result['voice'] == 'female'
            assert 'audio_url' in result
    
    @pytest.mark.asyncio
    async def test_text_to_speech_failure(self, sarvam_agent):
        """Test TTS conversion failure"""
        mock_response = Mock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value='Invalid request')
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response):
            result = await sarvam_agent.text_to_speech("Test text")
            
            assert result['success'] is False
            assert 'error' in result
            assert result['provider'] == 'sarvam'
    
    @pytest.mark.asyncio
    async def test_speech_to_text_success(self, sarvam_agent):
        """Test successful STT conversion"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'text': 'नमस्ते, यह एक परीक्षण है',
            'confidence': 0.95,
            'language': 'hi',
            'duration': 2.5
        })
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response):
            audio_data = b'fake_audio_data'
            result = await sarvam_agent.speech_to_text(audio_data)
            
            assert result['success'] is True
            assert result['provider'] == 'sarvam'
            assert result['text'] == 'नमस्ते, यह एक परीक्षण है'
            assert result['confidence'] == 0.95
            assert result['language'] == 'hi'
    
    @pytest.mark.asyncio
    async def test_speech_to_text_failure(self, sarvam_agent):
        """Test STT conversion failure"""
        mock_response = Mock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value='Internal server error')
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response):
            audio_data = b'fake_audio_data'
            result = await sarvam_agent.speech_to_text(audio_data)
            
            assert result['success'] is False
            assert 'error' in result
            assert result['provider'] == 'sarvam'
    
    @pytest.mark.asyncio
    async def test_make_call(self, sarvam_agent):
        """Test making a call"""
        result = await sarvam_agent.make_call("+1234567890", "Test message")
        
        assert result['success'] is True
        assert result['provider'] == 'sarvam'
        assert result['to'] == "+1234567890"
        assert result['language'] == 'hi'
        assert result['voice'] == 'female'
        assert 'call_id' in result
    
    @pytest.mark.asyncio
    async def test_handle_incoming_call_hindi(self, sarvam_agent):
        """Test handling incoming call in Hindi"""
        call_data = {'call_id': 'test-call-123'}
        result = await sarvam_agent.handle_incoming_call(call_data)
        
        assert result['success'] is True
        assert result['provider'] == 'sarvam'
        assert result['language'] == 'hi'
        assert result['voice'] == 'female'
        assert 'नमस्ते' in result['response']
    
    @pytest.mark.asyncio
    async def test_handle_incoming_call_english(self, sarvam_agent):
        """Test handling incoming call in English"""
        # Change language to English
        sarvam_agent.language = 'en'
        call_data = {'call_id': 'test-call-123'}
        result = await sarvam_agent.handle_incoming_call(call_data)
        
        assert result['success'] is True
        assert result['provider'] == 'sarvam'
        assert result['language'] == 'en'
        assert 'Hello' in result['response']
    
    def test_session_management(self, sarvam_agent):
        """Test session management"""
        # Test context manager
        async def test_context():
            async with sarvam_agent as agent:
                assert agent is sarvam_agent
                assert agent.session is not None
        
        asyncio.run(test_context())
        # Session should be closed after context
        assert sarvam_agent.session is None or sarvam_agent.session.closed
    
    @pytest.mark.asyncio
    async def test_custom_voice_config(self, sarvam_agent):
        """Test TTS with custom voice configuration"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'audio_url': 'https://api.sarvam.ai/audio/test.wav'
        })
        
        voice_config = {
            'voice': 'male',
            'language': 'en',
            'model': 'sarvam-tts-english'
        }
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response):
            result = await sarvam_agent.text_to_speech("Hello world", voice_config)
            
            assert result['success'] is True
            assert result['voice'] == 'male'
            assert result['language'] == 'en'
    
    @pytest.mark.asyncio
    async def test_custom_audio_config(self, sarvam_agent):
        """Test STT with custom audio configuration"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'text': 'Hello world',
            'confidence': 0.9
        })
        
        audio_config = {
            'format': 'mp3',
            'language': 'en'
        }
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response):
            audio_data = b'fake_audio_data'
            result = await sarvam_agent.speech_to_text(audio_data, audio_config)
            
            assert result['success'] is True
            assert result['language'] == 'en'
    
    def test_configuration_validation(self):
        """Test configuration validation"""
        # Test with missing API key
        config_no_key = {
            'api_secret': 'test-secret',
            'base_url': 'https://api.sarvam.ai'
        }
        
        agent = SarvamVoiceAgent(config_no_key)
        assert agent.api_key is None
        
        # Test with complete configuration
        complete_config = {
            'api_key': 'test-key',
            'api_secret': 'test-secret',
            'base_url': 'https://api.sarvam.ai',
            'model': 'sarvam-tts-hindi',
            'language': 'hi',
            'voice': 'female'
        }
        
        agent = SarvamVoiceAgent(complete_config)
        assert agent.api_key == 'test-key'
        assert agent.api_secret == 'test-secret'
        assert agent.base_url == 'https://api.sarvam.ai'
        assert agent.model == 'sarvam-tts-hindi'
        assert agent.language == 'hi'
        assert agent.voice == 'female'

class TestSarvamNodeIntegration:
    """Test class for Sarvam AI Node.js integration"""
    
    def test_sarvam_driver_initialization(self):
        """Test Sarvam driver initialization"""
        # This would test the Node.js driver
        # For now, we'll just verify the file exists
        driver_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'backend-node-realtime', 
            'src', 
            'voiceAgent', 
            'drivers', 
            'sarvamDriver.js'
        )
        assert os.path.exists(driver_path)
    
    def test_sarvam_config_integration(self):
        """Test Sarvam configuration integration"""
        # Test that Sarvam is included in the voice provider options
        config_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'backend-node-realtime', 
            'src', 
            'config.js'
        )
        
        with open(config_path, 'r') as f:
            config_content = f.read()
            assert 'sarvam' in config_content
            assert 'SARVAM_API_KEY' in config_content
            assert 'SARVAM_BASE_URL' in config_content

if __name__ == '__main__':
    pytest.main([__file__])












