#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function question(prompt) {
    return new Promise((resolve) => {
        rl.question(prompt, resolve);
    });
}

async function setupEnvironment() {
    console.log('🔧 Setting up environment variables for Voice Agent Orchestrator Node.js Backend\n');
    
    const envPath = path.join(__dirname, '.env');
    
    // Check if .env already exists
    if (fs.existsSync(envPath)) {
        const overwrite = await question('⚠️  .env file already exists. Overwrite? (y/N): ');
        if (overwrite.toLowerCase() !== 'y' && overwrite.toLowerCase() !== 'yes') {
            console.log('❌ Setup cancelled');
            rl.close();
            return;
        }
    }
    
    console.log('📝 Please provide the following configuration values:');
    console.log('(Press Enter to use default values)\n');
    
    // Collect environment variables
    const envVars = {};
    
    // Server Configuration
    envVars.PORT = await question('Server Port (default: 3000): ') || '3000';
    envVars.HOST = await question('Server Host (default: 0.0.0.0): ') || '0.0.0.0';
    envVars.NODE_ENV = await question('Environment (default: development): ') || 'development';
    
    // Voice Provider
    envVars.VOICE_PROVIDER = await question('Voice Provider (default: twilio): ') || 'twilio';
    
    // Twilio Configuration
    console.log('\n📞 Twilio Configuration:');
    envVars.TWILIO_ACCOUNT_SID = await question('Twilio Account SID: ') || 'your-twilio-account-sid-here';
    envVars.TWILIO_AUTH_TOKEN = await question('Twilio Auth Token: ') || 'your-twilio-auth-token-here';
    envVars.TWILIO_PHONE_NUMBER = await question('Twilio Phone Number: ') || '+1234567890';
    envVars.TWILIO_WEBHOOK_URL = await question('Twilio Webhook URL (default: http://localhost:3000/voice/webhook): ') || 'http://localhost:3000/voice/webhook';
    
    // Supabase Configuration
    console.log('\n🗄️  Supabase Configuration:');
    envVars.SUPABASE_URL = await question('Supabase URL: ') || 'https://your-project.supabase.co';
    envVars.SUPABASE_ANON_KEY = await question('Supabase Anon Key: ') || 'your-supabase-anon-key-here';
    envVars.SUPABASE_SERVICE_ROLE_KEY = await question('Supabase Service Role Key: ') || 'your-supabase-service-role-key-here';
    
    // Python Orchestrator Configuration
    console.log('\n🐍 Python Orchestrator Configuration:');
    envVars.ORCHESTRATOR_URL = await question('Orchestrator URL (default: http://localhost:8000): ') || 'http://localhost:8000';
    envVars.ORCHESTRATOR_TIMEOUT = await question('Orchestrator Timeout (default: 30000): ') || '30000';
    envVars.ORCHESTRATOR_RETRIES = await question('Orchestrator Retries (default: 3): ') || '3';
    
    // WebSocket Configuration
    console.log('\n🔌 WebSocket Configuration:');
    envVars.MAX_WS_CONNECTIONS = await question('Max WebSocket Connections (default: 100): ') || '100';
    envVars.WS_HEARTBEAT_INTERVAL = await question('WebSocket Heartbeat Interval (default: 30000): ') || '30000';
    
    // Logging Configuration
    console.log('\n📋 Logging Configuration:');
    envVars.LOG_LEVEL = await question('Log Level (default: info): ') || 'info';
    envVars.LOG_FORMAT = await question('Log Format (default: json): ') || 'json';
    
    // Security Configuration
    console.log('\n🔒 Security Configuration:');
    envVars.CORS_ORIGIN = await question('CORS Origin (default: *): ') || '*';
    envVars.CORS_CREDENTIALS = await question('CORS Credentials (default: false): ') || 'false';
    
    // Optional Configuration
    console.log('\n⚙️  Optional Configuration:');
    envVars.JWT_SECRET = await question('JWT Secret (optional): ') || 'your-jwt-secret-key-here';
    envVars.OPENAI_API_KEY = await question('OpenAI API Key (optional): ') || 'your-openai-api-key-here';
    envVars.REDIS_URL = await question('Redis URL (optional, default: redis://localhost:6379): ') || 'redis://localhost:6379';
    envVars.DATABASE_URL = await question('Database URL (optional): ') || 'postgresql://user:password@localhost:5432/database';
    envVars.CHROMA_HOST = await question('ChromaDB Host (optional, default: localhost): ') || 'localhost';
    envVars.CHROMA_PORT = await question('ChromaDB Port (optional, default: 8000): ') || '8000';
    envVars.SECTOR = await question('Sector (optional, default: generic): ') || 'generic';
    envVars.DEBUG = await question('Debug Mode (optional, default: true): ') || 'true';
    
    // Generate .env content
    const envContent = `# Node.js Backend Environment Configuration
# Voice Agent Orchestrator - Realtime Layer
# Generated on ${new Date().toISOString()}

# Server Configuration
PORT=${envVars.PORT}
HOST=${envVars.HOST}
NODE_ENV=${envVars.NODE_ENV}

# Voice Provider Configuration
VOICE_PROVIDER=${envVars.VOICE_PROVIDER}

# Twilio Configuration
TWILIO_ACCOUNT_SID=${envVars.TWILIO_ACCOUNT_SID}
TWILIO_AUTH_TOKEN=${envVars.TWILIO_AUTH_TOKEN}
TWILIO_PHONE_NUMBER=${envVars.TWILIO_PHONE_NUMBER}
TWILIO_WEBHOOK_URL=${envVars.TWILIO_WEBHOOK_URL}

# Supabase Configuration
SUPABASE_URL=${envVars.SUPABASE_URL}
SUPABASE_ANON_KEY=${envVars.SUPABASE_ANON_KEY}
SUPABASE_SERVICE_ROLE_KEY=${envVars.SUPABASE_SERVICE_ROLE_KEY}

# Python Orchestrator Configuration
ORCHESTRATOR_URL=${envVars.ORCHESTRATOR_URL}
ORCHESTRATOR_TIMEOUT=${envVars.ORCHESTRATOR_TIMEOUT}
ORCHESTRATOR_RETRIES=${envVars.ORCHESTRATOR_RETRIES}

# WebSocket Configuration
MAX_WS_CONNECTIONS=${envVars.MAX_WS_CONNECTIONS}
WS_HEARTBEAT_INTERVAL=${envVars.WS_HEARTBEAT_INTERVAL}

# Logging Configuration
LOG_LEVEL=${envVars.LOG_LEVEL}
LOG_FORMAT=${envVars.LOG_FORMAT}

# Security Configuration
CORS_ORIGIN=${envVars.CORS_ORIGIN}
CORS_CREDENTIALS=${envVars.CORS_CREDENTIALS}

# JWT Secret
JWT_SECRET=${envVars.JWT_SECRET}

# OpenAI Configuration
OPENAI_API_KEY=${envVars.OPENAI_API_KEY}

# Redis Configuration
REDIS_URL=${envVars.REDIS_URL}

# Database Configuration
DATABASE_URL=${envVars.DATABASE_URL}

# ChromaDB Configuration
CHROMA_HOST=${envVars.CHROMA_HOST}
CHROMA_PORT=${envVars.CHROMA_PORT}

# Sector Configuration
SECTOR=${envVars.SECTOR}

# Debug Mode
DEBUG=${envVars.DEBUG}
`;
    
    // Write .env file
    try {
        fs.writeFileSync(envPath, envContent);
        console.log('\n✅ .env file created successfully!');
        console.log(`📁 Location: ${envPath}`);
        console.log('\n🔧 Next steps:');
        console.log('1. Update the .env file with your actual API keys and credentials');
        console.log('2. Run "npm start" to start the server');
        console.log('3. Check the logs for any configuration warnings');
    } catch (error) {
        console.error('❌ Error creating .env file:', error.message);
    }
    
    rl.close();
}

// Run the setup
setupEnvironment().catch(console.error); 