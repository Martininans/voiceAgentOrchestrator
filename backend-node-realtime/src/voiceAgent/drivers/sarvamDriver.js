const BaseDriver = require('./baseDriver');
const config = require('../../config');
const axios = require('axios');

class SarvamDriver extends BaseDriver {
    constructor() {
        super(config);
        this.providerName = 'sarvam';
        this.apiKey = config.voice.sarvam.apiKey;
        this.apiSecret = config.voice.sarvam.apiSecret;
        this.baseUrl = config.voice.sarvam.baseUrl;
        this.model = config.voice.sarvam.model;
        this.language = config.voice.sarvam.language;
        this.voice = config.voice.sarvam.voice;
        this.webhookUrl = config.voice.sarvam.webhookUrl;
    }

    async initialize() {
        console.log('🎤 Initializing Sarvam AI driver...');
        
        if (!this.apiKey || !this.apiSecret) {
            console.warn('⚠️  Sarvam AI credentials not fully configured');
            return false;
        }

        // Test API connection
        try {
            await this.testConnection();
            console.log('✅ Sarvam AI driver initialized successfully');
            return true;
        } catch (error) {
            console.error('❌ Failed to initialize Sarvam AI driver:', error.message);
            return false;
        }
    }

    async validateConfig() {
        const required = ['apiKey', 'apiSecret', 'baseUrl'];
        const missing = required.filter(key => !this[key]);
        
        if (missing.length > 0) {
            console.warn(`⚠️  Missing Sarvam AI configuration: ${missing.join(', ')}`);
            return false;
        }
        
        return true;
    }

