#!/bin/bash

# Sovereign AI System Startup Script
# This script starts all components of the Sovereign AI system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/pids"

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ✗${NC} $1"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "$service_name is ready"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "$service_name failed to start after $max_attempts attempts"
            return 1
        fi
        
        sleep 2
        attempt=$((attempt + 1))
    done
}

# Function to start a service
start_service() {
    local service_name=$1
    local command=$2
    local port=$3
    local log_file="$LOG_DIR/${service_name}.log"
    local pid_file="$PID_DIR/${service_name}.pid"
    
    # Check if service is already running
    if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        print_warning "$service_name is already running (PID: $(cat "$pid_file"))"
        return 0
    fi
    
    # Check if port is in use
    if [ -n "$port" ] && check_port "$port"; then
        print_error "Port $port is already in use. Cannot start $service_name"
        return 1
    fi
    
    print_status "Starting $service_name..."
    
    # Start the service
    cd "$PROJECT_DIR"
    source "$VENV_PATH/bin/activate"
    
    nohup $command > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    
    # Give the service a moment to start
    sleep 3
    
    # Check if the service is still running
    if kill -0 $pid 2>/dev/null; then
        print_success "$service_name started successfully (PID: $pid)"
        return 0
    else
        print_error "$service_name failed to start"
        rm -f "$pid_file"
        return 1
    fi
}

# Function to check system prerequisites
check_prerequisites() {
    print_status "Checking system prerequisites..."
    
    # Check if we're in the right directory
    if [ ! -f "$PROJECT_DIR/chat_api.py" ]; then
        print_error "Cannot find chat_api.py. Please run this script from the Sovereign AI directory"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Virtual environment not found at $VENV_PATH"
        print_error "Please run: python3.11 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
    
    # Check if Ollama is running
    if ! systemctl is-active --quiet ollama; then
        print_warning "Ollama service is not running. Attempting to start..."
        sudo systemctl start ollama
        sleep 5
        
        if ! systemctl is-active --quiet ollama; then
            print_error "Failed to start Ollama service"
            exit 1
        fi
        print_success "Ollama service started"
    else
        print_success "Ollama service is running"
    fi
    
    # Check if AI model is available
    if ! ollama list | grep -q "tinyllama"; then
        print_warning "TinyLLama model not found. Downloading..."
        ollama pull tinyllama
        if [ $? -eq 0 ]; then
            print_success "TinyLLama model downloaded successfully"
        else
            print_error "Failed to download TinyLLama model"
            exit 1
        fi
    else
        print_success "TinyLLama model is available"
    fi
    
    # Check if Node.js dependencies are installed
    if [ ! -d "$PROJECT_DIR/sovereign-chat/node_modules" ]; then
        print_warning "Node.js dependencies not found. Installing..."
        cd "$PROJECT_DIR/sovereign-chat"
        pnpm install
        if [ $? -eq 0 ]; then
            print_success "Node.js dependencies installed successfully"
        else
            print_error "Failed to install Node.js dependencies"
            exit 1
        fi
        cd "$PROJECT_DIR"
    else
        print_success "Node.js dependencies are installed"
    fi
    
    print_success "All prerequisites satisfied"
}

# Function to initialize databases
initialize_databases() {
    print_status "Initializing databases..."
    
    cd "$PROJECT_DIR"
    source "$VENV_PATH/bin/activate"
    
    python3 -c "
import sys
sys.path.append('.')

try:
    from api_server.database import init_database
    print('Initializing main database...')
    init_database()
    print('Main database initialized successfully')
except Exception as e:
    print(f'Error initializing main database: {e}')
    sys.exit(1)

try:
    from time_capsule.backup_system import TimeCapsuleBackupSystem
    print('Initializing backup system...')
    backup_system = TimeCapsuleBackupSystem()
    print('Backup system initialized successfully')
except Exception as e:
    print(f'Error initializing backup system: {e}')
    sys.exit(1)

try:
    from time_capsule.recovery_manager import RecoveryManager
    print('Initializing recovery manager...')
    recovery_manager = RecoveryManager(backup_system)
    print('Recovery manager initialized successfully')
except Exception as e:
    print(f'Error initializing recovery manager: {e}')
    sys.exit(1)

print('All databases initialized successfully')
"
    
    if [ $? -eq 0 ]; then
        print_success "Databases initialized successfully"
    else
        print_error "Failed to initialize databases"
        exit 1
    fi
}

