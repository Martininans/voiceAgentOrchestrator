const BaseDriver = require('./baseDriver');
const config = require('../../config');
const axios = require('axios');

class TwilioDriver extends BaseDriver {
    constructor() {
        super(config);
        this.providerName = 'twilio';
        this.accountSid = config.voice.twilio.accountSid;
        this.authToken = config.voice.twilio.authToken;
        this.phoneNumber = config.voice.twilio.phoneNumber;
        this.webhookUrl = config.voice.twilio.webhookUrl;
    }

    async initialize() {
        console.log('📞 Initializing Twilio driver...');
        
        if (!this.accountSid || !this.authToken || !this.phoneNumber) {
            console.warn('⚠️  Twilio credentials not fully configured');
            return false;
        }

        console.log('✅ Twilio driver initialized successfully');
        return true;
    }

    async validateConfig() {
        const required = ['accountSid', 'authToken', 'phoneNumber'];
        const missing = required.filter(key => !this[key]);
        
        if (missing.length > 0) {
            console.warn(`⚠️  Missing Twilio configuration: ${missing.join(', ')}`);
            return false;
        }
        
        return true;
    }

    async handleInboundCall(payload) {
        console.log('📞 Twilio: Processing inbound call');
        console.log('Payload:', payload);

        try {
            // Extract call details
            const callSid = payload.CallSid;
            const from = payload.From;
            const to = payload.To;
            const callStatus = payload.CallStatus;

            // Generate TwiML response for voice interaction
            const twimlResponse = this.generateInboundTwiML();

            return this.generateSuccessResponse({
                callSid: callSid,
                from: from,
                to: to,
                status: callStatus,
                twiml: twimlResponse
            }, 'Inbound call processed successfully');
        } catch (error) {
            console.error('❌ Error processing inbound call:', error);
            return this.generateErrorResponse(`Failed to process inbound call: ${error.message}`);
        }
    }

    async handleOutboundCall(payload) {
        console.log('📞 Twilio: Initiating outbound call');
        console.log('Payload:', payload);

        try {
            const { to, message, callbackUrl } = payload;

            if (!to) {
                return this.generateErrorResponse('Recipient phone number is required', 400);
            }

            // In a real implementation, you would use Twilio's SDK
            // For now, we'll simulate the call initiation
            const callData = {
                to: to,
                from: this.phoneNumber,
                twiml: this.generateOutboundTwiML(message),
                statusCallback: callbackUrl || `${this.webhookUrl}/status`,
                statusCallbackEvent: ['initiated', 'ringing', 'answered', 'completed']
            };

            console.log('📞 Simulating outbound call with data:', callData);

            return this.generateSuccessResponse({
                callSid: `simulated_${Date.now()}`,
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
        console.log('🔊 Twilio: Processing TTS request');
        console.log('Payload:', payload);

        try {
            const { text, voice = 'alice', language = 'en-US' } = payload;

            if (!text) {
                return this.generateErrorResponse('Text content is required for TTS', 400);
            }

            // Generate TwiML with TTS
            const twimlResponse = this.generateTTSResponse(text, voice, language);

            return this.generateSuccessResponse({
                text: text,
                voice: voice,
                language: language,
                twiml: twimlResponse
            }, 'TTS processed successfully');
        } catch (error) {
            console.error('❌ Error processing TTS:', error);
            return this.generateErrorResponse(`Failed to process TTS: ${error.message}`);
        }
    }

    async sendSMS(payload) {
        console.log('📱 Twilio: Sending SMS');
        console.log('Payload:', payload);

        try {
            const { to, message, from = this.phoneNumber } = payload;

            if (!to || !message) {
                return this.generateErrorResponse('Recipient and message are required for SMS', 400);
            }

            // In a real implementation, you would use Twilio's SDK
            console.log('📱 Simulating SMS send:', { to, from, message });

            return this.generateSuccessResponse({
                messageSid: `simulated_sms_${Date.now()}`,
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
        console.log('🎤 Twilio: Processing speech input');
        console.log('Payload:', payload);

        try {
            const speechResult = payload.SpeechResult;
            const confidence = payload.Confidence;
            const callSid = payload.CallSid;

            if (!speechResult) {
                return this.generateTTSResponse("I didn't catch that. Could you please repeat?");
            }

            // Forward to Python orchestrator for processing
            const orchestratorResponse = await this.forwardToOrchestrator({
                type: 'speech',
                text: speechResult,
                confidence: confidence,
                callSid: callSid
            });

            return this.generateTTSResponse(orchestratorResponse.response || "Thank you for your input.");
        } catch (error) {
            console.error('❌ Error processing speech:', error);
            return this.generateTTSResponse("I'm sorry, I encountered an error. Please try again.");
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

    generateInboundTwiML() {
        return `<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" timeout="3" action="/voice/process-speech" method="POST">
        <Say voice="alice">Hello! I'm your AI voice assistant. How can I help you today?</Say>
    </Gather>
    <Say voice="alice">I didn't hear anything. Please try again.</Say>
</Response>`;
    }

    generateOutboundTwiML(message) {
        return `<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">${message || 'Hello! This is an automated call from your AI assistant.'}</Say>
    <Gather input="speech" timeout="3" action="/voice/process-speech" method="POST">
        <Say voice="alice">Please respond to continue our conversation.</Say>
    </Gather>
</Response>`;
    }

    generateTTSResponse(text, voice = 'alice', language = 'en-US') {
        return `<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="${voice}" language="${language}">${text}</Say>
</Response>`;
    }

    async forwardToOrchestrator(data) {
        try {
            const response = await axios.post(
                `${config.orchestrator.url}/process-intent`,
                {
                    text: data.text,
                    context: {
                        callSid: data.callSid,
                        confidence: data.confidence,
                        source: 'twilio'
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
}

module.exports = new TwilioDriver();
