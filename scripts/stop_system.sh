#!/bin/bash

# Sovereign AI System Shutdown Script
# This script stops all components of the Sovereign AI system

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
PID_DIR="$PROJECT_DIR/pids"

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

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [ ! -f "$pid_file" ]; then
        print_warning "$service_name PID file not found"
        return 0
    fi
    
    local pid=$(cat "$pid_file")
    
    if ! kill -0 "$pid" 2>/dev/null; then
        print_warning "$service_name is not running (stale PID file)"
        rm -f "$pid_file"
        return 0
    fi
    
    print_status "Stopping $service_name (PID: $pid)..."
    
    # Try graceful shutdown first
    if kill -TERM "$pid" 2>/dev/null; then
        # Wait up to 10 seconds for graceful shutdown
        local count=0
        while [ $count -lt 10 ] && kill -0 "$pid" 2>/dev/null; do
            sleep 1
            count=$((count + 1))
        done
        
        # Check if process is still running
        if kill -0 "$pid" 2>/dev/null; then
            print_warning "$service_name did not stop gracefully, forcing shutdown..."
            if kill -KILL "$pid" 2>/dev/null; then
                print_success "$service_name force stopped"
            else
                print_error "Failed to force stop $service_name"
                return 1
            fi
        else
            print_success "$service_name stopped gracefully"
        fi
    else
        print_error "Failed to send termination signal to $service_name"
        return 1
    fi
    
    # Remove PID file
    rm -f "$pid_file"
    return 0
}

# Function to stop services by port
stop_by_port() {
    local port=$1
    local service_name=$2
    
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    
    if [ -z "$pids" ]; then
        print_warning "No processes found on port $port"
        return 0
    fi
    
    print_status "Stopping processes on port $port ($service_name)..."
    
    for pid in $pids; do
        if kill -0 "$pid" 2>/dev/null; then
            print_status "Stopping process $pid on port $port..."
            
            # Try graceful shutdown first
            if kill -TERM "$pid" 2>/dev/null; then
                # Wait up to 5 seconds for graceful shutdown
                local count=0
                while [ $count -lt 5 ] && kill -0 "$pid" 2>/dev/null; do
                    sleep 1
                    count=$((count + 1))
                done
                
                # Force kill if still running
                if kill -0 "$pid" 2>/dev/null; then
                    kill -KILL "$pid" 2>/dev/null || true
                fi
            fi
        fi
    done
    
    # Verify port is free
    if lsof -ti:$port >/dev/null 2>&1; then
        print_error "Port $port is still in use after cleanup"
        return 1
    else
        print_success "Port $port is now free"
        return 0
    fi
}

# Function to stop processes by name pattern
stop_by_pattern() {
    local pattern=$1
    local service_name=$2
    
    local pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    
    if [ -z "$pids" ]; then
        print_warning "No $service_name processes found"
        return 0
    fi
    
    print_status "Stopping $service_name processes..."
    
    for pid in $pids; do
        if kill -0 "$pid" 2>/dev/null; then
            print_status "Stopping $service_name process $pid..."
            
            # Try graceful shutdown first
            if kill -TERM "$pid" 2>/dev/null; then
                # Wait up to 5 seconds for graceful shutdown
                local count=0
                while [ $count -lt 5 ] && kill -0 "$pid" 2>/dev/null; do
                    sleep 1
                    count=$((count + 1))
                done
                
                # Force kill if still running
                if kill -0 "$pid" 2>/dev/null; then
                    kill -KILL "$pid" 2>/dev/null || true
                fi
            fi
        fi
    done
    
    print_success "$service_name processes stopped"
    return 0
}

