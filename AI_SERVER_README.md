# AI Server Setup and Usage

## Overview
This Flask-based AI server is designed for PythonAnywhere hosting and provides REST API endpoints for processing AI requests through Together.ai. Requests are processed and returned directly (no job queue).

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```


## Starting the Server

On PythonAnywhere, the server starts automatically when you reload your web app. You do not need to run a startup script.

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

Response (direct result):
```json
{
  "status": "success",
  "ai_response": "...AI generated response...",
  "app_name": "FlashCards App",
  "request_type": "explain_concept",
  "model_used": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
  "completion_time": "2025-10-15T12:34:56.789Z",
  "token_usage": {
    "prompt_tokens": 50,
    "completion_tokens": 100,
    "total_tokens": 150
  }
}
```

### 2. Health Check
**GET** `/health`

Returns server status and app info.

### 3. List Available Apps
**GET** `/apps`

Returns info about available app codes and request types.

### 4. SSL/Certificate Debug
**GET** `/debug/ssl`

Returns SSL and certificate configuration info (for troubleshooting).

### 5. Root Endpoint
**GET** `/`

Returns server info and available endpoints.

## Testing

You can test the server using `curl`, Postman, or your own client code. See API examples below.

## Configuration Options

Configuration is handled in `flask_app_pa_v2.py`. The Together.ai API key is set directly in the code. App codes and allowed request types are defined in the `FlashCardsApp` and `GenericAIApp` classes.

## Default App Codes

The server comes with these pre-configured app codes (see `flask_app_pa_v2.py`):

1. **flashcards_app_001** - For flashcard applications
  - Allowed request types: generate_flashcard, explain_concept, create_quiz, summarize_content, generate_card_from_description

2. **generic_ai_001** - For general AI prompts
  - Allowed request types: prompt

## Adding Your Own App Classes

You can extend the server by creating your own `BaseApp` subclasses to handle custom request types and processing logic.

### Steps to Add a Custom App

1. **Create a new class** in `flask_app_pa_v2.py` that inherits from `BaseApp`:

   ```python
   class MyCustomApp(BaseApp):
     def _get_default_config(self) -> Dict[str, Any]:
       return {
         "max_tokens": 500,
         "temperature": 0.5,
         "rate_limit": "20/hour"
       }

     def get_allowed_request_types(self) -> list:
       return ["my_custom_type"]

     def process_request(self, request_type: str, request_text: str) -> Dict[str, Any]:
       # Implement your custom processing logic here
       result = {"status": "success", "custom_output": "Processed: " + request_text}
       return result
   ```

2. **Register your app** in the `_init_apps` method of `AIServerV2`:

   ```python
   def _init_apps(self):
     # ...existing code...
     my_custom_app = MyCustomApp(
       app_code="my_custom_app_001",
       name="My Custom App",
       together_client=self.together_client
     )
     self.apps["my_custom_app_001"] = my_custom_app
     # ...existing code...
   ```

3. **Use your app code and request type** in client requests:

   ```json
   {
   "app_code": "my_custom_app_001",
   "request_type": "my_custom_type",
   "request": "Your input data here"
   }
   ```

Your app will now be available at the `/ai_request` endpoint and listed in `/apps`.

## Security Notes

- The server supports CORS for cross-domain requests
- App codes act as authentication tokens
- Only pre-registered app codes and request types are accepted
- Rate limiting is configured per app code (see app config in code)

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure all dependencies are installed
  ```bash
  pip install -r requirements.txt
  ```

2. **Together.ai API errors**: 
  - Verify your API key is correct (set in `flask_app_pa_v2.py`)
  - Check your Together.ai account has credits
  - Ensure network connectivity

3. **PythonAnywhere errors**:
  - Check the error log in the PythonAnywhere dashboard
  - Make sure your WSGI file points to the correct app file
  - Restart your web app after making changes

### Logs
Check the PythonAnywhere dashboard for error logs and console output.

## Production Deployment

On PythonAnywhere, production deployment is handled automatically. No additional steps are required beyond uploading your files and restarting your web app.

## API Examples

### JavaScript/AJAX Example
```javascript
// Submit request
fetch('https://firettripperjeff.pythonanywhere.com/ai_request', {
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
    console.log('AI Response:', data.ai_response);
  }
});
```

### Python Example
```python
import requests

# Submit request
response = requests.post('https://firettripperjeff.pythonanywhere.com/ai_request', json={
    'app_code': 'flashcards_app_001',
    'request_type': 'explain_concept',
    'request': 'Explain photosynthesis'
})

if response.status_code == 200:
    data = response.json()
    print('AI Response:', data['ai_response'])
else:
    print('Error:', response.text)
```

**Note:** Change `firettripperjeff` to your own PythonAnywhere username in the server URL.