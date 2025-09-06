@echo off
REM MCP Multi-Agent Developer Pod Installation Script for Windows

echo 🚀 Installing MCP Multi-Agent Developer Pod...

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from https://python.org
    pause
    exit /b 1
)

echo ✅ Python is installed

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

REM Install the package
echo 📥 Installing MCP Multi-Agent Developer Pod...
pip install -e .

REM Check for Groq API key
if not exist .env (
    echo ⚠️  Please configure your Groq API key in .env file
    echo Get your API key from: https://console.groq.com
) else (
    echo ✅ Configuration file exists
)

REM Create configuration file
echo ⚙️ Creating configuration file...
if not exist .env (
    copy config.env.example .env
    echo ✅ Configuration file created: .env
) else (
    echo ✅ Configuration file already exists
)

REM Create logs directory
echo 📁 Creating logs directory...
if not exist logs mkdir logs

REM Create workspace directory
echo 📁 Creating workspace directory...
if not exist workspace mkdir workspace

echo.
echo 🎉 Installation completed successfully!
echo.
echo 📋 Next steps:
echo 1. Configure your Groq API key in .env file
echo 2. Activate virtual environment: venv\Scripts\activate.bat
echo 3. Run Streamlit app: streamlit run streamlit_app.py
echo    OR run CLI: python -m mcp_dev_pod.main start
echo.
echo 📖 For more information, see README.md
pause
