#!/bin/bash
# AI Server Startup Script

# Check if environment file exists
if [ -f "ai_server_env.sh" ]; then
    echo "Loading environment configuration..."
    source ai_server_env.sh
else
    echo "Warning: ai_server_env.sh not found. Please create it from ai_server_env_template.sh"
    echo "Copy the template and set your TOGETHER_AI_API_KEY"
    exit 1
fi

# Check if API key is set
if [ -z "$TOGETHER_AI_API_KEY" ] || [ "$TOGETHER_AI_API_KEY" = "your_together_ai_api_key_here" ]; then
    echo "Error: TOGETHER_AI_API_KEY not properly configured"
    echo "Please edit ai_server_env.sh and set your actual API key"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Activate virtual environment if it exists
if [ -d "flashCardEnv" ]; then
    echo "Activating virtual environment..."
    source flashCardEnv/bin/activate
fi

# Start the AI server
echo "Starting AI Server..."
echo "Server will be available at http://${SERVER_HOST:-0.0.0.0}:${SERVER_PORT:-5000}"
echo "Press Ctrl+C to stop the server"
echo ""

python ai_server.py