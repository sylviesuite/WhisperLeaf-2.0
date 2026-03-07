#!/bin/bash

# Sovereign AI System Status Check Script
# This script checks the status of all Sovereign AI components

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_DIR="$PROJECT_DIR/pids"
LOG_DIR="$PROJECT_DIR/logs"

# Function to print colored output
print_header() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

# Function to check if a service is running
check_service_status() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    local port=$2
    local health_url=$3
    
    echo -e "\n${BLUE}━━━ $service_name Status ━━━${NC}"
    
    # Check PID file
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            print_success "Process running (PID: $pid)"
            
            # Get process info
            local process_info=$(ps -p "$pid" -o pid,ppid,etime,pcpu,pmem,cmd --no-headers 2>/dev/null || echo "Process info unavailable")
            print_info "Process details: $process_info"
        else
            print_error "Process not running (stale PID file)"
            print_info "PID file contains: $pid"
        fi
    else
        print_warning "PID file not found"
    fi
    
    # Check port
    if [ -n "$port" ]; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            local port_pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
            print_success "Port $port is in use (PID: $port_pid)"
        else
            print_error "Port $port is not in use"
        fi
    fi
    
    # Check health endpoint
    if [ -n "$health_url" ]; then
        local response=$(curl -s -w "%{http_code}" "$health_url" 2>/dev/null || echo "000")
        local http_code="${response: -3}"
        local body="${response%???}"
        
        if [ "$http_code" = "200" ]; then
            print_success "Health check passed (HTTP $http_code)"
            if echo "$body" | grep -q "healthy"; then
                print_success "Service reports healthy status"
            else
                print_warning "Service responded but status unclear"
            fi
        else
            print_error "Health check failed (HTTP $http_code)"
        fi
    fi
    
    # Check log file
    local log_file="$LOG_DIR/${service_name}.log"
    if [ -f "$log_file" ]; then
        local log_size=$(du -h "$log_file" | cut -f1)
        local last_modified=$(stat -c %y "$log_file" | cut -d. -f1)
        print_info "Log file: $log_file ($log_size, modified: $last_modified)"
        
        # Show recent errors
        local recent_errors=$(tail -n 100 "$log_file" | grep -i error | tail -n 3 || true)
        if [ -n "$recent_errors" ]; then
            print_warning "Recent errors in log:"
            echo "$recent_errors" | while read -r line; do
                echo -e "  ${RED}→${NC} $line"
            done
        fi
    else
        print_warning "Log file not found: $log_file"
    fi
}

# Function to check system resources
check_system_resources() {
    echo -e "\n${BLUE}━━━ System Resources ━━━${NC}"
    
    # CPU usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    if (( $(echo "$cpu_usage < 80" | bc -l) )); then
        print_success "CPU usage: ${cpu_usage}%"
    else
        print_warning "CPU usage: ${cpu_usage}% (high)"
    fi
    
    # Memory usage
    local memory_info=$(free -h | grep "Mem:")
    local memory_used=$(echo $memory_info | awk '{print $3}')
    local memory_total=$(echo $memory_info | awk '{print $2}')
    local memory_percent=$(free | grep "Mem:" | awk '{printf "%.1f", $3/$2 * 100.0}')
    
    if (( $(echo "$memory_percent < 80" | bc -l) )); then
        print_success "Memory usage: $memory_used / $memory_total (${memory_percent}%)"
    else
        print_warning "Memory usage: $memory_used / $memory_total (${memory_percent}%) (high)"
    fi
    
    # Disk usage
    local disk_info=$(df -h "$PROJECT_DIR" | tail -1)
    local disk_used=$(echo $disk_info | awk '{print $3}')
    local disk_total=$(echo $disk_info | awk '{print $2}')
    local disk_percent=$(echo $disk_info | awk '{print $5}' | cut -d'%' -f1)
    
    if (( disk_percent < 80 )); then
        print_success "Disk usage: $disk_used / $disk_total (${disk_percent}%)"
    else
        print_warning "Disk usage: $disk_used / $disk_total (${disk_percent}%) (high)"
    fi
    
    # Load average
    local load_avg=$(uptime | awk -F'load average:' '{print $2}')
    print_info "Load average:$load_avg"
    
    # Uptime
    local uptime_info=$(uptime -p)
    print_info "System uptime: $uptime_info"
}

