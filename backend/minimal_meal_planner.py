from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import requests
import os
import json
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration
OLLAMA_URL = 'http://localhost:11434/api/generate'
REQUEST_TIMEOUT = 30  # seconds

# Simple cache to store responses
response_cache = {}

def get_cached_response(prompt):
    """Get a cached response if available and not expired"""
    cache_key = hash(prompt)
    if cache_key in response_cache:
        cached = response_cache[cache_key]
        # Cache valid for 5 minutes
        if time.time() - cached['timestamp'] < 300:
            return cached['response']
    return None

def call_ollama(prompt, max_retries=1):
    """Call Ollama API with streaming and better timeout handling"""
    request_data = {
        'model': 'llama3',
        'prompt': prompt,
        'stream': True,  # Use streaming for better progress
        'options': {
            'num_predict': 100,  # Limit response length
            'temperature': 0.7,
            'top_p': 0.9,
            'timeout': 120000  # 2 minutes in milliseconds
        }
    }
    
    last_update = time.time()
    full_response = ""
    
    for attempt in range(max_retries + 1):
        try:
            print(f"Attempt {attempt + 1}/{max_retries + 1} - Calling Ollama API with streaming...")
            start_time = time.time()
            
            # Make the streaming request
            with requests.post(
                OLLAMA_URL,
                json=request_data,
                stream=True,
                timeout=300  # 5 minutes total timeout
            ) as response:
                response.raise_for_status()
                
                # Process the streaming response
                for line in response.iter_lines():
                    if not line:
                        continue
                        
                    # Parse the response chunk
                    chunk = json.loads(line)
                    
                    # Update progress every 2 seconds
                    current_time = time.time()
                    if current_time - last_update > 2.0:
                        print(f"Received {len(full_response)} characters so far...")
                        last_update = current_time
                    
                    # Accumulate the response
                    if 'response' in chunk:
                        full_response += chunk['response']
                    
                    # Check if we're done
                    if chunk.get('done', False):
                        duration = time.time() - start_time
                        print(f"Ollama API call completed in {duration:.2f}s")
                        return {
                            'response': full_response,
                            'done_reason': chunk.get('done_reason', 'completed'),
                            'total_duration': chunk.get('total_duration', 0)
                        }
                
                # If we get here, the stream ended without done=True
                duration = time.time() - start_time
                print(f"Warning: Stream ended without completion after {duration:.2f}s")
                return {
                    'response': full_response,
                    'done_reason': 'stream_ended',
                    'total_duration': int(duration * 1000)  # Convert to ms
                }
                
        except requests.exceptions.Timeout:
            duration = time.time() - start_time
            print(f"Attempt {attempt + 1} timed out after {duration:.1f}s")
            if attempt == max_retries:
                return {
                    'response': full_response if full_response else "I'm having trouble generating a response right now. Please try again later.",
                    'done_reason': 'timeout',
                    'total_duration': int(duration * 1000)
                }
                
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries:
                return {
                    'response': "I'm having trouble connecting to the AI service right now. Please try again later.",
                    'done_reason': 'connection_error',
                    'total_duration': 0
                }
                
        # Short delay before retry
        if attempt < max_retries:
            wait_time = 2  # Shorter wait time since we're streaming
            print(f"Retrying in {wait_time}s...")
            time.sleep(wait_time)
    
    return {
        'response': "I'm having trouble generating a response right now. Please try again later.",
        'done_reason': 'max_retries_exceeded',
        'total_duration': 0
    }

@app.route('/api/test/meal_plan', methods=['POST', 'OPTIONS'])
@cross_origin(origins=['http://localhost:8081'], 
              methods=['POST', 'OPTIONS'],
              allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
              supports_credentials=True)
def test_meal_plan():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    start_time = time.time()
    request_id = int(time.time() * 1000)
    print(f"\n=== Request {request_id} started at {datetime.now().isoformat()} ===")
    
    try:
        # Get preferences from request or use defaults
        data = request.get_json() or {}
        print(f"Request data: {json.dumps(data, indent=2)}")
        
        # Build a simple prompt
        prompt = """List one Indian vegetarian high-protein breakfast, lunch, and dinner.
        Keep each meal name short (2-5 words).
        Format as a simple list with each meal on a new line.
        Include protein content for each meal."""
        
        # Check cache first
        cached_response = get_cached_response(prompt)
        if cached_response:
            print("Serving from cache")
            return jsonify(cached_response)
        
        print("Calling Ollama API...")
        response_data = call_ollama(prompt)
        
        # Process response
        meal_plan = response_data.get('response', '').strip()
        done_reason = response_data.get('done_reason', 'completed')
        
        # If we got a partial response, log it but don't cache
        if done_reason != 'completed':
            print(f"Warning: Incomplete response - {done_reason}")
            
        # Only cache successful completions
        if done_reason == 'completed':
            cache_key = hash(prompt)
            response_cache[cache_key] = {
                'response': {
                    'success': True,
                    'meal_plan': meal_plan,
                    'model': 'llama3',
                    'done_reason': done_reason,
                    'response_length': len(meal_plan),
                    'cached': False
                },
                'timestamp': time.time()
            }
        
        # Prepare response
        response = {
            'success': True,
            'meal_plan': meal_plan,
            'model': 'llama3',
            'done_reason': done_reason,
            'response_length': len(meal_plan),
            'cached': False
        }
        
        return jsonify(response)
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        
        # Provide a fallback response
        fallback_response = {
            'success': False,
            'error': error_msg,
            'fallback': True,
            'meal_plan': """Breakfast: Paneer Bhurji with Multigrain Toast (25g protein)
Lunch: Rajma Chawal with Yogurt (30g protein)
Dinner: Palak Tofu with Roti (28g protein)""",
            'note': 'This is a fallback response due to an error.'
        }
        
        return jsonify(fallback_response), 500 if 'fallback' not in error_msg.lower() else 200
        
    finally:
        duration = time.time() - start_time
        print(f"Request {request_id} completed in {duration:.2f}s")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting test meal planner on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
