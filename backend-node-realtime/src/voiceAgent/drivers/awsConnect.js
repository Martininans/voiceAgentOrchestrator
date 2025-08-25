const BaseDriver = require('./baseDriver');
const config = require('../../config');

class AWSConnectDriver extends BaseDriver {
    constructor() {
        super(config);
        this.providerName = 'aws-connect';
        this.accessKeyId = config.voice.awsConnect?.accessKeyId;
        this.secretAccessKey = config.voice.awsConnect?.secretAccessKey;
        this.region = config.voice.awsConnect?.region || 'us-east-1';
        this.instanceId = config.voice.awsConnect?.instanceId;
        this.phoneNumber = config.voice.awsConnect?.phoneNumber;
        this.webhookUrl = config.voice.awsConnect?.webhookUrl;
    }

    async initialize() {
        console.log('📞 Initializing AWS Connect driver...');
        
        if (!this.accessKeyId || !this.secretAccessKey || !this.instanceId) {
            console.warn('⚠️  AWS Connect credentials not fully configured');
            return false;
        }

        console.log('✅ AWS Connect driver initialized successfully');
        return true;
    }

    async validateConfig() {
        const required = ['accessKeyId', 'secretAccessKey', 'instanceId'];
        const missing = required.filter(key => !this[key]);
        
        if (missing.length > 0) {
            console.warn(`⚠️  Missing AWS Connect configuration: ${missing.join(', ')}`);
            return false;
        }
        
        return true;
    }

    async handleInboundCall(payload) {
        console.log('📞 AWS Connect: Processing inbound call');
        console.log('Payload:', payload);

        try {
            // Extract call details from AWS Connect webhook
            const callId = payload.Details?.ContactData?.ContactId;
            const from = payload.Details?.ContactData?.CustomerEndpoint?.Address;
            const to = payload.Details?.ContactData?.SystemEndpoint?.Address;
            const status = payload.Details?.ContactData?.Status;

            // Generate AWS Connect response
            const connectResponse = this.generateInboundResponse();

            return this.generateSuccessResponse({
                callId: callId,
                from: from,
                to: to,
                status: status,
                response: connectResponse
            }, 'Inbound call processed successfully');
        } catch (error) {
            console.error('❌ Error processing inbound call:', error);
            return this.generateErrorResponse(`Failed to process inbound call: ${error.message}`);
        }
    }

    async handleOutboundCall(payload) {
        console.log('📞 AWS Connect: Initiating outbound call');
        console.log('Payload:', payload);

        try {
            const { to, message, callbackUrl } = payload;

            if (!to) {
                return this.generateErrorResponse('Recipient phone number is required', 400);
            }

            // In a real implementation, you would use AWS SDK
            const callData = {
                InstanceId: this.instanceId,
                ContactFlowId: 'your-contact-flow-id',
                DestinationPhoneNumber: to,
                SourcePhoneNumber: this.phoneNumber,
                Attributes: {
                    message: message || 'Hello! This is an automated call from your AI assistant.'
                }
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
        console.log('🔊 AWS Connect: Processing TTS request');
        console.log('Payload:', payload);

        try {
            const { text, voice = 'Joanna', language = 'en-US' } = payload;

            if (!text) {
                return this.generateErrorResponse('Text content is required for TTS', 400);
            }

            // Generate AWS Connect TTS response
            const ttsResponse = this.generateTTSResponse(text, voice, language);

            return this.generateSuccessResponse({
                text: text,
                voice: voice,
                language: language,
                response: ttsResponse
            }, 'TTS processed successfully');
        } catch (error) {
            console.error('❌ Error processing TTS:', error);
            return this.generateErrorResponse(`Failed to process TTS: ${error.message}`);
        }
    }

    async sendSMS(payload) {
        console.log('📱 AWS Connect: Sending SMS');
        console.log('Payload:', payload);

        try {
            const { to, message, from = this.phoneNumber } = payload;

            if (!to || !message) {
                return this.generateErrorResponse('Recipient and message are required for SMS', 400);
            }

            // In a real implementation, you would use AWS SNS
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
        console.log('🎤 AWS Connect: Processing speech input');
        console.log('Payload:', payload);

        try {
            const speechResult = payload.Details?.Parameters?.speechResult;
            const confidence = payload.Details?.Parameters?.confidence;
            const callId = payload.Details?.ContactData?.ContactId;

            if (!speechResult) {
                return this.generateTTSResponse("I didn't catch that. Could you please repeat?");
            }

            // Forward to Python orchestrator for processing
            const orchestratorResponse = await this.forwardToOrchestrator({
                type: 'speech',
                text: speechResult,
                confidence: confidence,
                callId: callId
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
                instanceId: this.instanceId,
                region: this.region,
                phoneNumber: this.phoneNumber
            }
        };
    }

    generateInboundResponse() {
        return {
            actions: [
                {
                    type: 'Speak',
                    parameters: {
                        text: "Hello! I'm your AI voice assistant. How can I help you today?"
                    }
                },
                {
                    type: 'GetCustomerInput',
                    parameters: {
                        text: "Please tell me how I can assist you.",
                        timeout: 10
                    }
                }
            ]
        };
    }

    generateTTSResponse(text, voice = 'Joanna', language = 'en-US') {
        return {
            actions: [
                {
                    type: 'Speak',
                    parameters: {
                        text: text,
                        voice: voice,
                        language: language
                    }
                }
            ]
        };
    }
}

module.exports = new AWSConnectDriver(); 