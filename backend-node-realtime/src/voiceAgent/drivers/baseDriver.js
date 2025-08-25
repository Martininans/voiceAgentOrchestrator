/**
 * Base Voice Provider Driver
 * Defines the interface that all voice providers must implement
 */

class BaseDriver {
    constructor(config) {
        this.config = config;
        this.providerName = 'base';
    }

    /**
     * Initialize the driver
     * @returns {Promise<void>}
     */
    async initialize() {
        throw new Error('initialize() method must be implemented by subclass');
    }

    /**
     * Handle inbound call
     * @param {Object} payload - Call payload
     * @returns {Promise<Object>} Response object
     */
    async handleInboundCall(payload) {
        throw new Error('handleInboundCall() method must be implemented by subclass');
    }

    /**
     * Handle outbound call
     * @param {Object} payload - Call payload
     * @returns {Promise<Object>} Response object
     */
    async handleOutboundCall(payload) {
        throw new Error('handleOutboundCall() method must be implemented by subclass');
    }

    /**
     * Convert text to speech
     * @param {Object} payload - TTS payload
     * @returns {Promise<Object>} Response object
     */
    async textToSpeech(payload) {
        throw new Error('textToSpeech() method must be implemented by subclass');
    }

    /**
     * Send SMS message
     * @param {Object} payload - SMS payload
     * @returns {Promise<Object>} Response object
     */
    async sendSMS(payload) {
        throw new Error('sendSMS() method must be implemented by subclass');
    }

    /**
     * Process speech input
     * @param {Object} payload - Speech payload
     * @returns {Promise<Object>} Response object
     */
    async processSpeech(payload) {
        throw new Error('processSpeech() method must be implemented by subclass');
    }

    /**
     * Get provider status
     * @returns {Promise<Object>} Status object
     */
    async getStatus() {
        return {
            provider: this.providerName,
            status: 'unknown',
            capabilities: [],
            config: {}
        };
    }

    /**
     * Validate configuration
     * @returns {Promise<boolean>} Validation result
     */
    async validateConfig() {
        throw new Error('validateConfig() method must be implemented by subclass');
    }

    /**
     * Forward data to orchestrator
     * @param {Object} data - Data to forward
     * @returns {Promise<Object>} Orchestrator response
     */
    async forwardToOrchestrator(data) {
        const axios = require('axios');
        const config = require('../../config');

        try {
            const response = await axios.post(
                `${config.orchestrator.url}/process-intent`,
                {
                    text: data.text,
                    context: {
                        callSid: data.callSid,
                        confidence: data.confidence,
                        source: this.providerName
                    }
                },
                {
                    timeout: config.orchestrator.timeout,
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }
            );

            return response.data;
        } catch (error) {
            console.error(`❌ Error forwarding to orchestrator from ${this.providerName}:`, error);
            throw new Error('Failed to communicate with orchestrator');
        }
    }

    /**
     * Generate error response
     * @param {string} message - Error message
     * @param {number} code - Error code
     * @returns {Object} Error response
     */
    generateErrorResponse(message, code = 500) {
        return {
            success: false,
            error: message,
            code: code,
            provider: this.providerName,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Generate success response
     * @param {Object} data - Response data
     * @param {string} message - Success message
     * @returns {Object} Success response
     */
    generateSuccessResponse(data, message = 'Operation completed successfully') {
        return {
            success: true,
            data: data,
            message: message,
            provider: this.providerName,
            timestamp: new Date().toISOString()
        };
    }
}

module.exports = BaseDriver; 