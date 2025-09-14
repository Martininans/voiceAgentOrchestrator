const { test, expect } = require('@jest/globals');
const axios = require('axios');

// Test configuration
const REALTIME_URL = process.env.REALTIME_URL || 'http://localhost:3000';
const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL || 'http://localhost:8000';

describe('Health Check Tests', () => {
    test('Realtime service health check', async () => {
        const response = await axios.get(`${REALTIME_URL}/health`);
        
        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('status');
        expect(response.data.status).toBe('healthy');
        expect(response.data).toHaveProperty('timestamp');
        expect(response.data).toHaveProperty('uptime');
    });

    test('Orchestrator service health check', async () => {
        const response = await axios.get(`${ORCHESTRATOR_URL}/health`);
        
        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('status');
        expect(response.data.status).toBe('healthy');
        expect(response.data).toHaveProperty('timestamp');
        expect(response.data).toHaveProperty('uptime');
    });

    test('Realtime detailed health check', async () => {
        const response = await axios.get(`${REALTIME_URL}/health/detailed`);
        
        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('status');
        expect(response.data).toHaveProperty('checks');
        expect(response.data).toHaveProperty('system');
        expect(response.data.system).toHaveProperty('memory');
    });

    test('Orchestrator detailed health check', async () => {
        const response = await axios.get(`${ORCHESTRATOR_URL}/health/detailed`);
        
        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('status');
        expect(response.data).toHaveProperty('checks');
        expect(response.data).toHaveProperty('system');
    });

    test('Readiness probe - Realtime', async () => {
        const response = await axios.get(`${REALTIME_URL}/ready`);
        
        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('status');
        expect(response.data.status).toBe('ready');
    });

    test('Readiness probe - Orchestrator', async () => {
        const response = await axios.get(`${ORCHESTRATOR_URL}/ready`);
        
        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('status');
        expect(response.data.status).toBe('ready');
    });

    test('Liveness probe - Realtime', async () => {
        const response = await axios.get(`${REALTIME_URL}/live`);
        
        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('status');
        expect(response.data.status).toBe('alive');
    });

    test('Liveness probe - Orchestrator', async () => {
        const response = await axios.get(`${ORCHESTRATOR_URL}/live`);
        
        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('status');
        expect(response.data.status).toBe('alive');
    });
});

describe('API Endpoint Tests', () => {
    test('Voice providers endpoint', async () => {
        const response = await axios.get(`${REALTIME_URL}/voice/providers/current`);
        
        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('provider');
        expect(response.data).toHaveProperty('status');
    });

    test('Process intent endpoint', async () => {
        const testData = {
            text: "Hello, I need help with booking",
            user_id: "test-user-123",
            session_id: "test-session-456",
            sector: "generic"
        };

        const response = await axios.post(`${ORCHESTRATOR_URL}/process-intent`, testData);
        
        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('success');
        expect(response.data.success).toBe(true);
        expect(response.data).toHaveProperty('intent');
        expect(response.data).toHaveProperty('response');
    });
});

describe('Security Tests', () => {
    test('Rate limiting test', async () => {
        const requests = Array(20).fill().map(() => 
            axios.get(`${REALTIME_URL}/health`).catch(err => err.response)
        );
        
        const responses = await Promise.all(requests);
        const rateLimitedResponses = responses.filter(r => r.status === 429);
        
        // Should have some rate limited responses
        expect(rateLimitedResponses.length).toBeGreaterThan(0);
    });

    test('CORS headers test', async () => {
        const response = await axios.options(`${REALTIME_URL}/health`, {
            headers: {
                'Origin': 'http://localhost:3001',
                'Access-Control-Request-Method': 'GET'
            }
        });
        
        expect(response.headers).toHaveProperty('access-control-allow-origin');
    });

    test('Security headers test', async () => {
        const response = await axios.get(`${REALTIME_URL}/health`);
        
        expect(response.headers).toHaveProperty('x-frame-options');
        expect(response.headers).toHaveProperty('x-content-type-options');
        expect(response.headers).toHaveProperty('x-xss-protection');
    });
});

describe('Performance Tests', () => {
    test('Response time test', async () => {
        const startTime = Date.now();
        const response = await axios.get(`${REALTIME_URL}/health`);
        const endTime = Date.now();
        
        expect(response.status).toBe(200);
        expect(endTime - startTime).toBeLessThan(1000); // Should respond within 1 second
    });

    test('Concurrent requests test', async () => {
        const requests = Array(10).fill().map(() => 
            axios.get(`${REALTIME_URL}/health`)
        );
        
        const startTime = Date.now();
        const responses = await Promise.all(requests);
        const endTime = Date.now();
        
        expect(responses.every(r => r.status === 200)).toBe(true);
        expect(endTime - startTime).toBeLessThan(5000); // Should handle 10 concurrent requests within 5 seconds
    });
});












