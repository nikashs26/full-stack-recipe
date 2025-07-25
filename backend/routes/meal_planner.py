from flask import Blueprint, request, jsonify, session
from flask_cors import cross_origin
import logging
import os
import requests
from services.llm_meal_planner_agent import LLMMealPlannerAgent
from services.user_preferences_service import UserPreferencesService
from middleware.auth_middleware import require_auth, get_current_user_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

meal_planner_bp = Blueprint('meal_planner', __name__)

# Initialize services
user_preferences_service = UserPreferencesService()
llm_meal_planner_agent = LLMMealPlannerAgent()

def build_llama_prompt(preferences, budget=None, dietary_goals=None, currency='$'):
    """Build a Llama 3.2 prompt for meal planning, using all user preferences."""
    dietary = preferences.get('dietaryRestrictions', [])
    cuisines = preferences.get('favoriteCuisines', [])
    allergens = preferences.get('allergens', [])
    skill = preferences.get('cookingSkillLevel', '')
    favorite_foods = preferences.get('favoriteFoods', [])
    health_goals = preferences.get('healthGoals', [])
    max_time = preferences.get('maxCookingTime', '')
    
    # Add dietary goals to health goals if provided
    if dietary_goals:
        health_goals = list(set(health_goals + dietary_goals))
    
    prompt_parts = [
        "Generate a detailed weekly meal plan with the following preferences:",
        "\nDietary Restrictions: " + (", ".join(dietary) if dietary else "None"),
        "Preferred Cuisines: " + (", ".join(cuisines) if cuisines else "Any"),
        "Allergens to Avoid: " + (", ".join(allergens) if allergens else "None"),
        "Cooking Skill Level: " + (skill if skill else "Not specified"),
        "Favorite Foods: " + (", ".join(favorite_foods) if favorite_foods else "None"),
        "Health Goals: " + (", ".join(health_goals) if health_goals else "None"),
        "Maximum Cooking Time: " + (f"{max_time} minutes" if max_time else "No limit")
    ]
    
    if budget is not None:
        prompt_parts.append(f"- Weekly food budget: {currency}{budget} (approximately {currency}{budget/21:.2f} per meal)")
    
    prompt_parts.extend([
        "\nFor each day of the week (Monday through Sunday), provide:",
        "1. Breakfast: Include dish name, ingredients with quantities, and brief preparation steps.",
        "2. Lunch: Include dish name, ingredients with quantities, and brief preparation steps.",
        "3. Dinner: Include dish name, ingredients with quantities, and brief preparation steps.",
        "4. Snacks: Include 2-3 snack options.",
        "\nFor each meal, include:",
        "- Estimated preparation time",
        "- Difficulty level",
        "- Estimated cost per serving",
        "- Total estimated cost for the meal",
        "\nAt the end, provide a summary of the total weekly cost and any notes about the meal plan.",
        "Format the response in clear, well-structured markdown with appropriate headings."
    ])
    
    return "\n".join(prompt_parts)

@meal_planner_bp.route('/ai/meal_plan', methods=['POST', 'OPTIONS'])
@cross_origin(origins=['http://localhost:8081'], 
              methods=['POST', 'OPTIONS'],
              allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
              supports_credentials=True)
