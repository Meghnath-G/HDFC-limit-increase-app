#!/bin/bash

# Production Deployment Script for HDFC Card Limit Increase System
# This script provides automated deployment with comprehensive validation and rollback capabilities

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/hdfc/deployment_$(date +%Y%m%d_%H%M%S).log"
ROLLBACK_DIR="/backup/hdfc/rollback"
DEPLOYMENT_LOCK="/tmp/hdfc_deployment.lock"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Deployment configuration
ENVIRONMENT=${ENVIRONMENT:-production}
DEPLOY_TYPE=${DEPLOY_TYPE:-blue_green}
HEALTH_CHECK_RETRIES=${HEALTH_CHECK_RETRIES:-10}
HEALTH_CHECK_INTERVAL=${HEALTH_CHECK_INTERVAL:-30}

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
    
    case $level in
        ERROR)
            echo -e "${RED}[ERROR]${NC} ${message}" >&2
            ;;
        WARN)
            echo -e "${YELLOW}[WARN]${NC} ${message}"
            ;;
        INFO)
            echo -e "${BLUE}[INFO]${NC} ${message}"
            ;;
        SUCCESS)
            echo -e "${GREEN}[SUCCESS]${NC} ${message}"
            ;;
    esac
}

# Error handling
cleanup() {
    log "INFO" "Cleaning up deployment resources..."
    
    # Remove deployment lock
    if [[ -f "$DEPLOYMENT_LOCK" ]]; then
        rm -f "$DEPLOYMENT_LOCK"
        log "INFO" "Deployment lock removed"
    fi
    
    # Stop any background processes
    jobs -p | xargs -r kill
}

error_exit() {
    local error_message="$1"
    log "ERROR" "Deployment failed: $error_message"
    cleanup
    exit 1
}

trap cleanup EXIT
trap 'error_exit "Script interrupted"' INT TERM

# Check if deployment is already in progress
check_deployment_lock() {
    if [[ -f "$DEPLOYMENT_LOCK" ]]; then
        local lock_pid=$(cat "$DEPLOYMENT_LOCK")
        if kill -0 "$lock_pid" 2>/dev/null; then
            error_exit "Deployment already in progress (PID: $lock_pid)"
        else
            log "WARN" "Stale deployment lock found, removing..."
            rm -f "$DEPLOYMENT_LOCK"
        fi
    fi
    
    echo $$ > "$DEPLOYMENT_LOCK"
    log "INFO" "Deployment lock acquired"
}

