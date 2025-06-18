const VoiceAgent = require('../voiceAgent');
const config = require('../config');
console.log('✅ Loading VoiceAgent Routes');

module.exports = async function (fastify, opts) {
    console.log('🔧 Registering VoiceAgent routes with prefix:', opts.prefix || '/voice');
    
    // Inbound call handling
    fastify.post('/inbound-call', async (request, reply) => {
        console.log('📞 Received inbound call request');
        try {
            const result = await VoiceAgent.handleInboundCall(request.body);
            return result;
        } catch (error) {
            console.error('❌ Error handling inbound call:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    // Outbound call handling
    fastify.post('/outbound-call', async (request, reply) => {
        console.log('📞 Received outbound call request');
        try {
            const result = await VoiceAgent.handleOutboundCall(request.body);
            return result;
        } catch (error) {
            console.error('❌ Error handling outbound call:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    // Text-to-Speech
    fastify.post('/tts', async (request, reply) => {
        console.log('🔊 Received TTS request');
        try {
            const result = await VoiceAgent.textToSpeech(request.body);
            return result;
        } catch (error) {
            console.error('❌ Error handling TTS:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    // SMS sending
    fastify.post('/sms', async (request, reply) => {
        console.log('📱 Received SMS request');
        try {
            const result = await VoiceAgent.sendSMS(request.body);
            return result;
        } catch (error) {
            console.error('❌ Error handling SMS:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    // Speech processing (for Twilio webhooks)
    fastify.post('/process-speech', async (request, reply) => {
        console.log('🎤 Received speech processing request');
        try {
            const result = await VoiceAgent.processSpeech(request.body);
            // Return TwiML response
            reply.type('text/xml');
            return result;
        } catch (error) {
            console.error('❌ Error processing speech:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    // Twilio webhook for call status updates
    fastify.post('/webhook', async (request, reply) => {
        console.log('🔗 Received Twilio webhook');
        try {
            const webhookData = request.body;
            console.log('Webhook data:', webhookData);
            
            // Handle different webhook types
            switch (webhookData.EventType) {
                case 'call-status-changed':
                    console.log('📞 Call status changed:', webhookData.CallStatus);
                    break;
                case 'message-status-changed':
                    console.log('📱 Message status changed:', webhookData.MessageStatus);
                    break;
                default:
                    console.log('🔗 Unknown webhook event:', webhookData.EventType);
            }
            
            return { success: true, message: 'Webhook processed' };
        } catch (error) {
            console.error('❌ Error processing webhook:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    // Voice agent status
    fastify.get('/status', async (request, reply) => {
        console.log('📊 Received status request');
        try {
            const status = await VoiceAgent.getStatus();
            return status;
        } catch (error) {
            console.error('❌ Error getting status:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    // Health check endpoint
    fastify.get('/health', async (request, reply) => {
        return {
            status: 'healthy',
            service: 'voice-agent',
            provider: config.voice.provider,
            timestamp: new Date().toISOString()
        };
    });

    // Configuration endpoint
    fastify.get('/config', async (request, reply) => {
        return {
            provider: config.voice.provider,
            orchestrator: {
                url: config.orchestrator.url,
                timeout: config.orchestrator.timeout
            },
            websocket: {
                maxConnections: config.websocket.maxConnections
            }
        };
    });
    
    console.log('✅ VoiceAgent routes registered successfully');
};
