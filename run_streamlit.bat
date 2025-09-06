@echo off
REM Run Streamlit app for MCP Multi-Agent Developer Pod

echo 🚀 Starting MCP Multi-Agent Developer Pod Web Interface...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Streamlit app
streamlit run streamlit_app.py

pause
