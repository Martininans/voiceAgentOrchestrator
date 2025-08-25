const TwilioDriver = require('./drivers/twilioDriver');
const VonageDriver = require('./drivers/vonage');
const AWSConnectDriver = require('./drivers/awsConnect');
const GenericHttpDriver = require('./drivers/genericHttp');
const AfricasTalkingDriver = require('./drivers/africastalking');
const ExotelDriver = require('./drivers/exotelDriver');
const config = require('../config');

// Map of available drivers
const driverMap = {
    twilio: TwilioDriver,
    vonage: VonageDriver,
    'aws-connect': AWSConnectDriver,
    'generic-http': GenericHttpDriver,
    africastalking: AfricasTalkingDriver,
    exotel: ExotelDriver
};

// Get the configured provider
const DRIVER = config.voice.provider;

// Validate provider exists
if (!driverMap[DRIVER]) {
    console.error(`❌ VoiceAgent Driver "${DRIVER}" not found!`);
    console.error(`Available drivers: ${Object.keys(driverMap).join(', ')}`);
    process.exit(1);
}

// Get the driver instance
const driver = driverMap[DRIVER];

console.log(`✅ VoiceAgent Driver "${DRIVER}" loaded`);

class VoiceAgent {
    constructor() {
        this.driver = driver;
        this.config = config;
        this.provider = DRIVER;
    }

    async initialize() {
        console.log(`🔧 Initializing VoiceAgent with provider: ${this.provider}`);
        
        try {
            const initialized = await this.driver.initialize();
            if (!initialized) {
                console.warn(`⚠️  VoiceAgent initialization failed for provider: ${this.provider}`);
                return false;
            }

            const configValid = await this.driver.validateConfig();
            if (!configValid) {
                console.warn(`⚠️  VoiceAgent configuration validation failed for provider: ${this.provider}`);
                return false;
            }

            console.log(`✅ VoiceAgent initialized successfully with provider: ${this.provider}`);
            return true;
        } catch (error) {
            console.error(`❌ Error initializing VoiceAgent: ${error.message}`);
            return false;
        }
    }

    async handleInboundCall(payload) {
        try {
            console.log('📞 Processing outbound call request');
            return await this.driver.handleInboundCall(payload);
        } catch (error) {
            console.error('❌ Error in handleInboundCall:', error);
            return this.driver.generateErrorResponse(`Failed to handle inbound call: ${error.message}`);
        }
    }

    async handleOutboundCall(payload) {
        try {
            console.log('📞 Processing outbound call request');
            return await this.driver.handleOutboundCall(payload);
        } catch (error) {
            console.error('❌ Error in handleOutboundCall:', error);
            return this.driver.generateErrorResponse(`Failed to handle outbound call: ${error.message}`);
        }
    }

    async textToSpeech(payload) {
        try {
            console.log('🔊 Processing TTS request');
            return await this.driver.textToSpeech(payload);
        } catch (error) {
            console.error('❌ Error in textToSpeech:', error);
            return this.driver.generateErrorResponse(`Failed to process TTS: ${error.message}`);
        }
    }

    async sendSMS(payload) {
        try {
            console.log('📱 Processing SMS request');
            return await this.driver.sendSMS(payload);
        } catch (error) {
            console.error('❌ Error in sendSMS:', error);
            return this.driver.generateErrorResponse(`Failed to send SMS: ${error.message}`);
        }
    }

    async processSpeech(payload) {
        try {
            console.log('🎤 Processing speech request');
            return await this.driver.processSpeech(payload);
        } catch (error) {
            console.error('❌ Error in processSpeech:', error);
            return this.driver.generateErrorResponse(`Failed to process speech: ${error.message}`);
        }
    }

    async getStatus() {
        try {
            return await this.driver.getStatus();
        } catch (error) {
            console.error('❌ Error getting status:', error);
            return {
                provider: this.provider,
                status: 'error',
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    // Method to switch providers dynamically
    async switchProvider(newProvider) {
        if (!driverMap[newProvider]) {
            throw new Error(`Provider "${newProvider}" not supported. Available: ${Object.keys(driverMap).join(', ')}`);
        }

        console.log(`🔄 Switching from ${this.provider} to ${newProvider}`);
        
        // Initialize new driver
        const newDriver = driverMap[newProvider];
        const initialized = await newDriver.initialize();
        
        if (!initialized) {
            throw new Error(`Failed to initialize provider: ${newProvider}`);
        }

        // Update current driver
        this.driver = newDriver;
        this.provider = newProvider;
        
        console.log(`✅ Successfully switched to provider: ${newProvider}`);
        return true;
    }

    // Method to get available providers
    getAvailableProviders() {
        return Object.keys(driverMap);
    }

    // Method to get provider capabilities
    async getProviderCapabilities(provider = this.provider) {
        if (!driverMap[provider]) {
            return null;
        }

        const driver = driverMap[provider];
        const status = await driver.getStatus();
        return status.capabilities || [];
    }
}

// Create and export singleton instance
const voiceAgent = new VoiceAgent();

// Initialize on module load
voiceAgent.initialize().catch(error => {
    console.error('❌ Failed to initialize VoiceAgent:', error);
});

module.exports = voiceAgent;
