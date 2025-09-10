import json
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from flask_cors import cross_origin
import logging
import os
import requests
from datetime import datetime, timedelta
from services.free_llm_meal_planner import FreeLLMMealPlannerAgent
from services.user_preferences_service import UserPreferencesService
from middleware.auth_middleware import require_auth, get_current_user_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

meal_planner_bp = Blueprint('meal_planner', __name__)

# Initialize services
user_preferences_service = UserPreferencesService()
free_llm_meal_planner = FreeLLMMealPlannerAgent(user_preferences_service)

def build_llama_prompt(preferences, budget=None, dietary_goals=None, currency='$'):
    """Build a structured prompt for meal planning with nutritional requirements."""
    dietary = preferences.get('dietaryRestrictions', [])
    cuisines = preferences.get('favoriteCuisines', ['International'])
    allergens = preferences.get('allergens', [])
    skill = preferences.get('cookingSkillLevel', 'beginner')
    favorite_foods = preferences.get('favoriteFoods', [])
    health_goals = preferences.get('healthGoals', ['General wellness'])
    max_time = preferences.get('maxCookingTime', '30 minutes')
    
    # Add dietary goals to health goals if provided
    if dietary_goals:
        if isinstance(dietary_goals, list):
            health_goals = list(set(health_goals + dietary_goals))
        else:
            health_goals.append(str(dietary_goals))
    
    # Get target macros from preferences or use defaults
    macros = {
        'calories': preferences.get('targetCalories', 2000),
        'protein': preferences.get('targetProtein', 150),
        'carbs': preferences.get('targetCarbs', 200),
        'fat': preferences.get('targetFat', 65),
        'fiber': 30  # Default value
    }
    
    # Determine which meals to include based on preferences
    include_breakfast = preferences.get('includeBreakfast', True)
    include_lunch = preferences.get('includeLunch', True)
    include_dinner = preferences.get('includeDinner', True)
    include_snacks = preferences.get('includeSnacks', False)
    
    # Build meals list based on preferences
    meals_per_day = []
    meal_requirements = {}
    
    # Calculate calories per meal based on number of meals
    total_meals = sum([include_breakfast, include_lunch, include_dinner])
    calories_per_meal = macros['calories'] / total_meals if total_meals > 0 else 0
    
    if include_breakfast:
        meals_per_day.append('breakfast')
        meal_requirements['breakfast'] = {
            'description': 'A nutritious start to the day',
            'target_calories': f'{int(calories_per_meal * 0.8)}-{int(calories_per_meal * 1.2)}',
            'protein_goal': f"{int(macros['protein'] * 0.25)}-{int(macros['protein'] * 0.3)}g"
        }
    
    if include_snacks and include_breakfast:
        meals_per_day.append('morning_snack')
        meal_requirements['morning_snack'] = {
            'description': 'Light and energizing',
            'target_calories': f"{int(calories_per_meal * 0.3)}-{int(calories_per_meal * 0.4)}",
            'protein_goal': f"{int(macros['protein'] * 0.1)}g"
        }
    
    if include_lunch:
        meals_per_day.append('lunch')
        meal_requirements['lunch'] = {
            'description': 'Balanced and satisfying',
            'target_calories': f'{int(calories_per_meal * 0.9)}-{int(calories_per_meal * 1.1)}',
            'protein_goal': f"{int(macros['protein'] * 0.3)}-{int(macros['protein'] * 0.35)}g"
        }
    
    if include_snacks and include_lunch:
        meals_per_day.append('afternoon_snack')
        meal_requirements['afternoon_snack'] = {
            'description': 'Energy-boosting',
            'target_calories': f"{int(calories_per_meal * 0.3)}-{int(calories_per_meal * 0.4)}",
            'protein_goal': f"{int(macros['protein'] * 0.1)}g"
        }
    
    if include_dinner:
        meals_per_day.append('dinner')
        meal_requirements['dinner'] = {
            'description': 'Nutrient-dense and easy to digest',
            'target_calories': f'{int(calories_per_meal * 0.9)}-{int(calories_per_meal * 1.1)}',
            'protein_goal': f"{int(macros['protein'] * 0.35)}-{int(macros['protein'] * 0.4)}g"
        }
    
    if include_snacks and include_dinner:
        meals_per_day.append('evening_snack')
        meal_requirements['evening_snack'] = {
            'description': 'Light and protein-rich',
            'target_calories': f"{int(calories_per_meal * 0.2)}-{int(calories_per_meal * 0.3)}",
            'protein_goal': f"{int(macros['protein'] * 0.1)}g"
        }
    
    # Include user preferences in the prompt
    preferences_summary = {
        "dietary_restrictions": dietary,
        "preferred_cuisines": cuisines,
        "allergens_to_avoid": allergens,
        "cooking_skill_level": skill,
        "favorite_foods": favorite_foods,
        "health_goals": health_goals,
        "max_cooking_time": max_time,
        "meal_preferences": {
            "include_breakfast": include_breakfast,
            "include_lunch": include_lunch,
            "include_dinner": include_dinner,
            "include_snacks": include_snacks
        },
        "nutritional_targets": macros
    }
    
    # Prepare the prompt context with user preferences
    prompt_context = f"""You are a professional nutritionist and chef creating a personalized weekly meal plan based on user preferences.

    USER PREFERENCES:
    {json.dumps(preferences_summary, indent=2)}
    
    IMPORTANT INSTRUCTIONS:
    1. FAVORITE FOODS ARE THE HIGHEST PRIORITY - Include user's favorite foods in multiple meals throughout the week
    2. Cuisine preferences are secondary to favorite foods - don't force cuisine variety if it means excluding favorite foods
    3. Ensure favorite foods appear in at least 50% of the meals when possible
    4. Balance nutritional requirements while maximizing favorite food inclusion
    5. Variety in cuisines is good but should not override favorite food preferences
    """
    
    # Prepare the format instructions
    format_instructions = """
    Return a JSON object with the following structure:
    {
        "success": true,
        "meal_plan": {
            "week": {
                "monday": [
                    {
                        "meal": "breakfast",
                        "name": "Meal Name",
                        "description": "Brief description",
                        "ingredients": ["ingredient 1", "ingredient 2"],
                        "instructions": ["step 1", "step 2"],
                        "nutrition": {
                            "calories": 400,
                            "protein": 25,
                            "carbs": 50,
                            "fat": 12
                        }
                    }
                ],
                "tuesday": [],
                "wednesday": [],
                "thursday": [],
                "friday": [],
                "saturday": [],
                "sunday": []
            },
            "shopping_list": {
                "ingredients": [
                    {
                        "name": "ingredient name",
                        "amount": "1 cup",
                        "category": "produce"
                    }
                ],
                "estimated_cost": 50.00
            },
            "nutrition_summary": {
                "daily_average": {
                    "calories": 2000,
                    "protein": 150,
                    "carbs": 200,
                    "fat": 65
                },
                "weekly_totals": {
                    "calories": 14000,
                    "protein": 1050,
                    "carbs": 1400,
                    "fat": 455
                },
                "meal_inclusions": {{
                    "breakfast": {str(include_breakfast).lower()},
                    "lunch": {str(include_lunch).lower()},
                    "dinner": {str(include_dinner).lower()},
                    "snacks": {str(include_snacks).lower()}
                }},
                "dietary_considerations": {json.dumps(health_goals)}
            }
        }
    }
    Ensure the meal plan adheres to the user's dietary restrictions, preferences, and nutritional targets.
    """
    
    # Build the final prompt
    prompt = {
        "context": prompt_context,
        "user_preferences": {
            "dietary_restrictions": dietary,
            "preferred_cuisines": cuisines,
            "allergens_to_avoid": allergens,
            "cooking_skill_level": skill,
            "favorite_foods": favorite_foods,
            "health_goals": health_goals,
            "max_cooking_time": max_time,
            "meal_preferences": {
                "include_breakfast": include_breakfast,
                "include_lunch": include_lunch,
                "include_dinner": include_dinner,
                "include_snacks": include_snacks
            },
            "nutritional_targets": macros
        },
        "format_instructions": format_instructions,
        "notes": "Ensure all meals are diverse and don't repeat the same ingredients too often. Consider meal prep and leftovers where appropriate."
    }
    
    return prompt

