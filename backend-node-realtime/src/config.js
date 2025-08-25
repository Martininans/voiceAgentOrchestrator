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
        
        // Twilio Configuration
        twilio: {
            accountSid: process.env.TWILIO_ACCOUNT_SID,
            authToken: process.env.TWILIO_AUTH_TOKEN,
            phoneNumber: process.env.TWILIO_PHONE_NUMBER,
            webhookUrl: process.env.TWILIO_WEBHOOK_URL || 'http://localhost:3000/voice/webhook'
        },

        // Vonage Configuration
        vonage: {
            apiKey: process.env.VONAGE_API_KEY,
            apiSecret: process.env.VONAGE_API_SECRET,
            applicationId: process.env.VONAGE_APPLICATION_ID,
            privateKey: process.env.VONAGE_PRIVATE_KEY,
            phoneNumber: process.env.VONAGE_PHONE_NUMBER,
            webhookUrl: process.env.VONAGE_WEBHOOK_URL || 'http://localhost:3000/voice/webhook'
        },

        // AWS Connect Configuration
        awsConnect: {
            accessKeyId: process.env.AWS_ACCESS_KEY_ID,
            secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
            region: process.env.AWS_REGION || 'us-east-1',
            instanceId: process.env.AWS_CONNECT_INSTANCE_ID,
            phoneNumber: process.env.AWS_CONNECT_PHONE_NUMBER,
            webhookUrl: process.env.AWS_CONNECT_WEBHOOK_URL || 'http://localhost:3000/voice/webhook'
        },

        // Generic HTTP Configuration
        genericHttp: {
            webhookUrl: process.env.GENERIC_HTTP_WEBHOOK_URL,
            apiKey: process.env.GENERIC_HTTP_API_KEY,
            headers: process.env.GENERIC_HTTP_HEADERS ? JSON.parse(process.env.GENERIC_HTTP_HEADERS) : {},
            timeout: parseInt(process.env.GENERIC_HTTP_TIMEOUT) || 30000
        },

        // Africa's Talking Configuration
        africastalking: {
            username: process.env.AFRICASTALKING_USERNAME,
            apiKey: process.env.AFRICASTALKING_API_KEY,
            phoneNumber: process.env.AFRICASTALKING_PHONE_NUMBER,
            webhookUrl: process.env.AFRICASTALKING_WEBHOOK_URL || 'http://localhost:3000/voice/webhook'
        },

        // Exotel Configuration
        exotel: {
            sid: process.env.EXOTEL_SID,
            token: process.env.EXOTEL_TOKEN,
            phoneNumber: process.env.EXOTEL_PHONE_NUMBER,
            webhookUrl: process.env.EXOTEL_WEBHOOK_URL || 'http://localhost:3000/voice/webhook'
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
    vonage: ['VONAGE_API_KEY', 'VONAGE_API_SECRET'],
    'aws-connect': ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_CONNECT_INSTANCE_ID'],
    'generic-http': ['GENERIC_HTTP_WEBHOOK_URL'],
    supabase: ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
};

function validateConfig() {
    const provider = config.voice.provider;
    
    // Check provider-specific required variables
    if (requiredEnvVars[provider]) {
        const missing = requiredEnvVars[provider].filter(varName => !process.env[varName]);
        if (missing.length > 0) {
            console.warn(`⚠️  Missing ${provider} environment variables: ${missing.join(', ')}`);
        }
    }

    // Check Supabase configuration
    const missingSupabase = requiredEnvVars.supabase.filter(varName => !process.env[varName]);
    if (missingSupabase.length > 0) {
        console.warn(`⚠️  Missing Supabase environment variables: ${missingSupabase.join(', ')}`);
        console.warn(`📋 Using placeholder values for Supabase. Please update your .env file.`);
    }

    // Log current provider
    console.log(`🎯 Voice Provider: ${provider}`);
    console.log(`🔧 Available providers: ${Object.keys(requiredEnvVars).filter(key => key !== 'supabase').join(', ')}`);
}

// Run validation
validateConfig();

module.exports = config;
