#!/usr/bin/env python3
"""
Debug test to see what's different between curl and Python requests
"""

import requests
import json

def test_ollama_debug():
    """Test Ollama with debug info"""
    print("🧪 Testing Ollama with debug info")
    print("=" * 50)
    
    # Use the exact same payload that worked with curl
    payload = {
        "model": "llama3.2:latest",
        "prompt": "Hi",
        "stream": False,
        "options": {
            "max_tokens": 10
        }
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        print("\nSending request to Ollama...")
        
        # Try with different timeout settings
        for timeout in [5, 10, 15, 30]:
            print(f"\nTrying with {timeout}s timeout...")
            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json=payload,
                    timeout=timeout,
                    headers={'Content-Type': 'application/json'}
                )
                
                print(f"Status code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"Response: {result.get('response', 'No response')}")
                    print("✅ Success!")
                    return
                else:
                    print(f"Error: {response.text}")
                    
            except requests.exceptions.Timeout:
                print(f"❌ Request timed out after {timeout}s")
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ General error: {e}")

if __name__ == "__main__":
    test_ollama_debug()
