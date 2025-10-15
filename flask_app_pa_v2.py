#!/usr/bin/env python3
"""
AI Server - Flask WSGI app for Python Anywhere (Version 2)
Simplified version without threading - returns results directly
Uses app-specific classes for better organization
"""

import os
import json
import logging
import traceback
import certifi
import urllib3
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from flask import Flask, request, jsonify
from flask_cors import CORS
from together import Together

# Configure logging for Python Anywhere
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Only use console logging on Python Anywhere
    ]
)
logger = logging.getLogger(__name__)

class BaseApp(ABC):
    """Base class for all app implementations"""
    
    def __init__(self, app_code: str, name: str, together_client: Together):
        self.app_code = app_code
        self.name = name
        self.together_client = together_client
        self.config = self._get_default_config()
    
    @abstractmethod
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for this app"""
        pass
    
    @abstractmethod
    def get_allowed_request_types(self) -> list:
        """Get list of allowed request types for this app"""
        pass
    
    @abstractmethod
    def process_request(self, request_type: str, request_text: str) -> Dict[str, Any]:
        """Process a request and return the result"""
        pass
    
    def validate_request_type(self, request_type: str) -> bool:
        """Validate if the request type is allowed for this app"""
        return request_type in self.get_allowed_request_types()

class FlashCardsApp(BaseApp):
    """FlashCards application implementation"""
    
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "max_tokens": 1000,
            "temperature": 0.7,
            "rate_limit": "100/hour"
        }
    
    def get_allowed_request_types(self) -> list:
        return [
            "generate_flashcard",
            "explain_concept",
            "create_quiz",
            "summarize_content",
            "generate_card_from_description"
        ]
    
    def process_request(self, request_type: str, request_text: str) -> Dict[str, Any]:
        """Process FlashCards specific requests"""
        logger.info(f"[FLASHCARDS] Processing {request_type}: {request_text[:50]}...")
        
        try:
            # Customize prompt based on request type
            if request_type == "generate_flashcard":
                prompt = f"Create a flashcard for the following topic. Provide a clear question on one side and a comprehensive answer on the other side. Topic: {request_text}"
            elif request_type == "explain_concept":
                prompt = f"Explain the following concept in simple, clear terms that are easy to understand: {request_text}"
            elif request_type == "create_quiz":
                prompt = f"Create a quiz with 5 multiple choice questions about: {request_text}. Include the correct answers."
            elif request_type == "summarize_content":
                prompt = f"Summarize the following content in a concise and organized manner: {request_text}"
            elif request_type == "generate_card_from_description":
                prompt = self._create_card_generation_prompt(request_text)
            else:
                prompt = request_text
            
            # Make API call to Together.ai
            completion = self.together_client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                max_tokens=self.config["max_tokens"],
                temperature=self.config["temperature"]
            )
            
            ai_response = completion.choices[0].message.content
            
            return {
                "status": "success",
                "ai_response": ai_response,
                "app_name": self.name,
                "request_type": request_type,
                "model_used": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                "completion_time": datetime.now(timezone.utc).isoformat(),
                "token_usage": {
                    "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                    "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                    "total_tokens": completion.usage.total_tokens if completion.usage else 0
                }
            }
            
        except Exception as e:
            logger.error(f"[FLASHCARDS] Error processing request: {e}")
            logger.error(f"[FLASHCARDS] Traceback: {traceback.format_exc()}")
            
            return {
                "status": "error",
                "error_code": "AI_SERVICE_ERROR",
                "error_message": str(e),
                "app_name": self.name,
                "request_type": request_type
            }

    def _create_card_generation_prompt(self, request_text: str) -> str:
        """Create specialized prompt for card generation from description and examples"""
        try:
            # Parse the request data (expecting JSON)
            request_data = json.loads(request_text)
            set_description = request_data.get('set_description', '')
            example_cards = request_data.get('example_cards', [])
            
            prompt = f"""Create a new flashcard based on the following flashcard set description and examples.

SET DESCRIPTION:
{set_description}

EXISTING CARD EXAMPLES:
"""
            
            if example_cards:
                for i, card in enumerate(example_cards, 1):
                    prompt += f"\nExample {i}:\n"
                    prompt += f"Information: {card.get('information', 'N/A')}\n"
                    prompt += f"Answer: {card.get('answer', 'N/A')}\n"
            else:
                prompt += "No existing cards provided.\n"
            
            prompt += """

