import os
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMMealPlannerAgent:
    def __init__(self):
        """Initialize the LLM Meal Planner Agent with free LLM options"""
        self.huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY', '')
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        
        # Model options
        self.hf_model = "microsoft/phi-2"  # Better free Hugging Face model
        self.ollama_model = "llama3:8b"  # Smaller, faster model that works well on most systems
        
        # Determine which service to use
        self.service = self._determine_service()
        logger.info(f"Using LLM service: {self.service}")
        
    def _determine_service(self) -> str:
        """Determine which free LLM service to use"""
        # Try Ollama first (completely free, runs locally)
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if any(model['name'].startswith('llama') for model in models):
                    return 'ollama'
        except:
            pass
        
        # Try Hugging Face (free tier available)
        if self.huggingface_api_key:
            return 'huggingface'
        
        # Fallback to rule-based
        return 'fallback'
    
    def generate_weekly_meal_plan(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive weekly meal plan using free LLM
        
        Args:
            preferences: User dietary preferences and restrictions
            
        Returns:
            Dict containing the weekly meal plan with recipes and details
        """
        print(f'🔥 LLM_AGENT: generate_weekly_meal_plan called with preferences: {preferences}')
        print(f'🔥 LLM_AGENT: Using service: {self.service}')
        
        try:
            if self.service == 'ollama':
                return self._generate_with_ollama(preferences)
            elif self.service == 'huggingface':
                return self._generate_with_huggingface(preferences)
            else:
                logger.info("Using fallback meal plan generation")
                return self._generate_fallback_meal_plan(preferences)
                
        except Exception as e:
            logger.error(f"Error generating meal plan: {str(e)}")
            return self._generate_fallback_meal_plan(preferences)
    
    def _generate_with_ollama(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate meal plan using free Ollama LLM"""
        try:
            print("🔍 Building meal plan prompt...")
            prompt = self._build_meal_plan_prompt(preferences)
            print(f"📝 Prompt length: {len(prompt)} characters")
            
            print("🚀 Sending request to Ollama...")
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 2000,
                        "num_ctx": 4096
                    }
                },
                timeout=60
            )
            
            print(f"✅ Received response with status code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                meal_plan_text = result.get('response', '')
                print(f"📄 Raw response length: {len(meal_plan_text)} characters")
                
                # Try to extract JSON from the response
                try:
                    print("🔍 Looking for JSON in response...")
                    start_idx = meal_plan_text.find('{')
                    end_idx = meal_plan_text.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx != -1:
                        json_str = meal_plan_text[start_idx:end_idx]
                        print(f"📋 Extracted JSON string (first 500 chars): {json_str[:500]}...")
                        
                        # Try to fix common JSON issues
                        fixed_json_str = self._fix_common_json_issues(json_str)
                        
                        # Parse the JSON
                        raw_meal_plan = json.loads(fixed_json_str)
                        print("✅ Successfully parsed JSON response")
                        
                        # Convert to full format
                        print("🔄 Converting to full meal plan format...")
                        meal_plan = self._convert_simple_to_full_format(raw_meal_plan, preferences)
                        print("🎉 Successfully generated meal plan")
                        return meal_plan
                    else:
                        print("❌ No JSON object found in response")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {str(e)}")
                    print("🔄 Trying fallback text extraction...")
                    return self._extract_meal_plan_from_text(meal_plan_text, preferences)
                except Exception as e:
                    print(f"❌ Error processing response: {str(e)}")
                    raise
            else:
                print(f"❌ Request failed with status {response.status_code}")
                print(f"Response: {response.text}")
            
            print("🔄 Falling back to default meal plan")
            return self._generate_fallback_meal_plan(preferences)
                    
        except Exception as e:
            print(f"❌ Error in _generate_with_ollama: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._generate_fallback_meal_plan(preferences)
    
    def _generate_with_huggingface(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate meal plan using Hugging Face free inference API"""
        try:
            prompt = self._build_simplified_prompt(preferences)
            print(f'🔥 HUGGING_FACE: Generated prompt length: {len(prompt)} characters')
            print(f'🔥 HUGGING_FACE: Prompt preview (first 500 chars): {prompt[:500]}...')
            
            headers = {
                "Authorization": f"Bearer {self.huggingface_api_key}",
                "Content-Type": "application/json"
            }
            
            # Use a free text generation model
            api_url = f"https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
            print(f'🔥 HUGGING_FACE: Sending request to {api_url}')
            print(f'🔥 HUGGING_FACE: Using API key: {"Yes" if self.huggingface_api_key else "No"}')
            
            response = requests.post(
                api_url,
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_length": 1000,
                        "temperature": 0.7,
                        "do_sample": True
                    }
                },
                timeout=30
            )
            
            print(f'🔥 HUGGING_FACE: Response status code: {response.status_code}')
            
            if response.status_code == 200:
                result = response.json()
                print(f'🔥 HUGGING_FACE: Raw response: {result}')
                
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get('generated_text', '')
                    print(f'🔥 HUGGING_FACE: Generated text length: {len(generated_text)} characters')
                    print(f'🔥 HUGGING_FACE: Generated text preview: {generated_text[:500]}...')
                    
                    # Parse the generated text and create a structured meal plan
                    meal_plan = self._parse_generated_text_to_meal_plan(generated_text, preferences)
                    print(f'🔥 HUGGING_FACE: Successfully parsed meal plan')
                    
                    logger.info(f"Successfully generated meal plan with Hugging Face")
                    return meal_plan
                else:
                    print(f'🔥 HUGGING_FACE: Unexpected response format: {result}')
            else:
                print(f'🔥 HUGGING_FACE: Request failed with status {response.status_code}')
                print(f'🔥 HUGGING_FACE: Error response: {response.text}')
                    
        except Exception as e:
            print(f'🔥 HUGGING_FACE: Exception occurred: {str(e)}')
            logger.error(f"Error with Hugging Face: {str(e)}")
        
        return self._generate_fallback_meal_plan(preferences)
    
    def _build_meal_plan_prompt(self, preferences: Dict[str, Any]) -> str:
        """Build a comprehensive prompt for the LLM with detailed instructions"""
        try:
            # Extract preferences with defaults
            dietary_restrictions = preferences.get('dietary_restrictions', [])
            favorite_cuisines = preferences.get('favorite_cuisines', [])
            target_calories = preferences.get('target_calories', 2000)
            target_protein = preferences.get('target_protein', 150)
            target_carbs = preferences.get('target_carbs', 200)
            target_fat = preferences.get('target_fat', 65)
            
            # Calculate macros with distribution across meals
            macros = {
                'daily': {
                    'calories': target_calories,
                    'protein': target_protein,
                    'carbs': target_carbs,
                    'fat': target_fat
                },
                'breakfast': {
                    'calories': int(target_calories * 0.25),
                    'protein': int(target_protein * 0.25),
                    'carbs': int(target_carbs * 0.25),
                    'fat': int(target_fat * 0.25)
                },
                'lunch': {
                    'calories': int(target_calories * 0.35),
                    'protein': int(target_protein * 0.35),
                    'carbs': int(target_carbs * 0.35),
                    'fat': int(target_fat * 0.35)
                },
                'dinner': {
                    'calories': int(target_calories * 0.4),
                    'protein': int(target_protein * 0.4),
                    'carbs': int(target_carbs * 0.3),
                    'fat': int(target_fat * 0.4)
                },
                'snack': {
                    'calories': int(target_calories * 0.1),
                    'protein': int(target_protein * 0.1),
                    'carbs': int(target_carbs * 0.1),
                    'fat': int(target_fat * 0.1)
                }
            }
            
            prompt = f"""You are a professional nutritionist and chef with expertise in creating diverse, macro-balanced meal plans. 
            Create a detailed weekly meal plan with the following specifications:
            
            USER PREFERENCES:
            - Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
            - Favorite cuisines: {', '.join(favorite_cuisines) if favorite_cuisines else 'Any'}
            - Daily calorie target: {target_calories} calories
            - Daily macronutrient targets: {target_protein}g protein, {target_carbs}g carbs, {target_fat}g fat
            
            MEAL PLAN REQUIREMENTS:
            1. Include 3 main meals (breakfast, lunch, dinner) and 2 snacks per day
            2. Each meal must include detailed nutrition information (calories, protein, carbs, fat)
            3. Ensure variety in protein sources, vegetables, and preparation methods
            4. Include 1-2 vegetarian days if no dietary restrictions prevent it
            5. Provide detailed recipes with ingredients and instructions
            6. Ensure meals are nutritionally balanced and satisfying
            7. Include a variety of colors, textures, and flavors
            8. Consider food combinations that optimize nutrient absorption
            
            NUTRITIONAL GUIDELINES:
            - Breakfast: ~{macros['breakfast']['calories']} kcal, ~{macros['breakfast']['protein']}g protein
            - Lunch: ~{macros['lunch']['calories']} kcal, ~{macros['lunch']['protein']}g protein
            - Dinner: ~{macros['dinner']['calories']} kcal, ~{macros['dinner']['protein']}g protein
            - Snacks: ~{macros['snack']['calories']} kcal each
            
            FORMAT REQUIREMENTS:
            Return a JSON object with the following structure:
            {{
                "week": [
                    {{
                        "day": "Monday",
                        "meals": {{
                            "breakfast": {{
                                "name": "Meal name (e.g., 'Spinach & Feta Omelet with Whole Grain Toast')",
                                "description": "Brief description of the meal",
                                "ingredients": [
                                    {{"name": "ingredient 1", "amount": "1 cup", "notes": "optional notes"}},
                                    {{"name": "ingredient 2", "amount": "200g", "notes": "organic if possible"}}
                                ],
                                "nutrition": {{
                                    "calories": {macros['breakfast']['calories']},
                                    "protein": {macros['breakfast']['protein']},
                                    "carbs": {macros['breakfast']['carbs']},
                                    "fat": {macros['breakfast']['fat']},
                                    "fiber": 0  # Calculate based on ingredients
                                }},
                                "prep_time": "10 min",
                                "cook_time": "15 min",
                                "instructions": [
                                    "Step 1: Detailed instruction here.",
                                    "Step 2: Next step here."
                                ],
                                "meal_type": "breakfast",
                                "cuisine": "e.g., Mediterranean",
                                "tags": ["high-protein", "quick-meal", "vegetarian"]
                            }},
                            "lunch": {{...}},
                            "dinner": {{...}},
                            "snacks": [
                                {{
                                    "name": "Snack name",
                                    "description": "Brief description",
                                    "ingredients": [...],
                                    "nutrition": {{...}},
                                    "prep_time": "5 min",
                                    "instructions": [...],
                                    "tags": ["high-protein", "quick"]
                                }}
                            ]
                        }}
                    }},
                    ...
                ],
                "nutrition_summary": {{
                    "daily_average": {{
                        "calories": {target_calories},
                        "protein": {target_protein},
                        "carbs": {target_carbs},
                        "fat": {target_fat},
                        "fiber": 30
                    }},
                    "weekly_totals": {{
                        "calories": {target_calories * 7},
                        "protein": {target_protein * 7},
                        "carbs": {target_carbs * 7},
                        "fat": {target_fat * 7}
                    }}
                }},
                "shopping_list": {{
                    "produce": ["item 1", "item 2"],
                    "proteins": ["item 1", "item 2"],
                    "dairy": ["item 1", "item 2"],
                    "pantry": ["item 1", "item 2"],
                    "spices": ["item 1", "item 2"]
                }}
            }}
            
            IMPORTANT: 
            - Only return the JSON object, no other text or explanations.
            - Ensure all nutritional values are realistic for the ingredients used.
            - Include a variety of protein sources throughout the week.
            - Make sure the meal plan is practical and uses common ingredients."""
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error building meal plan prompt: {str(e)}")
            return self._build_simplified_prompt(preferences)
    
    def _convert_simple_to_full_format(self, simple_plan: Dict[str, Any], preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Convert simple LLM response format to full expected format with macros and preferences"""
        try:
            from datetime import datetime, timedelta
            
            # Get the days from the simple plan - ensure we have a list
            days_data = simple_plan.get('days', [])
            if not isinstance(days_data, list):
                days_data = [days_data] if days_data else []
                
            shopping_list = simple_plan.get('shopping_list', [])
            estimated_cost = simple_plan.get('estimated_cost', '$45-60')
            
            # Get preferences with fallbacks
            weekly_budget = preferences.get('weekly_budget', preferences.get('weeklyBudget', '100'))
            serving_amount = preferences.get('serving_amount', preferences.get('servingAmount', '2'))
            include_breakfast = preferences.get('includeBreakfast', True)
            include_lunch = preferences.get('includeLunch', True)
            include_dinner = preferences.get('includeDinner', True)
            include_snacks = preferences.get('includeSnacks', False)
            
            # Get target macros from preferences with reasonable defaults
            target_calories = int(preferences.get('targetCalories', 2000))
            target_protein = int(preferences.get('targetProtein', 150))
            target_carbs = int(preferences.get('targetCarbs', 225))
            target_fat = int(preferences.get('targetFat', 66))
            
            # Calculate macros per meal type based on preferences
            macros_per_meal = {
                'breakfast': {
                    'calories': int(target_calories * 0.25) if include_breakfast else 0,
                    'protein': int(target_protein * 0.25) if include_breakfast else 0,
                    'carbs': int(target_carbs * 0.25) if include_breakfast else 0,
                    'fat': int(target_fat * 0.25) if include_breakfast else 0
                },
                'lunch': {
                    'calories': int(target_calories * 0.35) if include_lunch else 0,
                    'protein': int(target_protein * 0.35) if include_lunch else 0,
                    'carbs': int(target_carbs * 0.35) if include_lunch else 0,
                    'fat': int(target_fat * 0.35) if include_lunch else 0
                },
                'dinner': {
                    'calories': int(target_calories * 0.4) if include_dinner else 0,
                    'protein': int(target_protein * 0.4) if include_dinner else 0,
                    'carbs': int(target_carbs * 0.4) if include_dinner else 0,
                    'fat': int(target_fat * 0.4) if include_dinner else 0
                },
                'snack': {
                    'calories': int(target_calories * 0.15) if include_snacks else 0,
                    'protein': int(target_protein * 0.15) if include_snacks else 0,
                    'carbs': int(target_carbs * 0.15) if include_snacks else 0,
                    'fat': int(target_fat * 0.15) if include_snacks else 0
                }
            }
            
            # Initialize daily macro totals
            daily_macro_totals = []
            full_days = []
            today = datetime.now()
            
            # Ensure we have exactly 7 days
            days_to_process = days_data[:7]  # Take first 7 days if more exist
            while len(days_to_process) < 7:
                days_to_process.append({'day': f'Day {len(days_to_process) + 1}'})
                
            for i, day_data in enumerate(days_to_process):
                day_name = day_data.get('day', f'Day {i+1}')
                day_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
                
                # Initialize daily macros
                daily_macros = {
                    'calories': 0,
                    'protein': 0,
                    'carbs': 0,
                    'fat': 0
                }
                
                # Process each meal type
                meals = {}
                
                # Define meal types based on preferences
                meal_types = []
                if include_breakfast:
                    meal_types.append('breakfast')
                if include_snacks and include_breakfast:
                    meal_types.append('morning_snack')
                if include_lunch:
                    meal_types.append('lunch')
                if include_snacks and include_lunch:
                    meal_types.append('afternoon_snack')
                if include_dinner:
                    meal_types.append('dinner')
                
                for meal_type in meal_types:
                    simple_meal = day_data.get(meal_type, {})
                    if not isinstance(simple_meal, dict):
                        simple_meal = {'name': str(simple_meal)}
                        
                    # Get base meal type (breakfast, lunch, dinner, snack)
                    base_meal_type = meal_type.split('_')[0] if '_' in meal_type else meal_type
                    if base_meal_type not in ['breakfast', 'lunch', 'dinner']:
                        base_meal_type = 'snack'
                        
                    # Use target macros if not provided
                    meal_macros = macros_per_meal.get(base_meal_type, macros_per_meal['snack'])
                    
                    # Extract nutritional info with fallbacks to target macros
                    meal_calories = simple_meal.get('calories', meal_macros['calories'])
                    meal_protein = simple_meal.get('protein', meal_macros['protein'])
                    meal_carbs = simple_meal.get('carbs', meal_macros['carbs'])
                    meal_fat = simple_meal.get('fat', meal_macros['fat'])
                        
                    # Update daily macros
                    daily_macros['calories'] += meal_calories
                    daily_macros['protein'] += meal_protein
                    daily_macros['carbs'] += meal_carbs
                    daily_macros['fat'] += meal_fat
                    
                    # Create full meal object
                    meal_name = simple_meal.get('name', '')
                    if not meal_name:
                        # Generate a simple meal name if not provided
                        meal_name = f"{meal_type.replace('_', ' ').title()}"
                        if 'cuisine' in simple_meal:
                            meal_name = f"{simple_meal['cuisine']} {meal_name}"
                        
                    # Clean up meal name
                    meal_name = meal_name.strip()
                    if meal_name.lower().startswith(('a ', 'an ', 'the ')):
                        meal_name = meal_name[meal_name.find(' ') + 1:] + ' ' + meal_name[:meal_name.find(' ')]
                        
                    # Create the meal object
                    meal_obj = {
                        "name": meal_name,
                        "prep_time": simple_meal.get('prep_time', '15 minutes'),
                        "cook_time": simple_meal.get('cook_time', '20 minutes'),
                        "difficulty": simple_meal.get('difficulty', 'Medium'),
                        "servings": int(simple_meal.get('servings', serving_amount) or 2),
                        "ingredients": simple_meal.get('ingredients', ["See recipe details"]),
                        "instructions": simple_meal.get('instructions', 
                            [f"Prepare {meal_name} according to your preferred recipe"]),
                        "nutritional_info": {
                            "calories": int(meal_calories),
                            "protein": f"{int(meal_protein)}g",
                            "carbs": f"{int(meal_carbs)}g",
                            "fat": f"{int(meal_fat)}g"
                        },
                        "tags": simple_meal.get('tags', ['balanced', 'nutritious'])
                    }
                    
                    # Only add cuisine if it's not already in the name
                    if 'cuisine' in simple_meal and simple_meal['cuisine'].lower() not in meal_name.lower():
                        meal_obj['cuisine'] = simple_meal['cuisine']
                        
                    meals[meal_type] = meal_obj
                
                # Add day to the list
                full_days.append({
                    "day": day_name,
                    "date": day_date,
                    "meals": meals,
                    "daily_notes": f"LLM-generated meal plan for {day_name}",
                    "daily_macros": daily_macros
                })
                
                # Add to weekly totals
                daily_macro_totals.append(daily_macros)
            
            # Calculate weekly averages
            if daily_macro_totals:
                weekly_averages = {
                    'calories': round(sum(d['calories'] for d in daily_macro_totals) / len(daily_macro_totals)),
                    'protein': f"{round(sum(d['protein'] for d in daily_macro_totals) / len(daily_macro_totals), 1)}g",
                    'carbs': f"{round(sum(d['carbs'] for d in daily_macro_totals) / len(daily_macro_totals), 1)}g",
                    'fat': f"{round(sum(d['fat'] for d in daily_macro_totals) / len(daily_macro_totals), 1)}g"
                }
            else:
                weekly_averages = {
                    'calories': 0,
                    'protein': '0g',
                    'carbs': '0g',
                    'fat': '0g'
                }
            
            # Create full format response matching frontend expectations
            shopping_items = []
            common_ingredients = [
                {"name": "Olive Oil", "amount": "1 bottle"},
                {"name": "Salt", "amount": "to taste"},
                {"name": "Black Pepper", "amount": "to taste"},
                {"name": "Garlic", "amount": "1 head"},
                {"name": "Onion", "amount": "2 medium"},
                {"name": "Lemon", "amount": "2"},
                {"name": "Olive Oil", "amount": "1/2 cup"},
                {"name": "Herbs (dried or fresh)", "amount": "assorted"}
            ]
            
            for day in full_days:
                for meal in day.get('meals', {}).values():
                    if 'ingredients' in meal and isinstance(meal['ingredients'], list):
                        for ingredient in meal['ingredients']:
                            if isinstance(ingredient, dict):
                                shopping_items.append({
                                    'name': ingredient.get('name', 'Ingredient'),
                                    'amount': ingredient.get('amount', 'As needed'),
                                    'category': 'Produce' if any(veg in ingredient.get('name', '').lower() 
                                                      for veg in ['tomato', 'cucumber', 'pepper', 'onion', 'garlic', 'lemon', 'herb']) 
                                        else 'Pantry'
                                })
            
            for item in common_ingredients:
                shopping_items.append({
                    'name': item['name'],
                    'amount': item['amount'],
                    'category': 'Pantry'
                })
            
            # Remove duplicates (simple approach - in a real app, we'd want to combine amounts)
            unique_items = {}
            for item in shopping_items:
                name = item['name'].lower()
                if name not in unique_items:
                    unique_items[name] = item
        
            shopping_list = {
                'ingredients': list(unique_items.values()),
                'total_items': len(unique_items)
            }
            
            full_plan = {
                "days": full_days,
                "shopping_list": shopping_list,
                "estimated_cost": estimated_cost if estimated_cost else 
                        (f"${weekly_budget}" if weekly_budget else "$45-60"),
                "nutrition_summary": {
                    "daily_average": {
                        "calories": weekly_averages['calories'],
                        "protein": weekly_averages['protein'],
                        "carbs": weekly_averages['carbs'],
                        "fat": weekly_averages['fat']
                    },
                    "weekly_totals": {
                        "calories": weekly_averages['calories'] * 7,
                        "protein": f"{float(weekly_averages['protein'].replace('g', '')) * 7}g",
                        "carbs": f"{float(weekly_averages['carbs'].replace('g', '')) * 7}g",
                        "fat": f"{float(weekly_averages['fat'].replace('g', '')) * 7}g"
                    },
                    "targets": {
                        "calories": preferences.get('nutritionTargets', {}).get('calories', 2000),
                        "protein": f"{preferences.get('nutritionTargets', {}).get('protein', 150)}g",
                        "carbs": f"{preferences.get('nutritionTargets', {}).get('carbs', 200)}g",
                        "fat": f"{preferences.get('nutritionTargets', {}).get('fat', 65)}g"
                    },
                    "dietary_considerations": preferences.get('dietaryRestrictions', []) + preferences.get('dietaryGoals', []),
                    "meal_inclusions": {
                        "breakfast": preferences.get('mealPreferences', {}).get('includeBreakfast', True),
                        "lunch": preferences.get('mealPreferences', {}).get('includeLunch', True),
                        "dinner": preferences.get('mealPreferences', {}).get('includeDinner', True),
                        "snacks": preferences.get('mealPreferences', {}).get('includeSnacks', True)
                    }
                },
                "generated_at": datetime.utcnow().isoformat() + 'Z',
                "preferences_used": {
                    "dietary_restrictions": preferences.get('dietaryRestrictions', []),
                    "favorite_cuisines": preferences.get('favoriteCuisines', []),
                    "allergens": preferences.get('allergens', []),
                    "include_breakfast": preferences.get('mealPreferences', {}).get('includeBreakfast', True),
                    "include_lunch": preferences.get('mealPreferences', {}).get('includeLunch', True),
                    "include_dinner": preferences.get('mealPreferences', {}).get('includeDinner', True),
                    "include_snacks": preferences.get('mealPreferences', {}).get('includeSnacks', True),
                    "serving_size": preferences.get('servingSize', 2)
                },
                "plan_type": "ai_generated"
            }
            
            return full_plan
            
        except Exception as e:
            print(f'🔥 CONVERT_FORMAT: Error converting format: {e}')
            import traceback
            traceback.print_exc()
            
            # Return the simple plan as-is if conversion fails
            simple_plan['generated_at'] = datetime.now().isoformat()
            simple_plan['preferences_used'] = preferences
            simple_plan['plan_type'] = 'llm_generated_simple'
            return simple_plan
    
    def _build_simplified_prompt(self, preferences: Dict[str, Any]) -> str:
        """Build a simpler prompt for less capable models"""
        print(f'🔥 SIMPLIFIED_PROMPT: Building simplified prompt with preferences: {preferences}')
        
        # Handle both camelCase and snake_case keys
        dietary_restrictions = preferences.get('dietary_restrictions', preferences.get('dietaryRestrictions', []))
        favorite_cuisines = preferences.get('favorite_cuisines', preferences.get('favoriteCuisines', []))
        
        print(f'🔥 SIMPLIFIED_PROMPT: Extracted dietary_restrictions: {dietary_restrictions}')
        print(f'🔥 SIMPLIFIED_PROMPT: Extracted favorite_cuisines: {favorite_cuisines}')
        
        return f"""Create a weekly meal plan for someone with these preferences:
Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
Favorite cuisines: {', '.join(favorite_cuisines) if favorite_cuisines else 'Any'}

List 7 days of meals with breakfast, lunch, and dinner for each day.
Make the meals varied and follow the dietary restrictions. Don't use random recipes, try to use ones that fill out a balanced day of eating."""
    
    def _parse_generated_text_to_meal_plan(self, text: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Parse generated text into a structured meal plan with macros"""
        print('🔥 PARSER: Starting to parse LLM response')
        
        try:
            # First try to parse as complete JSON
            try:
                # Look for the start of a valid JSON object
                start_idx = max(text.find('{'), text.find('['))
                if start_idx == -1:
                    raise ValueError("No JSON object or array found in response")
                
                # Extract the JSON part
                json_str = text[start_idx:]
                # Find the end of the JSON (last closing brace/bracket)
                stack = []
                in_string = False
                escape = False
                
                for i, char in enumerate(json_str):
                    if char == '"' and (i == 0 or json_str[i-1] != '\\'):
                        in_string = not in_string
                    elif char in '{[' and not in_string:
                        stack.append(char)
                    elif char in '}]' and not in_string:
                        if not stack:
                            break  # Unmatched closing bracket
                        stack.pop()
                        if not stack:  # Found the matching closing bracket
                            json_str = json_str[:i+1]
                            break
                    # Update escape state (true if current char is backslash and previous wasn't escaping)
                
                print(f'🔥 PARSER: Extracted JSON string: {json_str[:200]}...')
                
                # Fix common JSON issues
                json_str = self._fix_common_json_issues(json_str)
                parsed = json.loads(json_str)
                
                print('🔥 PARSER: Successfully parsed JSON response')
                return self._convert_simple_to_full_format(parsed, preferences)
                
            except json.JSONDecodeError as e:
                print(f'🔥 PARSER: JSON decode error: {e}')
                print(f'🔥 PARSER: Problematic JSON: {json_str[:500]}...' if 'json_str' in locals() else 'No JSON to display')
                
                # Try to extract individual day objects using a more flexible pattern
                day_objects = []
                
                # First try to find structured JSON objects
                json_objects = re.findall(r'({[^{}]*"(?:name|ingredients|calories|protein|carbs|fat)"[^{}]*})', text)
                if json_objects:
                    try:
                        # Try to parse as a complete JSON array first
                        combined = '[' + ','.join(json_objects) + ']'
                        parsed = json.loads(combined)
                        if isinstance(parsed, list):
                            # If we have a list of meals, group them by day
                            days = {}
                            for meal in parsed:
                                day_name = meal.get('day', 'Monday')
                                if day_name not in days:
                                    days[day_name] = {}
                                # Find the meal type from the meal name or position
                                meal_type = meal.get('meal_type', '').lower()
                                if not meal_type:
                                    if 'breakfast' in meal.get('name', '').lower():
                                        meal_type = 'breakfast'
                                    elif 'lunch' in meal.get('name', '').lower():
                                        meal_type = 'lunch'
                                    elif 'dinner' in meal.get('name', '').lower():
                                        meal_type = 'dinner'
                                    elif 'snack' in meal.get('name', '').lower():
                                        meal_type = 'snack'
                                
                                if meal_type:
                                    days[day_name][meal_type] = meal
                            
                            for day_name, meals in days.items():
                                if meals:  # Only add days that have meals
                                    day_objects.append({"day": day_name, **meals})
                            
                            if day_objects:
                                print(f'🔥 PARSER: Successfully extracted {len(day_objects)} days from JSON objects')
                                return self._convert_simple_to_full_format({"days": day_objects}, preferences)
                    except json.JSONDecodeError:
                        pass
                
                # If JSON parsing fails, try text-based extraction
                day_sections = re.split(r'(?i)(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', text)[1:]
                
                for i in range(0, len(day_sections)-1, 2):
                    day_name = day_sections[i].strip().title()
                    day_content = day_sections[i+1]
                    
                    day_meals = {}
                    # Look for meals in the day content
                    for meal_type in ['breakfast', 'lunch', 'dinner', 'snack']:
                        # First try to find a JSON object
                        meal_match = re.search(fr'(?i){meal_type}\s*[\:\-]?\s*({{\s*"name"\s*:\s*".*?"[^}}]*}})', day_content)
                        if meal_match:
                            try:
                                meal_json = meal_match.group(1)
                                meal_obj = json.loads(meal_json)
                                day_meals[meal_type] = meal_obj
                                continue  # Skip to next meal type if JSON parse succeeds
                            except json.JSONDecodeError:
                                pass
                        
                        # If JSON parsing fails, try to extract just the name
                        name_match = re.search(fr'(?i){meal_type}\s*[\:\-]?\s*"?([^"]+?)"?(?=\s*\n|$|,|\}})', day_content)
                        if name_match:
                            meal_name = name_match.group(1).strip('" ')
                            if meal_name:
                                day_meals[meal_type] = {
                                    "name": meal_name,
                                    "cuisine": "International",
                                    "ingredients": ["See recipe details"],
                                    "calories": 0,
                                    "protein": 0,
                                    "carbs": 0,
                                    "fat": 0,
                                    "prep_time": "15 minutes",
                                    "cook_time": "20 minutes",
                                    "instructions": [f"Prepare {meal_name}"]
                                }
                    
                    if day_meals:
                        day_objects.append({
                            "day": day_name,
                            **day_meals
                        })
                
                if day_objects:
                    print(f'🔥 PARSER: Successfully extracted {len(day_objects)} days with meals')
                    return self._convert_simple_to_full_format({"days": day_objects}, preferences)
            
            # If JSON parsing fails, try to extract information from text
            print('🔥 PARSER: Falling back to text extraction')
            return self._extract_meal_plan_from_text(text, preferences)
            
        except Exception as e:
            print(f'🔥 PARSER: Error in _parse_generated_text_to_meal_plan: {e}')
            import traceback
            traceback.print_exc()
            print(f'🔥 PARSER: Response text was: {text[:500]}...')  # Log first 500 chars
            
            # Return a fallback plan with error information
            return self._generate_fallback_meal_plan(preferences)
    
    def _generate_fallback_meal_plan(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a basic fallback meal plan when LLM is not available"""
        print(f'🔥 FALLBACK: Generating fallback meal plan')
        print(f'🔥 FALLBACK: Preferences received: {preferences}')
        
        from datetime import datetime, timedelta
        
        # Get current date
        today = datetime.now()
        
        # Extract preferences with fallbacks
        dietary_restrictions = preferences.get('dietary_restrictions', preferences.get('dietaryRestrictions', []))
        favorite_cuisines = preferences.get('favorite_cuisines', preferences.get('favoriteCuisines', []))
        cooking_skill = preferences.get('cooking_skill_level', preferences.get('cookingSkillLevel', 'intermediate'))
        max_time = preferences.get('max_cooking_time', preferences.get('maxCookingTime', '30 minutes'))
        
        # Extract meal preferences with fallbacks
        include_breakfast = preferences.get('includeBreakfast', True)
        include_lunch = preferences.get('includeLunch', True)
        include_dinner = preferences.get('includeDinner', True)
        include_snacks = preferences.get('includeSnacks', False)
        
        # Extract nutritional targets with defaults
        target_calories = preferences.get('targetCalories', 2000)
        target_protein = preferences.get('targetProtein', 150)
        target_carbs = preferences.get('targetCarbs', 200)
        target_fat = preferences.get('targetFat', 65)
        
        is_vegetarian = 'vegetarian' in [r.lower() for r in dietary_restrictions]
        is_vegan = 'vegan' in [r.lower() for r in dietary_restrictions]
        
        print(f'🔥 FALLBACK: Dietary restrictions: {dietary_restrictions}')
        print(f'🔥 FALLBACK: Favorite cuisines: {favorite_cuisines}')
        print(f'🔥 FALLBACK: Is vegetarian: {is_vegetarian}')
        print(f'🔥 FALLBACK: Is vegan: {is_vegan}')
        
        # Cuisine-specific meal templates with detailed nutrition info
        cuisine_meals = {
            "indian": {
                "breakfast": [
                    {"name": "Masala Chai with Paratha", "cuisine": "Indian", "vegetarian": True, "vegan": False, 
                     "calories": 350, "protein": 8, "carbs": 50, "fat": 12},
                    {"name": "Poha (Flattened Rice)", "cuisine": "Indian", "vegetarian": True, "vegan": True,
                     "calories": 280, "protein": 6, "carbs": 55, "fat": 5},
                    {"name": "Upma with Vegetables", "cuisine": "Indian", "vegetarian": True, "vegan": True,
                     "calories": 320, "protein": 10, "carbs": 45, "fat": 8},
                    {"name": "Idli with Sambar", "cuisine": "Indian", "vegetarian": True, "vegan": True,
                     "calories": 300, "protein": 12, "carbs": 50, "fat": 5},
                ],
                "lunch": [
                    {"name": "Dal Rice with Pickle", "cuisine": "Indian", "vegetarian": True, "vegan": True,
                     "calories": 450, "protein": 18, "carbs": 70, "fat": 10},
                    {"name": "Chana Masala with Roti", "cuisine": "Indian", "vegetarian": True, "vegan": True,
                     "calories": 500, "protein": 22, "carbs": 65, "fat": 15},
                    {"name": "Vegetable Biryani", "cuisine": "Indian", "vegetarian": True, "vegan": True,
                     "calories": 550, "protein": 15, "carbs": 85, "fat": 18},
                    {"name": "Rajma with Basmati Rice", "cuisine": "Indian", "vegetarian": True, "vegan": True,
                     "calories": 480, "protein": 20, "carbs": 75, "fat": 12},
                ],
                "dinner": [
                    {"name": "Palak Paneer with Naan", "cuisine": "Indian", "vegetarian": True, "vegan": False,
                     "calories": 600, "protein": 25, "carbs": 50, "fat": 30},
                    {"name": "Aloo Gobi with Chapati", "cuisine": "Indian", "vegetarian": True, "vegan": True,
                     "calories": 400, "protein": 12, "carbs": 60, "fat": 12},
                    {"name": "Mixed Vegetable Curry", "cuisine": "Indian", "vegetarian": True, "vegan": True,
                     "calories": 350, "protein": 10, "carbs": 40, "fat": 15},
                    {"name": "Dal Tadka with Rice", "cuisine": "Indian", "vegetarian": True, "vegan": True,
                     "calories": 450, "protein": 18, "carbs": 70, "fat": 10},
                ]
            },
            "italian": {
                "breakfast": [
                    {"name": "Cappuccino with Croissant", "cuisine": "Italian", "vegetarian": True, "vegan": False,
                     "calories": 380, "protein": 10, "carbs": 45, "fat": 18},
                    {"name": "Frittata with Vegetables", "cuisine": "Italian", "vegetarian": True, "vegan": False,
                     "calories": 320, "protein": 22, "carbs": 10, "fat": 20},
                    {"name": "Biscotti with Espresso", "cuisine": "Italian", "vegetarian": True, "vegan": True,
                     "calories": 280, "protein": 5, "carbs": 50, "fat": 8},
                    {"name": "Yogurt with Honey and Nuts", "cuisine": "Italian", "vegetarian": True, "vegan": False,
                     "calories": 300, "protein": 12, "carbs": 35, "fat": 14},
                ],
                "lunch": [
                    {"name": "Caprese Salad with Bread", "cuisine": "Italian", "vegetarian": True, "vegan": False,
                     "calories": 450, "protein": 18, "carbs": 40, "fat": 25},
                    {"name": "Margherita Pizza", "cuisine": "Italian", "vegetarian": True, "vegan": False,
                     "calories": 600, "protein": 25, "carbs": 80, "fat": 20},
                    {"name": "Pasta Primavera", "cuisine": "Italian", "vegetarian": True, "vegan": True,
                     "calories": 480, "protein": 15, "carbs": 75, "fat": 12},
                    {"name": "Minestrone Soup", "cuisine": "Italian", "vegetarian": True, "vegan": True,
                     "calories": 350, "protein": 12, "carbs": 50, "fat": 8},
                ],
                "dinner": [
                    {"name": "Eggplant Parmesan", "cuisine": "Italian", "vegetarian": True, "vegan": False,
                     "calories": 550, "protein": 22, "carbs": 45, "fat": 30},
                    {"name": "Risotto ai Funghi", "cuisine": "Italian", "vegetarian": True, "vegan": False,
                     "calories": 500, "protein": 15, "carbs": 65, "fat": 18},
                    {"name": "Pasta e Fagioli", "cuisine": "Italian", "vegetarian": True, "vegan": True,
                     "calories": 450, "protein": 20, "carbs": 70, "fat": 10},
                    {"name": "Bruschetta with Tomato and Basil", "cuisine": "Italian", "vegetarian": True, "vegan": True,
                     "calories": 350, "protein": 10, "carbs": 45, "fat": 15},
                ]
            },
            "mediterranean": {
                "breakfast": [
                    {"name": "Greek Yogurt with Honey and Nuts", "cuisine": "Mediterranean", "vegetarian": True, "vegan": False,
                     "calories": 350, "protein": 18, "carbs": 30, "fat": 18},
                    {"name": "Shakshuka with Whole Wheat Bread", "cuisine": "Mediterranean", "vegetarian": True, "vegan": False,
                     "calories": 400, "protein": 22, "carbs": 35, "fat": 20},
                    {"name": "Avocado Toast with Feta", "cuisine": "Mediterranean", "vegetarian": True, "vegan": False,
                     "calories": 380, "protein": 15, "carbs": 40, "fat": 22},
                    {"name": "Mediterranean Omelette", "cuisine": "Mediterranean", "vegetarian": True, "vegan": False,
                     "calories": 320, "protein": 25, "carbs": 10, "fat": 20},
                ],
                "lunch": [
                    {"name": "Greek Salad with Pita", "cuisine": "Mediterranean", "vegetarian": True, "vegan": False,
                     "calories": 450, "protein": 15, "carbs": 40, "fat": 25},
                    {"name": "Falafel Wrap with Tahini", "cuisine": "Mediterranean", "vegetarian": True, "vegan": True,
                     "calories": 500, "protein": 18, "carbs": 60, "fat": 20},
                    {"name": "Hummus and Vegetable Platter", "cuisine": "Mediterranean", "vegetarian": True, "vegan": True,
                     "calories": 380, "protein": 12, "carbs": 45, "fat": 18},
                    {"name": "Lentil Soup with Whole Wheat Bread", "cuisine": "Mediterranean", "vegetarian": True, "vegan": True,
                     "calories": 400, "protein": 22, "carbs": 55, "fat": 10},
                ],
                "dinner": [
                    {"name": "Stuffed Bell Peppers with Rice", "cuisine": "Mediterranean", "vegetarian": True, "vegan": True,
                     "calories": 480, "protein": 18, "carbs": 65, "fat": 15},
                    {"name": "Ratatouille with Quinoa", "cuisine": "Mediterranean", "vegetarian": True, "vegan": True,
                     "calories": 420, "protein": 15, "carbs": 60, "fat": 12},
                    {"name": "Greek Moussaka", "cuisine": "Mediterranean", "vegetarian": True, "vegan": False,
                     "calories": 550, "protein": 25, "carbs": 40, "fat": 30},
                    {"name": "Grilled Vegetable Platter with Tzatziki", "cuisine": "Mediterranean", "vegetarian": True, "vegan": False,
                     "calories": 400, "protein": 15, "carbs": 45, "fat": 20},
                ]
            },
            "american": {
                "breakfast": [
                    {"name": "Avocado Toast with Poached Eggs", "cuisine": "American", "vegetarian": True, "vegan": False,
                     "calories": 420, "protein": 20, "carbs": 35, "fat": 22},
                    {"name": "Overnight Oats with Berries", "cuisine": "American", "vegetarian": True, "vegan": True,
                     "calories": 380, "protein": 15, "carbs": 60, "fat": 10},
                    {"name": "Smoothie Bowl with Granola", "cuisine": "American", "vegetarian": True, "vegan": True,
                     "calories": 350, "protein": 12, "carbs": 55, "fat": 12},
                    {"name": "Veggie Breakfast Burrito", "cuisine": "American", "vegetarian": True, "vegan": False,
                     "calories": 450, "protein": 25, "carbs": 50, "fat": 18},
                ],
                "lunch": [
                    {"name": "Quinoa Buddha Bowl with Tahini Dressing", "cuisine": "American", "vegetarian": True, "vegan": True,
                     "calories": 500, "protein": 22, "carbs": 65, "fat": 18},
                    {"name": "Grilled Cheese with Tomato Soup", "cuisine": "American", "vegetarian": True, "vegan": False,
                     "calories": 550, "protein": 18, "carbs": 60, "fat": 25},
                    {"name": "Caesar Salad with Grilled Chicken", "cuisine": "American", "vegetarian": False, "vegan": False,
                     "calories": 480, "protein": 40, "carbs": 20, "fat": 25},
                    {"name": "Veggie Burger with Sweet Potato Fries", "cuisine": "American", "vegetarian": True, "vegan": True,
                     "calories": 600, "protein": 25, "carbs": 80, "fat": 20},
                ],
                "dinner": [
                    {"name": "Grilled Portobello Mushroom with Quinoa", "cuisine": "American", "vegetarian": True, "vegan": True,
                     "calories": 450, "protein": 20, "carbs": 60, "fat": 15},
                    {"name": "Mac and Cheese with Broccoli", "cuisine": "American", "vegetarian": True, "vegan": False,
                     "calories": 650, "protein": 25, "carbs": 75, "fat": 30},
                    {"name": "BBQ Jackfruit Sandwich with Coleslaw", "cuisine": "American", "vegetarian": True, "vegan": True,
                     "calories": 500, "protein": 15, "carbs": 85, "fat": 15},
                    {"name": "Stuffed Sweet Potato with Black Beans", "cuisine": "American", "vegetarian": True, "vegan": True,
                     "calories": 480, "protein": 18, "carbs": 80, "fat": 12},
                ]
            }
        }
        
        # Default fallback meals if no specific cuisine is found
        default_meals = {
            "breakfast": [
                {"name": "Overnight Oats with Berries", "cuisine": "International", "vegetarian": True, "vegan": True,
                 "calories": 380, "protein": 15, "carbs": 65, "fat": 8},
                {"name": "Avocado Toast with Poached Eggs", "cuisine": "International", "vegetarian": True, "vegan": False,
                 "calories": 420, "protein": 22, "carbs": 35, "fat": 22},
                {"name": "Smoothie Bowl with Granola", "cuisine": "International", "vegetarian": True, "vegan": True,
                 "calories": 350, "protein": 10, "carbs": 60, "fat": 10},
                {"name": "Greek Yogurt Parfait with Honey", "cuisine": "International", "vegetarian": True, "vegan": False,
                 "calories": 320, "protein": 20, "carbs": 45, "fat": 8},
            ],
            "lunch": [
                {"name": "Quinoa Buddha Bowl with Tahini", "cuisine": "International", "vegetarian": True, "vegan": True,
                 "calories": 520, "protein": 20, "carbs": 70, "fat": 18},
                {"name": "Lentil Soup with Whole Grain Bread", "cuisine": "International", "vegetarian": True, "vegan": True,
                 "calories": 450, "protein": 25, "carbs": 65, "fat": 12},
                {"name": "Veggie Wrap with Hummus", "cuisine": "International", "vegetarian": True, "vegan": True,
                 "calories": 480, "protein": 18, "carbs": 60, "fat": 20},
                {"name": "Mixed Green Salad with Grilled Tofu", "cuisine": "International", "vegetarian": True, "vegan": True,
                 "calories": 400, "protein": 25, "carbs": 25, "fat": 22},
            ],
            "dinner": [
                {"name": "Vegetable Stir-Fry with Tofu", "cuisine": "International", "vegetarian": True, "vegan": True,
                 "calories": 480, "protein": 25, "carbs": 50, "fat": 20},
                {"name": "Stuffed Bell Peppers with Quinoa", "cuisine": "International", "vegetarian": True, "vegan": True,
                 "calories": 450, "protein": 18, "carbs": 70, "fat": 12},
                {"name": "Mushroom Risotto with Parmesan", "cuisine": "International", "vegetarian": True, "vegan": False,
                 "calories": 550, "protein": 15, "carbs": 80, "fat": 20},
                {"name": "Roasted Vegetable Bowl with Tahini Dressing", "cuisine": "International", "vegetarian": True, "vegan": True,
                 "calories": 500, "protein": 18, "carbs": 60, "fat": 20},
            ]
        }
        
        # Choose meals based on favorite cuisines
        available_meals = default_meals
        if favorite_cuisines:
            print(f'🔥 FALLBACK: Using cuisine-specific meals for: {favorite_cuisines}')
            # Use the first favorite cuisine that we have meals for
            for cuisine in favorite_cuisines:
                cuisine_lower = cuisine.lower()
                if cuisine_lower in cuisine_meals:
                    available_meals = cuisine_meals[cuisine_lower]
                    print(f'🔥 FALLBACK: Found meals for cuisine: {cuisine}')
                    break
        
        # Generate 7 days
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekly_plan = []
        
        # Define meal types based on preferences
        meal_types = []
        if include_breakfast:
            meal_types.append("breakfast")
        if include_lunch:
            meal_types.append("lunch")
        if include_dinner:
            meal_types.append("dinner")
        
        for i, day in enumerate(days):
            day_date = today + timedelta(days=i)
            day_meals = []
            
            # Add main meals (breakfast, lunch, dinner)
            for meal_type in meal_types:
                available_for_meal = available_meals.get(meal_type, [])
                
                # Filter by dietary restrictions
                filtered_meals = []
                for meal in available_for_meal:
                    if is_vegan and not meal.get("vegan", False):
                        continue
                    if is_vegetarian and not meal.get("vegetarian", True):
                        continue
                    filtered_meals.append(meal)
                
                # If no meals pass the filter, use the original list
                if not filtered_meals:
                    filtered_meals = available_for_meal
                
                # Select a meal (cycle through to avoid repetition)
                if filtered_meals:  # Only add if there are meals available
                    selected_meal = filtered_meals[i % len(filtered_meals)]
                    
                    # Use the actual nutrition data from the meal
                    if 'calories' in selected_meal and 'protein' in selected_meal and 'carbs' in selected_meal and 'fat' in selected_meal:
                        calories = selected_meal['calories']
                        protein = selected_meal['protein']
                        carbs = selected_meal['carbs']
                        fat = selected_meal['fat']
                    else:
                        # Fallback calculation if nutrition data is missing
                        if meal_type == "breakfast":
                            calories = min(target_calories * 0.25, 500)
                            protein = min(target_protein * 0.25, 20)
                            carbs = min(target_carbs * 0.25, 70)
                            fat = min(target_fat * 0.25, 20)
                        elif meal_type == "lunch":
                            calories = min(target_calories * 0.35, 700)
                            protein = min(target_protein * 0.35, 30)
                            carbs = min(target_carbs * 0.35, 80)
                            fat = min(target_fat * 0.35, 25)
                        else:  # dinner
                            calories = min(target_calories * 0.4, 800)
                            protein = min(target_protein * 0.4, 35)
                            carbs = min(target_carbs * 0.3, 60)
                            fat = min(target_fat * 0.35, 25)
                    
                    # Ensure nutrition values are not None
                    meal_nutrition = {
                        "calories": round(calories) if calories is not None else 0,
                        "protein": round(protein, 1) if protein is not None else 0,
                        "carbs": round(carbs, 1) if carbs is not None else 0,
                        "fat": round(fat, 1) if fat is not None else 0
                    }
                    
                    # Create a basic ingredients list based on the meal type
                    ingredients = []
                    if meal_type == "breakfast":
                        ingredients = [
                            {"name": "Oats", "amount": "1/2 cup"},
                            {"name": "Milk", "amount": "1 cup"},
                            {"name": "Honey", "amount": "1 tbsp"},
                            {"name": "Nuts", "amount": "1/4 cup"}
                        ]
                    elif meal_type == "lunch":
                        ingredients = [
                            {"name": "Chicken Breast", "amount": "150g"},
                            {"name": "Brown Rice", "amount": "1/2 cup"},
                            {"name": "Mixed Vegetables", "amount": "1 cup"},
                            {"name": "Olive Oil", "amount": "1 tbsp"}
                        ]
                    else:  # dinner
                        ingredients = [
                            {"name": "Salmon Fillet", "amount": "150g"},
                            {"name": "Quinoa", "amount": "1/2 cup"},
                            {"name": "Steamed Vegetables", "amount": "1.5 cups"},
                            {"name": "Lemon", "amount": "1/2"}
                        ]
                    
                    day_meals.append({
                        "meal_type": meal_type,
                        "name": selected_meal["name"],
                        "cuisine": selected_meal["cuisine"],
                        "is_vegetarian": selected_meal.get("vegetarian", True),
                        "is_vegan": selected_meal.get("vegan", False),
                        "nutrition": meal_nutrition,
                        "ingredients": ingredients,
                        "instructions": "Prepare according to package instructions or personal preference."
                    })
            
            # Add snacks if enabled (two snacks per day)
            if include_snacks:
                snack_options = [
                    {
                        "name": "Mediterranean Snack Plate", 
                        "cuisine": "Mediterranean", 
                        "vegetarian": True, 
                        "vegan": True,
                        "calories": 220, 
                        "protein": 8, 
                        "carbs": 25, 
                        "fat": 12,
                        "ingredients": [
                            {"name": "Hummus", "amount": "1/4 cup"},
                            {"name": "Cucumber Slices", "amount": "1/2 cup"},
                            {"name": "Olives", "amount": "5-6"},
                            {"name": "Whole Wheat Pita", "amount": "1/2 small"}
                        ]
                    },
                    {
                        "name": "Asian Edamame Snack", 
                        "cuisine": "Asian", 
                        "vegetarian": True, 
                        "vegan": True,
                        "calories": 180, 
                        "protein": 12, 
                        "carbs": 15, 
                        "fat": 8,
                        "ingredients": [
                            {"name": "Edamame", "amount": "1/2 cup"},
                            {"name": "Sea Salt", "amount": "to taste"},
                            {"name": "Sesame Seeds", "amount": "1/2 tsp"},
                            {"name": "Red Pepper Flakes", "amount": "a pinch"}
                        ]
                    },
                    {
                        "name": "Greek Yogurt Parfait", 
                        "cuisine": "Mediterranean", 
                        "vegetarian": True, 
                        "vegan": False,
                        "calories": 200, 
                        "protein": 15, 
                        "carbs": 22, 
                        "fat": 6,
                        "ingredients": [
                            {"name": "Greek Yogurt", "amount": "1/2 cup"},
                            {"name": "Honey", "amount": "1 tsp"},
                            {"name": "Walnuts", "amount": "1 tbsp"},
                            {"name": "Berries", "amount": "1/4 cup"}
                        ]
                    },
                    {
                        "name": "Asian Rice Crackers with Peanut Butter", 
                        "cuisine": "Asian", 
                        "vegetarian": True, 
                        "vegan": True,
                        "calories": 190, 
                        "protein": 5, 
                        "carbs": 20, 
                        "fat": 10,
                        "ingredients": [
                            {"name": "Rice Crackers", "amount": "4-5"},
                            {"name": "Peanut Butter", "amount": "1 tbsp"},
                            {"name": "Sesame Seeds", "amount": "1/2 tsp"}
                        ]
                    }
                ]
                
                # Filter snacks based on dietary restrictions
                filtered_snacks = []
                for snack in snack_options:
                    if is_vegan and not snack.get("vegan", False):
                        continue
                    if is_vegetarian and not snack.get("vegetarian", True):
                        continue
                    filtered_snacks.append(snack)
                
                # Add two snacks per day, ensuring variety
                snacks_to_add = []
                if filtered_snacks:
                    # First snack - select based on day of week for variety
                    first_snack_idx = (i * 2) % len(filtered_snacks)
                    first_snack = filtered_snacks[first_snack_idx]
                    
                    # Second snack - select a different one
                    second_snack_idx = (first_snack_idx + 1) % len(filtered_snacks)
                    second_snack = filtered_snacks[second_snack_idx]
                    
                    # Add both snacks with appropriate meal types
                    for idx, selected_snack in enumerate([first_snack, second_snack]):
                        # Use the actual nutrition data from the snack
                        if all(key in selected_snack for key in ['calories', 'protein', 'carbs', 'fat']):
                            snack_calories = selected_snack['calories']
                            snack_protein = selected_snack['protein']
                            snack_carbs = selected_snack['carbs']
                            snack_fat = selected_snack['fat']
                        else:
                            # Fallback calculation if nutrition data is missing
                            snack_calories = 200
                            snack_protein = 5
                            snack_carbs = 25
                            snack_fat = 8
                        
                        snack_data = {
                            "meal_type": f"snack_{idx+1}",
                            "name": selected_snack.get("name", "Healthy Snack"),
                            "cuisine": selected_snack.get("cuisine", "International"),
                            "is_vegetarian": selected_snack.get("vegetarian", True),
                            "is_vegan": selected_snack.get("vegan", False),
                            "nutrition": {
                                "calories": round(snack_calories),
                                "protein": round(snack_protein, 1),
                                "carbs": round(snack_carbs, 1),
                                "fat": round(snack_fat, 1)
                            },
                            "ingredients": selected_snack.get("ingredients", ["ingredients vary"]),
                            "instructions": "Enjoy as is or prepare according to package instructions."
                        }
                        snacks_to_add.append(snack_data)
                
                # Add the snacks to the day's meals
                day_meals.extend(snacks_to_add)
            
            # Add the day to the weekly plan
            weekly_plan.append({
                "day": day,
                "date": day_date.strftime("%Y-%m-%d"),
                "meals": day_meals
            })
        
        # Generate shopping list based on cuisine
        shopping_list = self._generate_cuisine_shopping_list(favorite_cuisines, dietary_restrictions)
        
        # Calculate total nutritional values for the week
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        for day in weekly_plan:
            for meal in day.get('meals', []):
                if 'nutrition' in meal:
                    total_calories += meal['nutrition'].get('calories', 0)
                    total_protein += meal['nutrition'].get('protein', 0)
                    total_carbs += meal['nutrition'].get('carbs', 0)
                    total_fat += meal['nutrition'].get('fat', 0)
        
        # Calculate daily averages
        days_with_meals = len(weekly_plan)
        if days_with_meals > 0:
            avg_daily_calories = round(total_calories / days_with_meals)
            avg_daily_protein = round(total_protein / days_with_meals, 1)
            avg_daily_carbs = round(total_carbs / days_with_meals, 1)
            avg_daily_fat = round(total_fat / days_with_meals, 1)
        else:
            avg_daily_calories = avg_daily_protein = avg_daily_carbs = avg_daily_fat = 0
        
        # Calculate macronutrient distribution
        total_macros = avg_daily_protein * 4 + avg_daily_carbs * 4 + avg_daily_fat * 9
        if total_macros > 0:
            protein_pct = round(avg_daily_protein * 4 * 100 / total_macros)
            carbs_pct = round(avg_daily_carbs * 4 * 100 / total_macros)
            fat_pct = 100 - protein_pct - carbs_pct
        else:
            protein_pct = carbs_pct = fat_pct = 0
        
        return {
            "days": weekly_plan,
            "shopping_list": {
                "ingredients": shopping_list,
                "estimated_cost": sum(item.get('estimated_cost', 0) for item in shopping_list)
            },
            "nutrition_summary": {
                "daily_average": {
                    "calories": avg_daily_calories,
                    "protein": f"{avg_daily_protein}g",
                    "carbs": f"{avg_daily_carbs}g",
                    "fat": f"{avg_daily_fat}g"
                },
                "weekly_totals": {
                    "calories": round(total_calories),
                    "protein": f"{round(total_protein, 1)}g",
                    "carbs": f"{round(total_carbs, 1)}g",
                    "fat": f"{round(total_fat, 1)}g"
                },
                "targets": {
                    "calories": target_calories,
                    "protein": f"{target_protein}g",
                    "carbs": f"{target_carbs}g",
                    "fat": f"{target_fat}g"
                },
                "dietary_considerations": dietary_restrictions,
                "meal_inclusions": {
                    "breakfast": include_breakfast,
                    "lunch": include_lunch,
                    "dinner": include_dinner,
                    "snacks": include_snacks
                }
            },
            "generated_at": datetime.now().isoformat(),
            "preferences_used": preferences,
            "plan_type": "fallback"
        }
    
    def _generate_cuisine_shopping_list(self, favorite_cuisines: List[str], dietary_restrictions: List[str]) -> List[Dict[str, Any]]:
        """Generate a shopping list based on favorite cuisines"""
        
        cuisine_ingredients = {
            "indian": [
                {"item": "Basmati Rice", "category": "Grains", "estimated_cost": 3.00},
                {"item": "Red Lentils (Dal)", "category": "Legumes", "estimated_cost": 2.50},
                {"item": "Chickpeas", "category": "Legumes", "estimated_cost": 2.00},
                {"item": "Garam Masala", "category": "Spices", "estimated_cost": 3.50},
                {"item": "Turmeric", "category": "Spices", "estimated_cost": 2.00},
                {"item": "Cumin Seeds", "category": "Spices", "estimated_cost": 2.50},
                {"item": "Coriander Seeds", "category": "Spices", "estimated_cost": 2.00},
                {"item": "Onions", "category": "Vegetables", "estimated_cost": 2.00},
                {"item": "Tomatoes", "category": "Vegetables", "estimated_cost": 3.00},
                {"item": "Ginger", "category": "Vegetables", "estimated_cost": 1.50},
                {"item": "Garlic", "category": "Vegetables", "estimated_cost": 1.00},
                {"item": "Coconut Oil", "category": "Oils", "estimated_cost": 4.00},
                {"item": "Paneer", "category": "Dairy", "estimated_cost": 4.50},
                {"item": "Yogurt", "category": "Dairy", "estimated_cost": 3.00},
            ],
            "italian": [
                {"item": "Pasta (Various)", "category": "Grains", "estimated_cost": 4.00},
                {"item": "Arborio Rice", "category": "Grains", "estimated_cost": 3.50},
                {"item": "Canned Tomatoes", "category": "Canned Goods", "estimated_cost": 2.50},
                {"item": "Olive Oil", "category": "Oils", "estimated_cost": 5.00},
                {"item": "Parmesan Cheese", "category": "Dairy", "estimated_cost": 6.00},
                {"item": "Mozzarella", "category": "Dairy", "estimated_cost": 4.00},
                {"item": "Fresh Basil", "category": "Herbs", "estimated_cost": 2.50},
                {"item": "Garlic", "category": "Vegetables", "estimated_cost": 1.00},
                {"item": "Onions", "category": "Vegetables", "estimated_cost": 2.00},
                {"item": "Mushrooms", "category": "Vegetables", "estimated_cost": 3.00},
                {"item": "Eggplant", "category": "Vegetables", "estimated_cost": 2.50},
                {"item": "Zucchini", "category": "Vegetables", "estimated_cost": 2.00},
            ],
            "mediterranean": [
                {"item": "Quinoa", "category": "Grains", "estimated_cost": 4.00},
                {"item": "Chickpeas", "category": "Legumes", "estimated_cost": 2.00},
                {"item": "Lentils", "category": "Legumes", "estimated_cost": 2.50},
                {"item": "Olive Oil", "category": "Oils", "estimated_cost": 5.00},
                {"item": "Feta Cheese", "category": "Dairy", "estimated_cost": 4.50},
                {"item": "Greek Yogurt", "category": "Dairy", "estimated_cost": 4.00},
                {"item": "Cucumbers", "category": "Vegetables", "estimated_cost": 2.00},
                {"item": "Tomatoes", "category": "Vegetables", "estimated_cost": 3.00},
                {"item": "Bell Peppers", "category": "Vegetables", "estimated_cost": 3.50},
                {"item": "Red Onions", "category": "Vegetables", "estimated_cost": 2.00},
                {"item": "Fresh Herbs", "category": "Herbs", "estimated_cost": 3.00},
                {"item": "Tahini", "category": "Condiments", "estimated_cost": 5.00},
            ],
            "american": [
                {"item": "Quinoa", "category": "Grains", "estimated_cost": 4.00},
                {"item": "Brown Rice", "category": "Grains", "estimated_cost": 3.00},
                {"item": "Oats", "category": "Grains", "estimated_cost": 3.50},
                {"item": "Black Beans", "category": "Legumes", "estimated_cost": 2.00},
                {"item": "Avocados", "category": "Vegetables", "estimated_cost": 4.00},
                {"item": "Sweet Potatoes", "category": "Vegetables", "estimated_cost": 2.50},
                {"item": "Spinach", "category": "Vegetables", "estimated_cost": 2.00},
                {"item": "Broccoli", "category": "Vegetables", "estimated_cost": 2.50},
                {"item": "Carrots", "category": "Vegetables", "estimated_cost": 1.50},
                {"item": "Cheese", "category": "Dairy", "estimated_cost": 4.00},
                {"item": "Almond Milk", "category": "Dairy Alternatives", "estimated_cost": 3.50},
                {"item": "Nuts & Seeds", "category": "Snacks", "estimated_cost": 5.00},
            ]
        }
        
        # Default shopping list
        default_shopping_list = [
            {"item": "Mixed Vegetables", "category": "Vegetables", "estimated_cost": 8.00},
            {"item": "Fruits", "category": "Fruits", "estimated_cost": 6.00},
            {"item": "Grains", "category": "Grains", "estimated_cost": 5.00},
            {"item": "Legumes", "category": "Legumes", "estimated_cost": 4.00},
            {"item": "Herbs & Spices", "category": "Seasonings", "estimated_cost": 3.00},
        ]
        
        if not favorite_cuisines:
            return default_shopping_list
        
        # Use ingredients from the first favorite cuisine
        cuisine = favorite_cuisines[0].lower()
        if cuisine in cuisine_ingredients:
            shopping_list = cuisine_ingredients[cuisine]
            
            # Filter out non-vegan items if needed
            if 'vegan' in [r.lower() for r in dietary_restrictions]:
                shopping_list = [item for item in shopping_list if item["category"] not in ["Dairy", "Meat"]]
            
            return shopping_list
        
        return default_shopping_list
    
    def _fix_common_json_issues(self, json_str: str) -> str:
        """Fix common JSON formatting issues that LLMs make"""
        print(f'🔥 JSON_FIXER: Attempting to fix JSON issues')
        
        # Remove markdown code blocks
        json_str = json_str.replace('```json', '').replace('```', '')
        
        # Fix trailing commas before closing brackets/braces
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix missing commas between objects
        json_str = re.sub(r'}\s*{', '},{', json_str)
        json_str = re.sub(r']\s*\[', '],[', json_str)
        
        # Fix single quotes to double quotes
        json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
        json_str = re.sub(r": '([^']*)'", r': "\1"', json_str)
        
        # Fix unquoted keys
        json_str = re.sub(r'(\w+):', r'"\1":', json_str)
        
        # Fix serving_size issues (common LLM error)
        json_str = re.sub(r'"serving_size":\s*([^,}\]]+)', r'"serving_size": "1"', json_str)
        
        print(f'🔥 JSON_FIXER: Fixed JSON preview: {json_str[:300]}...')
        return json_str
    
    def _extract_meal_plan_from_text(self, text: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Extract meal plan information from text when JSON parsing fails"""
        print('🔥 TEXT_EXTRACTOR: Attempting to extract meal plan from text')
        
        # Get preferences with fallbacks
        favorite_cuisines = preferences.get('favorite_cuisines', preferences.get('favoriteCuisines', []))
        include_breakfast = preferences.get('includeBreakfast', True)
        include_lunch = preferences.get('includeLunch', True)
        include_dinner = preferences.get('includeDinner', True)
        include_snacks = preferences.get('includeSnacks', False)
        target_calories = preferences.get('targetCalories', 2000)
        target_protein = preferences.get('targetProtein', 150)
        target_carbs = preferences.get('targetCarbs', 200)
        target_fat = preferences.get('targetFat', 65)
        
        # Calculate macros per meal type
        macros = {
            'breakfast': {
                'calories': int(target_calories * 0.25) if include_breakfast else 0,
                'protein': int(target_protein * 0.25) if include_breakfast else 0,
                'carbs': int(target_carbs * 0.25) if include_breakfast else 0,
                'fat': int(target_fat * 0.25) if include_breakfast else 0
            },
            'lunch': {
                'calories': int(target_calories * 0.35) if include_lunch else 0,
                'protein': int(target_protein * 0.35) if include_lunch else 0,
                'carbs': int(target_carbs * 0.35) if include_lunch else 0,
                'fat': int(target_fat * 0.35) if include_lunch else 0
            },
            'dinner': {
                'calories': int(target_calories * 0.4) if include_dinner else 0,
                'protein': int(target_protein * 0.4) if include_dinner else 0,
                'carbs': int(target_carbs * 0.4) if include_dinner else 0,
                'fat': int(target_fat * 0.4) if include_dinner else 0
            },
            'snack': {
                'calories': int(target_calories * 0.15) if include_snacks else 0,
                'protein': int(target_protein * 0.15) if include_snacks else 0,
                'carbs': int(target_carbs * 0.15) if include_snacks else 0,
                'fat': int(target_fat * 0.15) if include_snacks else 0
            }
        }
        
        # Look for day patterns
        import re
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        extracted_days = []
        for day_idx, day in enumerate(days):
            # Look for day patterns in text
            day_pattern = rf"{day}[\s:]*([\s\S]*?)(?=(?:{'|'.join(days)})|$)"
            day_match = re.search(day_pattern, text, re.IGNORECASE | re.DOTALL)
            
            if day_match:
                day_text = day_match.group(1).strip()
                
                # Initialize day data with macros
                day_data = {
                    'day': day,
                    'date': '',  # Will be filled later
                    'meals': {},
                    'daily_macros': {
                        'calories': 0,
                        'protein': 0,
                        'carbs': 0,
                        'fat': 0
                    }
                }
                
                # Define meal types to look for
                meal_types = []
                if include_breakfast:
                    meal_types.append(('breakfast', r'breakfast[\s:]*([^\n]+)'))
                if include_lunch:
                    meal_types.append(('lunch', r'lunch[\s:]*([^\n]+)'))
                if include_dinner:
                    meal_types.append(('dinner', r'dinner[\s:]*([^\n]+)'))
                if include_snacks:
                    meal_types.extend([
                        ('morning_snack', r'(?:morning[\s-]*snack|snack[\s1])[\s:]*([^\n]+)'),
                        ('afternoon_snack', r'(?:afternoon[\s-]*snack|snack[\s2])[\s:]*([^\n]+)')
                    ])
                
                # Extract meals
                for meal_type, pattern in meal_types:
                    meal_match = re.search(pattern, day_text, re.IGNORECASE)
                    if meal_match:
                        meal_name = meal_match.group(1).strip()
                        meal_name = re.sub(r'^[\s"\'-]+|[\s"\'-]+$', '', meal_name)
                        
                        if meal_name:
                            # Use appropriate macros based on meal type
                            meal_macros = macros.get(meal_type.split('_')[0], macros['snack'])
                            
                            day_data['meals'][meal_type] = {
                                "name": meal_name,
                                "cuisine": favorite_cuisines[0] if favorite_cuisines else "International",
                                "prep_time": "15-20 minutes",
                                "cook_time": "20-30 minutes",
                                "difficulty": "Medium",
                                "servings": 2,
                                "ingredients": ["See recipe details for ingredients"],
                                "instructions": [f"Prepare {meal_name} according to your preferred recipe"],
                                "nutritional_info": {
                                    "calories": meal_macros['calories'],
                                    "protein": f"{meal_macros['protein']}g",
                                    "carbs": f"{meal_macros['carbs']}g",
                                    "fat": f"{meal_macros['fat']}g"
                                },
                                "tags": ["healthy", "balanced"]
                            }
                            
                            # Update daily macros
                            day_data['daily_macros']['calories'] += meal_macros['calories']
                            day_data['daily_macros']['protein'] += meal_macros['protein']
                            day_data['daily_macros']['carbs'] += meal_macros['carbs']
                            day_data['daily_macros']['fat'] += meal_macros['fat']
                
                if day_data['meals']:  # Only add days that have meals
                    extracted_days.append(day_data)
        
        if extracted_days:
            print(f'🔥 TEXT_EXTRACTOR: Successfully extracted {len(extracted_days)} days')
            
            # Fill in dates and calculate weekly totals
            from datetime import datetime, timedelta
            today = datetime.now()
            weekly_macros = {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0
            }
            
            for i, day_plan in enumerate(extracted_days):
                day_plan["date"] = (today + timedelta(days=i)).strftime("%Y-%m-%d")
                # Update weekly totals
                for macro in ['calories', 'protein', 'carbs', 'fat']:
                    weekly_macros[macro] += day_plan['daily_macros'][macro]
            
            # Calculate daily averages
            num_days = len(extracted_days) if extracted_days else 1
            daily_avg = {
                'calories': weekly_macros['calories'] // num_days,
                'protein': weekly_macros['protein'] // num_days,
                'carbs': weekly_macros['carbs'] // num_days,
                'fat': weekly_macros['fat'] // num_days
            }
            
            return {
                "week_summary": {
                    "theme": f"LLM-generated meal plan ({', '.join(favorite_cuisines) if favorite_cuisines else 'varied'} cuisine)",
                    "total_recipes": sum(len(day['meals']) for day in extracted_days),
                    "prep_tips": [
                        "Prep ingredients in advance",
                        "Cook grains in batches",
                        "Plan your shopping list"
                    ],
                    "shopping_highlights": ["Fresh vegetables", "Whole grains", "Lean proteins"],
                    "target_macros": {
                        'calories': target_calories,
                        'protein': target_protein,
                        'carbs': target_carbs,
                        'fat': target_fat
                    },
                    "weekly_averages": {
                        'calories': daily_avg['calories'],
                        'protein': f"{daily_avg['protein']}g",
                        'carbs': f"{daily_avg['carbs']}g",
                        'fat': f"{daily_avg['fat']}g"
                    }
                },
                "days": extracted_days,
                "weekly_shopping_list": self._generate_cuisine_shopping_list(
                    favorite_cuisines, 
                    preferences.get('dietary_restrictions', [])
                ),
                "nutritional_summary": {
                    "weekly_highlights": ["Balanced macronutrients", "Variety of vegetables", "Adequate protein"],
                    "variety_score": "Good",
                    "health_rating": "Excellent"
                },
                "generated_at": datetime.now().isoformat(),
                "preferences_used": {
                    "dietary_restrictions": preferences.get('dietary_restrictions', []),
                    "favorite_cuisines": favorite_cuisines,
                    "include_breakfast": include_breakfast,
                    "include_lunch": include_lunch,
                    "include_dinner": include_dinner,
                    "include_snacks": include_snacks
                },
                "plan_type": "llm_text_extracted"
            }
        
        print('🔥 TEXT_EXTRACTOR: Failed to extract meaningful meal plan')
        return self._generate_fallback_meal_plan(preferences)
    
    def get_recipe_suggestions(self, meal_type: str, preferences: Dict[str, Any], count: int = 5) -> List[Dict[str, Any]]:
        """Get recipe suggestions using free LLM or fallback"""
        try:
            if self.service == 'ollama':
                return self._get_suggestions_with_ollama(meal_type, preferences, count)
            elif self.service == 'huggingface':
                return self._get_suggestions_with_huggingface(meal_type, preferences, count)
            else:
                return self._get_fallback_suggestions(meal_type, preferences, count)
        except Exception as e:
            logger.error(f"Error getting recipe suggestions: {str(e)}")
            return self._get_fallback_suggestions(meal_type, preferences, count)
    
    def _get_suggestions_with_ollama(self, meal_type: str, preferences: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """Get recipe suggestions using Ollama"""
        # Implementation for Ollama recipe suggestions
        return self._get_fallback_suggestions(meal_type, preferences, count)
    
    def _get_suggestions_with_huggingface(self, meal_type: str, preferences: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """Get recipe suggestions using Hugging Face"""
        # Implementation for Hugging Face recipe suggestions
        return self._get_fallback_suggestions(meal_type, preferences, count)
    
    def _get_fallback_suggestions(self, meal_type: str, preferences: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """Get fallback recipe suggestions"""
        dietary_restrictions = preferences.get('dietary_restrictions', [])
        is_vegetarian = 'vegetarian' in [r.lower() for r in dietary_restrictions]
        
        suggestions = []
        base_recipes = {
            "breakfast": [
                {"name": "Overnight Oats", "cuisine": "American"},
                {"name": "Avocado Toast", "cuisine": "American"},
                {"name": "Smoothie Bowl", "cuisine": "American"},
                {"name": "Greek Yogurt Parfait", "cuisine": "Mediterranean"},
            ],
            "lunch": [
                {"name": "Quinoa Salad", "cuisine": "Mediterranean"},
                {"name": "Buddha Bowl", "cuisine": "American"},
                {"name": "Lentil Soup", "cuisine": "International"},
                {"name": "Veggie Wrap", "cuisine": "American"},
            ],
            "dinner": [
                {"name": "Grilled Chicken", "cuisine": "American"},
                {"name": "Vegetable Curry", "cuisine": "Indian"},
                {"name": "Pasta Primavera", "cuisine": "Italian"},
                {"name": "Stuffed Peppers", "cuisine": "Mediterranean"},
            ]
        }
        
        recipes = base_recipes.get(meal_type, [])
        for i, recipe in enumerate(recipes[:count]):
            suggestions.append({
                "name": recipe["name"],
                "cuisine": recipe["cuisine"],
                "prep_time": "15 minutes",
                "cook_time": "20 minutes",
                "difficulty": "Easy",
                "servings": 2,
                "ingredients": ["Basic ingredients"],
                "instructions": [f"Prepare {recipe['name']} following standard recipe"],
                "nutritional_highlights": ["Balanced nutrition"],
                "tags": ["healthy"]
            })
        
        return suggestions 