const config = require('../config');

class HealthChecker {
    constructor() {
        this.checks = new Map();
        this.startTime = Date.now();
    }

    addCheck(name, checkFunction, timeout = 5000) {
        this.checks.set(name, {
            check: checkFunction,
            timeout,
            lastCheck: null,
            lastResult: null
        });
    }

    async runCheck(name) {
        const check = this.checks.get(name);
        if (!check) {
            throw new Error(`Health check '${name}' not found`);
        }

        try {
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Health check timeout')), check.timeout);
            });

            const result = await Promise.race([
                check.check(),
                timeoutPromise
            ]);

            check.lastCheck = Date.now();
            check.lastResult = { status: 'healthy', ...result };
            return check.lastResult;
        } catch (error) {
            check.lastCheck = Date.now();
            check.lastResult = { 
                status: 'unhealthy', 
                error: error.message,
                timestamp: new Date().toISOString()
            };
            return check.lastResult;
        }
    }

    async runAllChecks() {
        const results = {};
        const checkPromises = Array.from(this.checks.keys()).map(async (name) => {
            try {
                results[name] = await this.runCheck(name);
            } catch (error) {
                results[name] = {
                    status: 'unhealthy',
                    error: error.message,
                    timestamp: new Date().toISOString()
                };
            }
        });

        await Promise.allSettled(checkPromises);
        return results;
    }

    getOverallStatus(checks) {
        const unhealthyChecks = Object.values(checks).filter(check => check.status === 'unhealthy');
        return {
            status: unhealthyChecks.length === 0 ? 'healthy' : 'unhealthy',
            healthy: Object.values(checks).filter(check => check.status === 'healthy').length,
            unhealthy: unhealthyChecks.length,
            total: Object.keys(checks).length
        };
    }

    getUptime() {
        return Date.now() - this.startTime;
    }
}

// Create health checker instance
const healthChecker = new HealthChecker();

// Add database health check
healthChecker.addCheck('database', async () => {
    try {
        const dataBackend = require('../data');
        const backend = await dataBackend.getDataBackend();
        await backend.testConnection();
        return { message: 'Database connection successful' };
    } catch (error) {
        throw new Error(`Database connection failed: ${error.message}`);
    }
});

// Add orchestrator health check
healthChecker.addCheck('orchestrator', async () => {
    try {
        const axios = require('axios');
        const response = await axios.get(`${config.orchestrator.url}/health`, {
            timeout: 5000
        });
        
        if (response.status === 200) {
            return { 
                message: 'Orchestrator is healthy',
                orchestratorStatus: response.data
            };
        } else {
            throw new Error(`Orchestrator returned status ${response.status}`);
        }
    } catch (error) {
        throw new Error(`Orchestrator health check failed: ${error.message}`);
    }
});

// Add Redis health check (if enabled)
if (!process.env.DISABLE_OPTIMIZATIONS) {
    healthChecker.addCheck('redis', async () => {
        try {
            const redis = require('redis');
            const client = redis.createClient({
                url: config.redis.url
            });
            
            await client.connect();
            await client.ping();
            await client.quit();
            
            return { message: 'Redis connection successful' };
        } catch (error) {
            throw new Error(`Redis connection failed: ${error.message}`);
        }
    });
}

// Add voice provider health check
healthChecker.addCheck('voiceProvider', async () => {
    try {
        const voiceAgent = require('../voiceAgent');
        const status = await voiceAgent.getStatus();
        
        if (status.status === 'operational') {
            return { 
                message: 'Voice provider is operational',
                provider: status.provider,
                capabilities: status.capabilities
            };
        } else {
            throw new Error(`Voice provider status: ${status.status}`);
        }
    } catch (error) {
        throw new Error(`Voice provider health check failed: ${error.message}`);
    }
});

// Add memory usage check
healthChecker.addCheck('memory', async () => {
    const memUsage = process.memoryUsage();
    const memUsageMB = {
        rss: Math.round(memUsage.rss / 1024 / 1024),
        heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024),
        heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024),
        external: Math.round(memUsage.external / 1024 / 1024)
    };

    // Consider unhealthy if heap usage is over 500MB
    if (memUsageMB.heapUsed > 500) {
        throw new Error(`High memory usage: ${memUsageMB.heapUsed}MB`);
    }

    return { 
        message: 'Memory usage is normal',
        usage: memUsageMB
    };
});

// Health check endpoints
const healthRoutes = (app) => {
    // Basic health check
    app.get('/health', async (request, reply) => {
        try {
            const checks = await healthChecker.runAllChecks();
            const overallStatus = healthChecker.getOverallStatus(checks);
            
            const response = {
                status: overallStatus.status,
                timestamp: new Date().toISOString(),
                uptime: healthChecker.getUptime(),
                version: process.env.npm_package_version || '1.0.0',
                environment: process.env.NODE_ENV || 'development',
                checks: overallStatus,
                details: checks
            };

            const statusCode = overallStatus.status === 'healthy' ? 200 : 503;
            reply.status(statusCode).send(response);
        } catch (error) {
            reply.status(503).send({
                status: 'unhealthy',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    });

    // Detailed health check
    app.get('/health/detailed', async (request, reply) => {
        try {
            const checks = await healthChecker.runAllChecks();
            const overallStatus = healthChecker.getOverallStatus(checks);
            
            const response = {
                status: overallStatus.status,
                timestamp: new Date().toISOString(),
                uptime: healthChecker.getUptime(),
                version: process.env.npm_package_version || '1.0.0',
                environment: process.env.NODE_ENV || 'development',
                nodeVersion: process.version,
                platform: process.platform,
                arch: process.arch,
                checks: overallStatus,
                details: checks,
                system: {
                    memory: process.memoryUsage(),
                    cpu: process.cpuUsage(),
                    uptime: process.uptime()
                }
            };

            const statusCode = overallStatus.status === 'healthy' ? 200 : 503;
            reply.status(statusCode).send(response);
        } catch (error) {
            reply.status(503).send({
                status: 'unhealthy',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    });

    // Individual health check
    app.get('/health/:checkName', async (request, reply) => {
        try {
            const { checkName } = request.params;
            const result = await healthChecker.runCheck(checkName);
            
            const statusCode = result.status === 'healthy' ? 200 : 503;
            reply.status(statusCode).send(result);
        } catch (error) {
            reply.status(404).send({
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    });

    // Readiness probe
    app.get('/ready', async (request, reply) => {
        try {
            const checks = await healthChecker.runAllChecks();
            const overallStatus = healthChecker.getOverallStatus(checks);
            
            if (overallStatus.status === 'healthy') {
                reply.status(200).send({ status: 'ready' });
            } else {
                reply.status(503).send({ 
                    status: 'not ready',
                    unhealthyChecks: Object.entries(checks)
                        .filter(([_, check]) => check.status === 'unhealthy')
                        .map(([name, check]) => ({ name, error: check.error }))
                });
            }
        } catch (error) {
            reply.status(503).send({
                status: 'not ready',
                error: error.message
            });
        }
    });

    // Liveness probe
    app.get('/live', async (request, reply) => {
        reply.status(200).send({ 
            status: 'alive',
            timestamp: new Date().toISOString(),
            uptime: healthChecker.getUptime()
        });
    });
};

module.exports = {
    healthChecker,
    healthRoutes
};












