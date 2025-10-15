#!/bin/bash
# AI Server Environment Configuration
# Copy this file to ai_server_env.sh and update with your actual API key

# Together.ai API Key (required)
export TOGETHER_AI_API_KEY="<put your key here>"

# Server Configuration (optional - defaults provided)
export SERVER_PORT="5000"
export SERVER_HOST="0.0.0.0"
export QUEUE_MAX_SIZE="100"
export REQUEST_TIMEOUT="300"
export DEBUG_MODE="false"

echo "AI Server environment variables configured"
echo "Server will run on ${SERVER_HOST}:${SERVER_PORT}"
echo "Queue max size: ${QUEUE_MAX_SIZE}"
echo "Request timeout: ${REQUEST_TIMEOUT} seconds"