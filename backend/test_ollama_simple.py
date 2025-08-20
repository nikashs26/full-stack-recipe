#!/usr/bin/env python3
"""
Very simple Ollama test
"""

import requests
import json

def test_ollama_simple():
    """Test Ollama with a very simple request"""
    print("🧪 Testing Ollama with simple request")
    print("=" * 50)
    
    # Very simple prompt
    prompt = "Say hello in one word."
    
    payload = {
        "model": "llama3:8b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "max_tokens": 50
        }
    }
    
    print(f"Prompt: {prompt}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        print("\nSending request to Ollama...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=10  # Very short timeout
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result.get('response', 'No response')}")
            print("✅ Success!")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ollama_simple()
