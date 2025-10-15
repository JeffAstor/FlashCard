#!/usr/bin/env python3
"""
Together.ai API Test for Zscaler Environment
Tests Together.ai API with corporate proxy/Zscaler certificates
"""

import os
import ssl
import certifi
from together import Together

def test_with_zscaler_certs():
    """Test with Zscaler certificate bundle"""
    print("Testing with Zscaler certificate setup...")
    
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
            print(f"Found Zscaler certificate at: {cert_file}")
            break
    
    if not cert_file:
        print("No Zscaler certificate found. Please ask IT for the certificate bundle.")
        print("Expected locations checked:")
        for path in zscaler_cert_paths:
            print(f"  - {path}")
        return False
    
    try:
        # Set the certificate bundle
        os.environ['REQUESTS_CA_BUNDLE'] = cert_file
        os.environ['SSL_CERT_FILE'] = cert_file
        
        api_key = "<put your key here>"
        
        client = Together(api_key=api_key)
        print("✓ Together client initialized with Zscaler certs")
        
        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            messages=[
                {
                    "role": "user",
                    "content": "Hello from behind Zscaler! What is 10 + 5?",
                }
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        response = completion.choices[0].message.content
        print("✓ API call successful through Zscaler!")
        print(f"\nAI Response: {response}")
        return True
        
    except Exception as e:
        print(f"✗ Error with Zscaler certs: {e}")
        return False

def test_with_proxy_bypass():
    """Test by bypassing SSL verification entirely (for development only)"""
    print("Testing with SSL verification completely disabled (Zscaler bypass)...")
    
    try:
        # Completely disable SSL verification
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # Also disable urllib3 warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Set environment variables
        os.environ['PYTHONHTTPSVERIFY'] = '0'
        os.environ['CURL_CA_BUNDLE'] = ''
        
        api_key = "<put your key here>"
        
        client = Together(api_key=api_key)
        print("✓ Together client initialized (SSL completely disabled)")
        
        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            messages=[
                {
                    "role": "user",
                    "content": "Testing from corporate network. What is the capital of France?",
                }
            ],
            max_tokens=30,
            temperature=0.7
        )
        
        response = completion.choices[0].message.content
        print("✓ API call successful with SSL disabled!")
        print(f"\nAI Response: {response}")
        
        print("\n⚠️  WARNING: SSL verification is completely disabled!")
        print("   This is only suitable for development/testing.")
        print("   For production, get proper Zscaler certificates from IT.")
        
        return True
        
    except Exception as e:
        print(f"✗ Error even with SSL disabled: {e}")
        return False

def test_with_proxy_settings():
    """Test with explicit proxy configuration"""
    print("Testing with proxy settings...")
    
    # Common corporate proxy patterns
    proxy_urls = [
        "http://proxy.company.com:8080",
        "http://zscaler-proxy:8080", 
        "http://localhost:8080"
    ]
    
    # Check if proxy is set in environment
    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    
    if http_proxy or https_proxy:
        print(f"Found proxy settings:")
        print(f"  HTTP_PROXY: {http_proxy}")
        print(f"  HTTPS_PROXY: {https_proxy}")
    else:
        print("No proxy environment variables found.")
        print("If your company uses a proxy, set these environment variables:")
        print("  export HTTP_PROXY=http://proxy.company.com:8080")
        print("  export HTTPS_PROXY=http://proxy.company.com:8080")
    
    return False

if __name__ == "__main__":
    print("Together.ai Zscaler/Corporate Environment Test")
    print("=" * 50)
    
    # Test 1: Try with Zscaler certificates
    print("\n1. Testing with Zscaler certificates:")
    print("-" * 40)
    success1 = test_with_zscaler_certs()
    
    if not success1:
        # Test 2: Check proxy settings
        print("\n2. Checking proxy configuration:")
        print("-" * 40)
        test_with_proxy_settings()
        
        # Test 3: Bypass SSL (development only)
        print("\n3. Testing with SSL completely disabled:")
        print("-" * 40)
        success3 = test_with_proxy_bypass()
        
        if success3:
            print("\n" + "=" * 50)
            print("RECOMMENDATION FOR ZSCALER ENVIRONMENT:")
            print("=" * 50)
            print("1. Contact your IT department for Zscaler root certificates")
            print("2. Save the certificate bundle to a known location")
            print("3. Set environment variables to point to the certificate bundle")
            print("4. For development only: SSL verification can be disabled")
            print("   but this should NEVER be used in production!")
    else:
        print("\n✓ Zscaler configuration working correctly!")
    
    print(f"\nTest completed.")