INSTRUCTIONS:
1. Create a NEW flashcard that fits the theme and style of the set
2. The flashcard should complement the existing cards without duplicating them
3. Follow the same format and difficulty level as the examples
4. Respond ONLY with valid JSON in this exact format:

{
  "information": "Your question or topic text here",
  "answer": "Your answer or explanation text here"
}

Do not include any other text, explanations, or formatting outside the JSON response."""
            
            return prompt
            
        except json.JSONDecodeError as e:
            logger.error(f"[FLASHCARDS] Invalid JSON in card generation request: {e}")
            return f"Create a flashcard based on this description: {request_text}"
        except Exception as e:
            logger.error(f"[FLASHCARDS] Error creating card generation prompt: {e}")
            return f"Create a flashcard based on this description: {request_text}"

class GenericAIApp(BaseApp):
    """Generic AI application for general prompts"""
    
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "max_tokens": 1500,
            "temperature": 0.8,
            "rate_limit": "50/hour"
        }
    
    def get_allowed_request_types(self) -> list:
        return ["prompt"]
    
    def process_request(self, request_type: str, request_text: str) -> Dict[str, Any]:
        """Process generic AI prompts"""
        logger.info(f"[GENERIC_AI] Processing {request_type}: {request_text[:50]}...")
        
        try:
            # For generic AI, use the request text as-is
            completion = self.together_client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                messages=[
                    {
                        "role": "user",
                        "content": request_text,
                    }
                ],
                max_tokens=self.config["max_tokens"],
                temperature=self.config["temperature"]
            )
            
            ai_response = completion.choices[0].message.content
            
            return {
                "status": "success",
                "ai_response": ai_response,
                "app_name": self.name,
                "request_type": request_type,
                "model_used": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                "completion_time": datetime.now(timezone.utc).isoformat(),
                "token_usage": {
                    "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                    "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                    "total_tokens": completion.usage.total_tokens if completion.usage else 0
                }
            }
            
        except Exception as e:
            logger.error(f"[GENERIC_AI] Error processing request: {e}")
            logger.error(f"[GENERIC_AI] Traceback: {traceback.format_exc()}")
            
            return {
                "status": "error",
                "error_code": "AI_SERVICE_ERROR",
                "error_message": str(e),
                "app_name": self.name,
                "request_type": request_type
            }

class AIServerV2:
    """Simplified AI Server without threading"""
    
    def __init__(self):
        self.together_client = None
        self.apps: Dict[str, BaseApp] = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize the AI server"""
        if self._initialized:
            logger.info("AI Server already initialized, skipping")
            return
        
        logger.info("Starting AI Server V2 initialization...")
        
        try:
            # Initialize Together.ai client
            logger.info("Step 1: Initializing Together.ai client...")
            self._init_together_client()
            logger.info("Step 1: Together.ai client initialized successfully")
            
            # Initialize applications
            logger.info("Step 2: Initializing applications...")
            self._init_apps()
            logger.info("Step 2: Applications initialized successfully")
            
            self._initialized = True
            logger.info("AI Server V2 initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Server V2: {e}")
            logger.error(f"Initialization traceback: {traceback.format_exc()}")
            raise
    
    def _init_together_client(self):
        """Initialize Together.ai client with proper SSL handling"""
        # Get API key
        api_key = '<put your key here>'  # Your API key
        if not api_key:
            logger.error("TOGETHER_AI_API_KEY environment variable not set")
            raise ValueError("TOGETHER_AI_API_KEY environment variable is required")
        
        try:
            # Setup SSL certificates
            zscaler_cert_paths = [
                "/opt/zscaler/cert/cacert.pem",
                "/usr/local/share/ca-certificates/zscaler.crt", 
                "/etc/ssl/certs/zscaler.pem",
                os.path.expanduser("~/zscaler_cert.pem"),
                "./zscaler_cert.pem",
                "/home/FiretTripperJeff/mysite/zscaler_cert.pem"
            ]
            
            cert_file = None
            for path in zscaler_cert_paths:
                if os.path.exists(path):
                    cert_file = path
                    logger.info(f"Found Zscaler certificate at: {cert_file}")
                    break
            
            if cert_file:
                os.environ['REQUESTS_CA_BUNDLE'] = cert_file
                os.environ['SSL_CERT_FILE'] = cert_file
                logger.info("Using Zscaler certificate bundle for SSL verification")
            else:
                os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
                os.environ['SSL_CERT_FILE'] = certifi.where()
                logger.info("Using default certificate bundle for SSL verification")
            
            # Initialize Together client
            self.together_client = Together(api_key=api_key)
            logger.info("Together.ai client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Together.ai client: {e}")
            logger.error(f"SSL/Certificate error details: {str(e)}")
            # Try alternative SSL approach
            try:
                logger.info("Attempting alternative SSL configuration...")
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                self.together_client = Together(api_key=api_key)
                logger.warning("Initialized with alternative SSL configuration")
            except Exception as e2:
                logger.error(f"Alternative SSL initialization also failed: {e2}")
                raise
    
    def _init_apps(self):
        """Initialize all supported applications"""
        # FlashCards App
        flashcards_app = FlashCardsApp(
            app_code="flashcards_app_001",
            name="FlashCards App",
            together_client=self.together_client
        )
        self.apps["flashcards_app_001"] = flashcards_app
        logger.info("Initialized FlashCards App")
        
        # Generic AI App
        generic_ai_app = GenericAIApp(
            app_code="generic_ai_001",
            name="Generic AI",
            together_client=self.together_client
        )
        self.apps["generic_ai_001"] = generic_ai_app
        logger.info("Initialized Generic AI App")
        
        logger.info(f"Total apps initialized: {len(self.apps)}")
    
    def validate_request(self, app_code: str, request_type: str) -> tuple[bool, str, str]:
        """Validate app code and request type"""
        if not app_code:
            return False, "INVALID_APP_CODE", "App code is required"
        
        if app_code not in self.apps:
            return False, "INVALID_APP_CODE", f"Unknown app code: {app_code}"
        
        app = self.apps[app_code]
        if not app.validate_request_type(request_type):
            allowed_types = app.get_allowed_request_types()
            return False, "UNSUPPORTED_REQUEST_TYPE", f"Request type '{request_type}' not supported. Allowed types: {allowed_types}"
        
        return True, "", ""
    
    def process_request(self, app_code: str, request_type: str, request_text: str) -> Dict[str, Any]:
        """Process a request and return the result directly"""
        try:
            # Ensure initialization
            if not self._initialized:
                self.initialize()
            
            # Validate request
            is_valid, error_code, error_message = self.validate_request(app_code, request_type)
            if not is_valid:
                return {
                    "status": "error",
                    "error_code": error_code,
                    "error_message": error_message
                }
            
            # Process request with the appropriate app
            app = self.apps[app_code]
            result = app.process_request(request_type, request_text)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            logger.error(f"Process request traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "error_code": "SYSTEM_ERROR",
                "error_message": str(e)
            }
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information and available apps"""
        app_info = {}
        for app_code, app in self.apps.items():
            app_info[app_code] = {
                "name": app.name,
                "allowed_request_types": app.get_allowed_request_types(),
                "config": app.config
            }
        
        return {
            "server_version": "2.0",
            "server_type": "direct_response",
            "threading": False,
            "together_ai_status": "connected" if self.together_client else "disconnected",
            "apps": app_info,
            "initialized": self._initialized
        }

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for cross-domain requests

# Create global AI server instance
ai_server = AIServerV2()

# Initialize immediately for Python Anywhere
try:
    logger.info("Attempting module-level AI server initialization...")
    ai_server.initialize()
    logger.info("Module-level AI server initialization successful")
except Exception as e:
    logger.error(f"Failed to initialize AI server at module level: {e}")
    logger.error(f"Module-level init traceback: {traceback.format_exc()}")
    ai_server = None

@app.route('/ai_request', methods=['POST'])
def ai_request():
    """Handle AI request submissions - returns result directly"""
    try:
        # Ensure AI server is initialized
        if ai_server is None or not ai_server._initialized:
            logger.error("AI server not initialized")
            return jsonify({
                "status": "error",
                "error_code": "SERVER_NOT_INITIALIZED",
                "error_message": "AI server is not properly initialized"
            }), 500
        
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error_code": "INVALID_REQUEST",
                "error_message": "Request must contain valid JSON data"
            }), 400
        
        app_code = data.get('app_code')
        request_type = data.get('request_type')
        request_text = data.get('request')
        
        # Validate required fields
        if not all([app_code, request_type, request_text]):
            return jsonify({
                "status": "error",
                "error_code": "MISSING_FIELDS",
                "error_message": "Missing required fields: app_code, request_type, request"
            }), 400
        
        # Process request and return result directly
        result = ai_server.process_request(app_code, request_type, request_text)
        
        # Return result with appropriate status code
        status_code = 200 if result.get("status") == "success" else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Error in ai_request endpoint: {e}")
        return jsonify({
            "status": "error",
            "error_code": "INTERNAL_ERROR",
            "error_message": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Ensure AI server is initialized
        if ai_server is None or not ai_server._initialized:
            return jsonify({
                "status": "unhealthy",
                "message": "AI server not initialized",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 500
        
        server_info = ai_server.get_server_info()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "server_info": server_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error in health endpoint: {e}")
        return jsonify({
            "status": "unhealthy",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/', methods=['GET'])
def index():
    """Root endpoint to verify the app is running"""
    try:
        server_info = ai_server.get_server_info() if ai_server and ai_server._initialized else {}
        
        return jsonify({
            "message": "AI Server V2 is running on Python Anywhere",
            "version": "2.0",
            "features": [
                "Direct response (no threading)",
                "App-specific classes",
                "Simplified architecture"
            ],
            "endpoints": [
                "/health",
                "/ai_request",
                "/apps",
                "/debug/ssl"
            ],
            "server_info": server_info,
            "ssl_info": {
                "requests_ca_bundle": os.getenv('REQUESTS_CA_BUNDLE', 'Not set'),
                "ssl_cert_file": os.getenv('SSL_CERT_FILE', 'Not set')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in index endpoint: {e}")
        return jsonify({
            "message": "AI Server V2 is running (with errors)",
            "version": "2.0",
            "error": str(e)
        }), 200

@app.route('/apps', methods=['GET'])
def get_apps():
    """Get information about available apps and their capabilities"""
    try:
        if ai_server is None or not ai_server._initialized:
            return jsonify({
                "status": "error",
                "error_code": "SERVER_NOT_INITIALIZED",
                "error_message": "AI server not initialized"
            }), 500
        
        server_info = ai_server.get_server_info()
        
        return jsonify({
            "status": "success",
            "apps": server_info["apps"],
            "total_apps": len(server_info["apps"])
        }), 200
        
    except Exception as e:
        logger.error(f"Error in apps endpoint: {e}")
        return jsonify({
            "status": "error",
            "error_code": "INTERNAL_ERROR",
            "error_message": str(e)
        }), 500

@app.route('/debug/ssl', methods=['GET'])
def debug_ssl():
    """Debug endpoint to check SSL and certificate configuration"""
    try:
        import ssl as ssl_module
        
        debug_info = {
            "ssl_context_info": {},
            "certificate_paths": {},
            "environment_variables": {},
            "together_ai_test": {}
        }
        
        # Check SSL context
        try:
            context = ssl_module.create_default_context()
            debug_info["ssl_context_info"] = {
                "check_hostname": context.check_hostname,
                "verify_mode": str(context.verify_mode),
                "protocol": str(context.protocol)
            }
        except Exception as e:
            debug_info["ssl_context_info"]["error"] = str(e)
        
        # Check certificate paths
        debug_info["certificate_paths"]["certifi_where"] = certifi.where()
        debug_info["certificate_paths"]["certifi_exists"] = os.path.exists(certifi.where())
        
        # Check environment variables
        debug_info["environment_variables"] = {
            "REQUESTS_CA_BUNDLE": os.getenv('REQUESTS_CA_BUNDLE', 'Not set'),
            "SSL_CERT_FILE": os.getenv('SSL_CERT_FILE', 'Not set'),
            "PYTHONHTTPSVERIFY": os.getenv('PYTHONHTTPSVERIFY', 'Not set')
        }
        
        # Check Zscaler certificates
        zscaler_paths = [
            "/opt/zscaler/cert/cacert.pem",
            "/usr/local/share/ca-certificates/zscaler.crt", 
            "/etc/ssl/certs/zscaler.pem",
            os.path.expanduser("~/zscaler_cert.pem"),
            "./zscaler_cert.pem",
            "/home/FiretTripperJeff/mysite/zscaler_cert.pem"
        ]
        
        debug_info["certificate_paths"]["zscaler_check"] = {}
        for path in zscaler_paths:
            debug_info["certificate_paths"]["zscaler_check"][path] = os.path.exists(path)
        
        # Test Together.ai connection
        debug_info["together_ai_test"]["client_initialized"] = ai_server.together_client is not None if ai_server else False
        
        return jsonify(debug_info), 200
        
    except Exception as e:
        logger.error(f"Error in debug_ssl endpoint: {e}")
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "status": "error",
        "error_code": "NOT_FOUND",
        "error_message": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "status": "error",
        "error_code": "INTERNAL_SERVER_ERROR",
        "error_message": "Internal server error occurred"
    }), 500

# This is required for Python Anywhere
if __name__ == '__main__':
    app.run(debug=True)