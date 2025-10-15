#!/usr/bin/env python3
"""
Python Anywhere AI Server V2 Test Script
Tests the simplified AI server without threading
"""

import requests
import json
import sys
import os
import ssl
import urllib3

def setup_zscaler_certificates():
    """Setup Zscaler certificates for corporate environment"""
    print("Setting up Zscaler certificate configuration...")
    
    # Common locations for Zscaler certificates
    zscaler_cert_paths = [
        "/opt/zscaler/cert/cacert.pem",
        "/usr/local/share/ca-certificates/zscaler.crt", 
        "/etc/ssl/certs/zscaler.pem",
        "~/zscaler_cert.pem",
        "./zscaler_cert.pem"
    ]
    
    cert_file = None
    for path in zscaler_cert_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            cert_file = expanded_path
            print(f"✓ Found Zscaler certificate at: {cert_file}")
            break
    
    if cert_file:
        # Set the certificate bundle for requests
        os.environ['REQUESTS_CA_BUNDLE'] = cert_file
        os.environ['SSL_CERT_FILE'] = cert_file
        print("✓ Zscaler certificates configured")
        return True
    else:
        print("⚠️  No Zscaler certificate found at common locations")
        return False

def setup_ssl_bypass():
    """Setup SSL bypass for Zscaler (development only)"""
    print("⚠️  Setting up SSL bypass (development only)...")
    
    # Disable SSL verification completely
    ssl._create_default_https_context = ssl._create_unverified_context
    
    # Disable urllib3 warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Set environment variables
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    os.environ['CURL_CA_BUNDLE'] = ''
    
    print("✓ SSL verification disabled")
    print("⚠️  WARNING: This should only be used for development/testing!")

