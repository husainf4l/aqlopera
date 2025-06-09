#!/bin/bash

# Web Operator Agent - Setup and Run Script
# This script sets up the environment and starts the agent

echo "🤖 Web Operator Agent - Setup & Run"
echo "===================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your OpenAI API key and other settings"
    echo "   You can edit it with: nano .env"
    read -p "Press Enter to continue after editing .env file..."
fi

# Create required directories
echo "📁 Creating required directories..."
mkdir -p screenshots logs

# Run basic tests
echo "🧪 Running basic tests..."
python test.py

# Start the server
echo "🚀 Starting Web Operator Agent..."
echo "   API Documentation: http://localhost:8000/docs"
echo "   Health Check: http://localhost:8000/health"
echo "   Press Ctrl+C to stop"
echo ""

python main.py
