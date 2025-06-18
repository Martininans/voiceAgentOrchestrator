const Fastify = require('fastify');
const websocket = require('@fastify/websocket');
const cors = require('@fastify/cors');
const config = require('./config');
const axios = require('axios');
const supabaseService = require('./supabase');

const app = Fastify({
    logger: {
        level: config.logging.level,
        format: config.logging.format === 'json' ? 'json' : 'simple'
    }
});

// Register plugins
app.register(cors, {
    origin: config.security.cors.origin,
    credentials: config.security.cors.credentials
});
app.register(websocket);

console.log('🚀 Starting Voice Agent Orchestrator Server...');
console.log(`📋 Environment: ${config.server.environment}`);
console.log(`🎯 Voice Provider: ${config.voice.provider}`);
console.log(`🔗 Orchestrator URL: ${config.orchestrator.url}`);
console.log(`🗄️  Supabase URL: ${config.supabase.url}`);

// Register VoiceAgent routes
console.log('📋 Registering VoiceAgent routes...');
app.register(require('./routes/voiceAgent'), { prefix: '/voice' });

// Register Supabase routes
console.log('📋 Registering Supabase routes...');
app.register(require('./routes/supabase'), { prefix: '/supabase' });

// WebSocket connection for real-time audio
app.register(async function (fastify) {
    fastify.get('/ws', { websocket: true }, (connection, req) => {
        console.log('🔌 WebSocket connection established');
        
        // Send welcome message
        connection.socket.send(JSON.stringify({
            type: 'connection',
            message: 'WebSocket connected successfully',
            timestamp: new Date().toISOString()
        }));
        
        connection.socket.on('message', async (message) => {
            try {
                const data = JSON.parse(message);
                console.log('📨 Received WebSocket message:', data.type);
                
                // Handle different message types
                switch (data.type) {
                    case 'audio':
                        await handleAudioMessage(data, connection);
                        break;
                    case 'text':
                        await handleTextMessage(data, connection);
                        break;
                    case 'ping':
                        connection.socket.send(JSON.stringify({
                            type: 'pong',
                            timestamp: new Date().toISOString()
                        }));
                        break;
                    default:
                        connection.socket.send(JSON.stringify({
                            type: 'error',
                            message: 'Unknown message type'
                        }));
                }
            } catch (error) {
                console.error('❌ WebSocket message error:', error);
                connection.socket.send(JSON.stringify({
                    type: 'error',
                    message: 'Invalid message format'
                }));
            }
        });
        
        connection.socket.on('close', () => {
            console.log('🔌 WebSocket connection closed');
        });
        
        connection.socket.on('error', (error) => {
            console.error('❌ WebSocket error:', error);
        });
    });
});

async function handleAudioMessage(data, connection) {
    console.log('🎵 Processing audio message');
    
    try {
        // Send acknowledgment
        connection.socket.send(JSON.stringify({
            type: 'audio_ack',
            message: 'Audio received, processing...',
            timestamp: new Date().toISOString()
        }));

        // Forward to Python orchestrator for processing
        const orchestratorResponse = await forwardToOrchestrator({
            type: 'audio',
            audio_data: data.audio_data,
            user_id: data.user_id,
            session_id: data.session_id,
            context: data.context
        });

        // Store interaction in Supabase
        try {
            await supabaseService.storeInteraction({
                user_id: data.user_id,
                session_id: data.session_id,
                call_sid: data.context?.call_sid,
                type: 'audio',
                input_text: orchestratorResponse.transcribed_text,
                output_text: orchestratorResponse.response,
                intent: orchestratorResponse.intent,
                confidence: orchestratorResponse.confidence,
                duration: Date.now() - new Date(data.timestamp).getTime()
            });
        } catch (dbError) {
            console.warn('⚠️  Failed to store interaction in Supabase:', dbError.message);
        }

        // Send response back to client
        connection.socket.send(JSON.stringify({
            type: 'audio_response',
            success: true,
            transcribed_text: orchestratorResponse.transcribed_text,
            intent: orchestratorResponse.intent,
            response: orchestratorResponse.response,
            voice_url: orchestratorResponse.voice_url,
            timestamp: new Date().toISOString()
        }));

    } catch (error) {
        console.error('❌ Error processing audio:', error);
        connection.socket.send(JSON.stringify({
            type: 'error',
            message: 'Failed to process audio',
            error: error.message,
            timestamp: new Date().toISOString()
        }));
    }
}

