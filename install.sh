#!/bin/bash

# MCP Multi-Agent Developer Pod Installation Script

set -e

echo "🚀 Installing MCP Multi-Agent Developer Pod..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.9 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install the package
echo "📥 Installing MCP Multi-Agent Developer Pod..."
pip install -e .

# Install Ollama (if not already installed)
if ! command -v ollama &> /dev/null; then
    echo "📥 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
else
    echo "✅ Ollama is already installed"
fi

# Pull the default model
echo "🤖 Pulling Llama 3.1 model..."
ollama pull llama3.1:8b

# Create configuration file
echo "⚙️ Creating configuration file..."
if [ ! -f .env ]; then
    cp config.env.example .env
    echo "✅ Configuration file created: .env"
else
    echo "✅ Configuration file already exists"
fi

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs

# Create workspace directory
echo "📁 Creating workspace directory..."
mkdir -p workspace

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Start Ollama: ollama serve"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the MCP Dev Pod: mcp-dev-pod start"
echo ""
echo "📖 For more information, see README.md"
