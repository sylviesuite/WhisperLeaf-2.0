#!/bin/bash

# WhisperLeaf Automated Installation Script
# This script sets up WhisperLeaf with all dependencies and configuration

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root for security reasons"
   exit 1
fi

log "Starting WhisperLeaf installation..."

# Check system requirements
log "Checking system requirements..."

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 11) else 1)'; then
        success "Python $PYTHON_VERSION found"
    else
        error "Python 3.11+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    error "Python 3 not found. Please install Python 3.11 or higher"
    exit 1
fi

# Check pip
if ! command -v pip3 &> /dev/null; then
    error "pip3 not found. Please install pip"
    exit 1
fi

# Check available disk space (require at least 2GB)
AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
if [ "$AVAILABLE_SPACE" -lt 2097152 ]; then  # 2GB in KB
    warning "Less than 2GB disk space available. Installation may fail."
fi

success "System requirements check passed"

# Create virtual environment
log "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    success "Virtual environment created"
else
    warning "Virtual environment already exists"
fi

# Activate virtual environment
log "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
log "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
log "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    success "Dependencies installed"
else
    error "requirements.txt not found"
    exit 1
fi

# Create necessary directories
log "Creating directory structure..."
mkdir -p data logs backups config

# Set up configuration files
log "Setting up configuration..."

# Copy example config files if they don't exist
if [ ! -f "config/config.yaml" ]; then
    if [ -f "config/config.yaml.example" ]; then
        cp config/config.yaml.example config/config.yaml
        success "Created config/config.yaml from example"
    else
        error "config.yaml.example not found"
        exit 1
    fi
fi

if [ ! -f "config/.env" ]; then
    if [ -f "config/.env.example" ]; then
        cp config/.env.example config/.env
        success "Created config/.env from example"
    else
        error ".env.example not found"
        exit 1
    fi
fi

if [ ! -f "config/constitutional_rules.yaml" ]; then
    if [ -f "config/constitutional_rules.yaml.example" ]; then
        cp config/constitutional_rules.yaml.example config/constitutional_rules.yaml
        success "Created config/constitutional_rules.yaml from example"
    else
        error "constitutional_rules.yaml.example not found"
        exit 1
    fi
fi

# Generate secure keys
log "Generating secure keys..."

# Generate secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
sed -i "s/your-super-secret-key-change-this-immediately/$SECRET_KEY/" config/.env

# Generate encryption key
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
sed -i "s/your-encryption-key-for-sensitive-data/$ENCRYPTION_KEY/" config/.env

# Generate JWT secret
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
sed -i "s/your-jwt-secret-key-for-authentication/$JWT_SECRET/" config/.env

# Generate backup encryption key
BACKUP_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
sed -i "s/your-backup-encryption-key/$BACKUP_KEY/" config/.env

# Generate database encryption key
DB_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
sed -i "s/your-database-encryption-key/$DB_KEY/" config/.env

success "Secure keys generated"

# Initialize database
log "Initializing database..."
if [ -f "src/core/database.py" ]; then
    python3 src/core/database.py --init
    success "Database initialized"
else
    warning "Database initialization script not found, will be created on first run"
fi

# Set proper permissions
log "Setting file permissions..."
chmod 600 config/.env
chmod 644 config/config.yaml
chmod 644 config/constitutional_rules.yaml
chmod 755 scripts/*.sh

# Create systemd service file (optional)
if command -v systemctl &> /dev/null; then
    log "Creating systemd service file..."
    
    cat > whisperleaf.service << EOF
[Unit]
Description=WhisperLeaf Sovereign AI System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python src/core/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    success "Systemd service file created (whisperleaf.service)"
    log "To install as system service, run: sudo cp whisperleaf.service /etc/systemd/system/ && sudo systemctl enable whisperleaf"
fi

# Run basic tests
log "Running basic system tests..."
if [ -f "tests/test_basic_setup.py" ]; then
    python3 -m pytest tests/test_basic_setup.py -v
    if [ $? -eq 0 ]; then
        success "Basic tests passed"
    else
        warning "Some tests failed, but installation can continue"
    fi
else
    warning "Basic test file not found"
fi

# Installation complete
success "WhisperLeaf installation completed successfully!"

echo ""
echo "🌿 WhisperLeaf is now installed and ready to use!"
echo ""
echo "Next steps:"
echo "1. Review and customize config/config.yaml"
echo "2. Review and customize config/constitutional_rules.yaml"
echo "3. Start WhisperLeaf: ./scripts/start_system.sh"
echo "4. Access the API at: http://localhost:8000"
echo "5. View documentation at: http://localhost:8000/docs"
echo ""
echo "For help and documentation, visit: https://github.com/sylviesuite/WhisperLeaf"
echo ""

# Deactivate virtual environment
deactivate

log "Installation script completed"

