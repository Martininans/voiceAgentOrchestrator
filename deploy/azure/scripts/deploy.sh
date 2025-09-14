#!/bin/bash

# Azure Deployment Script for Voice Agent Orchestrator
# This script automates the deployment process to Azure

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TERRAFORM_DIR="$PROJECT_ROOT/deploy/azure/terraform"

# Default values
ENVIRONMENT="production"
RESOURCE_GROUP="voice-agent-rg"
LOCATION="East US"
APP_NAME="voice-agent-orchestrator"
SKIP_TERRAFORM=false
SKIP_BUILD=false
SKIP_DEPLOY=false
DRY_RUN=false

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
Azure Deployment Script for Voice Agent Orchestrator

Usage: $0 [OPTIONS]

Options:
    -e, --environment ENV     Environment (development|staging|production) [default: production]
    -g, --resource-group RG   Azure resource group name [default: voice-agent-rg]
    -l, --location LOC        Azure location [default: East US]
    -a, --app-name NAME       Application name [default: voice-agent-orchestrator]
    -s, --skip-terraform      Skip Terraform infrastructure deployment
    -b, --skip-build          Skip Docker image build
    -d, --skip-deploy         Skip application deployment
    -n, --dry-run             Show what would be done without executing
    -h, --help                Show this help message

Examples:
    $0                                    # Deploy to production
    $0 -e staging                         # Deploy to staging
    $0 -e development --skip-terraform    # Deploy app only to development
    $0 --dry-run                          # Show what would be done

EOF
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check Azure CLI login
    if ! az account show &> /dev/null; then
        log_error "Not logged in to Azure CLI. Please run 'az login' first."
        exit 1
    fi
    
    log_success "All prerequisites are met"
}

deploy_infrastructure() {
    if [ "$SKIP_TERRAFORM" = true ]; then
        log_info "Skipping Terraform infrastructure deployment"
        return
    fi
    
    log_info "Deploying infrastructure with Terraform..."
    
    cd "$TERRAFORM_DIR"
    
    # Initialize Terraform
    log_info "Initializing Terraform..."
    terraform init
    
    # Plan Terraform deployment
    log_info "Planning Terraform deployment..."
    terraform plan \
        -var="resource_group_name=$RESOURCE_GROUP" \
        -var="location=$LOCATION" \
        -var="environment=$ENVIRONMENT" \
        -var="app_name=$APP_NAME" \
        -out="terraform.tfplan"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "Dry run mode - showing Terraform plan:"
        terraform show terraform.tfplan
        return
    fi
    
    # Apply Terraform deployment
    log_info "Applying Terraform deployment..."
    terraform apply -auto-approve terraform.tfplan
    
    # Get outputs
    log_info "Getting Terraform outputs..."
    ACR_LOGIN_SERVER=$(terraform output -raw container_registry_login_server)
    ACR_USERNAME=$(terraform output -raw container_registry_admin_username)
    ACR_PASSWORD=$(terraform output -raw container_registry_admin_password)
    AKS_CLUSTER_NAME=$(terraform output -raw aks_cluster_name)
    KEY_VAULT_URI=$(terraform output -raw key_vault_uri)
    
    log_success "Infrastructure deployed successfully"
}

build_images() {
    if [ "$SKIP_BUILD" = true ]; then
        log_info "Skipping Docker image build"
        return
    fi
    
    log_info "Building Docker images..."
    
    # Get ACR details from Terraform
    cd "$TERRAFORM_DIR"
    ACR_LOGIN_SERVER=$(terraform output -raw container_registry_login_server)
    ACR_USERNAME=$(terraform output -raw container_registry_admin_username)
    ACR_PASSWORD=$(terraform output -raw container_registry_admin_password)
    
    # Login to ACR
    log_info "Logging in to Azure Container Registry..."
    echo "$ACR_PASSWORD" | docker login "$ACR_LOGIN_SERVER" --username "$ACR_USERNAME" --password-stdin
    
    # Build and push orchestrator image
    log_info "Building orchestrator image..."
    cd "$PROJECT_ROOT/backend-python-orchestrator"
    docker build -t "$ACR_LOGIN_SERVER/voice-agent-orchestrator:latest" .
    docker push "$ACR_LOGIN_SERVER/voice-agent-orchestrator:latest"
    
    # Build and push realtime image
    log_info "Building realtime image..."
    cd "$PROJECT_ROOT/backend-node-realtime"
    docker build -t "$ACR_LOGIN_SERVER/voice-agent-realtime:latest" .
    docker push "$ACR_LOGIN_SERVER/voice-agent-realtime:latest"
    
    log_success "Docker images built and pushed successfully"
}