def generate_meal_plan_with_llm(prompt, user_id, preferences=None, model_name="llama3.2"):
    """Generate a meal plan using the LLM agent"""
    try:
        logger.info("Generating meal plan with LLM agent...")
        
        # Generate the meal plan using the LLM agent with user_id and preferences
        logger.info(f"Calling LLM agent to generate meal plan for user: {user_id}")
        if preferences:
            # Use the provided preferences instead of loading from database
            result = free_llm_meal_planner.generate_weekly_meal_plan_with_preferences(user_id, preferences)
        else:
            # Fall back to loading preferences from database
            result = free_llm_meal_planner.generate_weekly_meal_plan(user_id)
        
        # Check if the LLM agent returned an error
        if 'error' in result:
            logger.error(f"LLM agent returned error: {result['error']}")
            raise ValueError(f"LLM agent error: {result['error']}")
        
        # Check if the result has the expected structure
        if not result.get('success') or 'meal_plan' not in result:
            logger.error("LLM agent returned invalid response structure")
            raise ValueError("Invalid response structure from LLM agent")
        
        # Extract the actual meal plan from the result
        meal_plan = result.get('meal_plan', {})
        
        if not meal_plan or 'days' not in meal_plan:
            logger.error("Failed to generate valid meal plan from LLM agent")
            raise ValueError("Failed to generate valid meal plan")
            
        logger.info("Successfully generated meal plan with LLM agent")
        return {
            "success": True,
            "plan": meal_plan
        }
        
    except Exception as e:
        logger.error(f"Error generating meal plan with LLM agent: {str(e)}")
        # Fall back to the test meal plan if LLM generation fails
        logger.info("Falling back to test meal plan")
        return {
            "success": True,
            "plan": {
                "days": [],
                "shopping_list": {
                    "ingredients": []
                },
                "nutrition_summary": {}
            }
        }

