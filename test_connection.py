#!/usr/bin/env python3
"""
Quick test of the AI connection with SSL handling
"""

import requests
import json
import ssl
import urllib3
import os

def setup_ssl_handling():
    """Setup SSL certificate handling for corporate environments"""
    # Common locations for Zscaler certificates
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
            print(f"Found certificate: {cert_file}")
            break
    
    if cert_file:
        # Set the certificate bundle for requests
        os.environ['REQUESTS_CA_BUNDLE'] = cert_file
        os.environ['SSL_CERT_FILE'] = cert_file
        print("Certificate configured")
    else:
        print("No Zscaler certificates found, using system certificates")
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_connection():
    """Test connection to PythonAnywhere server"""
    setup_ssl_handling()
    
    server_url = "https://firettripperjeff.pythonanywhere.com"
    
    # Test data
    request_data = {
        "set_description": "Test set for connection",
        "example_cards": []
    }
    
    payload = {
        "app_code": "flashcards_app_001",
        "request_type": "generate_card_from_description",
        "request": json.dumps(request_data)
    }
    
    print(f"Testing connection to {server_url}")
    
    try:
        # Try with SSL verification first
        print("Attempting with SSL verification...")
        response = requests.post(
            f"{server_url}/ai_request", 
            json=payload, 
            timeout=30,
            verify=True
        )
        print(f"✅ Success with SSL verification! Status: {response.status_code}")
        
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL Error: {e}")
        print("Trying without SSL verification...")
        
        try:
            response = requests.post(
                f"{server_url}/ai_request", 
                json=payload, 
                timeout=30,
                verify=False
            )
            print(f"✅ Success without SSL verification! Status: {response.status_code}")
            
        except Exception as e2:
            print(f"❌ Failed even without SSL verification: {e2}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    # Check response
    if response.status_code == 200:
        result = response.json()
        if result.get("status") == "success":
            print("✅ AI request successful!")
            print(f"Generated card: {result.get('ai_response', 'No response')}")
            return True
        else:
            print(f"❌ AI request failed: {result.get('error_message', 'Unknown error')}")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return False

if __name__ == "__main__":
    success = test_connection()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")