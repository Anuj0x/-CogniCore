#!/bin/bash
# Modern deployment script for Mini AutoGPT

set -e

echo "🚀 Setting up Mini AutoGPT..."

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed."; exit 1; }
command -v pip >/dev/null 2>&1 || { echo "❌ pip is required but not installed."; exit 1; }

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data

# Setup environment file
if [ ! -f ".env" ]; then
    echo "⚙️ Setting up environment configuration..."
    cp .env.template .env
    echo "🔧 Please edit .env file with your configuration"
else
    echo "✅ Environment file already exists"
fi

# Run basic health checks
echo "🔍 Running health checks..."

# Check if required modules can be imported
python3 -c "
import asyncio
from core.config import Config
from core.logger import logger
print('✅ Core modules imported successfully')
"

# Test LLM connection if configured
if [ -n "$LLM_API_URL" ] && [ -n "$LLM_SERVER_TYPE" ]; then
    echo "🔗 Testing LLM connection..."
    python3 -c "
import asyncio
from core.config import Config
from llm.provider import create_llm_provider

async def test():
    try:
        config = Config.load()
        provider = create_llm_provider(config.llm)
        connected = await provider.test_connection()
        print('✅ LLM connection successful' if connected else '❌ LLM connection failed')
    except Exception as e:
        print(f'❌ LLM test failed: {e}')

asyncio.run(test())
"
else
    echo "⚠️ LLM configuration not found, skipping LLM test"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Start LLM server (Ollama, etc.) if needed"
echo "3. Run: python main.py"
echo ""
echo "For development:"
source venv/bin/activate

# Make script executable
chmod +x "$0"
