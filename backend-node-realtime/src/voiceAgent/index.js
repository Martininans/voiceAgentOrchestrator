const TwilioDriver = require('./drivers/twilioDriver');
const config = require('../config');

const DRIVER = config.voice.provider;  // Use config instead of env directly

const driverMap = {
    twilio: TwilioDriver
};

const driver = driverMap[DRIVER];

if (!driver) {
    console.error(`❌ VoiceAgent Driver "${DRIVER}" not found!`);
    console.error(`Available drivers: ${Object.keys(driverMap).join(', ')}`);
    process.exit(1);
}

console.log(`✅ VoiceAgent Driver "${DRIVER}" loaded`);

// Enhanced VoiceAgent interface
class VoiceAgent {
    constructor() {
        this.driver = driver;
        this.config = config;
    }

    async handleInboundCall(payload) {
        try {
            console.log('📞 Processing inbound call request');
            return await this.driver.handleInboundCall(payload);
        } catch (error) {
            console.error('❌ Error in handleInboundCall:', error);
            throw error;
        }
    }

    async handleOutboundCall(payload) {
        try {
            console.log('📞 Processing outbound call request');
            return await this.driver.handleOutboundCall(payload);
        } catch (error) {
            console.error('❌ Error in handleOutboundCall:', error);
            throw error;
        }
    }

    async textToSpeech(payload) {
        try {
            console.log('🔊 Processing TTS request');
            return await this.driver.textToSpeech(payload);
        } catch (error) {
            console.error('❌ Error in textToSpeech:', error);
            throw error;
        }
    }

    async sendSMS(payload) {
        try {
            console.log('📱 Processing SMS request');
            return await this.driver.sendSMS(payload);
        } catch (error) {
            console.error('❌ Error in sendSMS:', error);
            throw error;
        }
    }

    async processSpeech(payload) {
        try {
            console.log('🎤 Processing speech input');
            return await this.driver.processSpeech(payload);
        } catch (error) {
            console.error('❌ Error in processSpeech:', error);
            throw error;
        }
    }

    async getStatus() {
        return {
            provider: DRIVER,
            status: 'operational',
            capabilities: ['inbound_calls', 'outbound_calls', 'tts', 'sms', 'speech_processing'],
            config: {
                phoneNumber: this.config.voice.twilio.phoneNumber,
                orchestratorUrl: this.config.orchestrator.url
            }
        };
    }
}

const voiceAgent = new VoiceAgent();

module.exports = voiceAgent;
