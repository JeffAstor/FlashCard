# AI Server Requirements

## Overview
A Flask-based REST API server that processes AI requests through Together.ai, with a job queue system for asynchronous processing and cross-domain support for internet deployment.

## Server Architecture

### Core Components
1. **Flask Web Server** - Main REST API server
2. **Job Queue System** - Asynchronous request processing
3. **Together.ai Integration** - AI model communication
4. **Authentication/Authorization** - App code validation
5. **Request Status Tracking** - Job lifecycle management

### Cross-Domain Support
- CORS (Cross-Origin Resource Sharing) enabled
- Support for internet deployment
- Secure headers and authentication

## REST API Endpoints

### 1. AI Request Endpoint
**Endpoint:** `POST /ai_request`

**Parameters:**
- `app_code` (string, required): Hash identifier for the application
  - Only pre-registered app codes are accepted
  - Used for authentication and request validation
- `request_type` (string, required): Type of AI request
  - Each app has its own supported request types
  - Must be in the allowed list for the given app_code
- `request` (string, required): The actual request text to send to the AI model

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "request_id": "unique_request_id",
    "message": "Request queued successfully"
  }
  ```
- **Rejection (400/401/403):**
  ```json
  {
    "status": "error",
    "error_code": "INVALID_APP_CODE|UNSUPPORTED_REQUEST_TYPE|INVALID_REQUEST",
    "message": "Descriptive error message"
  }
  ```

### 2. Get Request Status Endpoint
**Endpoint:** `GET /get_request/<request_id>`

**Parameters:**
- `request_id` (string, path parameter): The unique request identifier

**Response Options:**

- **Rejection (404):**
  ```json
  {
    "status": "error",
    "error_code": "REQUEST_NOT_FOUND",
    "message": "Request ID not found"
  }
  ```

- **In Queue (200):**
  ```json
  {
    "status": "queued",
    "position": 5,
    "estimated_wait_time": "2-3 minutes",
    "message": "Request is in queue"
  }
  ```

- **Processing (200):**
  ```json
  {
    "status": "processing",
    "message": "Request is currently being processed"
  }
  ```

- **Ready (200):**
  ```json
  {
    "status": "completed",
    "response": {
      "ai_response": "The AI's response text",
      "model_used": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
      "completion_time": "2024-10-14T10:30:00Z",
      "token_usage": {
        "prompt_tokens": 25,
        "completion_tokens": 150,
        "total_tokens": 175
      }
    }
  }
  ```

- **Error (200):**
  ```json
  {
    "status": "error",
    "error_code": "AI_SERVICE_ERROR|TIMEOUT|INVALID_REQUEST",
    "message": "Detailed error message",
    "retry_possible": true
  }
  ```

### 3. Health Check Endpoint (Additional)
**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "queue_size": 12,
  "active_workers": 3,
  "uptime": "2d 5h 30m",
  "together_ai_status": "connected"
}
```

## Job Queue System

### Queue Management
- **Queue Type:** In-memory or Redis-based queue
- **Processing Model:** Background worker threads/processes
- **Capacity:** Configurable maximum queue size
- **Timeout:** Configurable request timeout (default: 5 minutes)

### Job Lifecycle
1. **Queued:** Request received and added to queue
2. **Processing:** Worker picked up the job
3. **Completed:** AI response received and stored
4. **Error:** Processing failed with error details
5. **Expired:** Request timed out and removed

### Queue Features
- Position tracking for queued requests
- Estimated wait time calculation
- Priority levels (if needed for different app codes)
- Automatic cleanup of completed/expired requests

## Together.ai Integration

### Model Configuration
- **Primary Model:** `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo`
- **Fallback Models:** Configurable list of alternative models
- **Request Format:** Chat completion format with user messages

### API Key Management
- Environment variable for API key storage
- Key validation on server startup
- Error handling for API failures

### Request Processing
```python
# Example integration structure
completion = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    messages=[
        {
            "role": "user",
            "content": request_text,
        }
    ],
    max_tokens=1000,  # Configurable
    temperature=0.7,  # Configurable per request type
)
```

## Security & Authentication

### App Code System
- **Registration:** Pre-registered hash codes for known applications
- **Validation:** Server maintains whitelist of valid app codes
- **Request Types:** Each app code has associated allowed request types

### Security Headers
- CORS configuration for cross-domain requests
- Rate limiting per app code
- Request size limits
- Input sanitization

## Configuration Management

### App Code Configuration
```json
{
  "app_codes": {
    "abc123hash": {
      "name": "FlashCards App",
      "allowed_request_types": [
        "generate_flashcard",
        "explain_concept",
        "create_quiz"
      ],
      "rate_limit": "100/hour",
      "max_tokens": 1000
    }
  }
}
```

### Server Configuration
- Port and host settings
- Queue size limits
- Worker thread count
- Request timeout values
- Together.ai model preferences

## Error Handling

### Error Categories
1. **Authentication Errors:** Invalid app codes
2. **Validation Errors:** Unsupported request types, malformed requests
3. **Queue Errors:** Queue full, request not found
4. **AI Service Errors:** Together.ai API failures
5. **System Errors:** Server overload, network issues

### Logging
- Request/response logging
- Error tracking and alerting
- Performance metrics
- Queue statistics

## Deployment Requirements

### Dependencies
- Flask and Flask-CORS
- Together.ai Python SDK
- Queue management (Redis or in-memory)
- Request validation libraries
- Environment management

### Environment Variables
- `TOGETHER_AI_API_KEY`: API key for Together.ai
- `SERVER_PORT`: Server port (default: 5000)
- `QUEUE_MAX_SIZE`: Maximum queue size
- `REQUEST_TIMEOUT`: Request timeout in seconds
- `DEBUG_MODE`: Enable/disable debug logging

### Scalability Considerations
- Horizontal scaling with shared queue (Redis)
- Load balancing support
- Database persistence for request history (optional)
- Monitoring and metrics collection

## Future Enhancements

### Potential Features
1. **WebSocket Support:** Real-time status updates
2. **Batch Processing:** Multiple requests in single call
3. **Result Caching:** Cache responses for identical requests
4. **Analytics Dashboard:** Usage statistics and monitoring
5. **Multiple AI Providers:** Support for other AI services
6. **Request History:** Persistent storage of completed requests
