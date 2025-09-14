const Fastify = require('fastify');
const websocket = require('@fastify/websocket');
const cors = require('@fastify/cors');
const helmet = require('@fastify/helmet');
const rateLimit = require('@fastify/rate-limit');
const jwt = require('@fastify/jwt');
const client = require('prom-client');
const config = require('./config');
const axios = require('axios');
const dataBackend = require('./data');

const app = Fastify({
    logger: {
        level: config.logging.level,
        format: config.logging.format === 'json' ? 'json' : 'simple'
    },
    bodyLimit: 2 * 1024 * 1024 // 2MB
});

// Register plugins
app.register(cors, {
    origin: config.security.cors.origin,
    credentials: config.security.cors.credentials
});
app.register(websocket);
app.register(helmet);
app.register(rateLimit, {
    max: 100,
    timeWindow: '1 minute'
});
app.register(jwt, {
    secret: process.env.JWT_SECRET || 'change-me-in-prod'
});

// Correlation ID hook
app.addHook('onRequest', async (request, reply) => {
    const existing = request.headers['x-request-id'];
    const id = existing || Math.random().toString(36).slice(2);
    request.id = id;
    reply.header('x-request-id', id);
});

// Basic auth guard for protected routes
function requireAuth(request, reply, done) {
    const auth = request.headers['authorization'];
    if (!auth) {
        reply.code(401).send({ error: 'Unauthorized' });
        return;
    }
    const token = auth.startsWith('Bearer ') ? auth.slice(7) : auth;
    try {
        request.user = app.jwt.verify(token);
        done();
    } catch (e) {
        reply.code(401).send({ error: 'Invalid token' });
    }
}

// Prometheus metrics
const register = new client.Registry();
client.collectDefaultMetrics({ register });
const httpRequestsCounter = new client.Counter({
    name: 'http_requests_total',
    help: 'Total HTTP requests',
    labelNames: ['method', 'route', 'status']
});
register.registerMetric(httpRequestsCounter);
app.addHook('onResponse', async (request, reply) => {
    try {
        const route = request.routerPath || request.url;
        httpRequestsCounter.inc({ method: request.method, route, status: reply.statusCode });
    } catch {}
});
app.get('/metrics', async (req, reply) => {
    reply.header('Content-Type', register.contentType);
    return register.metrics();
});

console.log('🚀 Starting Voice Agent Orchestrator Server...');
console.log(`📋 Environment: ${config.server.environment}`);
console.log(`🎯 Voice Provider: ${config.voice.provider}`);
console.log(`🔗 Orchestrator URL: ${config.orchestrator.url}`);
console.log(`🗄️  Data Backend: ${config.dataBackend}`);

console.log("Loaded environment variables:");
console.log({
  DATA_BACKEND: process.env.DATA_BACKEND,
  AZURE_PG_CONNECTION_STRING: process.env.AZURE_PG_CONNECTION_STRING ? '***' : undefined,
  SUPABASE_URL: process.env.SUPABASE_URL,
  SUPABASE_ANON_KEY: process.env.SUPABASE_ANON_KEY ? '***' : undefined,
  SUPABASE_SERVICE_ROLE_KEY: process.env.SUPABASE_SERVICE_ROLE_KEY ? '***' : undefined,
  JWT_SECRET: process.env.JWT_SECRET ? '***' : undefined,
  OPENAI_API_KEY: process.env.OPENAI_API_KEY ? '***' : undefined,
  TWILIO_ACCOUNT_SID: process.env.TWILIO_ACCOUNT_SID ? '***' : undefined,
  TWILIO_AUTH_TOKEN: process.env.TWILIO_AUTH_TOKEN ? '***' : undefined,
  TWILIO_PHONE_NUMBER: process.env.TWILIO_PHONE_NUMBER ? '***' : undefined
});

// Register VoiceAgent routes
console.log('📋 Registering VoiceAgent routes...');
app.register(require('./routes/voiceAgent'), { prefix: '/voice' });

// Register Supabase routes (kept for compatibility during migration)
console.log('📋 Registering Supabase routes...');
app.register(require('./routes/supabase'), { prefix: '/supabase' });

// WebSocket connection for real-time audio
app.register(async function (fastify) {
    fastify.get('/ws', { websocket: true }, (connection, req) => {
        // JWT auth for WebSocket
        try {
            const authHeader = req.headers['authorization'];
            if (!authHeader) {
                connection.socket.send(JSON.stringify({ type: 'error', message: 'Unauthorized' }));
                connection.socket.close();
                return;
            }
            const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7) : authHeader;
            req.user = fastify.jwt.verify(token);
        } catch (e) {
            connection.socket.send(JSON.stringify({ type: 'error', message: 'Invalid token' }));
            connection.socket.close();
            return;
        }
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
                // Basic message size guard
                if (message && message.length > 512 * 1024) {
                    connection.socket.send(JSON.stringify({ type: 'error', message: 'Payload too large' }));
                    return;
                }
                
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

        // Store interaction via data backend
        try {
            await dataBackend.storeInteraction({
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
            console.warn('⚠️  Failed to store interaction:', dbError.message);
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

        // Store interaction via data backend
        try {
            await dataBackend.storeInteraction({
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
            console.warn('⚠️  Failed to store interaction:', dbError.message);
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
                    'Content-Type': 'application/json',
                    'x-request-id': typeof app?.request?.id === 'string' ? app.request.id : ''
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
    const dataStatus = await dataBackend.testConnection();
    
    return {
        status: 'healthy',
        service: 'voice-agent-orchestrator',
        version: '1.0.0',
        timestamp: new Date().toISOString(),
        config: {
            voice_provider: config.voice.provider,
            orchestrator_url: config.orchestrator.url,
            environment: config.server.environment,
            data_backend: config.dataBackend
        },
        data: dataStatus
    };
});

// Readiness endpoint checks orchestrator and minimal data backend
app.get('/ready', async (req, reply) => {
    try {
        const orch = await axios.get(`${config.orchestrator.url}/health`, { timeout: 2000 });
        const dataStatus = await dataBackend.testConnection();
        return {
            ready: true,
            orchestrator: orch.data?.status || 'unknown',
            data: dataStatus?.status || 'unknown',
            timestamp: new Date().toISOString()
        };
    } catch (e) {
        reply.code(503).send({ ready: false, error: e.message });
    }
});

// Root endpoint
app.get('/', async (req, reply) => {
    return { 
        message: 'AI Voice Agent Orchestrator Running',
        version: '1.0.0',
        services: ['voice', 'websocket', 'orchestrator', 'data'],
        endpoints: {
            health: '/health',
            voice: '/voice',
            supabase: '/supabase',
            websocket: '/ws'
        },
        config: {
            voice_provider: config.voice.provider,
            orchestrator_url: config.orchestrator.url,
            data_backend: config.dataBackend
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
    console.log(`🔌 WebSocket: ws://${HOST}:${PORT}/ws`);
});

app.ready(err => {
    if (err) throw err;
    console.log('📋 Registered routes:');
    console.log(app.printRoutes());
});
