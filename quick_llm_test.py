#!/usr/bin/env python3
"""Quick LLM Test - Single prompt"""

import requests
import json
import sys

def quick_test(prompt):
    """Send a quick prompt to Ollama"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:latest",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(result.get('response', ''))
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = input("Enter your prompt: ")
    
    quick_test(prompt) 