# Function to check Ollama status
check_ollama_status() {
    echo -e "\n${BLUE}━━━ Ollama AI Service ━━━${NC}"
    
    # Check systemd service
    if systemctl is-active --quiet ollama; then
        print_success "Ollama service is active"
        
        local service_status=$(systemctl status ollama --no-pager -l | head -n 10)
        print_info "Service status:"
        echo "$service_status" | while read -r line; do
            echo -e "  ${CYAN}→${NC} $line"
        done
    else
        print_error "Ollama service is not active"
        print_info "Try: sudo systemctl start ollama"
    fi
    
    # Check Ollama API
    if curl -s "http://localhost:11434/api/tags" >/dev/null 2>&1; then
        print_success "Ollama API is responding"
        
        # List available models
        local models=$(curl -s "http://localhost:11434/api/tags" | jq -r '.models[].name' 2>/dev/null || echo "Unable to parse models")
        if [ "$models" != "Unable to parse models" ] && [ -n "$models" ]; then
            print_success "Available models:"
            echo "$models" | while read -r model; do
                echo -e "  ${GREEN}→${NC} $model"
            done
        else
            print_warning "No models found or unable to list models"
        fi
    else
        print_error "Ollama API is not responding"
    fi
}

# Function to check database status
check_database_status() {
    echo -e "\n${BLUE}━━━ Database Status ━━━${NC}"
    
    local databases=(
        "api-server/sovereign_ai.db:Main Database"
        "time_capsule/metadata/backup_metadata.db:Backup Metadata"
        "time_capsule/recovery/recovery.db:Recovery Database"
    )
    
    for db_info in "${databases[@]}"; do
        local db_path="${db_info%%:*}"
        local db_name="${db_info##*:}"
        local full_path="$PROJECT_DIR/$db_path"
        
        if [ -f "$full_path" ]; then
            local db_size=$(du -h "$full_path" | cut -f1)
            local last_modified=$(stat -c %y "$full_path" | cut -d. -f1)
            print_success "$db_name: $db_size (modified: $last_modified)"
            
            # Check database integrity
            if sqlite3 "$full_path" "PRAGMA integrity_check;" | grep -q "ok"; then
                print_success "$db_name integrity check passed"
            else
                print_error "$db_name integrity check failed"
            fi
            
            # Count tables
            local table_count=$(sqlite3 "$full_path" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo "0")
            print_info "$db_name has $table_count tables"
        else
            print_error "$db_name not found: $full_path"
        fi
    done
}

# Function to check network connectivity
check_network_status() {
    echo -e "\n${BLUE}━━━ Network Connectivity ━━━${NC}"
    
    # Check internet connectivity
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        print_success "Internet connectivity available"
    else
        print_error "No internet connectivity"
    fi
    
    # Check DNS resolution
    if nslookup google.com >/dev/null 2>&1; then
        print_success "DNS resolution working"
    else
        print_error "DNS resolution failed"
    fi
    
    # Check if required ports are available
    local ports=("8003:Chat API" "8002:Curation API" "5174:React App" "11434:Ollama")
    
    for port_info in "${ports[@]}"; do
        local port="${port_info%%:*}"
        local service="${port_info##*:}"
        
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_success "Port $port ($service) is in use"
        else
            print_warning "Port $port ($service) is not in use"
        fi
    done
}