async function handleTextMessage(data, connection) {
    console.log('📝 Processing text message');
    
    try {
        // Send acknowledgment
        connection.socket.send(JSON.stringify({
            type: 'text_ack',
            message: 'Text received, processing...',
            timestamp: new Date().toISOString()
        }));

        // Forward to Python orchestrator for processing
        const orchestratorResponse = await forwardToOrchestrator({
            type: 'text',
            text: data.text,
            user_id: data.user_id,
            session_id: data.session_id,
            context: data.context
        });

        // Store interaction in Supabase
        try {
            await supabaseService.storeInteraction({
                user_id: data.user_id,
                session_id: data.session_id,
                call_sid: data.context?.call_sid,
                type: 'text',
                input_text: data.text,
                output_text: orchestratorResponse.response,
                intent: orchestratorResponse.intent,
                confidence: orchestratorResponse.confidence,
                duration: Date.now() - new Date(data.timestamp).getTime()
            });
        } catch (dbError) {
            console.warn('⚠️  Failed to store interaction in Supabase:', dbError.message);
        }

        // Send response back to client
        connection.socket.send(JSON.stringify({
            type: 'text_response',
            success: true,
            intent: orchestratorResponse.intent,
            response: orchestratorResponse.response,
            timestamp: new Date().toISOString()
        }));

    } catch (error) {
        console.error('❌ Error processing text:', error);
        connection.socket.send(JSON.stringify({
            type: 'error',
            message: 'Failed to process text',
            error: error.message,
            timestamp: new Date().toISOString()
        }));
    }
}

async function forwardToOrchestrator(data) {
    try {
        let endpoint = '';
        let payload = {};

        if (data.type === 'audio') {
            endpoint = '/process-audio';
            payload = {
                audio_data: data.audio_data,
                user_id: data.user_id,
                session_id: data.session_id
            };
        } else if (data.type === 'text') {
            endpoint = '/process-intent';
            payload = {
                text: data.text,
                context: {
                    user_id: data.user_id,
                    session_id: data.session_id,
                    source: 'websocket',
                    ...data.context
                }
            };
        }

        const response = await axios.post(
            `${config.orchestrator.url}${endpoint}`,
            payload,
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
        throw new Error(`Failed to communicate with orchestrator: ${error.message}`);
    }
}

// Health check endpoint
app.get('/health', async (req, reply) => {
    // Test Supabase connection
    const supabaseStatus = await supabaseService.testConnection();
    
    return {
        status: 'healthy',
        service: 'voice-agent-orchestrator',
        version: '1.0.0',
        timestamp: new Date().toISOString(),
        config: {
            voice_provider: config.voice.provider,
            orchestrator_url: config.orchestrator.url,
            environment: config.server.environment
        },
        supabase: supabaseStatus
    };
});

// Root endpoint
app.get('/', async (req, reply) => {
    return { 
        message: 'AI Voice Agent Orchestrator Running',
        version: '1.0.0',
        services: ['voice', 'websocket', 'orchestrator', 'supabase'],
        endpoints: {
            health: '/health',
            voice: '/voice',
            supabase: '/supabase',
            websocket: '/ws'
        },
        config: {
            voice_provider: config.voice.provider,
            orchestrator_url: config.orchestrator.url,
            supabase_url: config.supabase.url
        }
    };
});

// Error handler
app.setErrorHandler((error, request, reply) => {
    console.error('❌ Global error handler:', error);
    reply.status(500).send({
        error: 'Internal server error',
        message: error.message,
        timestamp: new Date().toISOString()
    });
});

const PORT = config.server.port;
const HOST = config.server.host;

app.listen({ port: PORT, host: HOST }, err => {
    if (err) {
        console.error('❌ Failed to start server:', err);
        process.exit(1);
    }
    console.log(`🎯 Node.js WebSocket server running on ${HOST}:${PORT}`);
    console.log(`🔗 Health check: http://${HOST}:${PORT}/health`);
    console.log(`📞 Voice endpoints: http://${HOST}:${PORT}/voice`);
    console.log(`🗄️  Supabase endpoints: http://${HOST}:${PORT}/supabase`);
    console.log(`🔌 WebSocket: ws://${HOST}:${PORT}/ws`);
});

app.ready(err => {
    if (err) throw err;
    console.log('📋 Registered routes:');
    console.log(app.printRoutes());
});
