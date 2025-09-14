const VoiceAgent = require('../voiceAgent');
const config = require('../config');
console.log('✅ Loading VoiceAgent Routes');

module.exports = async function (fastify, opts) {
    console.log('🔧 Registering VoiceAgent routes with prefix:', opts.prefix || '/voice');
    const requireAuth = (request, reply, done) => {
        const auth = request.headers['authorization'];
        if (!auth) return reply.code(401).send({ error: 'Unauthorized' });
        const token = auth.startsWith('Bearer ') ? auth.slice(7) : auth;
        try {
            request.user = fastify.jwt.verify(token);
            done();
        } catch (e) {
            reply.code(401).send({ error: 'Invalid token' });
        }
    };
    
    // Schemas
    const schemas = {
        inbound: {
            body: {
                type: 'object',
                properties: {
                    from: { type: 'string' },
                    to: { type: 'string' },
                    metadata: { type: 'object', additionalProperties: true }
                },
                required: ['from', 'to'],
                additionalProperties: false
            }
        },
        outbound: {
            body: {
                type: 'object',
                properties: {
                    to: { type: 'string' },
                    message: { type: 'string' },
                    options: { type: 'object', additionalProperties: true }
                },
                required: ['to'],
                additionalProperties: false
            }
        },
        tts: {
            body: {
                type: 'object',
                properties: {
                    text: { type: 'string', minLength: 1, maxLength: 1000 },
                    voice: { type: 'string' },
                    language: { type: 'string' }
                },
                required: ['text'],
                additionalProperties: false
            }
        },
        sms: {
            body: {
                type: 'object',
                properties: {
                    to: { type: 'string' },
                    text: { type: 'string', minLength: 1, maxLength: 1000 }
                },
                required: ['to', 'text'],
                additionalProperties: false
            }
        }
    };

    // Inbound call handling
    fastify.post('/inbound-call', { preHandler: requireAuth, schema: schemas.inbound }, async (request, reply) => {
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
    fastify.post('/outbound-call', { preHandler: requireAuth, schema: schemas.outbound }, async (request, reply) => {
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
    fastify.post('/tts', { preHandler: requireAuth, schema: schemas.tts }, async (request, reply) => {
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
    fastify.post('/sms', { preHandler: requireAuth, schema: schemas.sms }, async (request, reply) => {
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

    // Twilio webhook for call status updates (signature verification to be implemented per provider docs)
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
    fastify.get('/status', { preHandler: requireAuth }, async (request, reply) => {
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
    fastify.get('/config', { preHandler: requireAuth }, async (request, reply) => {
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

    // Provider management routes
    fastify.get('/providers', { preHandler: requireAuth }, async (request, reply) => {
        console.log('📋 Received providers list request');
        try {
            const providers = VoiceAgent.getAvailableProviders();
            const currentProvider = VoiceAgent.provider;
            const capabilities = await VoiceAgent.getProviderCapabilities();
            
            return {
                current: currentProvider,
                available: providers,
                capabilities: capabilities
            };
        } catch (error) {
            console.error('❌ Error getting providers:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    fastify.post('/providers/switch', { preHandler: requireAuth }, async (request, reply) => {
        console.log('🔄 Received provider switch request');
        try {
            const { provider } = request.body;
            
            if (!provider) {
                return reply.code(400).send({ error: 'Provider name is required' });
            }

            const result = await VoiceAgent.switchProvider(provider);
            
            return {
                success: true,
                message: `Successfully switched to ${provider}`,
                provider: provider
            };
        } catch (error) {
            console.error('❌ Error switching provider:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    fastify.get('/providers/:provider/capabilities', { preHandler: requireAuth }, async (request, reply) => {
        console.log('📋 Received provider capabilities request');
        try {
            const { provider } = request.params;
            const capabilities = await VoiceAgent.getProviderCapabilities(provider);
            
            if (!capabilities) {
                return reply.code(404).send({ error: `Provider ${provider} not found` });
            }
            
            return {
                provider: provider,
                capabilities: capabilities
            };
        } catch (error) {
            console.error('❌ Error getting provider capabilities:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    // Provider-specific webhook endpoints
    fastify.post('/webhooks/vonage', async (request, reply) => {
        console.log('🔗 Received Vonage webhook');
        try {
            const webhookData = request.body;
            console.log('Vonage webhook data:', webhookData);
            
            // Handle Vonage-specific webhook processing
            return { success: true, message: 'Vonage webhook processed' };
        } catch (error) {
            console.error('❌ Error processing Vonage webhook:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    fastify.post('/webhooks/aws-connect', async (request, reply) => {
        console.log('🔗 Received AWS Connect webhook');
        try {
            const webhookData = request.body;
            console.log('AWS Connect webhook data:', webhookData);
            
            // Handle AWS Connect-specific webhook processing
            return { success: true, message: 'AWS Connect webhook processed' };
        } catch (error) {
            console.error('❌ Error processing AWS Connect webhook:', error);
            reply.code(500).send({ error: error.message });
        }
    });

    fastify.post('/webhooks/generic', async (request, reply) => {
        console.log('🔗 Received Generic HTTP webhook');
        try {
            const webhookData = request.body;
            console.log('Generic webhook data:', webhookData);
            
            // Handle generic webhook processing
            return { success: true, message: 'Generic webhook processed' };
        } catch (error) {
            console.error('❌ Error processing generic webhook:', error);
            reply.code(500).send({ error: error.message });
        }
    });
    
    console.log('✅ VoiceAgent routes registered successfully');
};