def test_ai_server_v2(base_url="http://localhost:5000", use_ssl_bypass=False):
    """Test the AI Server V2 endpoints on Python Anywhere"""
    
    # Setup certificate handling (skip for localhost)
    if not base_url.startswith("http://localhost") and not base_url.startswith("http://127.0.0.1"):
        if use_ssl_bypass:
            setup_ssl_bypass()
        else:
            cert_found = setup_zscaler_certificates()
            if not cert_found:
                print("\nNo Zscaler certificates found. You can:")
                print("1. Get Zscaler certificates from your IT department")
                print("2. Run with SSL bypass: python test_pa_v2.py --bypass-ssl")
                print("3. Continue anyway (may fail with SSL errors)")
                
                user_input = input("\nContinue anyway? (y/N): ").lower()
                if user_input != 'y':
                    return False
    
    print(f"\nTesting AI Server V2...")
    print(f"Base URL: {base_url}")
    print("=" * 60)
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        verify_ssl = not use_ssl_bypass
        response = requests.get(f"{base_url}/health", verify=verify_ssl)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Health check failed: {e}")
        if "SSL" in str(e) or "certificate" in str(e).lower():
            print("\n💡 SSL/Certificate error detected!")
            print("Try running with SSL bypass: python test_pa_v2.py --bypass-ssl")
        return False
    
    print("\n" + "-" * 60)
    
    # Test 2: Get available apps
    print("2. Testing apps endpoint...")
    try:
        verify_ssl = not use_ssl_bypass
        response = requests.get(f"{base_url}/apps", verify=verify_ssl)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Apps endpoint failed: {e}")
    
    print("\n" + "-" * 60)
    
    # Test 3: FlashCards App - Explain Concept
    print("3. Testing FlashCards App - Explain Concept...")
    flashcards_request = {
        "app_code": "flashcards_app_001",
        "request_type": "explain_concept",
        "request": "Explain photosynthesis in simple terms"
    }
    
    try:
        verify_ssl = not use_ssl_bypass
        response = requests.post(f"{base_url}/ai_request", json=flashcards_request, verify=verify_ssl)
        print(f"Status: {response.status_code}")
        response_data = response.json()
        print(f"Status: {response_data.get('status')}")
        if response_data.get('status') == 'success':
            print(f"App Name: {response_data.get('app_name')}")
            print(f"Request Type: {response_data.get('request_type')}")
            print(f"Model: {response_data.get('model_used')}")
            print(f"Tokens: {response_data.get('token_usage', {})}")
            print(f"\n📝 AI Response from Together.ai:")
            print(f"{'='*60}")
            print(response_data.get('ai_response', 'No response'))
            print(f"{'='*60}")
        else:
            print(f"Error Code: {response_data.get('error_code')}")
            print(f"Error Message: {response_data.get('error_message')}")
    except Exception as e:
        print(f"FlashCards request failed: {e}")
    
    print("\n" + "-" * 60)
    
    # Test 4: FlashCards App - Generate Flashcard
    print("4. Testing FlashCards App - Generate Flashcard...")
    flashcard_request = {
        "app_code": "flashcards_app_001",
        "request_type": "generate_flashcard",
        "request": "Python list comprehensions"
    }
    
    try:
        verify_ssl = not use_ssl_bypass
        response = requests.post(f"{base_url}/ai_request", json=flashcard_request, verify=verify_ssl)
        print(f"Status: {response.status_code}")
        response_data = response.json()
        print(f"Status: {response_data.get('status')}")
        if response_data.get('status') == 'success':
            print(f"\n📝 Flashcard from Together.ai:")
            print(f"{'='*60}")
            print(response_data.get('ai_response', 'No response'))
            print(f"{'='*60}")
        else:
            print(f"Error: {response_data.get('error_message')}")
    except Exception as e:
        print(f"Generate flashcard request failed: {e}")
    
    print("\n" + "-" * 60)
    
    # Test 5: Generic AI App
    print("5. Testing Generic AI App...")
    generic_request = {
        "app_code": "generic_ai_001",
        "request_type": "prompt",
        "request": "Describe a pomeranian dog"
    }
    
    try:
        verify_ssl = not use_ssl_bypass
        response = requests.post(f"{base_url}/ai_request", json=generic_request, verify=verify_ssl)
        print(f"Status: {response.status_code}")
        response_data = response.json()
        print(f"Status: {response_data.get('status')}")
        if response_data.get('status') == 'success':
            print(f"App Name: {response_data.get('app_name')}")
            print(f"\n🐕 Pomeranian Description from Together.ai:")
            print(f"{'='*60}")
            print(response_data.get('ai_response', 'No response'))
            print(f"{'='*60}")
        else:
            print(f"Error: {response_data.get('error_message')}")
    except Exception as e:
        print(f"Generic AI request failed: {e}")
    
    print("\n" + "-" * 60)
    
    # Test 6: Invalid app code
    print("6. Testing invalid app code...")
    invalid_app_request = {
        "app_code": "invalid_app",
        "request_type": "test",
        "request": "Test request"
    }
    
    try:
        verify_ssl = not use_ssl_bypass
        response = requests.post(f"{base_url}/ai_request", json=invalid_app_request, verify=verify_ssl)
        print(f"Status: {response.status_code}")
        response_data = response.json()
        print(f"Status: {response_data.get('status')}")
        print(f"Error Code: {response_data.get('error_code')}")
        print(f"Error Message: {response_data.get('error_message')}")
    except Exception as e:
        print(f"Invalid app code test failed: {e}")
    
    print("\n" + "-" * 60)
    
    # Test 7: Invalid request type for FlashCards
    print("7. Testing invalid request type for FlashCards...")
    invalid_type_request = {
        "app_code": "flashcards_app_001",
        "request_type": "invalid_type",
        "request": "Test request"
    }
    
    try:
        verify_ssl = not use_ssl_bypass
        response = requests.post(f"{base_url}/ai_request", json=invalid_type_request, verify=verify_ssl)
        print(f"Status: {response.status_code}")
        response_data = response.json()
        print(f"Status: {response_data.get('status')}")
        print(f"Error Code: {response_data.get('error_code')}")
        print(f"Error Message: {response_data.get('error_message')}")
    except Exception as e:
        print(f"Invalid request type test failed: {e}")
    
    print("\n" + "-" * 60)
    
    # Test 8: Missing fields
    print("8. Testing missing fields...")
    incomplete_request = {
        "app_code": "flashcards_app_001",
        # Missing request_type and request
    }
    
    try:
        verify_ssl = not use_ssl_bypass
        response = requests.post(f"{base_url}/ai_request", json=incomplete_request, verify=verify_ssl)
        print(f"Status: {response.status_code}")
        response_data = response.json()
        print(f"Status: {response_data.get('status')}")
        print(f"Error Code: {response_data.get('error_code')}")
        print(f"Error Message: {response_data.get('error_message')}")
    except Exception as e:
        print(f"Missing fields test failed: {e}")
    
    print("\n" + "-" * 60)
    
    # Test 9: FlashCards App - Create Quiz
    print("9. Testing FlashCards App - Create Quiz...")
    quiz_request = {
        "app_code": "flashcards_app_001",
        "request_type": "create_quiz",
        "request": "Basic Python programming concepts"
    }
    
    try:
        verify_ssl = not use_ssl_bypass
        response = requests.post(f"{base_url}/ai_request", json=quiz_request, verify=verify_ssl)
        print(f"Status: {response.status_code}")
        response_data = response.json()
        print(f"Status: {response_data.get('status')}")
        if response_data.get('status') == 'success':
            print(f"\n📚 Quiz from Together.ai:")
            print(f"{'='*60}")
            print(response_data.get('ai_response', 'No response'))
            print(f"{'='*60}")
        else:
            print(f"Error: {response_data.get('error_message')}")
    except Exception as e:
        print(f"Create quiz request failed: {e}")
    
    print("\n" + "=" * 60)
    print("Testing completed!")
    print("\nSUMMARY:")
    print("- AI Server V2 uses direct response (no threading)")
    print("- FlashCards App supports: generate_flashcard, explain_concept, create_quiz, summarize_content")
    print("- Generic AI App supports: prompt")
    print("- All responses include complete AI output immediately")
    
    return True  # Tests completed successfully

