from flask import Blueprint, jsonify, request
import requests
import json

test_meal_bp = Blueprint('test_meal', __name__)

@test_meal_bp.route('/test/meal_plan', methods=['POST'])
def test_meal_plan():
    try:
        # Get preferences from request or use defaults
        data = request.get_json() or {}
        
        # Build the prompt
        prompt = """Generate a CONCISE weekly meal plan (Monday-Sunday) with:
        - Breakfast: Name only
        - Snack: Name only
        - Lunch: Name only
        - Snack: Name only
        - Dinner: Name only
        
        Include 3 prep tips, weekly cost estimate, and key nutritional focus.
        Keep response under 300 tokens.
        
        User preferences:
        - Cuisine: Indian
        - Cooking Level: Beginner
        - Max Cooking Time: 30 minutes
        - Budget: $200/week
        - Dietary Goals: High Protein
        
        Format response in markdown with clear section headers."""
        
        # Call Ollama API
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llama3.2:latest',
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'num_predict': 300,
                    'stop': ['###', '---']
                }
            },
            timeout=60  # 60 second timeout
        )
        
        if response.status_code == 200:
            response_data = response.json()
            meal_plan_text = response_data.get('response', '').strip()
            
            # Return the raw response for debugging
            return jsonify({
                'success': True,
                'meal_plan': meal_plan_text,
                'raw_response': response_data
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
            'error': str(e),
            'type': type(e).__name__
        }), 500
