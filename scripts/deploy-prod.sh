#!/bin/bash

# Production Deployment Script for Voice Agent Orchestrator
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="voice-agent-orchestrator"
ENVIRONMENT="production"
BACKUP_DIR="/backups"
LOG_FILE="/var/log/deployment.log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    
    # Check if .env.prod exists
    if [[ ! -f "env.prod" ]]; then
        error "Production environment file (env.prod) not found"
    fi
    
    success "Prerequisites check passed"
}

# Backup current deployment
backup_current() {
    log "Creating backup of current deployment..."
    
    local backup_name="${PROJECT_NAME}-backup-$(date +%Y%m%d-%H%M%S)"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    mkdir -p "$backup_path"
    
    # Backup volumes
    if docker volume ls | grep -q "${PROJECT_NAME}"; then
        docker run --rm -v "${PROJECT_NAME}_redis_data:/data" -v "${backup_path}:/backup" alpine tar czf /backup/redis_data.tar.gz -C /data .
        docker run --rm -v "${PROJECT_NAME}_chroma_data:/data" -v "${backup_path}:/backup" alpine tar czf /backup/chroma_data.tar.gz -C /data .
    fi
    
    # Backup configuration
    cp -r nginx/ "$backup_path/" 2>/dev/null || true
    cp -r monitoring/ "$backup_path/" 2>/dev/null || true
    cp env.prod "$backup_path/" 2>/dev/null || true
    
    success "Backup created at $backup_path"
}

# Pull latest images
pull_images() {
    log "Pulling latest Docker images..."
    
    docker-compose -f docker-compose.prod.yml pull
    
    success "Images pulled successfully"
}

# Build custom images
build_images() {
    log "Building custom Docker images..."
    
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    success "Images built successfully"
}

# Run security scan
security_scan() {
    log "Running security scan on images..."
    
    # Check if trivy is available
    if command -v trivy &> /dev/null; then
        trivy image --exit-code 1 --severity HIGH,CRITICAL voice-agent-orchestrator_realtime:latest
        trivy image --exit-code 1 --severity HIGH,CRITICAL voice-agent-orchestrator_orchestrator:latest
        success "Security scan passed"
    else
        warning "Trivy not found, skipping security scan"
    fi
}

# Deploy services
deploy_services() {
    log "Deploying services..."
    
    # Stop existing services
    docker-compose -f docker-compose.prod.yml down --remove-orphans
    
    # Start services
    docker-compose -f docker-compose.prod.yml up -d
    
    success "Services deployed successfully"
}

# Wait for services to be healthy
wait_for_health() {
    log "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        log "Health check attempt $attempt/$max_attempts"
        
        # Check realtime service
        if curl -f http://localhost:3000/health > /dev/null 2>&1; then
            success "Realtime service is healthy"
        else
            warning "Realtime service not ready yet"
        fi
        
        # Check orchestrator service
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            success "Orchestrator service is healthy"
        else
            warning "Orchestrator service not ready yet"
        fi
        
        # Check if all services are healthy
        if curl -f http://localhost:3000/health > /dev/null 2>&1 && \
           curl -f http://localhost:8000/health > /dev/null 2>&1; then
            success "All services are healthy"
            return 0
        fi
        
        sleep 10
        ((attempt++))
    done
    
    error "Services failed to become healthy within timeout"
}

# Run smoke tests
smoke_tests() {
    log "Running smoke tests..."
    
    # Test health endpoints
    curl -f http://localhost:3000/health || error "Realtime health check failed"
    curl -f http://localhost:8000/health || error "Orchestrator health check failed"
    
    # Test API endpoints
    curl -f http://localhost:3000/voice/providers/current || error "Voice providers endpoint failed"
    
    # Test WebSocket connection
    # This would require a more sophisticated test
    
    success "Smoke tests passed"
}

# Cleanup old images
cleanup_images() {
    log "Cleaning up old Docker images..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove unused images older than 7 days
    docker image prune -a -f --filter "until=168h"
    
    success "Image cleanup completed"
}

# Send deployment notification
send_notification() {
    local status=$1
    local message=$2
    
    # This would integrate with your notification system
    # e.g., Slack, Teams, email, etc.
    log "Deployment $status: $message"
}

# Rollback function
rollback() {
    error "Deployment failed, initiating rollback..."
    
    # Stop current services
    docker-compose -f docker-compose.prod.yml down
    
    # Restore from backup
    local latest_backup=$(ls -t "$BACKUP_DIR" | head -n1)
    if [[ -n "$latest_backup" ]]; then
        log "Rolling back to $latest_backup"
        # Restore volumes and configuration
        # Implementation depends on your backup strategy
    fi
    
    # Start previous version
    docker-compose -f docker-compose.prod.yml up -d
    
    error "Rollback completed"
}

# Main deployment function
main() {
    log "Starting production deployment..."
    
    # Set up error handling
    trap 'rollback' ERR
    
    check_root
    check_prerequisites
    backup_current
    pull_images
    build_images
    security_scan
    deploy_services
    wait_for_health
    smoke_tests
    cleanup_images
    
    success "Production deployment completed successfully!"
    send_notification "SUCCESS" "Voice Agent Orchestrator deployed successfully"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --skip-backup    Skip backup creation"
            echo "  --skip-tests     Skip smoke tests"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Run main function
main










