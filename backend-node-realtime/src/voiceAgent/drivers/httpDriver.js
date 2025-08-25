const BaseDriver = require('./baseDriver');
const config = require('../../config');
const axios = require('axios');

class HTTPDriver extends BaseDriver {
    constructor() {
        super(config);
        this.providerName = 'http';
        this.webhookUrl = config.voice.http?.webhookUrl;
        this.apiKey = config.voice.http?.apiKey;
        this.headers = config.voice.http?.headers || {};
        this.timeout = config.voice.http?.timeout || 30000;
    }

    async initialize() {
        console.log('📞 Initializing HTTP driver...');
        
        if (!this.webhookUrl) {
            console.warn('⚠️  HTTP webhook URL not configured');
            return false;
        }

        // Add API key to headers if provided
        if (this.apiKey) {
            this.headers['Authorization'] = `Bearer ${this.apiKey}`;
        }

        console.log('✅ HTTP driver initialized successfully');
        return true;
    }

    async validateConfig() {
        const required = ['webhookUrl'];
        const missing = required.filter(key => !this[key]);
        
        if (missing.length > 0) {
            console.warn(`⚠️  Missing HTTP configuration: ${missing.join(', ')}`);
            return false;
        }
        
        return true;
    }

    async handleInboundCall(payload) {
        console.log('📞 HTTP: Processing inbound call');
        console.log('Payload:', payload);

        try {
            const response = await this.makeRequest('/inbound-call', {
                method: 'POST',
                data: payload
            });

            return this.generateSuccessResponse(response.data, 'Inbound call processed successfully');
        } catch (error) {
            console.error('❌ Error processing inbound call:', error);
            return this.generateErrorResponse(`Failed to process inbound call: ${error.message}`);
        }
    }

    async handleOutboundCall(payload) {
        console.log('📞 HTTP: Initiating outbound call');
        console.log('Payload:', payload);

        try {
            const response = await this.makeRequest('/outbound-call', {
                method: 'POST',
                data: payload
            });

            return this.generateSuccessResponse(response.data, 'Outbound call initiated successfully');
        } catch (error) {
            console.error('❌ Error initiating outbound call:', error);
            return this.generateErrorResponse(`Failed to initiate outbound call: ${error.message}`);
        }
    }

    async textToSpeech(payload) {
        console.log('🔊 HTTP: Processing TTS request');
        console.log('Payload:', payload);

        try {
            const response = await this.makeRequest('/tts', {
                method: 'POST',
                data: payload
            });

            return this.generateSuccessResponse(response.data, 'TTS processed successfully');
        } catch (error) {
            console.error('❌ Error processing TTS:', error);
            return this.generateErrorResponse(`Failed to process TTS: ${error.message}`);
        }
    }

    async sendSMS(payload) {
        console.log('📱 HTTP: Sending SMS');
        console.log('Payload:', payload);

        try {
            const response = await this.makeRequest('/sms', {
                method: 'POST',
                data: payload
            });

            return this.generateSuccessResponse(response.data, 'SMS sent successfully');
        } catch (error) {
            console.error('❌ Error sending SMS:', error);
            return this.generateErrorResponse(`Failed to send SMS: ${error.message}`);
        }
    }

    async processSpeech(payload) {
        console.log('🎤 HTTP: Processing speech input');
        console.log('Payload:', payload);

        try {
            const response = await this.makeRequest('/process-speech', {
                method: 'POST',
                data: payload
            });

            return response.data;
        } catch (error) {
            console.error('❌ Error processing speech:', error);
            return this.generateErrorResponse(`Failed to process speech: ${error.message}`);
        }
    }

    async getStatus() {
        try {
            const response = await this.makeRequest('/status', {
                method: 'GET'
            });

            return {
                provider: this.providerName,
                status: 'operational',
                capabilities: ['inbound_calls', 'outbound_calls', 'tts', 'sms', 'speech_processing'],
                config: {
                    webhookUrl: this.webhookUrl,
                    timeout: this.timeout
                },
                externalStatus: response.data
            };
        } catch (error) {
            return {
                provider: this.providerName,
                status: 'error',
                capabilities: ['inbound_calls', 'outbound_calls', 'tts', 'sms', 'speech_processing'],
                config: {
                    webhookUrl: this.webhookUrl,
                    timeout: this.timeout
                },
                error: error.message
            };
        }
    }

    async makeRequest(endpoint, options = {}) {
        const url = `${this.webhookUrl}${endpoint}`;
        
        const config = {
            method: options.method || 'POST',
            url: url,
            headers: {
                'Content-Type': 'application/json',
                ...this.headers,
                ...options.headers
            },
            timeout: this.timeout,
            ...options
        };

        if (options.data) {
            config.data = options.data;
        }

        console.log(`🌐 Making ${config.method} request to: ${url}`);
        
        return axios(config);
    }
}

module.exports = new HTTPDriver(); 