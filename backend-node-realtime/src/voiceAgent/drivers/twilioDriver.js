const config = require('../../config');
const axios = require('axios');

class TwilioDriver {
    constructor() {
        this.accountSid = config.voice.twilio.accountSid;
        this.authToken = config.voice.twilio.authToken;
        this.phoneNumber = config.voice.twilio.phoneNumber;
        this.webhookUrl = config.voice.twilio.webhookUrl;
        
        if (!this.accountSid || !this.authToken || !this.phoneNumber) {
            console.warn('⚠️  Twilio credentials not fully configured');
        }
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

            return {
                success: true,
                callSid: callSid,
                from: from,
                to: to,
                status: callStatus,
                twiml: twimlResponse,
                message: 'Inbound call processed successfully'
            };
        } catch (error) {
            console.error('❌ Error processing inbound call:', error);
            throw new Error(`Failed to process inbound call: ${error.message}`);
        }
    }

    async handleOutboundCall(payload) {
        console.log('📞 Twilio: Initiating outbound call');
        console.log('Payload:', payload);

        try {
            const { to, message, callbackUrl } = payload;

            if (!to) {
                throw new Error('Recipient phone number is required');
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

            return {
                success: true,
                callSid: `simulated_${Date.now()}`,
                to: to,
                from: this.phoneNumber,
                status: 'initiated',
                message: 'Outbound call initiated successfully'
            };
        } catch (error) {
            console.error('❌ Error initiating outbound call:', error);
            throw new Error(`Failed to initiate outbound call: ${error.message}`);
        }
    }

    async textToSpeech(payload) {
        console.log('🔊 Twilio: Processing TTS request');
        console.log('Payload:', payload);

        try {
            const { text, voice = 'alice', language = 'en-US' } = payload;

            if (!text) {
                throw new Error('Text content is required for TTS');
            }

            // Generate TwiML with TTS
            const twimlResponse = this.generateTTSResponse(text, voice, language);

            return {
                success: true,
                text: text,
                voice: voice,
                language: language,
                twiml: twimlResponse,
                message: 'TTS processed successfully'
            };
        } catch (error) {
            console.error('❌ Error processing TTS:', error);
            throw new Error(`Failed to process TTS: ${error.message}`);
        }
    }

    async sendSMS(payload) {
        console.log('📱 Twilio: Sending SMS');
        console.log('Payload:', payload);

        try {
            const { to, message, from = this.phoneNumber } = payload;

            if (!to || !message) {
                throw new Error('Recipient and message are required for SMS');
            }

            // In a real implementation, you would use Twilio's SDK
            console.log('📱 Simulating SMS send:', { to, from, message });

            return {
                success: true,
                messageSid: `simulated_sms_${Date.now()}`,
                to: to,
                from: from,
                status: 'sent',
                message: 'SMS sent successfully'
            };
        } catch (error) {
            console.error('❌ Error sending SMS:', error);
            throw new Error(`Failed to send SMS: ${error.message}`);
        }
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
