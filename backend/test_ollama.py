from flask import Blueprint, jsonify, request
import requests
import json

test_bp = Blueprint('test', __name__)

@test_bp.route('/test/ollama', methods=['POST'])
def test_ollama():
    try:
        # Simple test prompt
        prompt = "Tell me a very short joke in one sentence."
        
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
            }
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'response': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Ollama API returned status code {response.status_code}',
                'response_text': response.text
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