# Function to clean up temporary files
cleanup_files() {
    print_status "Cleaning up temporary files..."
    
    # Remove PID files
    if [ -d "$PID_DIR" ]; then
        rm -f "$PID_DIR"/*.pid
        print_success "PID files cleaned up"
    fi
    
    # Clean up any socket files
    find "$PROJECT_DIR" -name "*.sock" -type f -delete 2>/dev/null || true
    
    # Clean up any temporary lock files
    find "$PROJECT_DIR" -name "*.lock" -type f -delete 2>/dev/null || true
    
    print_success "Temporary files cleaned up"
}

# Main shutdown function
main() {
    echo -e "${BLUE}"
    echo "=================================================================="
    echo "           Sovereign AI System Shutdown"
    echo "=================================================================="
    echo -e "${NC}"
    
    print_status "Stopping Sovereign AI services..."
    
    # Stop services using PID files first
    stop_service "react_app"
    stop_service "curation_api"
    stop_service "chat_api"
    
    # Stop any remaining processes by port (fallback)
    print_status "Checking for remaining processes on service ports..."
    stop_by_port "5174" "React Application"
    stop_by_port "8002" "Curation API"
    stop_by_port "8003" "Chat API"
    
    # Stop any remaining processes by pattern (fallback)
    print_status "Checking for remaining processes by pattern..."
    stop_by_pattern "chat_api.py" "Chat API"
    stop_by_pattern "curation_api.py" "Curation API"
    stop_by_pattern "pnpm run dev" "React Application"
    
    # Clean up temporary files
    cleanup_files
    
    # Final verification
    print_status "Performing final verification..."
    
    local all_stopped=true
    
    # Check if any services are still running
    if lsof -ti:8003 >/dev/null 2>&1; then
        print_error "Chat API (port 8003) is still running"
        all_stopped=false
    fi
    
    if lsof -ti:8002 >/dev/null 2>&1; then
        print_error "Curation API (port 8002) is still running"
        all_stopped=false
    fi
    
    if lsof -ti:5174 >/dev/null 2>&1; then
        print_error "React Application (port 5174) is still running"
        all_stopped=false
    fi
    
    # Check for any remaining Python processes
    local python_processes=$(pgrep -f "chat_api.py\|curation_api.py" 2>/dev/null || true)
    if [ -n "$python_processes" ]; then
        print_error "Some Python API processes are still running: $python_processes"
        all_stopped=false
    fi
    
    # Check for any remaining Node.js processes
    local node_processes=$(pgrep -f "pnpm run dev" 2>/dev/null || true)
    if [ -n "$node_processes" ]; then
        print_error "Some Node.js processes are still running: $node_processes"
        all_stopped=false
    fi
    
    echo
    echo -e "${BLUE}=================================================================="
    
    if [ "$all_stopped" = true ]; then
        echo -e "${GREEN}✅ Sovereign AI System Stopped Successfully! ✅${NC}"
        echo
        echo -e "${GREEN}All services have been stopped:${NC}"
        echo -e "  ${GREEN}✓${NC} Chat API Server stopped"
        echo -e "  ${GREEN}✓${NC} Curation API Server stopped"
        echo -e "  ${GREEN}✓${NC} React Application stopped"
        echo -e "  ${GREEN}✓${NC} All ports freed (8003, 8002, 5174)"
        echo -e "  ${GREEN}✓${NC} Temporary files cleaned up"
        echo
        echo -e "${BLUE}Note:${NC} Ollama service is still running (system service)"
        echo -e "${YELLOW}To stop Ollama:${NC} sudo systemctl stop ollama"
        echo -e "${YELLOW}To start the system again:${NC} ./scripts/start_system.sh"
    else
        echo -e "${RED}⚠️  System shutdown completed with warnings ⚠️${NC}"
        echo
        echo -e "${RED}Some processes may still be running.${NC}"
        echo -e "${YELLOW}You may need to manually kill remaining processes:${NC}"
        echo -e "  sudo lsof -ti:8003,8002,5174 | xargs -r sudo kill -9"
        echo -e "  sudo pkill -f 'chat_api.py|curation_api.py|pnpm run dev'"
        echo
        echo -e "${YELLOW}Check running processes:${NC}"
        echo -e "  ps aux | grep -E '(chat_api|curation_api|pnpm)'"
        echo -e "  sudo lsof -i:8003,8002,5174"
    fi
    
    echo -e "${BLUE}==================================================================${NC}"
}

# Handle script interruption
cleanup() {
    print_warning "Shutdown interrupted. Forcing cleanup..."
    
    # Force kill all related processes
    pkill -f "chat_api.py" 2>/dev/null || true
    pkill -f "curation_api.py" 2>/dev/null || true
    pkill -f "pnpm run dev" 2>/dev/null || true
    
    # Clean up files
    rm -f "$PID_DIR"/*.pid 2>/dev/null || true
    
    exit 1
}

trap cleanup INT TERM

# Run main function
main "$@"