# Function to show recent activity
show_recent_activity() {
    echo -e "\n${BLUE}━━━ Recent Activity ━━━${NC}"
    
    # Show recent log entries from all services
    local log_files=("$LOG_DIR"/*.log)
    
    if [ ${#log_files[@]} -gt 0 ] && [ -f "${log_files[0]}" ]; then
        print_info "Recent log entries (last 10 minutes):"
        
        # Get timestamp from 10 minutes ago
        local ten_minutes_ago=$(date -d '10 minutes ago' '+%Y-%m-%d %H:%M:%S')
        
        for log_file in "${log_files[@]}"; do
            if [ -f "$log_file" ]; then
                local service_name=$(basename "$log_file" .log)
                local recent_entries=$(awk -v since="$ten_minutes_ago" '$0 >= since' "$log_file" | tail -n 5)
                
                if [ -n "$recent_entries" ]; then
                    echo -e "\n  ${CYAN}$service_name:${NC}"
                    echo "$recent_entries" | while read -r line; do
                        echo -e "    ${CYAN}→${NC} $line"
                    done
                fi
            fi
        done
    else
        print_warning "No log files found"
    fi
}

# Function to generate status summary
generate_summary() {
    echo -e "\n${BLUE}━━━ Status Summary ━━━${NC}"
    
    local services_running=0
    local services_total=3
    
    # Check each service
    if [ -f "$PID_DIR/chat_api.pid" ] && kill -0 "$(cat "$PID_DIR/chat_api.pid")" 2>/dev/null; then
        services_running=$((services_running + 1))
    fi
    
    if [ -f "$PID_DIR/curation_api.pid" ] && kill -0 "$(cat "$PID_DIR/curation_api.pid")" 2>/dev/null; then
        services_running=$((services_running + 1))
    fi
    
    if [ -f "$PID_DIR/react_app.pid" ] && kill -0 "$(cat "$PID_DIR/react_app.pid")" 2>/dev/null; then
        services_running=$((services_running + 1))
    fi
    
    # Overall status
    if [ $services_running -eq $services_total ]; then
        print_success "All services are running ($services_running/$services_total)"
        echo -e "\n${GREEN}🎉 Sovereign AI System is fully operational! 🎉${NC}"
        echo -e "${GREEN}Access your system at: http://localhost:5174${NC}"
    elif [ $services_running -gt 0 ]; then
        print_warning "Some services are running ($services_running/$services_total)"
        echo -e "\n${YELLOW}⚠️  Sovereign AI System is partially operational${NC}"
        echo -e "${YELLOW}Some services may need to be restarted${NC}"
    else
        print_error "No services are running ($services_running/$services_total)"
        echo -e "\n${RED}❌ Sovereign AI System is not running${NC}"
        echo -e "${YELLOW}Start the system with: ./scripts/start_system.sh${NC}"
    fi
    
    # Quick actions
    echo -e "\n${BLUE}Quick Actions:${NC}"
    echo -e "  ${CYAN}Start system:${NC} ./scripts/start_system.sh"
    echo -e "  ${CYAN}Stop system:${NC}  ./scripts/stop_system.sh"
    echo -e "  ${CYAN}View logs:${NC}    tail -f logs/*.log"
    echo -e "  ${CYAN}Health check:${NC} curl http://localhost:8003/health"
}

# Main status check function
main() {
    echo -e "${BLUE}"
    echo "=================================================================="
    echo "           Sovereign AI System Status Check"
    echo "=================================================================="
    echo -e "${NC}"
    
    # System information
    print_header "System Information"
    print_info "Hostname: $(hostname)"
    print_info "OS: $(lsb_release -d | cut -f2)"
    print_info "Kernel: $(uname -r)"
    print_info "Architecture: $(uname -m)"
    print_info "Current time: $(date)"
    print_info "Project directory: $PROJECT_DIR"
    
    # Check system resources
    check_system_resources
    
    # Check Ollama
    check_ollama_status
    
    # Check databases
    check_database_status
    
    # Check network
    check_network_status
    
    # Check individual services
    check_service_status "Chat API" "8003" "http://localhost:8003/health"
    check_service_status "Curation API" "8002" "http://localhost:8002/health"
    check_service_status "React App" "5174" "http://localhost:5174"
    
    # Show recent activity
    show_recent_activity
    
    # Generate summary
    generate_summary
    
    echo -e "\n${BLUE}==================================================================${NC}"
}

# Handle script interruption
cleanup() {
    echo -e "\n${YELLOW}Status check interrupted${NC}"
    exit 1
}

trap cleanup INT TERM

# Run main function
main "$@"

