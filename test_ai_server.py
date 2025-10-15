#!/usr/bin/env python3
"""
AI Server Test Script
Tests the AI server endpoints with sample requests
"""

import requests
import json
import time
import sys

def test_ai_server(base_url="http://localhost:5000"):
    """Test the AI server endpoints"""
    
    print("Testing AI Server...")
    print(f"Base URL: {base_url}")
    print("-" * 50)
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return False
    
    print("\n" + "-" * 50)
    
    # Test 2: Valid AI request
    print("2. Testing valid AI request...")
    test_request = {
        "app_code": "flashcards_app_001",
        "request_type": "explain_concept",
        "request": "Explain the concept of photosynthesis in simple terms"
    }
    
    try:
        response = requests.post(f"{base_url}/ai_request", json=test_request)
        print(f"Status: {response.status_code}")
        response_data = response.json()
        print(f"Response: {json.dumps(response_data, indent=2)}")
        
        if response.status_code == 200 and response_data.get("status") == "success":
            request_id = response_data.get("request_id")
            print(f"\nRequest ID: {request_id}")
            
            # Test 3: Check request status
            print("\n3. Checking request status...")
            for i in range(10):  # Check status up to 10 times
                time.sleep(2)  # Wait 2 seconds between checks
                
                try:
                    status_response = requests.get(f"{base_url}/get_request/{request_id}")
                    print(f"Status check {i+1}: {status_response.status_code}")
                    status_data = status_response.json()
                    print(f"Status: {status_data.get('status')}")
                    
                    if status_data.get("status") == "completed":
                        print("Request completed!")
                        print(f"AI Response: {status_data.get('response', {}).get('ai_response', 'No response')}")
                        break
                    elif status_data.get("status") == "error":
                        print(f"Request failed: {status_data.get('message')}")
                        break
                    elif status_data.get("status") == "queued":
                        print(f"Position in queue: {status_data.get('position')}")
                    elif status_data.get("status") == "processing":
                        print("Request is being processed...")
                        
                except Exception as e:
                    print(f"Status check failed: {e}")
                    break
                    
        else:
            print("AI request failed")
            
    except Exception as e:
        print(f"AI request failed: {e}")
    
    print("\n" + "-" * 50)
    
    # Test 4: Invalid app code
    print("4. Testing invalid app code...")
    invalid_request = {
        "app_code": "invalid_code",
        "request_type": "test",
        "request": "Test request"
    }
    
    try:
        response = requests.post(f"{base_url}/ai_request", json=invalid_request)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Invalid app code test failed: {e}")
    
    print("\n" + "-" * 50)
    
    # Test 5: Invalid request type
    print("5. Testing invalid request type...")
    invalid_type_request = {
        "app_code": "flashcards_app_001",
        "request_type": "invalid_type",
        "request": "Test request"
    }
    
    try:
        response = requests.post(f"{base_url}/ai_request", json=invalid_type_request)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Invalid request type test failed: {e}")
    
    print("\nTesting completed!")

if __name__ == "__main__":
    # Allow custom base URL as command line argument
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    test_ai_server(base_url)