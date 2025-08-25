const BaseDriver = require('./baseDriver');
const config = require('../../config');

class VonageDriver extends BaseDriver {
    constructor() {
        super(config);
        this.providerName = 'vonage';
        this.apiKey = config.voice.vonage?.apiKey;
        this.apiSecret = config.voice.vonage?.apiSecret;
        this.applicationId = config.voice.vonage?.applicationId;
        this.privateKey = config.voice.vonage?.privateKey;
        this.phoneNumber = config.voice.vonage?.phoneNumber;
        this.webhookUrl = config.voice.vonage?.webhookUrl;
    }

    async initialize() {
        console.log('📞 Initializing Vonage driver...');
        
        if (!this.apiKey || !this.apiSecret) {
            console.warn('⚠️  Vonage credentials not fully configured');
            return false;
        }

        console.log('✅ Vonage driver initialized successfully');
        return true;
    }

    async validateConfig() {
        const required = ['apiKey', 'apiSecret'];
        const missing = required.filter(key => !this[key]);
        
        if (missing.length > 0) {
            console.warn(`⚠️  Missing Vonage configuration: ${missing.join(', ')}`);
            return false;
        }
        
        return true;
    }

    async handleInboundCall(payload) {
        console.log('📞 Vonage: Processing inbound call');
        console.log('Payload:', payload);

        try {
            // Extract call details from Vonage webhook
            const callId = payload.uuid;
            const from = payload.from;
            const to = payload.to;
            const status = payload.status;

            // Generate NCCO (Nexmo Call Control Object) response
            const nccoResponse = this.generateInboundNCCO();

            return this.generateSuccessResponse({
                callId: callId,
                from: from,
                to: to,
                status: status,
                ncco: nccoResponse
            }, 'Inbound call processed successfully');
        } catch (error) {
            console.error('❌ Error processing inbound call:', error);
            return this.generateErrorResponse(`Failed to process inbound call: ${error.message}`);
        }
    }

    async handleOutboundCall(payload) {
        console.log('📞 Vonage: Initiating outbound call');
        console.log('Payload:', payload);

        try {
            const { to, message, callbackUrl } = payload;

            if (!to) {
                return this.generateErrorResponse('Recipient phone number is required', 400);
            }

            // In a real implementation, you would use Vonage's SDK
            const callData = {
                to: [{ type: 'phone', number: to }],
                from: { type: 'phone', number: this.phoneNumber },
                ncco: this.generateOutboundNCCO(message),
                eventUrl: [callbackUrl || `${this.webhookUrl}/status`]
            };

            console.log('📞 Simulating outbound call with data:', callData);

            return this.generateSuccessResponse({
                callId: `simulated_${Date.now()}`,
                to: to,
                from: this.phoneNumber,
                status: 'initiated'
            }, 'Outbound call initiated successfully');
        } catch (error) {
            console.error('❌ Error initiating outbound call:', error);
            return this.generateErrorResponse(`Failed to initiate outbound call: ${error.message}`);
        }
    }

    async textToSpeech(payload) {
        console.log('🔊 Vonage: Processing TTS request');
        console.log('Payload:', payload);

        try {
            const { text, voice = 'en-US', language = 'en-US' } = payload;

            if (!text) {
                return this.generateErrorResponse('Text content is required for TTS', 400);
            }

            // Generate NCCO with TTS
            const nccoResponse = this.generateTTSNCCO(text, voice, language);

            return this.generateSuccessResponse({
                text: text,
                voice: voice,
                language: language,
                ncco: nccoResponse
            }, 'TTS processed successfully');
        } catch (error) {
            console.error('❌ Error processing TTS:', error);
            return this.generateErrorResponse(`Failed to process TTS: ${error.message}`);
        }
    }

    async sendSMS(payload) {
        console.log('📱 Vonage: Sending SMS');
        console.log('Payload:', payload);

        try {
            const { to, message, from = this.phoneNumber } = payload;

            if (!to || !message) {
                return this.generateErrorResponse('Recipient and message are required for SMS', 400);
            }

            // In a real implementation, you would use Vonage's SMS API
            console.log('📱 Simulating SMS send:', { to, from, message });

            return this.generateSuccessResponse({
                messageId: `simulated_sms_${Date.now()}`,
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
        console.log('🎤 Vonage: Processing speech input');
        console.log('Payload:', payload);

        try {
            const speechResult = payload.speech?.results?.[0]?.text;
            const confidence = payload.speech?.results?.[0]?.confidence;
            const callId = payload.uuid;

            if (!speechResult) {
                return this.generateTTSNCCO("I didn't catch that. Could you please repeat?");
            }

            // Forward to Python orchestrator for processing
            const orchestratorResponse = await this.forwardToOrchestrator({
                type: 'speech',
                text: speechResult,
                confidence: confidence,
                callId: callId
            });

            return this.generateTTSNCCO(orchestratorResponse.response || "Thank you for your input.");
        } catch (error) {
            console.error('❌ Error processing speech:', error);
            return this.generateTTSNCCO("I'm sorry, I encountered an error. Please try again.");
        }
    }

    async getStatus() {
        return {
            provider: this.providerName,
            status: 'operational',
            capabilities: ['inbound_calls', 'outbound_calls', 'tts', 'sms', 'speech_processing'],
            config: {
                phoneNumber: this.phoneNumber,
                webhookUrl: this.webhookUrl
            }
        };
    }

    generateInboundNCCO() {
        return [
            {
                action: 'talk',
                text: "Hello! I'm your AI voice assistant. How can I help you today?"
            },
            {
                action: 'input',
                type: ['speech'],
                speech: {
                    endOnSilence: 3,
                    language: 'en-US'
                },
                eventUrl: [`${this.webhookUrl}/process-speech`]
            }
        ];
    }

    generateOutboundNCCO(message) {
        return [
            {
                action: 'talk',
                text: message || 'Hello! This is an automated call from your AI assistant.'
            },
            {
                action: 'input',
                type: ['speech'],
                speech: {
                    endOnSilence: 3,
                    language: 'en-US'
                },
                eventUrl: [`${this.webhookUrl}/process-speech`]
            }
        ];
    }

    generateTTSNCCO(text, voice = 'en-US', language = 'en-US') {
        return [
            {
                action: 'talk',
                text: text,
                voiceName: voice,
                language: language
            }
        ];
    }
}

module.exports = new VonageDriver(); 