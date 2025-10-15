# AI Server Setup and Usage

## Overview
This Flask-based AI server provides REST API endpoints for processing AI requests through Together.ai with a job queue system for asynchronous processing.

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
1. Copy the environment template:
   ```bash
   cp ai_server_env_template.sh ai_server_env.sh
   ```

2. Edit `ai_server_env.sh` and set your Together.ai API key:
   ```bash
   export TOGETHER_AI_API_KEY="your_actual_api_key_here"
   ```

### 3. Configure Applications
Edit `config/ai_app_config.json` to add or modify application codes and their allowed request types.

Example configuration:
```json
{
  "app_codes": {
    "your_app_hash": {
      "name": "Your Application",
      "allowed_request_types": [
        "your_request_type1",
        "your_request_type2"
      ],
      "rate_limit": "100/hour",
      "max_tokens": 1000,
      "temperature": 0.7
    }
  }
}
```

## Starting the Server

### Option 1: Using the startup script (recommended)
```bash
./start_ai_server.sh
```

### Option 2: Manual startup
```bash
# Set environment variables
source ai_server_env.sh

# Start the server
python ai_server.py
```

The server will start on `http://localhost:5000` by default.

## API Endpoints

### 1. Submit AI Request
**POST** `/ai_request`

Request body:
```json
{
  "app_code": "flashcards_app_001",
  "request_type": "explain_concept",
  "request": "Explain photosynthesis"
}
```

Success response:
```json
{
  "status": "success",
  "request_id": "uuid-string",
  "message": "Request queued successfully"
}
```

### 2. Check Request Status
**GET** `/get_request/<request_id>`

Possible responses:
- **Queued**: Request is waiting in queue
- **Processing**: Request is being processed
- **Completed**: Request finished with AI response
- **Error**: Request failed with error details

### 3. Health Check
**GET** `/health`

Returns server status and queue statistics.

## Testing

Run the test script to verify the server is working:
```bash
python test_ai_server.py
```

Or test against a remote server:
```bash
python test_ai_server.py http://your-server:5000
```

## Configuration Options

Environment variables you can set in `ai_server_env.sh`:

- `TOGETHER_AI_API_KEY`: Your Together.ai API key (required)
- `SERVER_PORT`: Port to run the server on (default: 5000)
- `SERVER_HOST`: Host to bind to (default: 0.0.0.0)
- `QUEUE_MAX_SIZE`: Maximum queue size (default: 100)
- `REQUEST_TIMEOUT`: Request timeout in seconds (default: 300)
- `DEBUG_MODE`: Enable debug logging (default: false)

## Default App Codes

The server comes with these pre-configured app codes:

1. **flashcards_app_001** - For flashcard applications
   - Allowed request types: generate_flashcard, explain_concept, create_quiz, summarize_content, generate_questions, create_study_guide

2. **test_app_123** - For testing
   - Allowed request types: test_request, debug_request

## Security Notes

- The server supports CORS for cross-domain requests
- App codes act as authentication tokens
- Only pre-registered app codes and request types are accepted
- Rate limiting is configured per app code
- Request size and queue capacity are limited

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Together.ai API errors**: 
   - Verify your API key is correct
   - Check your Together.ai account has credits
   - Ensure network connectivity

3. **Permission errors**: Make sure the scripts are executable
   ```bash
   chmod +x start_ai_server.sh
   ```

4. **Port conflicts**: Change the SERVER_PORT in your environment file

### Logs
Check the logs directory for detailed error information:
- `logs/ai_server.log`: Application logs
- Console output: Real-time server activity

## Production Deployment

For production deployment:

1. Set `DEBUG_MODE=false`
2. Use a proper WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 ai_server:app
   ```
3. Set up proper logging and monitoring
4. Configure firewall and reverse proxy (nginx)
5. Use environment variables for sensitive configuration
6. Consider using Redis for the job queue in multi-server setups

## API Examples

### JavaScript/AJAX Example
```javascript
// Submit request
fetch('http://localhost:5000/ai_request', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    app_code: 'flashcards_app_001',
    request_type: 'explain_concept',
    request: 'Explain quantum physics'
  })
})
.then(response => response.json())
.then(data => {
  if (data.status === 'success') {
    const requestId = data.request_id;
    // Poll for results
    checkStatus(requestId);
  }
});

// Check status
function checkStatus(requestId) {
  fetch(`http://localhost:5000/get_request/${requestId}`)
    .then(response => response.json())
    .then(data => {
      if (data.status === 'completed') {
        console.log('AI Response:', data.response.ai_response);
      } else if (data.status === 'queued' || data.status === 'processing') {
        // Check again in a few seconds
        setTimeout(() => checkStatus(requestId), 3000);
      }
    });
}
```

### Python Example
```python
import requests
import time

# Submit request
response = requests.post('http://localhost:5000/ai_request', json={
    'app_code': 'flashcards_app_001',
    'request_type': 'explain_concept',
    'request': 'Explain photosynthesis'
})

if response.status_code == 200:
    request_id = response.json()['request_id']
    
    # Poll for results
    while True:
        status_response = requests.get(f'http://localhost:5000/get_request/{request_id}')
        status_data = status_response.json()
        
        if status_data['status'] == 'completed':
            print('AI Response:', status_data['response']['ai_response'])
            break
        elif status_data['status'] == 'error':
            print('Error:', status_data['message'])
            break
        else:
            time.sleep(2)  # Wait before checking again
```