@meal_planner_bp.route('/ai/meal_plan', methods=['POST', 'OPTIONS'])
@cross_origin(origins=['http://localhost:8081', 'https://betterbulk.netlify.app'], 
             methods=['POST', 'OPTIONS'],
             allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
             supports_credentials=True)
@require_auth
def ai_meal_plan():
    """Generate a meal plan using the AI meal planner (requires authentication)"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
            
        logger.info("Received meal plan generation request")
        
        # Get user from session
        user_id = get_current_user_id()
        if not user_id:
            logger.error('User not logged in')
            return jsonify({'error': 'Not logged in'}), 401

        # Get preferences from user profile
        preferences = user_preferences_service.get_preferences(user_id)
        if not preferences:
            logger.error(f'No preferences found for user {user_id}')
            return jsonify({'error': 'No preferences found for user'}), 404
    
        # Get parameters from request
        data = request.get_json() or {}
        logger.debug(f"Request data: {data}")
        
        budget = data.get('budget')
        dietary_goals = data.get('dietary_goals', [])
        currency = data.get('currency', '$')
        
        # Get preferences from request (this is the main preferences object)
        request_preferences = data.get('preferences', {})
        meal_preferences = data.get('meal_preferences', {})
        nutrition_targets = data.get('nutrition_targets', {})
        
        logger.debug(f"Request preferences: {request_preferences}")
        logger.debug(f"Meal preferences: {meal_preferences}")
        logger.debug(f"Nutrition targets: {nutrition_targets}")
        
        # Update preferences with request data - prioritize request preferences over stored ones
        if request_preferences:
            # Update main preferences from request
            preferences.update({
                'dietaryRestrictions': request_preferences.get('dietaryRestrictions', preferences.get('dietaryRestrictions', [])),
                'favoriteCuisines': request_preferences.get('favoriteCuisines', preferences.get('favoriteCuisines', [])),
                'allergens': request_preferences.get('allergens', preferences.get('allergens', [])),
                'cookingSkillLevel': request_preferences.get('cookingSkillLevel', preferences.get('cookingSkillLevel', 'beginner')),
                'favoriteFoods': request_preferences.get('favoriteFoods', preferences.get('favoriteFoods', [])),
                'healthGoals': request_preferences.get('healthGoals', preferences.get('healthGoals', [])),
                'maxCookingTime': request_preferences.get('maxCookingTime', preferences.get('maxCookingTime', '30 minutes')),
                'targetCalories': request_preferences.get('targetCalories', preferences.get('targetCalories', 2000)),
                'targetProtein': request_preferences.get('targetProtein', preferences.get('targetProtein', 150)),
                'targetCarbs': request_preferences.get('targetCarbs', preferences.get('targetCarbs', 200)),
                'targetFat': request_preferences.get('targetFat', preferences.get('targetFat', 65))
            })
        
        # Update meal preferences if provided
        if meal_preferences:
            preferences.update({
                'includeBreakfast': meal_preferences.get('includeBreakfast', True),
                'includeLunch': meal_preferences.get('includeLunch', True),
                'includeDinner': meal_preferences.get('includeDinner', True),
                'includeSnacks': meal_preferences.get('includeSnacks', False)
            })
            
        # Update nutrition targets if provided (override any from request preferences)
        if nutrition_targets:
            preferences.update({
                'targetCalories': nutrition_targets.get('calories'),
                'targetProtein': nutrition_targets.get('protein'),
                'targetCarbs': nutrition_targets.get('carbs'),
                'targetFat': nutrition_targets.get('fat')
            })
        
        logger.debug(f"Final merged preferences: {preferences}")
        
        # Build structured prompt with all parameters
        try:
            prompt = build_llama_prompt(
                preferences,
                budget=float(budget) if budget is not None else None,
                dietary_goals=dietary_goals,
                currency=currency
            )
            logger.debug("Successfully built prompt")
        except Exception as e:
            logger.error(f"Error building prompt: {str(e)}", exc_info=True)
            return jsonify({
                'error': 'Failed to build meal plan prompt',
                'details': str(e)
            }), 500
        
        # Generate meal plan using LLM
        try:
            # Pass the updated preferences to the LLM agent
            result = generate_meal_plan_with_llm(prompt, user_id, preferences)
            logger.debug(f"LLM response: {result}")
        except Exception as e:
            logger.error(f"Error generating meal plan with LLM: {str(e)}", exc_info=True)
            return jsonify({
                'error': 'Failed to generate meal plan with AI',
                'details': str(e)
            }), 500
        
        if not result or not result.get('success'):
            error_msg = result.get('error', 'Unknown error') if result else 'No response from AI service'
            logger.error(f"Failed to generate meal plan: {error_msg}")
            return jsonify({
                'error': 'Failed to generate meal plan',
                'details': error_msg
            }), 500
            
        # Process and return the response
        meal_plan = result.get('plan', {})
        
        # Add metadata
        meal_plan.update({
            'generated_at': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'preferences_used': {
                'dietary_restrictions': preferences.get('dietaryRestrictions', []),
                'health_goals': preferences.get('healthGoals', []),
                'allergens': preferences.get('allergens', []),
                'budget': budget,
                'currency': currency,
                'meal_preferences': {
                    'include_breakfast': preferences.get('includeBreakfast', True),
                    'include_lunch': preferences.get('includeLunch', True),
                    'include_dinner': preferences.get('includeDinner', True),
                    'include_snacks': preferences.get('includeSnacks', False)
                },
                'nutrition_targets': {
                    'calories': preferences.get('targetCalories'),
                    'protein': preferences.get('targetProtein'),
                    'carbs': preferences.get('targetCarbs'),
                    'fat': preferences.get('targetFat')
                }
            }
        })
        
        return jsonify({
            'success': True,
            'meal_plan': meal_plan,
            'message': 'Meal plan generated successfully'
        })
        
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        return jsonify({'error': f'Invalid input: {str(ve)}'}), 400
    except Exception as e:
        logger.error(f"Error generating meal plan: {str(e)}")
        return jsonify({'error': 'Failed to generate meal plan'}), 500
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
        
        full_prompt = f"""Generate a CONCISE weekly meal plan (Monday-Sunday) with:
        - Breakfast: Name only
        - Snack: Name only
        - Lunch: Name only
        - Snack: Name only
        - Dinner: Name only
        
        Include 3 prep tips, weekly cost estimate, and key nutritional focus.
        Keep response under 300 tokens.
        
        User preferences:
        {prompt}
        
        Format response in markdown with clear section headers.
        Focus on variety and simplicity."""
        
        # Prepare the request data with stricter limits
        request_data = {
            'model': 'llama3.2:latest',
            'prompt': full_prompt,
            'stream': False,
            'options': {
                'temperature': 0.7,
                'num_ctx': 1024,
                'top_p': 0.9,
                'top_k': 30,
                'repeat_penalty': 1.1,
                'num_predict': 300,  # Reduced from 500 to prevent truncation
                'stop': ['###', '---']  # Add stop sequences to help with completion
            }
        }
        
        print("\n=== SENDING REQUEST TO OLLAMA ===")
        print(f"URL: {ollama_url}")
        print("Request Data:", request_data)
        
        try:
            # Call Ollama API with optimized parameters
            response = requests.post(
                ollama_url,
                json=request_data,
                timeout=60,  # 1 minute timeout
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"\n=== OLLAMA RESPONSE ===")
            print(f"Status Code: {response.status_code}")
            print("Response Headers:", dict(response.headers))
            
            if response.status_code != 200:
                error_msg = f"Ollama API request failed with status {response.status_code}"
                try:
                    error_details = response.json().get('error', 'No error details')
                    error_msg += f": {error_details}"
                    print(f"Error Details: {error_details}")
                except Exception as e:
                    error_msg += f": {response.text}"
                    print(f"Failed to parse error response: {str(e)}")
                print(f"Ollama API Error: {error_msg}")
                return jsonify({'error': error_msg}), 500
                
        except requests.exceptions.Timeout:
            error_msg = "Request to Ollama API timed out after 60 seconds"
            print(error_msg)
            return jsonify({'error': error_msg}), 504
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to connect to Ollama API: {str(e)}"
            print(error_msg)
            return jsonify({'error': error_msg}), 503

        # Extract the response from Ollama
        response_data = response.json()
        print("\n=== RAW LLM RESPONSE ===")
        print(response_data)
        print("======================\n")
        
        meal_plan_text = response_data.get('response', '').strip()
        
        # Check if response was truncated
        if response_data.get('done_reason') == 'length':
            print("WARNING: Response was truncated due to length limit")
            # We'll still try to use the partial response
        
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

@meal_planner_bp.route('/ai/simple_meal_plan', methods=['POST', 'OPTIONS'])
@cross_origin(origins=['http://localhost:8081', 'https://betterbulk.netlify.app'], 
             methods=['POST', 'OPTIONS'],
             allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
             supports_credentials=True)
@require_auth
def simple_ai_meal_plan():
    """Generate a simple meal plan using the free LLM agent"""
    try:
        if request.method == "OPTIONS":
            return jsonify({'status': 'ok'}), 200
            
        logger.info("Received simple meal plan generation request")
        
        # Get user from session
        user_id = get_current_user_id()
        logger.info(f"Current user ID: {user_id}")
        
        if not user_id:
            logger.error('User not logged in')
            return jsonify({'error': 'Not logged in'}), 401

        # Get preferences from user profile
        preferences = user_preferences_service.get_preferences(user_id)
        logger.info(f"Retrieved preferences for user {user_id}: {preferences}")
        
        if not preferences:
            logger.error(f'No preferences found for user {user_id}')
            # Return a more helpful error message
            return jsonify({
                'error': 'No preferences found for user',
                'user_id': user_id,
                'message': 'Please set your preferences first. The system cannot find any saved preferences for your account.'
            }), 404
    
        logger.debug(f"User preferences: {preferences}")
        
        # Use the free LLM meal planner agent
        result = free_llm_meal_planner.generate_weekly_meal_plan(user_id)
        
        if not result or result.get('error'):
            error_msg = result.get('error', 'Unknown error') if result else 'No response from AI service'
            logger.error(f"Failed to generate meal plan: {error_msg}")
            return jsonify({
                'error': 'Failed to generate meal plan',
                'details': error_msg
            }), 500
            
        logger.info("Successfully generated meal plan with free LLM")
        return jsonify({
            "success": True,
            "plan": result.get('plan', result),  # Use result.plan if it exists, otherwise use result
            "preferences_used": preferences
        }), 200
        
    except Exception as e:
        logger.error(f"Error in simple meal plan generation: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to generate meal plan',
            'details': str(e)
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
        result = free_llm_meal_planner.generate_weekly_meal_plan(user_id)
        
        if "error" in result:
            logger.error(f"Meal plan generation failed: {result['error']}")
            return jsonify({"error": result["error"]}), 500
        
        logger.info("Meal plan generated successfully")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Exception in generate_meal_plan: {str(e)}")
        return jsonify({"error": f"Failed to generate meal plan: {str(e)}"}), 500

@meal_planner_bp.route('/meal-plan/regenerate-meal', methods=['POST', 'OPTIONS'])
@require_auth  
def regenerate_specific_meal():
    """Regenerate a specific meal in the plan (requires authentication)"""
    
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
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
        result = free_llm_meal_planner.regenerate_specific_meal(user_id, day, meal_type, current_plan)
        
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
        
        recipes = free_llm_meal_planner.get_recipe_suggestions(meal_type, preferences, count)
        
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
        plan_result = free_llm_meal_planner.generate_weekly_meal_plan(test_preferences)
        
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

@meal_planner_bp.route('/test/meal_plan', methods=['GET'])
@cross_origin(origins=['http://localhost:8081', 'https://betterbulk.netlify.app'])
def test_meal_plan():
    """Test endpoint that returns a sample meal plan"""
    try:
        # Generate dates for the next 7 days
        today = datetime.utcnow().date()
        days = [today + timedelta(days=i) for i in range(7)]
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        
        # Sample meal plan data
        meal_plan = {
            'days': [],
            'shopping_list': {
                'ingredients': [
                    {'name': 'chicken breast', 'total_amount': '1.5 kg', 'estimated_cost': 12.99},
                    {'name': 'brown rice', 'total_amount': '1 kg', 'estimated_cost': 3.49},
                    {'name': 'mixed vegetables', 'total_amount': '2 kg', 'estimated_cost': 8.99},
                    {'name': 'olive oil', 'total_amount': '250 ml', 'estimated_cost': 5.99},
                    {'name': 'eggs', 'total_amount': '12', 'estimated_cost': 4.49},
                    {'name': 'whole wheat bread', 'total_amount': '1 loaf', 'estimated_cost': 3.99},
                    {'name': 'avocado', 'total_amount': '3', 'estimated_cost': 3.99},
                    {'name': 'greek yogurt', 'total_amount': '1 kg', 'estimated_cost': 4.99},
                    {'name': 'mixed berries', 'total_amount': '500g', 'estimated_cost': 5.99},
                    {'name': 'honey', 'total_amount': '250g', 'estimated_cost': 4.49},
                    {'name': 'almonds', 'total_amount': '200g', 'estimated_cost': 5.99},
                    {'name': 'salmon fillet', 'total_amount': '800g', 'estimated_cost': 15.99},
                    {'name': 'quinoa', 'total_amount': '500g', 'estimated_cost': 4.99},
                    {'name': 'broccoli', 'total_amount': '1 kg', 'estimated_cost': 2.99},
                    {'name': 'carrots', 'total_amount': '1 kg', 'estimated_cost': 1.99},
                    {'name': 'chickpeas', 'total_amount': '400g', 'estimated_cost': 1.49},
                    {'name': 'spinach', 'total_amount': '400g', 'estimated_cost': 2.99},
                    {'name': 'tomatoes', 'total_amount': '1 kg', 'estimated_cost': 3.49},
                    {'name': 'cucumber', 'total_amount': '500g', 'estimated_cost': 1.99},
                    {'name': 'feta cheese', 'total_amount': '200g', 'estimated_cost': 3.99},
                    {'name': 'whole grain pasta', 'total_amount': '500g', 'estimated_cost': 2.99},
                    {'name': 'pesto sauce', 'total_amount': '200g', 'estimated_cost': 3.99},
                    {'name': 'chicken thighs', 'total_amount': '1 kg', 'estimated_cost': 8.99},
                    {'name': 'sweet potatoes', 'total_amount': '1 kg', 'estimated_cost': 2.49},
                    {'name': 'green beans', 'total_amount': '500g', 'estimated_cost': 2.99},
                    {'name': 'mushrooms', 'total_amount': '400g', 'estimated_cost': 3.49},
                    {'name': 'onions', 'total_amount': '1 kg', 'estimated_cost': 1.49},
                    {'name': 'garlic', 'total_amount': '100g', 'estimated_cost': 0.99},
                    {'name': 'lemons', 'total_amount': '4', 'estimated_cost': 1.99},
                    {'name': 'herbs and spices', 'total_amount': 'assorted', 'estimated_cost': 5.00}
                ],
                'total_estimated_cost': {'amount': 120.00, 'currency': 'USD'}
            },
            'nutrition_summary': {
                'weekly_average_daily': {
                    'calories': 2100,
                    'protein_g': 150,
                    'carbs_g': 200,
                    'fat_g': 70,
                    'fiber_g': 35
                },
                'weekly_totals': {
                    'calories': 14700,
                    'protein_g': 1050,
                    'carbs_g': 1400,
                    'fat_g': 490,
                    'fiber_g': 245
                }
            },
            'preparation_tips': [
                "Meal prep on Sunday for the week's breakfasts and lunches.",
                "Use leftovers from dinner for next day's lunch.",
                "Chop vegetables in advance to save time during weekdays.",
                "Cook grains and proteins in bulk at the beginning of the week.",
                "Store dressings and sauces separately to keep meals fresh.",
                "Portion out snacks in advance to avoid overeating.",
                "Use a slow cooker or instant pot for easy meal preparation.",
                "Freeze any meals you won't eat within 3-4 days.",
                "Wash and prep all produce when you get home from the store.",
                "Keep a well-stocked spice rack to add variety to your meals."
            ],
            'notes': 'This is a sample meal plan. Adjust portion sizes based on your specific nutritional needs and preferences. The shopping list includes all ingredients needed for the week. Estimated costs are approximate and may vary by location.'
        }
        
        # Sample meals for each day
        sample_meals = {
            'breakfast': {
                'name': 'Greek Yogurt with Berries and Almonds',
                'description': 'Creamy Greek yogurt topped with mixed berries, honey, and sliced almonds',
                'cuisine': 'Mediterranean',
                'cook_time': '0 mins',
                'prep_time': '5 mins',
                'total_time': '5 mins',
                'difficulty': 'easy',
                'ingredients': [
                    {'name': 'Greek yogurt', 'amount': '1 cup', 'notes': 'plain, non-fat'},
                    {'name': 'mixed berries', 'amount': '1/2 cup', 'notes': 'fresh or frozen'},
                    {'name': 'honey', 'amount': '1 tsp', 'notes': 'optional'},
                    {'name': 'almonds', 'amount': '1 tbsp', 'notes': 'sliced'}
                ],
                'nutrition': {
                    'calories': 250,
                    'protein_g': 20,
                    'carbs_g': 30,
                    'fat_g': 6,
                    'fiber_g': 5,
                    'sugar_g': 18,
                    'sodium_mg': 80
                },
                'instructions': [
                    'Scoop yogurt into a bowl.',
                    'Top with berries and almonds.',
                    'Drizzle with honey if desired.'
                ],
                'estimated_cost': {'amount': 2.50, 'currency': 'USD'}
            },
            'lunch': {
                'name': 'Mediterranean Chicken Bowl',
                'description': 'Grilled chicken with quinoa, roasted vegetables, and tzatziki',
                'cuisine': 'Mediterranean',
                'cook_time': '20 mins',
                'prep_time': '15 mins',
                'total_time': '35 mins',
                'difficulty': 'medium',
                'ingredients': [
                    {'name': 'chicken breast', 'amount': '150g', 'notes': 'boneless, skinless'},
                    {'name': 'quinoa', 'amount': '1/2 cup', 'notes': 'cooked'},
                    {'name': 'cucumber', 'amount': '1/2 cup', 'notes': 'diced'},
                    {'name': 'tomatoes', 'amount': '1/2 cup', 'notes': 'cherry, halved'},
                    {'name': 'red onion', 'amount': '2 tbsp', 'notes': 'thinly sliced'},
                    {'name': 'feta cheese', 'amount': '30g', 'notes': 'crumbled'},
                    {'name': 'olive oil', 'amount': '1 tbsp', 'notes': 'extra virgin'},
                    {'name': 'lemon juice', 'amount': '1 tbsp', 'notes': 'freshly squeezed'},
                    {'name': 'dried oregano', 'amount': '1/2 tsp', 'notes': ''},
                    {'name': 'salt and pepper', 'amount': 'to taste', 'notes': ''}
                ],
                'nutrition': {
                    'calories': 550,
                    'protein_g': 42,
                    'carbs_g': 45,
                    'fat_g': 22,
                    'fiber_g': 8,
                    'sugar_g': 6,
                    'sodium_mg': 450
                },
                'instructions': [
                    'Marinate chicken with olive oil, lemon juice, oregano, salt, and pepper for 15 minutes.',
                    'Grill chicken for 6-7 minutes per side or until cooked through.',
                    'Let rest for 5 minutes, then slice.',
                    'Assemble bowl with quinoa, vegetables, and chicken.',
                    'Top with feta cheese and additional dressing if desired.'
                ],
                'estimated_cost': {'amount': 6.50, 'currency': 'USD'}
            },
            'dinner': {
                'name': 'Baked Salmon with Roasted Vegetables',
                'description': 'Herb-crusted salmon with a medley of seasonal roasted vegetables',
                'cuisine': 'American',
                'cook_time': '20 mins',
                'prep_time': '15 mins',
                'total_time': '35 mins',
                'difficulty': 'easy',
                'ingredients': [
                    {'name': 'salmon fillet', 'amount': '200g', 'notes': 'skin-on'},
                    {'name': 'broccoli', 'amount': '1 cup', 'notes': 'cut into florets'},
                    {'name': 'carrots', 'amount': '1/2 cup', 'notes': 'sliced'},
                    {'name': 'sweet potato', 'amount': '1/2 cup', 'notes': 'cubed'},
                    {'name': 'olive oil', 'amount': '2 tbsp', 'notes': 'extra virgin'},
                    {'name': 'lemon', 'amount': '1/2', 'notes': 'sliced'},
                    {'name': 'garlic powder', 'amount': '1/2 tsp', 'notes': ''},
                    {'name': 'dried dill', 'amount': '1/2 tsp', 'notes': ''},
                    {'name': 'salt and pepper', 'amount': 'to taste', 'notes': ''}
                ],
                'nutrition': {
                    'calories': 600,
                    'protein_g': 45,
                    'carbs_g': 35,
                    'fat_g': 32,
                    'fiber_g': 8,
                    'sugar_g': 10,
                    'sodium_mg': 380
                },
                'instructions': [
                    'Preheat oven to 400°F (200°C).',
                    'Toss vegetables with 1 tbsp olive oil, salt, and pepper. Spread on a baking sheet.',
                    'Rub salmon with remaining olive oil, garlic powder, dill, salt, and pepper.',
                    'Place salmon on top of vegetables. Add lemon slices on top of salmon.',
                    'Bake for 15-20 minutes until salmon is cooked through and vegetables are tender.',
                    'Serve immediately with a side of quinoa or brown rice if desired.'
                ],
                'estimated_cost': {'amount': 8.75, 'currency': 'USD'}
            },
            'morning_snack': {
                'name': 'Hard-Boiled Eggs with Avocado Toast',
                'description': 'Protein-packed snack with healthy fats',
                'cuisine': 'International',
                'cook_time': '10 mins',
                'prep_time': '5 mins',
                'total_time': '15 mins',
                'difficulty': 'easy',
                'ingredients': [
                    {'name': 'eggs', 'amount': '2', 'notes': 'large'},
                    {'name': 'whole wheat bread', 'amount': '1 slice', 'notes': 'toasted'},
                    {'name': 'avocado', 'amount': '1/4', 'notes': 'mashed'},
                    {'name': 'red pepper flakes', 'amount': 'pinch', 'notes': 'optional'},
                    {'name': 'salt and pepper', 'amount': 'to taste', 'notes': ''}
                ],
                'nutrition': {
                    'calories': 280,
                    'protein_g': 16,
                    'carbs_g': 18,
                    'fat_g': 17,
                    'fiber_g': 6,
                    'sugar_g': 2,
                    'sodium_mg': 220
                },
                'instructions': [
                    'Place eggs in a pot and cover with cold water by 1 inch.',
                    'Bring to a boil, then cover and remove from heat.',
                    'Let sit for 10-12 minutes, then transfer to ice water to cool.',
                    'Peel eggs and slice in half.',
                    'Spread mashed avocado on toast and top with eggs.',
                    'Season with salt, pepper, and red pepper flakes if desired.'
                ],
                'estimated_cost': {'amount': 2.25, 'currency': 'USD'}
            },
            'afternoon_snack': {
                'name': 'Hummus and Veggie Sticks',
                'description': 'Creamy hummus with fresh vegetable crudités',
                'cuisine': 'Middle Eastern',
                'cook_time': '0 mins',
                'prep_time': '10 mins',
                'total_time': '10 mins',
                'difficulty': 'easy',
                'ingredients': [
                    {'name': 'chickpeas', 'amount': '1/2 cup', 'notes': 'cooked'},
                    {'name': 'tahini', 'amount': '1 tbsp', 'notes': ''},
                    {'name': 'lemon juice', 'amount': '1 tbsp', 'notes': 'freshly squeezed'},
                    {'name': 'garlic', 'amount': '1 clove', 'notes': 'minced'},
                    {'name': 'olive oil', 'amount': '1 tbsp', 'notes': 'extra virgin'},
                    {'name': 'cumin', 'amount': '1/4 tsp', 'notes': 'ground'},
                    {'name': 'carrot', 'amount': '1', 'notes': 'cut into sticks'},
                    {'name': 'cucumber', 'amount': '1/2', 'notes': 'cut into sticks'},
                    {'name': 'bell pepper', 'amount': '1/2', 'notes': 'sliced'}
                ],
                'nutrition': {
                    'calories': 220,
                    'protein_g': 8,
                    'carbs_g': 25,
                    'fat_g': 11,
                    'fiber_g': 7,
                    'sugar_g': 6,
                    'sodium_mg': 180
                },
                'instructions': [
                    'In a food processor, combine chickpeas, tahini, lemon juice, garlic, olive oil, and cumin.',
                    'Blend until smooth, adding water 1 tbsp at a time if needed to reach desired consistency.',
                    'Season with salt to taste.',
                    'Serve with fresh vegetable sticks for dipping.'
                ],
                'estimated_cost': {'amount': 2.00, 'currency': 'USD'}
            },
            'evening_snack': {
                'name': 'Cottage Cheese with Cinnamon and Walnuts',
                'description': 'High-protein nighttime snack with healthy fats',
                'cuisine': 'International',
                'cook_time': '0 mins',
                'prep_time': '2 mins',
                'total_time': '2 mins',
                'difficulty': 'easy',
                'ingredients': [
                    {'name': 'cottage cheese', 'amount': '1/2 cup', 'notes': 'low-fat'},
                    {'name': 'walnuts', 'amount': '5 halves', 'notes': 'chopped'},
                    {'name': 'cinnamon', 'amount': '1/4 tsp', 'notes': 'ground'},
                    {'name': 'honey', 'amount': '1/2 tsp', 'notes': 'optional'}
                ],
                'nutrition': {
                    'calories': 180,
                    'protein_g': 15,
                    'carbs_g': 10,
                    'fat_g': 9,
                    'fiber_g': 1,
                    'sugar_g': 6,
                    'sodium_mg': 300
                },
                'instructions': [
                    'Spoon cottage cheese into a bowl.',
                    'Top with chopped walnuts and a sprinkle of cinnamon.',
                    'Drizzle with honey if desired.'
                ],
                'estimated_cost': {'amount': 1.50, 'currency': 'USD'}
            }
        }
        
        # Generate meals for each day of the week
        for i, day in enumerate(days):
            day_meals = {
                'day': day_names[day.weekday()],
                'date': day.isoformat(),
                'meals': {
                    'breakfast': sample_meals['breakfast'].copy(),
                    'morning_snack': sample_meals['morning_snack'].copy(),
                    'lunch': sample_meals['lunch'].copy(),
                    'afternoon_snack': sample_meals['afternoon_snack'].copy(),
                    'dinner': sample_meals['dinner'].copy(),
                    'evening_snack': sample_meals['evening_snack'].copy()
                },
                'nutrition_totals': {
                    'calories': 2100,
                    'protein_g': 150,
                    'carbs_g': 200,
                    'fat_g': 70,
                    'fiber_g': 35
                }
            }
            
            # Add some variety to the meals
            if i % 2 == 0:
                day_meals['meals']['lunch']['name'] = 'Quinoa Salad with Chickpeas and Feta'
                day_meals['meals']['dinner']['name'] = 'Grilled Chicken with Sweet Potato Mash'
            else:
                day_meals['meals']['lunch']['name'] = 'Turkey and Avocado Wrap'
                day_meals['meals']['dinner']['name'] = 'Vegetable Stir-Fry with Tofu'
            
            meal_plan['days'].append(day_meals)
        
        return jsonify({
            'success': True,
            'data': meal_plan,
            'message': 'Sample meal plan generated successfully',
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'currency': 'USD'
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating test meal plan: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate test meal plan',
            'details': str(e)
        }), 500

@meal_planner_bp.route('/debug/user-preferences', methods=['GET'])
@cross_origin(origins=['http://localhost:8081', 'https://betterbulk.netlify.app'])
@require_auth
def debug_user_preferences():
    """Debug endpoint to check user ID and preferences"""
    try:
        user_id = get_current_user_id()
        preferences = user_preferences_service.get_preferences(user_id)
        
        # Get all user IDs in the database
        all_users = user_preferences_service.collection.get()
        
        return jsonify({
            'current_user_id': user_id,
            'current_user_preferences': preferences,
            'all_user_ids': all_users.get('ids', []),
            'total_users': len(all_users.get('ids', [])),
            'message': 'Debug information retrieved successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        return jsonify({
            'error': 'Debug endpoint failed',
            'details': str(e)
        }), 500

@meal_planner_bp.route('/simple-meal-plan', methods=['GET'])
@cross_origin(origins=['http://localhost:8081', 'https://betterbulk.netlify.app'])
@require_auth
def simple_meal_plan():
    """Generate a simple meal plan using user preferences (no LLM required)"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        # Get user preferences
        preferences = user_preferences_service.get_preferences(user_id)
        if not preferences:
            return jsonify({
                "error": "No preferences found. Please set your preferences first."
            }), 400
        
        # Generate simple meal plan
        result = free_llm_meal_planner.generate_weekly_meal_plan(user_id)
        
        if "error" in result:
            return jsonify(result), 400
        
        return jsonify({
            "success": True,
            "meal_plan": result.get("plan", {}),
            "preferences_used": result.get("preferences_used", {}),
            "llm_used": result.get("llm_used", "Rule-based"),
            "generated_at": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating simple meal plan: {str(e)}")
        return jsonify({"error": f"Failed to generate meal plan: {str(e)}"}), 500