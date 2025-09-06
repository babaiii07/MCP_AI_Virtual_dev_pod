#!/bin/bash

# Run Streamlit app for MCP Multi-Agent Developer Pod

echo "🚀 Starting MCP Multi-Agent Developer Pod Web Interface..."

# Activate virtual environment
source venv/bin/activate

# Start Streamlit app
streamlit run streamlit_app.py
