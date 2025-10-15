#!/usr/bin/env python3
"""
AI Server - Flask-based REST API server for processing AI requests through Together.ai
Based on requirements in ai_server_requirements.md
"""

import os
import json
import uuid
import time
import threading
import logging
import certifi
from datetime import datetime, timezone
from queue import Queue, Empty
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify
from flask_cors import CORS
from together import Together

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class JobRequest:
    """Represents a job request in the queue"""
    id: str
    app_code: str
    request_type: str
    request_text: str
    timestamp: datetime
    status: str = "queued"  # queued, processing, completed, error, expired
    position: int = 0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None

class AIJobQueue:
    """Manages the job queue and processing"""
    
    def __init__(self, max_size: int = 100, timeout: int = 300):
        self.queue = Queue(maxsize=max_size)
        self.jobs: Dict[str, JobRequest] = {}
        self.max_size = max_size
        self.timeout = timeout
        self.workers = []
        self.together_client = None
        self.app_config = {}
        self.lock = threading.Lock()
        
        # Initialize Together.ai client
        self._init_together_client()
        
        # Load app configuration
        self._load_app_config()
        
        # Start worker threads
        self._start_workers(num_workers=3)
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def _init_together_client(self):
        """Initialize Together.ai client"""
        api_key = os.getenv('TOGETHER_AI_API_KEY')
        if not api_key:
            logger.error("TOGETHER_AI_API_KEY environment variable not set")
            raise ValueError("TOGETHER_AI_API_KEY environment variable is required")
        
        try:
            # Check for Zscaler certificate bundle first
            zscaler_cert_paths = [
                "/opt/zscaler/cert/cacert.pem",
                "/usr/local/share/ca-certificates/zscaler.crt", 
                "/etc/ssl/certs/zscaler.pem",
                os.path.expanduser("~/zscaler_cert.pem"),
                "./zscaler_cert.pem"
            ]
            
            cert_file = None
            for path in zscaler_cert_paths:
                if os.path.exists(path):
                    cert_file = path
                    logger.info(f"Found Zscaler certificate at: {cert_file}")
                    break
            
            if cert_file:
                # Use Zscaler certificate bundle
                os.environ['REQUESTS_CA_BUNDLE'] = cert_file
                os.environ['SSL_CERT_FILE'] = cert_file
                logger.info("Using Zscaler certificate bundle for SSL verification")
            else:
                # Fallback to default certificate bundle
                os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
                os.environ['SSL_CERT_FILE'] = certifi.where()
                logger.info("Using default certificate bundle for SSL verification")
            
            # Initialize Together client normally
            self.together_client = Together(api_key=api_key)
            logger.info("Together.ai client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Together.ai client: {e}")
            raise
    
    def _load_app_config(self):
        """Load app configuration from JSON file"""
        config_path = "config/ai_app_config.json"
        try:
            with open(config_path, 'r') as f:
                self.app_config = json.load(f)
            logger.info(f"Loaded app configuration from {config_path}")
        except FileNotFoundError:
            logger.warning(f"App config file {config_path} not found, using default config")
            self.app_config = {
                "app_codes": {
                    "flashcards_app_001": {
                        "name": "FlashCards App",
                        "allowed_request_types": [
                            "generate_flashcard",
                            "explain_concept",
                            "create_quiz",
                            "summarize_content"
                        ],
                        "rate_limit": "100/hour",
                        "max_tokens": 1000,
                        "temperature": 0.7
                    }
                }
            }
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in app config file: {e}")
            raise
    
    def _start_workers(self, num_workers: int = 3):
        """Start worker threads for processing jobs"""
        for i in range(num_workers):
            worker = threading.Thread(target=self._worker, name=f"AIWorker-{i+1}")
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        logger.info(f"Started {num_workers} worker threads")
    
    def _start_cleanup_thread(self):
        """Start cleanup thread for expired jobs"""
        cleanup_thread = threading.Thread(target=self._cleanup_expired_jobs, name="CleanupWorker")
        cleanup_thread.daemon = True
        cleanup_thread.start()
        logger.info("Started cleanup thread")
    
    def _worker(self):
        """Worker thread function to process jobs"""
        while True:
            try:
                # Get job from queue with timeout
                job_id = self.queue.get(timeout=1)
                
                with self.lock:
                    if job_id not in self.jobs:
                        continue
                    job = self.jobs[job_id]
                    job.status = "processing"
                
                logger.info(f"Processing job {job_id}")
                
                # Process the job
                self._process_job(job)
                
                self.queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
                if 'job' in locals():
                    with self.lock:
                        job.status = "error"
                        job.error_code = "SYSTEM_ERROR"
                        job.error_message = str(e)
    
    def _process_job(self, job: JobRequest):
        """Process a single job by calling Together.ai"""
        try:
            # Get app configuration
            app_config = self.app_config.get("app_codes", {}).get(job.app_code, {})
            max_tokens = app_config.get("max_tokens", 1000)
            temperature = app_config.get("temperature", 0.7)
            
            # Create the AI request
            completion = self.together_client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                messages=[
                    {
                        "role": "user",
                        "content": job.request_text,
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract response data
            ai_response = completion.choices[0].message.content
            
            # Prepare result
            result = {
                "ai_response": ai_response,
                "model_used": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                "completion_time": datetime.now(timezone.utc).isoformat(),
                "token_usage": {
                    "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                    "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                    "total_tokens": completion.usage.total_tokens if completion.usage else 0
                }
            }
            
            with self.lock:
                job.status = "completed"
                job.result = result
            
            logger.info(f"Successfully processed job {job.id}")
            
        except Exception as e:
            logger.error(f"Error processing job {job.id}: {e}")
            with self.lock:
                job.status = "error"
                job.error_code = "AI_SERVICE_ERROR"
                job.error_message = str(e)
    
    def _cleanup_expired_jobs(self):
        """Cleanup thread to remove expired jobs"""
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                expired_jobs = []
                
                with self.lock:
                    for job_id, job in self.jobs.items():
                        time_diff = (current_time - job.timestamp).total_seconds()
                        if time_diff > self.timeout:
                            if job.status in ["queued", "processing"]:
                                job.status = "expired"
                                job.error_code = "TIMEOUT"
                                job.error_message = "Request timed out"
                            # Mark for removal if completed/error/expired for more than 1 hour
                            elif time_diff > 3600:
                                expired_jobs.append(job_id)
                
                # Remove expired jobs
                for job_id in expired_jobs:
                    with self.lock:
                        del self.jobs[job_id]
                        logger.info(f"Removed expired job {job_id}")
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Cleanup thread error: {e}")
                time.sleep(60)
    
    def validate_request(self, app_code: str, request_type: str) -> tuple[bool, str]:
        """Validate app code and request type"""
        if not app_code:
            return False, "INVALID_APP_CODE"
        
        app_config = self.app_config.get("app_codes", {}).get(app_code)
        if not app_config:
            return False, "INVALID_APP_CODE"
        
        allowed_types = app_config.get("allowed_request_types", [])
        if request_type not in allowed_types:
            return False, "UNSUPPORTED_REQUEST_TYPE"
        
        return True, ""
    
    def add_job(self, app_code: str, request_type: str, request_text: str) -> tuple[bool, str, str]:
        """Add a new job to the queue"""
        try:
            # Validate request
            is_valid, error_code = self.validate_request(app_code, request_type)
            if not is_valid:
                return False, "", error_code
            
            # Check if queue is full
            if self.queue.qsize() >= self.max_size:
                return False, "", "QUEUE_FULL"
            
            # Create job
            job_id = str(uuid.uuid4())
            job = JobRequest(
                id=job_id,
                app_code=app_code,
                request_type=request_type,
                request_text=request_text,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Add to jobs dict and queue
            with self.lock:
                self.jobs[job_id] = job
                self.queue.put(job_id)
                
                # Update positions for all queued jobs
                self._update_queue_positions()
            
            logger.info(f"Added job {job_id} to queue")
            return True, job_id, ""
            
        except Exception as e:
            logger.error(f"Error adding job to queue: {e}")
            return False, "", "SYSTEM_ERROR"
    
    def _update_queue_positions(self):
        """Update position numbers for queued jobs"""
        queued_jobs = [job for job in self.jobs.values() if job.status == "queued"]
        queued_jobs.sort(key=lambda x: x.timestamp)
        
        for i, job in enumerate(queued_jobs, 1):
            job.position = i
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a job"""
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return None
            
            if job.status == "queued":
                return {
                    "status": "queued",
                    "position": job.position,
                    "estimated_wait_time": f"{job.position * 30} seconds",
                    "message": "Request is in queue"
                }
            elif job.status == "processing":
                return {
                    "status": "processing",
                    "message": "Request is currently being processed"
                }
            elif job.status == "completed":
                return {
                    "status": "completed",
                    "response": job.result
                }
            elif job.status in ["error", "expired"]:
                return {
                    "status": "error",
                    "error_code": job.error_code,
                    "message": job.error_message,
                    "retry_possible": job.error_code != "TIMEOUT"
                }
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        with self.lock:
            total_jobs = len(self.jobs)
            queued_count = sum(1 for job in self.jobs.values() if job.status == "queued")
            processing_count = sum(1 for job in self.jobs.values() if job.status == "processing")
            completed_count = sum(1 for job in self.jobs.values() if job.status == "completed")
            error_count = sum(1 for job in self.jobs.values() if job.status in ["error", "expired"])
            
            return {
                "queue_size": queued_count,
                "processing": processing_count,
                "total_jobs": total_jobs,
                "completed": completed_count,
                "errors": error_count,
                "active_workers": len(self.workers)
            }

# Initialize Flask app and job queue
app = Flask(__name__)
CORS(app)  # Enable CORS for cross-domain requests

# Global job queue instance
job_queue = None

def init_server():
    """Initialize the server components"""
    global job_queue
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Initialize job queue
    max_queue_size = int(os.getenv('QUEUE_MAX_SIZE', '100'))
    request_timeout = int(os.getenv('REQUEST_TIMEOUT', '300'))
    
    job_queue = AIJobQueue(max_size=max_queue_size, timeout=request_timeout)
    logger.info("AI Server initialized successfully")

@app.route('/ai_request', methods=['POST'])
def ai_request():
    """Handle AI request submissions"""
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error_code": "INVALID_REQUEST",
                "message": "Request body must be valid JSON"
            }), 400
        
        app_code = data.get('app_code')
        request_type = data.get('request_type')
        request_text = data.get('request')
        
        # Validate required fields
        if not all([app_code, request_type, request_text]):
            return jsonify({
                "status": "error",
                "error_code": "INVALID_REQUEST",
                "message": "Missing required fields: app_code, request_type, request"
            }), 400
        
        # Add job to queue
        success, job_id, error_code = job_queue.add_job(app_code, request_type, request_text)
        
        if success:
            return jsonify({
                "status": "success",
                "request_id": job_id,
                "message": "Request queued successfully"
            }), 200
        else:
            error_messages = {
                "INVALID_APP_CODE": "Invalid application code",
                "UNSUPPORTED_REQUEST_TYPE": "Unsupported request type for this application",
                "QUEUE_FULL": "Server queue is full, please try again later",
                "SYSTEM_ERROR": "Internal server error"
            }
            
            status_codes = {
                "INVALID_APP_CODE": 401,
                "UNSUPPORTED_REQUEST_TYPE": 403,
                "QUEUE_FULL": 503,
                "SYSTEM_ERROR": 500
            }
            
            return jsonify({
                "status": "error",
                "error_code": error_code,
                "message": error_messages.get(error_code, "Unknown error")
            }), status_codes.get(error_code, 500)
            
    except Exception as e:
        logger.error(f"Error in ai_request endpoint: {e}")
        return jsonify({
            "status": "error",
            "error_code": "SYSTEM_ERROR",
            "message": "Internal server error"
        }), 500

@app.route('/get_request/<request_id>', methods=['GET'])
def get_request(request_id):
    """Get the status of a request"""
    try:
        status = job_queue.get_job_status(request_id)
        
        if status is None:
            return jsonify({
                "status": "error",
                "error_code": "REQUEST_NOT_FOUND",
                "message": "Request ID not found"
            }), 404
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Error in get_request endpoint: {e}")
        return jsonify({
            "status": "error",
            "error_code": "SYSTEM_ERROR",
            "message": "Internal server error"
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        stats = job_queue.get_queue_stats()
        
        # Calculate uptime (simplified - would be better to track actual start time)
        uptime = "Running"
        
        # Check Together.ai status (simplified)
        together_ai_status = "connected" if job_queue.together_client else "disconnected"
        
        return jsonify({
            "status": "healthy",
            "queue_size": stats["queue_size"],
            "active_workers": stats["active_workers"],
            "uptime": uptime,
            "together_ai_status": together_ai_status,
            "stats": stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error in health endpoint: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/', methods=['GET'])
def index():
    """Root endpoint to verify the server is running"""
    try:
        stats = job_queue.get_queue_stats() if job_queue else {"message": "Initializing..."}
        
        return jsonify({
            "message": "AI Server is running on Python Anywhere",
            "status": "healthy",
            "version": "1.0",
            "endpoints": [
                "/health",
                "/ai_request", 
                "/get_request/<request_id>"
            ],
            "stats": stats
        }), 200
    except Exception as e:
        logger.error(f"Error in index endpoint: {e}")
        return jsonify({
            "status": "error",
            "message": "Server error",
            "error": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "status": "error",
        "error_code": "ENDPOINT_NOT_FOUND",
        "message": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "status": "error",
        "error_code": "INTERNAL_SERVER_ERROR",
        "message": "Internal server error"
    }), 500

init_server()
if __name__ == '__main__':
    # Initialize server

    
    # Get configuration from environment
    port = int(os.getenv('SERVER_PORT', '5000'))
    debug = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    host = os.getenv('SERVER_HOST', '0.0.0.0')
    
    logger.info(f"Starting AI Server on {host}:{port}")
    
    # Start Flask app
    app.run(host=host, port=port, debug=debug, threaded=True)