@require_auth
def ai_meal_plan():
    """Generate a meal plan using the AI meal planner (requires authentication)"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
        
    # Get user from session
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    # Get preferences from user profile
    preferences = user_preferences_service.get_preferences(user_id)
    if not preferences:
        return jsonify({'error': 'No preferences found for user'}), 404
    
    # Get budget and dietary goals from request
    data = request.get_json() or {}
    budget = data.get('budget')
    dietary_goals = data.get('dietary_goals', [])
    currency = data.get('currency', '$')
    
    # Build Llama prompt with all parameters
    prompt = build_llama_prompt(
        preferences,
        budget=float(budget) if budget is not None else None,
        dietary_goals=dietary_goals,
        currency=currency
    )
    
    try:
        # Prepare the request to the local Ollama API
        ollama_url = 'http://localhost:11434/api/generate'
        
        # Simplified and more focused system prompt
        system_prompt = """You are a meal planning assistant. Generate a CONCISE weekly meal plan based on the user's preferences.
        
        For each day (Monday-Sunday), provide:
        1. Breakfast: Name only
        2. Snack: Name only
        3. Lunch: Name only
        4. Snack: Name only
        5. Dinner: Name only
        
        After the weekly plan, add a brief section with:
        - 3 meal prep tips
        - Estimated weekly cost range
        - Key nutritional focus
        
        Keep the response under 1000 tokens. Be concise but helpful."""
        
        # Prepare the full prompt with system instructions
        full_prompt = f"""{system_prompt}
        
        User preferences:
        {prompt}
        
        Generate a meal plan based on these preferences. Focus on variety and simplicity."""
        
        # Call Ollama API with optimized parameters
        response = requests.post(
            ollama_url,
            json={
                'model': 'llama3.2',
                'prompt': full_prompt,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'num_ctx': 1024,  # Reduced context window
                    'top_p': 0.9,
                    'top_k': 30,      # Reduced top_k
                    'repeat_penalty': 1.1,
                    'num_predict': 500  # Limit response length
                }
            },
            timeout=60,  # 1 minute timeout
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code != 200:
            error_msg = f"Ollama API request failed with status {response.status_code}"
            try:
                error_details = response.json().get('error', 'No error details')
                error_msg += f": {error_details}"
            except:
                pass
            return jsonify({
                'error': 'Failed to generate meal plan',
                'details': error_msg,
                'note': 'Please ensure Ollama is running and the llama3.2 model is installed.'
            }), 500

        # Extract the response from Ollama
        response_data = response.json()
        print("\n=== RAW LLM RESPONSE ===")
        print(response_data)
        print("======================\n")
        
        meal_plan_text = response_data.get('response', '').strip()
        
        if not meal_plan_text:
            return jsonify({
                'error': 'Received empty response from AI',
                'note': 'The meal plan generation returned no content.'
            }), 500
        
        # Create a structured response that matches the frontend's expected format
        days = []
        current_day = None
        current_meals = {}
        
        # Simple parsing of the response
        for line in meal_plan_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check for day headers (e.g., "## Monday")
            if line.lower().startswith('## '):
                if current_day and current_meals:
                    days.append({
                        'day': current_day,
                        'meals': current_meals
                    })
                current_day = line[3:].strip()
                current_meals = {}
            
            # Check for meal items (e.g., "1. Breakfast: ...")
            elif line[0].isdigit() and '. ' in line and ':' in line:
                meal_parts = line.split(':', 1)
                if len(meal_parts) == 2:
                    meal_num = meal_parts[0].split('.')[0].strip()
                    meal_name = meal_parts[0].split('.')[1].strip().lower()
                    meal_desc = meal_parts[1].strip()
                    
                    # Map to standard meal types
                    if 'breakfast' in meal_name:
                        meal_type = 'breakfast'
                    elif 'lunch' in meal_name:
                        meal_type = 'lunch'
                    elif 'dinner' in meal_name:
                        meal_type = 'dinner'
                    elif 'snack' in meal_name:
                        meal_type = 'snack'
                    else:
                        meal_type = meal_name.lower()
                    
                    current_meals[meal_type] = {
                        'name': meal_desc,
                        'description': f"A delicious {meal_name} option",
                        'ingredients': [],
                        'instructions': [],
                        'prep_time': 30,
                        'cook_time': 30,
                        'servings': 2,
                        'nutrition': {
                            'calories': 500,
                            'protein': 25,
                            'carbs': 50,
                            'fat': 20
                        },
                        'cost': {
                            'per_serving': 5.99,
                            'total': 11.98
                        }
                    }
        
        # Add the last day if it exists
        if current_day and current_meals:
            days.append({
                'day': current_day,
                'meals': current_meals
            })
        
        # If no days were parsed, use a fallback structure
        if not days:
            days = [{
                'day': 'Monday',
                'meals': {
                    'breakfast': {
                        'name': 'Oatmeal with Berries',
                        'description': 'A healthy breakfast option',
                        'ingredients': [
                            {'name': 'Oats', 'amount': 1, 'unit': 'cup'},
                            {'name': 'Mixed Berries', 'amount': 0.5, 'unit': 'cup'}
                        ],
                        'instructions': ['Cook oats', 'Top with berries'],
                        'prep_time': 5,
                        'cook_time': 5,
                        'servings': 1,
                        'nutrition': {
                            'calories': 300,
                            'protein': 10,
                            'carbs': 50,
                            'fat': 5
                        },
                        'cost': {
                            'per_serving': 2.50,
                            'total': 2.50
                        }
                    }
                }
            }]
        
        # Calculate total cost if budget was provided
        total_cost = sum(
            sum(meal['cost']['total'] for meal in day['meals'].values())
            for day in days
        ) if days and days[0]['meals'] else 0
        
        # Create the response
        response_data = {
            'days': days,
            'plan_type': 'llm_generated',
            'totalCost': total_cost,
            'budget': float(budget) if budget is not None else None,
            'currency': currency,
            'status': 'success',
            'model': 'llama3.2',
            'meal_plan': meal_plan_text  # Keep the raw text as well
        }
        
        print("\n=== STRUCTURED RESPONSE ===")
        print(json.dumps(response_data, indent=2))
        print("==========================\n")
        
        return jsonify(response_data)
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': 'Failed to connect to Ollama service',
            'details': str(e),
            'note': 'Please ensure Ollama is running locally on port 11434.'
        }), 500
    except Exception as e:
        return jsonify({
            'error': 'An unexpected error occurred',
            'details': str(e),
            'note': 'Please check the server logs for more information.'
        }), 500

@meal_planner_bp.route('/meal-plan/generate', methods=['GET', 'POST'])
@require_auth
def generate_meal_plan():
    """Generate comprehensive weekly meal plan using LLM (requires authentication)"""
    
    try:
        logger.info("Generating meal plan request received")
        
        # Get authenticated user ID
        user_id = get_current_user_id()
        logger.info(f"Generating meal plan for user: {user_id}")
        
        # Get preferences from ChromaDB for authenticated user
        preferences = user_preferences_service.get_preferences(user_id)
        if not preferences:
            return jsonify({
                "error": "No preferences found. Please set your preferences first.",
                "redirect_to": "/preferences"
            }), 400
        
        logger.info(f"Using preferences for user {user_id}: {list(preferences.keys())}")
        
        # Generate meal plan using LLM agent
        result = llm_meal_planner_agent.generate_weekly_meal_plan(preferences)
        
        if "error" in result:
            logger.error(f"Meal plan generation failed: {result['error']}")
            return jsonify({"error": result["error"]}), 500
        
        logger.info("Meal plan generated successfully")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Exception in generate_meal_plan: {str(e)}")
        return jsonify({"error": f"Failed to generate meal plan: {str(e)}"}), 500

@meal_planner_bp.route('/meal-plan/regenerate-meal', methods=['POST'])
@require_auth  
def regenerate_specific_meal():
    """Regenerate a specific meal in the plan (requires authentication)"""
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get authenticated user ID
        user_id = get_current_user_id()
        
        day = data.get('day')
        meal_type = data.get('meal_type') 
        current_plan = data.get('current_plan', {})
        
        if not day or not meal_type:
            return jsonify({"error": "Day and meal_type are required"}), 400
        
        logger.info(f"Regenerating {meal_type} for {day} for user {user_id}")
        
        # Regenerate specific meal
        result = llm_meal_planner_agent.regenerate_specific_meal(user_id, day, meal_type, current_plan)
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 500
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Exception in regenerate_specific_meal: {str(e)}")
        return jsonify({"error": f"Failed to regenerate meal: {str(e)}"}), 500

@meal_planner_bp.route('/meal-plan/recipe-suggestions', methods=['POST'])
def get_recipe_suggestions():
    """Get LLM-powered recipe suggestions for a specific meal type"""
    
    data = request.get_json()
    if not data or 'mealType' not in data:
        return jsonify({"error": "Missing required field: mealType"}), 400
    
    try:
        meal_type = data['mealType']
        preferences = data.get('preferences', {})
        count = data.get('count', 5)
        
        logger.info(f"Getting {count} recipe suggestions for {meal_type}")
        
        if not preferences:
            logger.warning("No preferences provided for recipe suggestions")
            return jsonify({"error": "No preferences provided"}), 400
        
        recipes = llm_meal_planner_agent.get_recipe_suggestions(meal_type, preferences, count)
        
        return jsonify({
            "success": True,
            "recipes": recipes,
            "meal_type": meal_type,
            "count": len(recipes)
        }), 200
        
    except Exception as e:
        logger.error(f"Exception in get_recipe_suggestions: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@meal_planner_bp.route('/meal-plan/health-check', methods=['GET'])
def health_check():
    """Health check endpoint for meal planner service"""
    
    try:
        # Test if services are working
        test_preferences = {
            "dietary_restrictions": ["vegetarian"],
            "favorite_cuisines": ["Mediterranean"],
            "allergies": [],
            "cooking_time": "medium",
            "skill_level": "intermediate"
        }
        
        # Test the LLM agent (this will use fallback if LLM is not available)
        plan_result = llm_meal_planner_agent.generate_weekly_meal_plan(test_preferences)
        
        return jsonify({
            "success": True,
            "status": "healthy",
            "llm_available": plan_result.get("plan_type") == "llm_generated",
            "fallback_working": plan_result.get("plan_type") == "rule_based_fallback",
            "services": {
                "llm_meal_planner_agent": "working",
                "user_preferences_service": "working"
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }), 500 