def show_usage():
    """Show usage information"""
    print("AI Server V2 Test Script")
    print("=" * 40)
    print("Usage:")
    print("  python test_pa_v2.py [URL] [--bypass-ssl]")
    print()
    print("Examples:")
    print("  python test_pa_v2.py")
    print("  python test_pa_v2.py https://yourusername.pythonanywhere.com")
    print("  python test_pa_v2.py --bypass-ssl")
    print("  python test_pa_v2.py https://yourusername.pythonanywhere.com --bypass-ssl")
    print()
    print("Notes:")
    print("- Default URL: http://localhost:5000")
    print("- --bypass-ssl disables SSL verification (development only)")
    print("- This version tests the simplified server without threading")

if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        show_usage()
        sys.exit(0)
    
    print("AI Server V2 Test Script")
    print("=" * 40)
    print("This tests the simplified AI server without threading")
    print("Responses are returned directly without request IDs")
    print("=" * 40)
    
    # Parse command line arguments
    use_ssl_bypass = "--bypass-ssl" in sys.argv
    
    # Remove --bypass-ssl from argv before processing URL
    if use_ssl_bypass:
        sys.argv.remove("--bypass-ssl")
    
    # Allow custom base URL as command line argument
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    if use_ssl_bypass:
        print("🔓 SSL bypass mode enabled (development only)")
    
    success = test_ai_server_v2(base_url, use_ssl_bypass)
    
    if not success:
        print("\n❌ Tests failed to run. Check your connection and SSL configuration.")
        sys.exit(1)
    else:
        print("\n✅ Tests completed successfully!")