#!/usr/bin/env python3
"""
Test the new generate_card_from_description feature
"""

import requests
import json

def test_card_generation():
    """Test the new card generation feature"""
    
    # Sample data structure as it would come from the client
    request_data = {
        "set_description": "Linux File System & Navigation - Learn basic Linux file system concepts and navigation commands",
        "example_cards": [
            {
                "information": "What command is used to list files and directories in the current directory?",
                "answer": "ls command. Use 'ls' to list files, 'ls -l' for detailed listing, 'ls -a' to show hidden files."
            },
            {
                "information": "How do you change to a different directory in Linux?",
                "answer": "cd command. Use 'cd /path/to/directory' to change to specific directory, 'cd ..' to go up one level, 'cd ~' to go to home directory."
            }
        ]
    }
    
    # Create the request payload
    payload = {
        "app_code": "flashcards_app_001",
        "request_type": "generate_card_from_description",
        "request": json.dumps(request_data)
    }
    
    print("Testing new card generation feature...")
    print("Request data:")
    print(json.dumps(payload, indent=2))
    print("\n" + "="*60)
    
    try:
        response = requests.post("http://localhost:5000/ai_request", json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Status: {result.get('status')}")
            
            if result.get('status') == 'success':
                print(f"App Name: {result.get('app_name')}")
                print(f"Request Type: {result.get('request_type')}")
                print(f"Model: {result.get('model_used')}")
                print(f"Tokens: {result.get('token_usage', {})}")
                print(f"\n📝 AI Generated Card:")
                print("="*60)
                print(result.get('ai_response', 'No response'))
                print("="*60)
                
                # Try to parse the AI response as JSON
                try:
                    ai_response = result.get('ai_response', '')
                    card_data = json.loads(ai_response)
                    print(f"\n✅ Successfully parsed JSON response:")
                    print(f"Information: {card_data.get('information')}")
                    print(f"Answer: {card_data.get('answer')}")
                except json.JSONDecodeError as e:
                    print(f"\n❌ Failed to parse JSON response: {e}")
                    print("Raw response:", ai_response)
            else:
                print(f"Error: {result.get('error_message')}")
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_card_generation()