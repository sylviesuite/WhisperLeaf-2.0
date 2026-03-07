# WhisperLeaf Installation Guide

## System Requirements

### Minimum Requirements
- **Operating System**: Ubuntu 22.04+, macOS 12+, or Windows 10+
- **Python**: 3.11 or higher
- **Memory**: 4GB RAM
- **Storage**: 2GB free space
- **Network**: Internet connection for initial setup only

### Recommended Requirements
- **Memory**: 8GB RAM for optimal performance
- **Storage**: 10GB free space for extended usage
- **CPU**: Multi-core processor for better performance

## Installation Methods

### Method 1: Quick Install (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/sylviesuite/WhisperLeaf.git
   cd WhisperLeaf
   ```

2. **Run the automated installer**
   ```bash
   chmod +x scripts/install.sh
   ./scripts/install.sh
   ```

3. **Start the system**
   ```bash
   ./scripts/start_system.sh
   ```

### Method 2: Manual Installation

1. **Clone and navigate**
   ```bash
   git clone https://github.com/sylviesuite/WhisperLeaf.git
   cd WhisperLeaf
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv whisperleaf_env
   source whisperleaf_env/bin/activate  # On Windows: whisperleaf_env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the system**
   ```bash
   cp config/config.yaml.example config/config.yaml
   cp config/.env.example config/.env
   ```

5. **Initialize the database**
   ```bash
   python src/core/database.py --init
   ```

6. **Start WhisperLeaf**
   ```bash
   python src/core/main.py
   ```

## Configuration

### Basic Configuration

Edit `config/config.yaml` to customize your installation:

```yaml
# Basic system settings
system:
  host: "localhost"
  port: 8000
  debug: false

# Database configuration
database:
  path: "data/whisperleaf.db"
  backup_enabled: true

# Emotional processing settings
emotional:
  crisis_detection_enabled: true
  mood_tracking_enabled: true
  
# Content curation settings
curation:
  rss_enabled: true
  web_scraping_enabled: true
  update_interval: 3600  # seconds
```

### Environment Variables

Create `config/.env` with your specific settings:

```bash
# Encryption settings
ENCRYPTION_KEY=your_secure_encryption_key_here

# API settings
API_SECRET_KEY=your_api_secret_key_here

# Optional: External service keys (if using)
OPENAI_API_KEY=your_openai_key_here  # Optional for enhanced AI features
```

### Constitutional Rules

Customize AI behavior by editing `config/constitutional_rules.yaml`:

```yaml
rules:
  - name: "Privacy Protection"
    description: "Never share personal information externally"
    priority: 1
    
  - name: "Emotional Safety"
    description: "Prioritize user emotional well-being"
    priority: 1
    
  - name: "Crisis Response"
    description: "Provide appropriate crisis intervention"
    priority: 1
```

## Verification

### System Health Check

Run the system health check to verify installation:

```bash
./scripts/check_status.sh
```

Expected output:
```
✅ Database: Connected
✅ API Server: Running on http://localhost:8000
✅ Emotional Engine: Operational
✅ Content Curator: Active
✅ Backup System: Enabled
✅ Constitutional AI: Enforcing 7 rules
```

### API Test

Test the API endpoints:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "database": "connected",
    "emotional_engine": "operational",
    "content_curator": "active",
    "backup_system": "enabled"
  }
}
```

### Integration Tests

Run the comprehensive test suite:

```bash
python -m pytest tests/ -v
```

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'whisperleaf'`
**Solution**: Ensure you're in the correct directory and virtual environment is activated.

**Issue**: Database connection errors
**Solution**: Check that the data directory exists and has proper permissions:
```bash
mkdir -p data
chmod 755 data
```

**Issue**: Port already in use
**Solution**: Change the port in `config/config.yaml` or stop the conflicting service:
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

**Issue**: Permission denied on scripts
**Solution**: Make scripts executable:
```bash
chmod +x scripts/*.sh
```

### Log Files

Check log files for detailed error information:
- System logs: `logs/whisperleaf.log`
- Error logs: `logs/error.log`
- API logs: `logs/api.log`

### Getting Help

1. Check the [FAQ](FAQ.md)
2. Search [existing issues](https://github.com/sylviesuite/WhisperLeaf/issues)
3. Create a [new issue](https://github.com/sylviesuite/WhisperLeaf/issues/new) with:
   - Your operating system
   - Python version
   - Error messages
   - Steps to reproduce

## Next Steps

After successful installation:

1. **Read the [User Guide](USER_GUIDE.md)** to learn how to use WhisperLeaf
2. **Explore the [API Documentation](API.md)** for integration possibilities
3. **Review [Privacy & Security](PRIVACY.md)** to understand data protection
4. **Join the [Community](https://github.com/sylviesuite/WhisperLeaf/discussions)** for support and discussions

## Uninstallation

To completely remove WhisperLeaf:

```bash
# Stop the system
./scripts/stop_system.sh

# Remove the installation directory
cd ..
rm -rf WhisperLeaf

# Remove virtual environment (if created)
rm -rf whisperleaf_env
```

**Note**: This will permanently delete all your emotional data and memories. Consider backing up important data before uninstalling.