    async testConnection() {
        try {
            const response = await axios.get(`${this.baseUrl}/v1/models`, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                },
                timeout: 10000
            });
            return response.status === 200;
        } catch (error) {
            throw new Error(`Sarvam AI connection test failed: ${error.message}`);
        }
    }

    async handleInboundCall(payload) {
        console.log('📞 Sarvam AI: Processing inbound call');
        console.log('Payload:', payload);

        try {
            // Extract call details
            const callId = payload.callId || payload.call_id || `sarvam_${Date.now()}`;
            const from = payload.from || payload.caller_id;
            const to = payload.to || payload.called_number;
            const callStatus = payload.status || 'in_progress';

            // Generate response for voice interaction
            const response = await this.generateInboundResponse();

            return this.generateSuccessResponse({
                callId: callId,
                from: from,
                to: to,
                status: callStatus,
                response: response
            }, 'Inbound call processed successfully');
        } catch (error) {
            console.error('❌ Error processing inbound call:', error);
            return this.generateErrorResponse(`Failed to process inbound call: ${error.message}`);
        }
    }

    async handleOutboundCall(payload) {
        console.log('📞 Sarvam AI: Initiating outbound call');
        console.log('Payload:', payload);

        try {
            const { to, message, callbackUrl } = payload;

            if (!to) {
                return this.generateErrorResponse('Recipient phone number is required', 400);
            }

            // In a real implementation, you would use Sarvam AI's calling API
            // For now, we'll simulate the call initiation
            const callData = {
                to: to,
                message: message || 'Hello! This is an automated call from your AI assistant.',
                callbackUrl: callbackUrl || `${this.webhookUrl}/status`,
                language: this.language,
                voice: this.voice
            };

            console.log('📞 Simulating outbound call with data:', callData);

            return this.generateSuccessResponse({
                callId: `sarvam_${Date.now()}`,
                to: to,
                status: 'initiated',
                language: this.language,
                voice: this.voice
            }, 'Outbound call initiated successfully');
        } catch (error) {
            console.error('❌ Error initiating outbound call:', error);
            return this.generateErrorResponse(`Failed to initiate outbound call: ${error.message}`);
        }
    }

    async textToSpeech(payload) {
        console.log('🔊 Sarvam AI: Processing TTS request');
        console.log('Payload:', payload);

        try {
            const { text, voice = this.voice, language = this.language, model = this.model } = payload;

            if (!text) {
                return this.generateErrorResponse('Text content is required for TTS', 400);
            }

            // Call Sarvam AI TTS API
            const ttsResponse = await this.callSarvamTTS(text, voice, language, model);

            return this.generateSuccessResponse({
                text: text,
                voice: voice,
                language: language,
                model: model,
                audioUrl: ttsResponse.audio_url,
                audioData: ttsResponse.audio_data
            }, 'TTS processed successfully');
        } catch (error) {
            console.error('❌ Error processing TTS:', error);
            return this.generateErrorResponse(`Failed to process TTS: ${error.message}`);
        }
    }

    async speechToText(payload) {
        console.log('🎤 Sarvam AI: Processing STT request');
        console.log('Payload:', payload);

        try {
            const { audioData, audioFormat = 'wav', language = this.language } = payload;

            if (!audioData) {
                return this.generateErrorResponse('Audio data is required for STT', 400);
            }

            // Call Sarvam AI STT API
            const sttResponse = await this.callSarvamSTT(audioData, audioFormat, language);

            return this.generateSuccessResponse({
                text: sttResponse.text,
                confidence: sttResponse.confidence,
                language: sttResponse.language,
                duration: sttResponse.duration
            }, 'STT processed successfully');
        } catch (error) {
            console.error('❌ Error processing STT:', error);
            return this.generateErrorResponse(`Failed to process STT: ${error.message}`);
        }
    }

    async sendSMS(payload) {
        console.log('📱 Sarvam AI: Sending SMS');
        console.log('Payload:', payload);

        try {
            const { to, message, from } = payload;

            if (!to || !message) {
                return this.generateErrorResponse('Recipient and message are required for SMS', 400);
            }

            // In a real implementation, you would use Sarvam AI's SMS API
            console.log('📱 Simulating SMS send:', { to, from, message });

            return this.generateSuccessResponse({
                messageId: `sarvam_sms_${Date.now()}`,
                to: to,
                from: from,
                status: 'sent'
            }, 'SMS sent successfully');
        } catch (error) {
            console.error('❌ Error sending SMS:', error);
            return this.generateErrorResponse(`Failed to send SMS: ${error.message}`);
        }
    }

    async processSpeech(payload) {
        console.log('🎤 Sarvam AI: Processing speech input');
        console.log('Payload:', payload);

        try {
            const speechResult = payload.speechResult || payload.text;
            const confidence = payload.confidence || 0.9;
            const callId = payload.callId || payload.call_id;

            if (!speechResult) {
                return this.generateTTSResponse("मुझे समझ नहीं आया। क्या आप दोबारा कह सकते हैं?", this.language);
            }

            // Forward to Python orchestrator for processing
            const orchestratorResponse = await this.forwardToOrchestrator({
                type: 'speech',
                text: speechResult,
                confidence: confidence,
                callId: callId,
                language: this.language
            });

            // Generate response in the appropriate language
            const responseText = orchestratorResponse.response || "आपके इनपुट के लिए धन्यवाद।";
            return this.generateTTSResponse(responseText, this.language);
        } catch (error) {
            console.error('❌ Error processing speech:', error);
            return this.generateTTSResponse("माफ़ करें, मुझे एक त्रुटि का सामना करना पड़ा। कृपया दोबारा कोशिश करें।", this.language);
        }
    }

    async callSarvamTTS(text, voice, language, model) {
        try {
            const response = await axios.post(`${this.baseUrl}/v1/tts`, {
                text: text,
                voice: voice,
                language: language,
                model: model,
                format: 'wav'
            }, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                },
                timeout: 30000
            });

            return response.data;
        } catch (error) {
            throw new Error(`Sarvam AI TTS API error: ${error.response?.data?.message || error.message}`);
        }
    }

    async callSarvamSTT(audioData, audioFormat, language) {
        try {
            const formData = new FormData();
            formData.append('audio', audioData);
            formData.append('format', audioFormat);
            formData.append('language', language);

            const response = await axios.post(`${this.baseUrl}/v1/stt`, formData, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'multipart/form-data'
                },
                timeout: 30000
            });

            return response.data;
        } catch (error) {
            throw new Error(`Sarvam AI STT API error: ${error.response?.data?.message || error.message}`);
        }
    }

    async generateInboundResponse() {
        const welcomeMessage = this.language === 'hi' 
            ? "नमस्ते! मैं आपकी AI आवाज़ सहायक हूं। आज मैं आपकी कैसे मदद कर सकती हूं?"
            : "Hello! I'm your AI voice assistant. How can I help you today?";
        
        return {
            message: welcomeMessage,
            language: this.language,
            voice: this.voice,
            action: 'listen'
        };
    }

    generateTTSResponse(text, language = this.language) {
        return {
            text: text,
            language: language,
            voice: this.voice,
            model: this.model,
            action: 'speak'
        };
    }

    async forwardToOrchestrator(data) {
        try {
            const response = await axios.post(
                `${config.orchestrator.url}/process-intent`,
                {
                    text: data.text,
                    context: {
                        callId: data.callId,
                        confidence: data.confidence,
                        source: 'sarvam',
                        language: data.language
                    }
                },
                {
                    timeout: config.orchestrator.timeout,
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }
            );

            return response.data;
        } catch (error) {
            console.error('❌ Error forwarding to orchestrator:', error);
            throw new Error('Failed to communicate with orchestrator');
        }
    }

    async getStatus() {
        return {
            provider: this.providerName,
            status: 'operational',
            capabilities: ['inbound_calls', 'outbound_calls', 'tts', 'stt', 'sms', 'speech_processing'],
            config: {
                baseUrl: this.baseUrl,
                model: this.model,
                language: this.language,
                voice: this.voice,
                webhookUrl: this.webhookUrl
            }
        };
    }
}

module.exports = new SarvamDriver();












