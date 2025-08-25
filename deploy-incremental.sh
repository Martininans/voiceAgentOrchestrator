#!/bin/bash

# Voice Agent Orchestrator - Incremental Deployment Script
# This script allows you to deploy backend services while frontend continues working

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STAGING_PORTS=(
    "orchestrator:8001"
    "realtime:3001"
    "redis:6380"
    "chromadb:8002"
)

PRODUCTION_PORTS=(
    "orchestrator:8000"
    "realtime:3000"
    "redis:6379"
    "chromadb:8001"
)

echo -e "${BLUE}🚀 Voice Agent Orchestrator - Incremental Deployment${NC}"
echo "=================================================="

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $port is already in use${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Port $port is available${NC}"
        return 0
    fi
}

# Function to check environment variables
check_env() {
    echo -e "${YELLOW}🔍 Checking environment variables...${NC}"
    
    required_vars=(
        "SUPABASE_URL"
        "SUPABASE_ANON_KEY"
        "JWT_SECRET"
        "OPENAI_API_KEY"
    )
    
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        echo -e "${RED}❌ Missing required environment variables:${NC}"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo -e "${YELLOW}💡 Create .env file from env-template.txt${NC}"
        return 1
    else
        echo -e "${GREEN}✅ All required environment variables are set${NC}"
        return 0
    fi
}

# Function to deploy staging environment
deploy_staging() {
    echo -e "${BLUE}📦 Deploying to staging environment...${NC}"
    
    # Check if staging ports are available
    for port_info in "${STAGING_PORTS[@]}"; do
        service=$(echo $port_info | cut -d: -f1)
        port=$(echo $port_info | cut -d: -f2)
        check_port $port
    done
    
    # Deploy staging services
    echo -e "${YELLOW}🐳 Starting staging services...${NC}"
    docker-compose -f docker-compose.staging.yml up -d
    
    echo -e "${GREEN}✅ Staging deployment complete!${NC}"
    echo -e "${BLUE}📋 Staging URLs:${NC}"
    echo "  - Orchestrator: http://localhost:8001"
    echo "  - Realtime: http://localhost:3001"
    echo "  - Health Check: http://localhost:8001/health"
    echo "  - WebSocket: ws://localhost:3001/ws"
}

# Function to test staging environment
test_staging() {
    echo -e "${BLUE}🧪 Testing staging environment...${NC}"
    
    # Test orchestrator health
    echo -e "${YELLOW}🔍 Testing orchestrator health...${NC}"
    if curl -f http://localhost:8001/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Orchestrator is healthy${NC}"
    else
        echo -e "${RED}❌ Orchestrator health check failed${NC}"
        return 1
    fi
    
    # Test realtime health
    echo -e "${YELLOW}🔍 Testing realtime health...${NC}"
    if curl -f http://localhost:3001/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Realtime is healthy${NC}"
    else
        echo -e "${RED}❌ Realtime health check failed${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ All staging tests passed!${NC}"
    return 0
}

# Function to deploy production
deploy_production() {
    echo -e "${BLUE}🚀 Deploying to production...${NC}"
    
    # Check if production ports are available
    for port_info in "${PRODUCTION_PORTS[@]}"; do
        service=$(echo $port_info | cut -d: -f1)
        port=$(echo $port_info | cut -d: -f2)
        check_port $port
    done
    
    # Deploy production services
    echo -e "${YELLOW}🐳 Starting production services...${NC}"
    docker-compose up -d
    
    echo -e "${GREEN}✅ Production deployment complete!${NC}"
    echo -e "${BLUE}📋 Production URLs:${NC}"
    echo "  - Orchestrator: http://localhost:8000"
    echo "  - Realtime: http://localhost:3000"
    echo "  - Health Check: http://localhost:8000/health"
    echo "  - WebSocket: ws://localhost:3000/ws"
}

# Function to rollback
rollback() {
    echo -e "${YELLOW}🔄 Rolling back...${NC}"
    
    # Stop all services
    docker-compose down
    docker-compose -f docker-compose.staging.yml down
    
    echo -e "${GREEN}✅ Rollback complete${NC}"
}

# Function to show status
show_status() {
    echo -e "${BLUE}📊 Service Status${NC}"
    echo "=================="
    
    echo -e "${YELLOW}🐳 Docker Compose Services:${NC}"
    docker-compose ps
    
    echo -e "${YELLOW}🐳 Staging Services:${NC}"
    docker-compose -f docker-compose.staging.yml ps
}

# Main script logic
case "${1:-help}" in
    "staging")
        check_env && deploy_staging
        ;;
    "test")
        test_staging
        ;;
    "production")
        check_env && deploy_production
        ;;
    "rollback")
        rollback
        ;;
    "status")
        show_status
        ;;
    "full-deploy")
        check_env && deploy_staging && test_staging && deploy_production
        ;;
    "help"|*)
        echo -e "${BLUE}Usage: $0 [command]${NC}"
        echo ""
        echo "Commands:"
        echo "  staging     - Deploy to staging environment (ports 8001, 3001)"
        echo "  test        - Test staging environment"
        echo "  production  - Deploy to production environment (ports 8000, 3000)"
        echo "  rollback    - Stop all services and rollback"
        echo "  status      - Show service status"
        echo "  full-deploy - Complete deployment: staging → test → production"
        echo "  help        - Show this help message"
        echo ""
        echo -e "${YELLOW}💡 Example workflow:${NC}"
        echo "  1. $0 staging    # Deploy to staging"
        echo "  2. Test with your frontend using staging URLs"
        echo "  3. $0 production # Deploy to production"
        echo "  4. Switch frontend to production URLs"
        ;;
esac 