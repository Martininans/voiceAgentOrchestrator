#!/bin/bash

# Voice Agent Orchestrator - Deployment Script
# This script helps deploy your application to various cloud platforms

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="voice-agent-orchestrator"
REGISTRY="ghcr.io"
IMAGE_NAME="$REGISTRY/$GITHUB_REPOSITORY"

echo -e "${BLUE}🚀 Voice Agent Orchestrator - Deployment Script${NC}"
echo "=================================================="

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    print_status "Prerequisites check passed!"
}

# Function to build Docker images
build_images() {
    print_status "Building Docker images..."
    
    # Build Python Orchestrator
    print_status "Building Python Orchestrator..."
    docker build -t $IMAGE_NAME-orchestrator:latest ./backend-python-orchestrator
    
    # Build Node.js Realtime
    print_status "Building Node.js Realtime..."
    docker build -t $IMAGE_NAME-realtime:latest ./backend-node-realtime
    
    print_status "Docker images built successfully!"
}

# Function to push Docker images
push_images() {
    print_status "Pushing Docker images to registry..."
    
    # Login to registry (if needed)
    if [ "$REGISTRY" = "ghcr.io" ]; then
        echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_ACTOR --password-stdin
    fi
    
    # Push images
    docker push $IMAGE_NAME-orchestrator:latest
    docker push $IMAGE_NAME-realtime:latest
    
    print_status "Docker images pushed successfully!"
}

# Function to deploy with Docker Compose
deploy_local() {
    print_status "Deploying with Docker Compose..."
    
    # Check if .env files exist
    if [ ! -f "./backend-python-orchestrator/.env" ]; then
        print_warning "Python .env file not found. Creating from template..."
        cp ./backend-python-orchestrator/.env.example ./backend-python-orchestrator/.env 2>/dev/null || \
        echo "Please create backend-python-orchestrator/.env file manually"
    fi
    
    if [ ! -f "./backend-node-realtime/.env" ]; then
        print_warning "Node.js .env file not found. Creating from template..."
        cp ./backend-node-realtime/env-template.txt ./backend-node-realtime/.env 2>/dev/null || \
        echo "Please create backend-node-realtime/.env file manually"
    fi
    
    # Start services
    docker-compose up -d
    
    print_status "Local deployment completed!"
    echo -e "${BLUE}Services available at:${NC}"
    echo "  - Orchestrator: http://localhost:8000"
    echo "  - Realtime: http://localhost:3000"
    echo "  - ChromaDB: http://localhost:8001"
    echo "  - Redis: localhost:6379"
}

# Function to deploy to AWS ECS
deploy_aws() {
    print_status "Deploying to AWS ECS..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if task definition exists
    if [ ! -f "./deploy/aws-ecs/task-definition.json" ]; then
        print_error "AWS ECS task definition not found."
        exit 1
    fi
    
    # Register task definition
    aws ecs register-task-definition --cli-input-json file://deploy/aws-ecs/task-definition.json
    
    print_status "AWS ECS deployment completed!"
}

# Function to deploy to Google Cloud Run
deploy_gcp() {
    print_status "Deploying to Google Cloud Run..."
    
    # Check gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        print_error "Google Cloud SDK is not installed. Please install it first."
        exit 1
    fi
    
    # Check if service config exists
    if [ ! -f "./deploy/google-cloud-run/service.yaml" ]; then
        print_error "Google Cloud Run service configuration not found."
        exit 1
    fi
    
    # Deploy services
    gcloud run services replace deploy/google-cloud-run/service.yaml
    
    print_status "Google Cloud Run deployment completed!"
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  build       Build Docker images"
    echo "  push        Push Docker images to registry"
    echo "  local       Deploy locally with Docker Compose"
    echo "  aws         Deploy to AWS ECS"
    echo "  gcp         Deploy to Google Cloud Run"
    echo "  all         Build, push, and deploy (requires environment setup)"
    echo "  help        Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  GITHUB_REPOSITORY    GitHub repository (e.g., username/repo)"
    echo "  GITHUB_TOKEN         GitHub token for registry access"
    echo "  GITHUB_ACTOR         GitHub username"
    echo ""
    echo "Examples:"
    echo "  $0 local              # Deploy locally"
    echo "  $0 build              # Build images only"
    echo "  $0 aws                # Deploy to AWS ECS"
}

# Main script logic
case "${1:-help}" in
    "build")
        check_prerequisites
        build_images
        ;;
    "push")
        check_prerequisites
        push_images
        ;;
    "local")
        check_prerequisites
        deploy_local
        ;;
    "aws")
        check_prerequisites
        build_images
        push_images
        deploy_aws
        ;;
    "gcp")
        check_prerequisites
        build_images
        push_images
        deploy_gcp
        ;;
    "all")
        check_prerequisites
        build_images
        push_images
        print_warning "Please choose a deployment target: local, aws, or gcp"
        ;;
    "help"|*)
        show_help
        ;;
esac 