deploy_application() {
    if [ "$SKIP_DEPLOY" = true ]; then
        log_info "Skipping application deployment"
        return
    fi
    
    log_info "Deploying application to AKS..."
    
    # Get AKS details from Terraform
    cd "$TERRAFORM_DIR"
    AKS_CLUSTER_NAME=$(terraform output -raw aks_cluster_name)
    ACR_LOGIN_SERVER=$(terraform output -raw container_registry_login_server)
    ACR_USERNAME=$(terraform output -raw container_registry_admin_username)
    ACR_PASSWORD=$(terraform output -raw container_registry_admin_password)
    
    # Get AKS credentials
    log_info "Getting AKS credentials..."
    az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$AKS_CLUSTER_NAME" --overwrite-existing
    
    # Create namespace
    log_info "Creating Kubernetes namespace..."
    kubectl create namespace voice-agent --dry-run=client -o yaml | kubectl apply -f -
    
    # Create ACR secret
    log_info "Creating ACR secret in Kubernetes..."
    kubectl create secret docker-registry acr-secret \
        --docker-server="$ACR_LOGIN_SERVER" \
        --docker-username="$ACR_USERNAME" \
        --docker-password="$ACR_PASSWORD" \
        --namespace=voice-agent \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy application
    log_info "Deploying application manifests..."
    kubectl apply -f "$PROJECT_ROOT/deploy/azure/k8s-production.yaml"
    
    # Wait for deployments
    log_info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/voice-agent-orchestrator -n voice-agent
    kubectl wait --for=condition=available --timeout=300s deployment/voice-agent-realtime -n voice-agent
    
    # Get service URLs
    log_info "Getting service URLs..."
    ORCHESTRATOR_IP=$(kubectl get service voice-agent-orchestrator-service -n voice-agent -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    REALTIME_IP=$(kubectl get service voice-agent-realtime-service -n voice-agent -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    log_success "Application deployed successfully"
    log_info "Orchestrator URL: http://$ORCHESTRATOR_IP"
    log_info "Realtime URL: http://$REALTIME_IP"
}

run_health_checks() {
    log_info "Running health checks..."
    
    # Get service URLs
    cd "$TERRAFORM_DIR"
    AKS_CLUSTER_NAME=$(terraform output -raw aks_cluster_name)
    
    # Get AKS credentials
    az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$AKS_CLUSTER_NAME" --overwrite-existing
    
    # Get service IPs
    ORCHESTRATOR_IP=$(kubectl get service voice-agent-orchestrator-service -n voice-agent -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    REALTIME_IP=$(kubectl get service voice-agent-realtime-service -n voice-agent -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    # Wait for IPs to be assigned
    while [ -z "$ORCHESTRATOR_IP" ] || [ -z "$REALTIME_IP" ]; do
        log_info "Waiting for load balancer IPs to be assigned..."
        sleep 10
        ORCHESTRATOR_IP=$(kubectl get service voice-agent-orchestrator-service -n voice-agent -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        REALTIME_IP=$(kubectl get service voice-agent-realtime-service -n voice-agent -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    done
    
    # Check orchestrator health
    log_info "Checking orchestrator health..."
    if curl -f "http://$ORCHESTRATOR_IP/health" > /dev/null 2>&1; then
        log_success "Orchestrator is healthy"
    else
        log_error "Orchestrator health check failed"
        return 1
    fi
    
    # Check realtime health
    log_info "Checking realtime health..."
    if curl -f "http://$REALTIME_IP/health" > /dev/null 2>&1; then
        log_success "Realtime service is healthy"
    else
        log_error "Realtime health check failed"
        return 1
    fi
    
    log_success "All health checks passed"
}

cleanup() {
    log_info "Cleaning up temporary files..."
    cd "$TERRAFORM_DIR"
    rm -f terraform.tfplan
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -a|--app-name)
            APP_NAME="$2"
            shift 2
            ;;
        -s|--skip-terraform)
            SKIP_TERRAFORM=true
            shift
            ;;
        -b|--skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -d|--skip-deploy)
            SKIP_DEPLOY=true
            shift
            ;;
        -n|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    log_info "Starting Azure deployment for Voice Agent Orchestrator"
    log_info "Environment: $ENVIRONMENT"
    log_info "Resource Group: $RESOURCE_GROUP"
    log_info "Location: $LOCATION"
    log_info "App Name: $APP_NAME"
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY RUN MODE - No changes will be made"
    fi
    
    # Set up trap for cleanup
    trap cleanup EXIT
    
    # Execute deployment steps
    check_prerequisites
    deploy_infrastructure
    build_images
    deploy_application
    
    if [ "$DRY_RUN" = false ]; then
        run_health_checks
    fi
    
    log_success "Deployment completed successfully!"
    
    if [ "$DRY_RUN" = false ]; then
        log_info "Next steps:"
        log_info "1. Configure your secrets in Azure Key Vault"
        log_info "2. Update your DNS records to point to the load balancer IPs"
        log_info "3. Configure SSL certificates for HTTPS"
        log_info "4. Set up monitoring and alerting"
    fi
}

# Run main function
main "$@"
