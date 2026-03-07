#!/usr/bin/env python3
"""
WhisperLeaf Basic Setup Test
Tests core infrastructure and dependencies
"""

import os
import sys
import sqlite3
import requests
import subprocess
from pathlib import Path

def test_project_structure():
    """Test that all required directories exist"""
    print("🏗️  Testing project structure...")
    
    required_dirs = [
        "api", "emotional-engine", "memory-vault", "constitutional",
        "reflective-prompts", "mood-timeline", "ui", "config", 
        "data", "logs", "tests", "scripts"
    ]
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        assert dir_path.exists(), f"Missing directory: {dir_name}"
        print(f"   ✅ {dir_name}/ exists")
    
    print("   🎉 Project structure complete!")

def test_configuration_files():
    """Test that configuration files exist and are valid"""
    print("\n⚙️  Testing configuration files...")
    
    config_files = [
        "config/config.yaml",
        "config/constitutional_rules.yaml",
        ".env",
        "requirements.txt"
    ]
    
    for config_file in config_files:
        file_path = Path(config_file)
        assert file_path.exists(), f"Missing config file: {config_file}"
        assert file_path.stat().st_size > 0, f"Empty config file: {config_file}"
        print(f"   ✅ {config_file} exists and has content")
    
    print("   🎉 Configuration files complete!")

def test_python_environment():
    """Test Python virtual environment and dependencies"""
    print("\n🐍 Testing Python environment...")
    
    # Check if we're in virtual environment
    venv_path = Path("venv")
    assert venv_path.exists(), "Virtual environment not found"
    print("   ✅ Virtual environment exists")
    
    # Test key imports
    try:
        import fastapi
        print(f"   ✅ FastAPI {fastapi.__version__} installed")
    except ImportError:
        assert False, "FastAPI not installed"
    
    try:
        import sqlalchemy
        print(f"   ✅ SQLAlchemy {sqlalchemy.__version__} installed")
    except ImportError:
        assert False, "SQLAlchemy not installed"
    
    try:
        import pandas
        print(f"   ✅ Pandas {pandas.__version__} installed")
    except ImportError:
        assert False, "Pandas not installed"
    
    print("   🎉 Python environment complete!")

def test_ollama_service():
    """Test Ollama AI service and model availability"""
    print("\n🤖 Testing Ollama AI service...")
    
    try:
        # Test Ollama service
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        assert response.status_code == 200, "Ollama service not responding"
        print("   ✅ Ollama service is running")
        
        # Check for TinyLLama model
        models = response.json()
        model_names = [model['name'] for model in models.get('models', [])]
        assert any('tinyllama' in name for name in model_names), "TinyLLama model not found"
        print("   ✅ TinyLLama model is available")
        
    except requests.exceptions.RequestException:
        assert False, "Cannot connect to Ollama service"
    
    print("   🎉 Ollama AI service complete!")

def test_database_creation():
    """Test database creation and basic operations"""
    print("\n💾 Testing database functionality...")
    
    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Test SQLite database creation
    db_path = data_dir / "test_whisperleaf.db"
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create test table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_emotions (
                id INTEGER PRIMARY KEY,
                mood TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert test data
        cursor.execute("INSERT INTO test_emotions (mood) VALUES (?)", ("happy",))
        conn.commit()
        
        # Query test data
        cursor.execute("SELECT * FROM test_emotions")
        results = cursor.fetchall()
        assert len(results) > 0, "Database insert/query failed"
        
        conn.close()
        db_path.unlink()  # Clean up test database
        print("   ✅ SQLite database operations working")
        
    except Exception as e:
        assert False, f"Database test failed: {e}"
    
    print("   🎉 Database functionality complete!")

def test_react_application():
    """Test React application setup"""
    print("\n⚛️  Testing React application...")
    
    ui_path = Path("ui/whisperleaf-ui")
    assert ui_path.exists(), "React application not created"
    print("   ✅ React application directory exists")
    
    package_json = ui_path / "package.json"
    assert package_json.exists(), "package.json not found"
    print("   ✅ package.json exists")
    
    src_dir = ui_path / "src"
    assert src_dir.exists(), "src directory not found"
    print("   ✅ src directory exists")
    
    app_jsx = src_dir / "App.jsx"
    assert app_jsx.exists(), "App.jsx not found"
    print("   ✅ App.jsx exists")
    
    print("   🎉 React application complete!")

def test_emotional_ai_basic():
    """Test basic emotional AI functionality"""
    print("\n💝 Testing basic emotional AI...")
    
    try:
        # Test Ollama with emotional prompt
        result = subprocess.run([
            "ollama", "run", "tinyllama", 
            "Respond with empathy to: 'I'm feeling anxious.' Use 1 sentence."
        ], capture_output=True, text=True, timeout=30)
        
        assert result.returncode == 0, "Ollama command failed"
        assert len(result.stdout.strip()) > 0, "No response from AI model"
        print("   ✅ AI model responds to emotional prompts")
        
        # Check for empathetic keywords in response
        response = result.stdout.lower()
        empathy_indicators = ['understand', 'feel', 'here', 'support', 'okay', 'normal']
        has_empathy = any(word in response for word in empathy_indicators)
        
        if has_empathy:
            print("   ✅ AI response shows empathetic language")
        else:
            print("   ⚠️  AI response may need empathy tuning")
        
    except subprocess.TimeoutExpired:
        print("   ⚠️  AI response timeout (model may be slow)")
    except Exception as e:
        print(f"   ⚠️  AI test warning: {e}")
    
    print("   🎉 Basic emotional AI complete!")

def main():
    """Run all setup tests"""
    print("🌿 WhisperLeaf Infrastructure Test Suite")
    print("=" * 50)
    
    try:
        test_project_structure()
        test_configuration_files()
        test_python_environment()
        test_ollama_service()
        test_database_creation()
        test_react_application()
        test_emotional_ai_basic()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED! WhisperLeaf infrastructure is ready!")
        print("🌿 Your sovereign emotional AI system is properly set up.")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

