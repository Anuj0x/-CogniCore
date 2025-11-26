#!/bin/bash
# Run script for Mini AutoGPT

set -e

echo "🤖 Starting Mini AutoGPT..."

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Run setup.sh first."
    exit 1
fi

# Set Python path to include current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run the application
echo "🚀 Launching application..."
python main.py

echo ""
echo "👋 Mini AutoGPT stopped."
