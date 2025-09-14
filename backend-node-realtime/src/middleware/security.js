const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const cors = require('cors');
const config = require('../config');

// Security headers middleware
const securityHeaders = helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            scriptSrc: ["'self'"],
            imgSrc: ["'self'", "data:", "https:"],
            connectSrc: ["'self'", "wss:", "ws:"],
            fontSrc: ["'self'"],
            objectSrc: ["'none'"],
            mediaSrc: ["'self'"],
            frameSrc: ["'none'"],
        },
    },
    crossOriginEmbedderPolicy: false,
    hsts: {
        maxAge: 31536000,
        includeSubDomains: true,
        preload: true
    }
});

// CORS configuration
const corsOptions = {
    origin: function (origin, callback) {
        // Allow requests with no origin (mobile apps, curl, etc.)
        if (!origin) return callback(null, true);
        
        const allowedOrigins = config.server.cors?.allowedOrigins || ['http://localhost:3000', 'http://localhost:3001'];
        
        if (allowedOrigins.includes(origin)) {
            callback(null, true);
        } else {
            callback(new Error('Not allowed by CORS'));
        }
    },
    credentials: config.server.cors?.credentials || true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
    maxAge: 86400 // 24 hours
};

// Rate limiting
const createRateLimit = (windowMs, max, message) => {
    return rateLimit({
        windowMs,
        max,
        message: {
            error: message,
            retryAfter: Math.ceil(windowMs / 1000)
        },
        standardHeaders: true,
        legacyHeaders: false,
        handler: (req, res) => {
            res.status(429).json({
                error: message,
                retryAfter: Math.ceil(windowMs / 1000),
                timestamp: new Date().toISOString()
            });
        }
    });
};

// Different rate limits for different endpoints
const generalLimiter = createRateLimit(
    15 * 60 * 1000, // 15 minutes
    100, // 100 requests per window
    'Too many requests from this IP, please try again later'
);

const strictLimiter = createRateLimit(
    15 * 60 * 1000, // 15 minutes
    20, // 20 requests per window
    'Too many requests from this IP, please try again later'
);

const voiceLimiter = createRateLimit(
    60 * 1000, // 1 minute
    10, // 10 requests per minute
    'Too many voice requests from this IP, please try again later'
);

// Input validation middleware
const validateInput = (req, res, next) => {
    // Remove any potentially dangerous characters
    const sanitizeInput = (obj) => {
        if (typeof obj === 'string') {
            return obj.replace(/[<>\"'%;()&+]/g, '');
        }
        if (typeof obj === 'object' && obj !== null) {
            const sanitized = {};
            for (const [key, value] of Object.entries(obj)) {
                sanitized[key] = sanitizeInput(value);
            }
            return sanitized;
        }
        return obj;
    };

    if (req.body) {
        req.body = sanitizeInput(req.body);
    }
    if (req.query) {
        req.query = sanitizeInput(req.query);
    }
    if (req.params) {
        req.params = sanitizeInput(req.params);
    }

    next();
};

// Request logging middleware
const requestLogger = (req, res, next) => {
    const start = Date.now();
    const originalSend = res.send;
    
    res.send = function(data) {
        const duration = Date.now() - start;
        const logData = {
            method: req.method,
            url: req.url,
            statusCode: res.statusCode,
            duration: `${duration}ms`,
            userAgent: req.get('User-Agent'),
            ip: req.ip || req.connection.remoteAddress,
            timestamp: new Date().toISOString()
        };
        
        if (res.statusCode >= 400) {
            console.error('HTTP Error:', logData);
        } else {
            console.log('HTTP Request:', logData);
        }
        
        originalSend.call(this, data);
    };
    
    next();
};

// Error handling middleware
const errorHandler = (err, req, res, next) => {
    console.error('Unhandled Error:', {
        error: err.message,
        stack: err.stack,
        url: req.url,
        method: req.method,
        ip: req.ip,
        timestamp: new Date().toISOString()
    });

    // Don't leak error details in production
    const isDevelopment = process.env.NODE_ENV === 'development';
    
    res.status(err.status || 500).json({
        error: isDevelopment ? err.message : 'Internal Server Error',
        timestamp: new Date().toISOString(),
        requestId: req.id || 'unknown'
    });
};

// 404 handler
const notFoundHandler = (req, res) => {
    res.status(404).json({
        error: 'Endpoint not found',
        path: req.url,
        method: req.method,
        timestamp: new Date().toISOString()
    });
};

module.exports = {
    securityHeaders,
    cors: cors(corsOptions),
    generalLimiter,
    strictLimiter,
    voiceLimiter,
    validateInput,
    requestLogger,
    errorHandler,
    notFoundHandler
};












