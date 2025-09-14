#!/bin/bash

# Backup Script for Voice Agent Orchestrator
set -e

# Configuration
PROJECT_NAME="voice-agent-orchestrator"
BACKUP_DIR="/backups"
RETENTION_DAYS=30
LOG_FILE="/var/log/backup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Create backup directory
create_backup_dir() {
    local backup_name="${PROJECT_NAME}-backup-$(date +%Y%m%d-%H%M%S)"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    mkdir -p "$backup_path"
    echo "$backup_path"
}

# Backup database
backup_database() {
    local backup_path=$1
    
    log "Backing up database..."
    
    # Check if using Azure PostgreSQL
    if [[ -n "$AZURE_PG_CONNECTION_STRING" ]]; then
        # Use pg_dump for Azure PostgreSQL
        pg_dump "$AZURE_PG_CONNECTION_STRING" > "$backup_path/database.sql"
        success "Database backup completed"
    else
        # Backup Supabase data (if applicable)
        warning "Database backup not configured for current setup"
    fi
}

# Backup Redis data
backup_redis() {
    local backup_path=$1
    
    log "Backing up Redis data..."
    
    if docker volume ls | grep -q "${PROJECT_NAME}_redis_data"; then
        docker run --rm \
            -v "${PROJECT_NAME}_redis_data:/data" \
            -v "$backup_path:/backup" \
            alpine tar czf /backup/redis_data.tar.gz -C /data .
        success "Redis backup completed"
    else
        warning "Redis volume not found"
    fi
}

# Backup ChromaDB data
backup_chroma() {
    local backup_path=$1
    
    log "Backing up ChromaDB data..."
    
    if docker volume ls | grep -q "${PROJECT_NAME}_chroma_data"; then
        docker run --rm \
            -v "${PROJECT_NAME}_chroma_data:/data" \
            -v "$backup_path:/backup" \
            alpine tar czf /backup/chroma_data.tar.gz -C /data .
        success "ChromaDB backup completed"
    else
        warning "ChromaDB volume not found"
    fi
}

# Backup configuration files
backup_config() {
    local backup_path=$1
    
    log "Backing up configuration files..."
    
    # Backup nginx configuration
    if [[ -d "nginx" ]]; then
        cp -r nginx/ "$backup_path/"
    fi
    
    # Backup monitoring configuration
    if [[ -d "monitoring" ]]; then
        cp -r monitoring/ "$backup_path/"
    fi
    
    # Backup environment files
    if [[ -f "env.prod" ]]; then
        cp env.prod "$backup_path/"
    fi
    
    # Backup docker-compose files
    cp docker-compose.prod.yml "$backup_path/" 2>/dev/null || true
    cp docker-compose.yml "$backup_path/" 2>/dev/null || true
    
    success "Configuration backup completed"
}

# Backup application logs
backup_logs() {
    local backup_path=$1
    
    log "Backing up application logs..."
    
    # Create logs directory in backup
    mkdir -p "$backup_path/logs"
    
    # Copy container logs
    if docker ps | grep -q "${PROJECT_NAME}_realtime"; then
        docker logs "${PROJECT_NAME}_realtime" > "$backup_path/logs/realtime.log" 2>&1 || true
    fi
    
    if docker ps | grep -q "${PROJECT_NAME}_orchestrator"; then
        docker logs "${PROJECT_NAME}_orchestrator" > "$backup_path/logs/orchestrator.log" 2>&1 || true
    fi
    
    success "Logs backup completed"
}

# Upload backup to cloud storage
upload_to_cloud() {
    local backup_path=$1
    
    log "Uploading backup to cloud storage..."
    
    # Check if Azure CLI is available and configured
    if command -v az &> /dev/null && az account show &> /dev/null; then
        local container_name="backups"
        local blob_name="$(basename "$backup_path").tar.gz"
        
        # Create tar archive
        tar czf "${backup_path}.tar.gz" -C "$(dirname "$backup_path")" "$(basename "$backup_path")"
        
        # Upload to Azure Blob Storage
        az storage blob upload \
            --account-name "$AZURE_STORAGE_ACCOUNT" \
            --container-name "$container_name" \
            --name "$blob_name" \
            --file "${backup_path}.tar.gz" \
            --auth-mode login
        
        success "Backup uploaded to Azure Blob Storage"
        
        # Clean up local tar file
        rm "${backup_path}.tar.gz"
    else
        warning "Azure CLI not configured, skipping cloud upload"
    fi
}

# Clean up old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    # Remove local backups older than retention period
    find "$BACKUP_DIR" -type d -name "${PROJECT_NAME}-backup-*" -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
    
    # Remove cloud backups older than retention period
    if command -v az &> /dev/null && az account show &> /dev/null; then
        local cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d)
        az storage blob list \
            --account-name "$AZURE_STORAGE_ACCOUNT" \
            --container-name "backups" \
            --query "[?properties.lastModified < '$cutoff_date'].name" \
            --output tsv | xargs -I {} az storage blob delete \
            --account-name "$AZURE_STORAGE_ACCOUNT" \
            --container-name "backups" \
            --name {} \
            --auth-mode login 2>/dev/null || true
    fi
    
    success "Old backups cleaned up"
}

# Verify backup integrity
verify_backup() {
    local backup_path=$1
    
    log "Verifying backup integrity..."
    
    # Check if backup directory exists and has content
    if [[ ! -d "$backup_path" ]]; then
        error "Backup directory not found"
    fi
    
    # Check if essential files exist
    local essential_files=("nginx" "monitoring" "env.prod")
    for file in "${essential_files[@]}"; do
        if [[ ! -e "$backup_path/$file" ]]; then
            warning "Essential file $file not found in backup"
        fi
    done
    
    success "Backup verification completed"
}

# Main backup function
main() {
    log "Starting backup process..."
    
    # Create backup directory
    local backup_path=$(create_backup_dir)
    
    # Perform backups
    backup_database "$backup_path"
    backup_redis "$backup_path"
    backup_chroma "$backup_path"
    backup_config "$backup_path"
    backup_logs "$backup_path"
    
    # Verify backup
    verify_backup "$backup_path"
    
    # Upload to cloud (optional)
    if [[ "$UPLOAD_TO_CLOUD" == "true" ]]; then
        upload_to_cloud "$backup_path"
    fi
    
    # Clean up old backups
    cleanup_old_backups
    
    success "Backup process completed successfully!"
    log "Backup location: $backup_path"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --upload-cloud)
            UPLOAD_TO_CLOUD=true
            shift
            ;;
        --retention-days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --upload-cloud     Upload backup to cloud storage"
            echo "  --retention-days   Number of days to retain backups (default: 30)"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Run main function
main












