require('dotenv').config();

const config = {
    // Server Configuration
    server: {
        port: process.env.PORT || 3000,
        host: process.env.HOST || '0.0.0.0',
        environment: process.env.NODE_ENV || 'development'
    },

    // Voice Provider Configuration
    voice: {
        provider: process.env.VOICE_PROVIDER || 'twilio',
        twilio: {
            accountSid: process.env.TWILIO_ACCOUNT_SID,
            authToken: process.env.TWILIO_AUTH_TOKEN,
            phoneNumber: process.env.TWILIO_PHONE_NUMBER,
            webhookUrl: process.env.TWILIO_WEBHOOK_URL || 'http://localhost:3000/voice/webhook'
        }
    },

    // Supabase Configuration
    supabase: {
        url: process.env.SUPABASE_URL || 'https://your-project.supabase.co',
        anonKey: process.env.SUPABASE_ANON_KEY || 'your-anon-key-here',
        serviceRoleKey: process.env.SUPABASE_SERVICE_ROLE_KEY || 'your-service-role-key-here',
        database: {
            host: process.env.SUPABASE_DB_HOST || 'db.your-project.supabase.co',
            port: process.env.SUPABASE_DB_PORT || 5432,
            name: process.env.SUPABASE_DB_NAME || 'postgres',
            user: process.env.SUPABASE_DB_USER || 'postgres',
            password: process.env.SUPABASE_DB_PASSWORD || 'your-db-password-here'
        }
    },

    // Python Orchestrator Configuration
    orchestrator: {
        url: process.env.ORCHESTRATOR_URL || 'http://localhost:8000',
        timeout: parseInt(process.env.ORCHESTRATOR_TIMEOUT) || 30000,
        retries: parseInt(process.env.ORCHESTRATOR_RETRIES) || 3
    },

    // WebSocket Configuration
    websocket: {
        maxConnections: parseInt(process.env.MAX_WS_CONNECTIONS) || 100,
        heartbeatInterval: parseInt(process.env.WS_HEARTBEAT_INTERVAL) || 30000
    },

    // Logging Configuration
    logging: {
        level: process.env.LOG_LEVEL || 'info',
        format: process.env.LOG_FORMAT || 'json'
    },

    // Security Configuration
    security: {
        cors: {
            origin: process.env.CORS_ORIGIN || '*',
            credentials: process.env.CORS_CREDENTIALS === 'true'
        }
    }
};

// Validation
const requiredEnvVars = {
    twilio: ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER'],
    supabase: ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
};

function validateConfig() {
    const provider = config.voice.provider;
    if (provider === 'twilio') {
        const missing = requiredEnvVars.twilio.filter(varName => !process.env[varName]);
        if (missing.length > 0) {
            console.warn(`⚠️  Missing Twilio environment variables: ${missing.join(', ')}`);
        }
    }

    // Check Supabase configuration
    const missingSupabase = requiredEnvVars.supabase.filter(varName => !process.env[varName]);
    if (missingSupabase.length > 0) {
        console.warn(`⚠️  Missing Supabase environment variables: ${missingSupabase.join(', ')}`);
        console.warn(`📋 Using placeholder values for Supabase. Please update your .env file.`);
    }
}

validateConfig();

module.exports = config;