# Pre-deployment validation
validate_environment() {
    log "INFO" "Validating deployment environment..."
    
    # Check required environment variables
    local required_vars=(
        "DB_PASSWORD"
        "SENDGRID_API_KEY"
        "FIREBASE_PRIVATE_KEY"
        "TWILIO_ACCOUNT_SID"
        "TWILIO_AUTH_TOKEN"
        "ONESIGNAL_APP_ID"
        "ENCRYPTION_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error_exit "Required environment variable $var is not set"
        fi
    done
    
    # Check disk space
    local available_space=$(df / | tail -1 | awk '{print $4}')
    local required_space=1048576  # 1GB in KB
    
    if [[ $available_space -lt $required_space ]]; then
        error_exit "Insufficient disk space: ${available_space}KB available, ${required_space}KB required"
    fi
    
    # Check system resources
    local memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [[ $memory_usage -gt 90 ]]; then
        log "WARN" "High memory usage detected: ${memory_usage}%"
    fi
    
    log "SUCCESS" "Environment validation completed"
}

# Database backup before deployment
create_pre_deployment_backup() {
    log "INFO" "Creating pre-deployment database backup..."
    
    local backup_name="pre_deployment_$(date +%Y%m%d_%H%M%S)"
    
    # Use Django management command for backup
    cd "$PROJECT_DIR"
    python manage.py backup_database --type=full --name="$backup_name" || {
        error_exit "Pre-deployment backup failed"
    }
    
    log "SUCCESS" "Pre-deployment backup created: $backup_name"
    echo "$backup_name" > "$ROLLBACK_DIR/last_backup.txt"
}

# Git deployment
deploy_code() {
    log "INFO" "Deploying application code..."
    
    local git_branch=${GIT_BRANCH:-main}
    local git_commit=${GIT_COMMIT:-HEAD}
    
    cd "$PROJECT_DIR"
    
    # Fetch latest changes
    git fetch origin "$git_branch" || error_exit "Failed to fetch git changes"
    
    # Store current commit for rollback
    local current_commit=$(git rev-parse HEAD)
    echo "$current_commit" > "$ROLLBACK_DIR/last_commit.txt"
    
    # Checkout new code
    git checkout "$git_commit" || error_exit "Failed to checkout commit $git_commit"
    
    # Install/update dependencies
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt || error_exit "Failed to install Python dependencies"
    fi
    
    log "SUCCESS" "Code deployment completed"
}

# Run database migrations
run_migrations() {
    log "INFO" "Running database migrations..."
    
    cd "$PROJECT_DIR"
    
    # Check for pending migrations
    local pending_migrations=$(python manage.py showmigrations --plan | grep '\[ \]' | wc -l)
    
    if [[ $pending_migrations -eq 0 ]]; then
        log "INFO" "No pending migrations found"
        return 0
    fi
    
    log "INFO" "Found $pending_migrations pending migrations"
    
    # Run migrations with timeout
    timeout 1800 python manage.py migrate --noinput || {
        error_exit "Database migration failed"
    }
    
    log "SUCCESS" "Database migrations completed"
}

# Collect static files
collect_static_files() {
    log "INFO" "Collecting static files..."
    
    cd "$PROJECT_DIR"
    
    # Collect static files
    python manage.py collectstatic --noinput --clear || {
        error_exit "Static files collection failed"
    }
    
    log "SUCCESS" "Static files collection completed"
}

# Restart application services
restart_services() {
    log "INFO" "Restarting application services..."
    
    local services=(
        "hdfc-card-limit-gunicorn"
        "hdfc-card-limit-celery"
        "hdfc-card-limit-celery-beat"
        "nginx"
    )
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log "INFO" "Restarting service: $service"
            systemctl restart "$service" || {
                log "WARN" "Failed to restart service: $service"
            }
        else
            log "INFO" "Starting service: $service"
            systemctl start "$service" || {
                log "WARN" "Failed to start service: $service"
            }
        fi
    done
    
    # Wait for services to start
    sleep 10
    
    log "SUCCESS" "Service restart completed"
}

# Health check
perform_health_check() {
    log "INFO" "Performing health checks..."
    
    local health_url="https://card-limit-api.hdfc.com/health/"
    local retry_count=0
    
    while [[ $retry_count -lt $HEALTH_CHECK_RETRIES ]]; do
        local http_status=$(curl -s -o /dev/null -w "%{http_code}" "$health_url" || echo "000")
        
        if [[ "$http_status" == "200" ]]; then
            log "SUCCESS" "Health check passed"
            return 0
        else
            log "WARN" "Health check failed (attempt $((retry_count + 1))/$HEALTH_CHECK_RETRIES): HTTP $http_status"
            retry_count=$((retry_count + 1))
            
            if [[ $retry_count -lt $HEALTH_CHECK_RETRIES ]]; then
                sleep "$HEALTH_CHECK_INTERVAL"
            fi
        fi
    done
    
    error_exit "Health check failed after $HEALTH_CHECK_RETRIES attempts"
}

# Smoke tests
run_smoke_tests() {
    log "INFO" "Running smoke tests..."
    
    cd "$PROJECT_DIR"
    
    # Run basic API tests
    python manage.py test tests.smoke --verbosity=2 || {
        log "WARN" "Smoke tests failed, but deployment continues"
        return 1
    }
    
    log "SUCCESS" "Smoke tests completed"
}

# Blue-Green deployment
blue_green_deployment() {
    log "INFO" "Performing blue-green deployment..."
    
    local current_env=$(curl -s "http://localhost:8080/current-env" || echo "unknown")
    local target_env="green"
    
    if [[ "$current_env" == "green" ]]; then
        target_env="blue"
    fi
    
    log "INFO" "Current environment: $current_env, Target environment: $target_env"
    
    # Deploy to target environment
    export DJANGO_ENVIRONMENT="$target_env"
    
    # Update target environment
    restart_services
    
    # Health check on target environment
    local target_health_url="http://localhost:808${target_env: -1}/health/"
    
    if ! perform_health_check_on_url "$target_health_url"; then
        error_exit "Health check failed on target environment: $target_env"
    fi
    
    # Switch traffic to target environment
    log "INFO" "Switching traffic to $target_env environment"
    
    # Update load balancer configuration (implementation depends on your setup)
    update_load_balancer_config "$target_env" || {
        error_exit "Failed to switch traffic to $target_env environment"
    }
    
    log "SUCCESS" "Blue-green deployment completed"
}

# Load balancer configuration update
update_load_balancer_config() {
    local target_env=$1
    
    # This is a placeholder - implement based on your load balancer
    # For example, for nginx:
    local nginx_config="/etc/nginx/sites-available/hdfc-card-limit"
    local temp_config="/tmp/nginx_config_$$"
    
    # Update upstream configuration
    sed "s/server 127.0.0.1:808[0-9]/server 127.0.0.1:808${target_env: -1}/" "$nginx_config" > "$temp_config"
    
    # Validate nginx configuration
    nginx -t -c "$temp_config" || {
        rm -f "$temp_config"
        return 1
    }
    
    # Apply configuration
    cp "$temp_config" "$nginx_config"
    rm -f "$temp_config"
    
    # Reload nginx
    systemctl reload nginx
    
    return 0
}

# Health check on specific URL
perform_health_check_on_url() {
    local url=$1
    local retry_count=0
    
    while [[ $retry_count -lt $HEALTH_CHECK_RETRIES ]]; do
        local http_status=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
        
        if [[ "$http_status" == "200" ]]; then
            return 0
        else
            retry_count=$((retry_count + 1))
            if [[ $retry_count -lt $HEALTH_CHECK_RETRIES ]]; then
                sleep "$HEALTH_CHECK_INTERVAL"
            fi
        fi
    done
    
    return 1
}

# Rollback function
rollback_deployment() {
    log "INFO" "Starting deployment rollback..."
    
    # Rollback database
    if [[ -f "$ROLLBACK_DIR/last_backup.txt" ]]; then
        local backup_name=$(cat "$ROLLBACK_DIR/last_backup.txt")
        log "INFO" "Rolling back database to backup: $backup_name"
        
        cd "$PROJECT_DIR"
        python manage.py restore_database --name="$backup_name" || {
            log "ERROR" "Database rollback failed"
        }
    fi
    
    # Rollback code
    if [[ -f "$ROLLBACK_DIR/last_commit.txt" ]]; then
        local last_commit=$(cat "$ROLLBACK_DIR/last_commit.txt")
        log "INFO" "Rolling back code to commit: $last_commit"
        
        cd "$PROJECT_DIR"
        git checkout "$last_commit" || {
            log "ERROR" "Code rollback failed"
        }
    fi
    
    # Restart services
    restart_services
    
    log "SUCCESS" "Rollback completed"
}

# Post-deployment tasks
post_deployment_tasks() {
    log "INFO" "Running post-deployment tasks..."
    
    cd "$PROJECT_DIR"
    
    # Clear cache
    python manage.py clear_cache || log "WARN" "Cache clear failed"
    
    # Warm up cache
    python manage.py warm_cache || log "WARN" "Cache warm-up failed"
    
    # Update search indexes (if using)
    # python manage.py update_index || log "WARN" "Search index update failed"
    
    # Send deployment notification
    python manage.py send_deployment_notification --status=success || {
        log "WARN" "Deployment notification failed"
    }
    
    log "SUCCESS" "Post-deployment tasks completed"
}

# Main deployment function
main() {
    log "INFO" "Starting HDFC Card Limit System deployment..."
    log "INFO" "Environment: $ENVIRONMENT, Deploy Type: $DEPLOY_TYPE"
    
    # Ensure log directory exists
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$ROLLBACK_DIR"
    
    # Pre-deployment checks
    check_deployment_lock
    validate_environment
    
    # Create backup
    create_pre_deployment_backup
    
    # Deployment steps
    deploy_code
    run_migrations
    collect_static_files
    
    # Service management based on deployment type
    if [[ "$DEPLOY_TYPE" == "blue_green" ]]; then
        blue_green_deployment
    else
        restart_services
        perform_health_check
    fi
    
    # Post-deployment
    run_smoke_tests
    post_deployment_tasks
    
    log "SUCCESS" "Deployment completed successfully!"
    
    # Display deployment summary
    echo ""
    echo "========================================"
    echo "    DEPLOYMENT SUMMARY"
    echo "========================================"
    echo "Environment: $ENVIRONMENT"
    echo "Deploy Type: $DEPLOY_TYPE"
    echo "Git Commit: $(git rev-parse HEAD)"
    echo "Deployment Time: $(date)"
    echo "Log File: $LOG_FILE"
    echo "========================================"
}

# Help function
show_help() {
    cat << EOF
HDFC Card Limit System Deployment Script

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -e, --environment ENV   Set deployment environment (default: production)
    -t, --type TYPE         Set deployment type: rolling|blue_green (default: blue_green)
    -r, --rollback          Perform rollback to previous deployment
    --dry-run              Perform dry run without actual deployment
    --health-check-only    Only perform health checks

Environment Variables:
    ENVIRONMENT             Deployment environment
    DEPLOY_TYPE            Deployment type
    GIT_BRANCH             Git branch to deploy (default: main)
    GIT_COMMIT             Specific git commit to deploy (default: HEAD)
    HEALTH_CHECK_RETRIES   Number of health check retries (default: 10)
    HEALTH_CHECK_INTERVAL  Health check interval in seconds (default: 30)

Examples:
    # Standard production deployment
    $0

    # Blue-green deployment
    $0 --type blue_green

    # Rollback deployment
    $0 --rollback

    # Dry run
    $0 --dry-run
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--type)
            DEPLOY_TYPE="$2"
            shift 2
            ;;
        -r|--rollback)
            rollback_deployment
            exit 0
            ;;
        --dry-run)
            log "INFO" "Dry run mode - no actual deployment will be performed"
            DRY_RUN=true
            shift
            ;;
        --health-check-only)
            perform_health_check
            exit 0
            ;;
        *)
            log "ERROR" "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run main deployment if not in dry run mode
if [[ "${DRY_RUN:-false}" == "true" ]]; then
    log "INFO" "Dry run completed - no changes made"
else
    main
fi