import requests
import json

def test_ollama():
    try:
        # Simple test prompt
        prompt = "Tell me a very short joke in one sentence."
        
        print("Sending request to Ollama...")
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llama3.2:latest',
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'num_predict': 100
                }
            },
            timeout=30  # 30 second timeout
        )
        
        print(f"Status Code: {response.status_code}")
        print("Response Headers:", response.headers)
        
        if response.status_code == 200:
            response_data = response.json()
            print("\n=== OLLAMA RESPONSE ===")
            print(json.dumps(response_data, indent=2))
            print("======================")
            return True
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Ollama API...")
    success = test_ollama()
    if success:
        print("✅ Test successful! Ollama is responding correctly.")
    else:
        print("❌ Test failed. Check the error messages above.")
