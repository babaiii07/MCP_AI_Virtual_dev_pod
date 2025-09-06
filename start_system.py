#!/usr/bin/env python3
"""
Startup script for the MCP Multi-Agent Developer Pod system.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_requirements():
    """Check if all requirements are installed."""
    print("🔍 Checking requirements...")
    
    try:
        import streamlit
        import httpx
        import aiofiles
        import sqlalchemy
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists and has required keys."""
    print("🔍 Checking environment configuration...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("Please create a .env file with your Groq API key:")
        print("GROQ_API_KEY=your_api_key_here")
        return False
    
    with open(env_file) as f:
        content = f.read()
        if "GROQ_API_KEY" not in content or "your_api_key_here" in content:
            print("❌ GROQ_API_KEY not properly configured in .env file")
            print("Please set your actual Groq API key in the .env file")
            return False
    
    print("✅ Environment configuration looks good")
    return True

def create_workspace():
    """Create workspace directory if it doesn't exist."""
    print("🔍 Checking workspace directory...")
    
    workspace = Path("./workspace")
    if not workspace.exists():
        workspace.mkdir()
        print("✅ Created workspace directory")
    else:
        print("✅ Workspace directory exists")
    
    return True

def start_streamlit():
    """Start the Streamlit application."""
    print("🚀 Starting MCP Multi-Agent Developer Pod...")
    print("=" * 50)
    print("The system will be available at: http://localhost:8501")
    print("Press Ctrl+C to stop the system")
    print("=" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n👋 System stopped by user")
    except Exception as e:
        print(f"❌ Error starting system: {e}")

def main():
    """Main startup function."""
    print("🤖 MCP Multi-Agent Developer Pod Startup")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment
    if not check_env_file():
        sys.exit(1)
    
    # Create workspace
    if not create_workspace():
        sys.exit(1)
    
    print("\n✅ All checks passed! Starting the system...")
    time.sleep(1)
    
    # Start the system
    start_streamlit()

if __name__ == "__main__":
    main()

