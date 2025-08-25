# Use Node.js 18 Alpine for smaller size
FROM node:18-alpine

# Set environment variables
ENV NODE_ENV=production \
    NPM_CONFIG_LOGLEVEL=warn

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    curl \
    dumb-init

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy application code
COPY . .

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs \
    && adduser -S nodejs -u 1001
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Run the application
CMD ["node", "src/index.js"] 