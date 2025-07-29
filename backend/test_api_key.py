import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from the root .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Get the API key
api_key = os.getenv('HUGGINGFACE_API_KEY')

if not api_key:
    print("❌ Error: HUGGINGFACE_API_KEY not found in environment variables")
    print(f"Tried to load from: {env_path}")
    exit(1)

print("🔑 Found HUGGINGFACE_API_KEY in environment variables")
print(f"Key starts with: {api_key[:10]}...")  # Only show first 10 chars for security

# Test the API key with a simple request
import requests

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

try:
    print("\n🔍 Testing Mixtral model access...")
    
    # Test if we can access the model
    model_check = requests.get(
        "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1",
        headers=headers,
        timeout=10
    )
    
    if model_check.status_code == 200:
        print("✅ Success! You have access to the Mixtral model.")
        
        # Try a simple text generation
        print("\n🧪 Testing text generation...")
        data = {
            "inputs": "Generate a short meal plan for Monday:",
            "parameters": {
                "max_length": 100,
                "temperature": 0.7
            }
        }
        
        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1",
            headers=headers,
            json=data,
            timeout=30  # Give it more time for the first request
        )
        
        if response.status_code == 200:
            print("✅ Success! Model response:")
            print(response.json())
        else:
            print(f"❌ Error generating text (status {response.status_code}): {response.text}")
            
    elif model_check.status_code == 401:
        print("❌ Error: Invalid API key. Please check your HUGGINGFACE_API_KEY in the .env file.")
    elif model_check.status_code == 403:
        print("❌ Error: Access forbidden. Please make sure you've accepted the model's terms of use at:")
        print("https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1")
    else:
        print(f"❌ Unexpected response (status code: {model_check.status_code}): {model_check.text}")

except requests.exceptions.Timeout:
    print("❌ Error: Request timed out. Please check your internet connection.")
except Exception as e:
    print(f"❌ Error making API request: {str(e)}")
    print("Please check your internet connection and try again.")