# Main startup function
main() {
    echo -e "${BLUE}"
    echo "=================================================================="
    echo "           Sovereign AI System Startup"
    echo "=================================================================="
    echo -e "${NC}"
    
    # Check prerequisites
    check_prerequisites
    
    # Initialize databases if needed
    if [ ! -f "$PROJECT_DIR/api-server/sovereign_ai.db" ]; then
        initialize_databases
    fi
    
    # Start services
    print_status "Starting Sovereign AI services..."
    
    # Start Chat API Server
    if start_service "chat_api" "python chat_api.py" "8003"; then
        wait_for_service "http://localhost:8003/health" "Chat API"
    else
        print_error "Failed to start Chat API server"
        exit 1
    fi
    
    # Start Curation API Server
    if start_service "curation_api" "python curation_api.py" "8002"; then
        wait_for_service "http://localhost:8002/health" "Curation API"
    else
        print_error "Failed to start Curation API server"
        exit 1
    fi
    
    # Start React Application
    cd "$PROJECT_DIR/sovereign-chat"
    if start_service "react_app" "pnpm run dev --host" "5174"; then
        wait_for_service "http://localhost:5174" "React Application"
    else
        print_error "Failed to start React application"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    # Final system health check
    print_status "Performing final system health check..."
    
    local all_healthy=true
    
    # Check Chat API
    if curl -s "http://localhost:8003/health" | grep -q "healthy"; then
        print_success "Chat API is healthy"
    else
        print_error "Chat API health check failed"
        all_healthy=false
    fi
    
    # Check Curation API
    if curl -s "http://localhost:8002/health" | grep -q "healthy"; then
        print_success "Curation API is healthy"
    else
        print_error "Curation API health check failed"
        all_healthy=false
    fi
    
    # Check React App
    if curl -s "http://localhost:5174" | grep -q "Sovereign AI"; then
        print_success "React Application is healthy"
    else
        print_error "React Application health check failed"
        all_healthy=false
    fi
    
    echo
    echo -e "${BLUE}=================================================================="
    
    if [ "$all_healthy" = true ]; then
        echo -e "${GREEN}🎉 Sovereign AI System Started Successfully! 🎉${NC}"
        echo
        echo -e "${GREEN}Access your Sovereign AI system at:${NC}"
        echo -e "  ${BLUE}Web Interface:${NC} http://localhost:5174"
        echo -e "  ${BLUE}Chat API:${NC}      http://localhost:8003"
        echo -e "  ${BLUE}Curation API:${NC}  http://localhost:8002"
        echo
        echo -e "${GREEN}System Status:${NC}"
        echo -e "  ${GREEN}✓${NC} Chat API Server running (PID: $(cat "$PID_DIR/chat_api.pid" 2>/dev/null || echo "unknown"))"
        echo -e "  ${GREEN}✓${NC} Curation API Server running (PID: $(cat "$PID_DIR/curation_api.pid" 2>/dev/null || echo "unknown"))"
        echo -e "  ${GREEN}✓${NC} React Application running (PID: $(cat "$PID_DIR/react_app.pid" 2>/dev/null || echo "unknown"))"
        echo -e "  ${GREEN}✓${NC} Ollama AI Model Service running"
        echo
        echo -e "${BLUE}Logs are available in:${NC} $LOG_DIR"
        echo -e "${BLUE}Process IDs stored in:${NC} $PID_DIR"
        echo
        echo -e "${YELLOW}To stop the system, run:${NC} ./scripts/stop_system.sh"
        echo -e "${YELLOW}To check system status:${NC} ./scripts/check_status.sh"
    else
        echo -e "${RED}❌ System startup completed with errors ❌${NC}"
        echo
        echo -e "${RED}Some services failed to start properly.${NC}"
        echo -e "${YELLOW}Check the logs in $LOG_DIR for more details.${NC}"
        echo -e "${YELLOW}You can try stopping and restarting the system:${NC}"
        echo -e "  ./scripts/stop_system.sh"
        echo -e "  ./scripts/start_system.sh"
        exit 1
    fi
    
    echo -e "${BLUE}==================================================================${NC}"
}

# Handle script interruption
cleanup() {
    print_warning "Startup interrupted. Cleaning up..."
    "$SCRIPT_DIR/stop_system.sh" >/dev/null 2>&1
    exit 1
}

trap cleanup INT TERM

# Run main function
main "$@"

