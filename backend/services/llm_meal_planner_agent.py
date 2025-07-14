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
        
        # Free model options
        self.hf_model = "microsoft/DialoGPT-medium"  # Free Hugging Face model
        self.ollama_model = "llama3.2:latest"  # Free Ollama model (3.2B parameters)
        
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
            prompt = self._build_meal_plan_prompt(preferences)
            print(f'🔥 OLLAMA: Generated prompt length: {len(prompt)} characters')
            print(f'🔥 OLLAMA: Prompt preview (first 500 chars): {prompt[:500]}...')
            
            print(f'🔥 OLLAMA: Sending request to {self.ollama_url}/api/generate')
            print(f'🔥 OLLAMA: Using model: {self.ollama_model}')
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 4000
                    }
                },
                timeout=120  # Ollama can be slow
            )
            
            print(f'🔥 OLLAMA: Response status code: {response.status_code}')
            
            if response.status_code == 200:
                result = response.json()
                meal_plan_text = result.get('response', '')
                
                print(f'🔥 OLLAMA: Raw response length: {len(meal_plan_text)} characters')
                print(f'🔥 OLLAMA: Raw response preview (first 1000 chars): {meal_plan_text[:1000]}...')
                
                # Try to extract JSON from the response
                try:
                    # Look for JSON in the response
                    start_idx = meal_plan_text.find('{')
                    end_idx = meal_plan_text.rfind('}') + 1
                    print(f'🔥 OLLAMA: JSON start index: {start_idx}, end index: {end_idx}')
                    
                    if start_idx != -1 and end_idx != -1:
                        json_str = meal_plan_text[start_idx:end_idx]
                        print(f'🔥 OLLAMA: Extracted JSON string length: {len(json_str)} characters')
                        print(f'🔥 OLLAMA: JSON preview (first 500 chars): {json_str[:500]}...')
                        
                        # Try to fix common JSON issues
                        fixed_json_str = self._fix_common_json_issues(json_str)
                        
                        raw_meal_plan = json.loads(fixed_json_str)
                        print(f'🔥 OLLAMA: Successfully parsed JSON meal plan')
                        print(f'🔥 OLLAMA: Raw meal plan keys: {list(raw_meal_plan.keys())}')
                        
                        # Convert simple format to expected format
                        meal_plan = self._convert_simple_to_full_format(raw_meal_plan, preferences)
                        print(f'🔥 OLLAMA: Converted meal plan keys: {list(meal_plan.keys())}')
                        
                        logger.info(f"Successfully generated meal plan with Ollama")
                        return meal_plan
                    else:
                        print(f'🔥 OLLAMA: No valid JSON found in response')
                except json.JSONDecodeError as e:
                    print(f'🔥 OLLAMA: JSON decode error: {e}')
                    print(f'🔥 OLLAMA: Problematic JSON string: {json_str[:200]}...')
                    logger.warning("Failed to parse Ollama response as JSON")
                    
                    # Try alternative JSON extraction methods
                    try:
                        alternative_plan = self._extract_meal_plan_from_text(meal_plan_text, preferences)
                        if alternative_plan:
                            print(f'🔥 OLLAMA: Successfully extracted meal plan using alternative method')
                            return alternative_plan
                    except Exception as alt_e:
                        print(f'🔥 OLLAMA: Alternative extraction also failed: {alt_e}')
            else:
                print(f'🔥 OLLAMA: Request failed with status {response.status_code}')
                print(f'🔥 OLLAMA: Error response: {response.text}')
                    
        except Exception as e:
            logger.error(f"Error with Ollama: {str(e)}")
        
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
        """Build a simple, effective prompt for free LLMs"""
        print(f'🔥 PROMPT_BUILDER: Building prompt with preferences: {preferences}')
        
        # Handle both camelCase and snake_case keys
        dietary_restrictions = preferences.get('dietary_restrictions', preferences.get('dietaryRestrictions', []))
        favorite_cuisines = preferences.get('favorite_cuisines', preferences.get('favoriteCuisines', []))
        allergies = preferences.get('allergies', preferences.get('allergens', []))
        weekly_budget = preferences.get('weekly_budget', preferences.get('weeklyBudget', ''))
        serving_amount = preferences.get('serving_amount', preferences.get('servingAmount', ''))
        
        print(f'🔥 PROMPT_BUILDER: Extracted dietary_restrictions: {dietary_restrictions}')
        print(f'🔥 PROMPT_BUILDER: Extracted favorite_cuisines: {favorite_cuisines}')
        print(f'🔥 PROMPT_BUILDER: Extracted allergies: {allergies}')
        print(f'🔥 PROMPT_BUILDER: Extracted weekly_budget: {weekly_budget}')
        print(f'🔥 PROMPT_BUILDER: Extracted serving_amount: {serving_amount}')
        
        # Build dietary info
        dietary_info = []
        if dietary_restrictions:
            dietary_info.append(f"Diet: {', '.join(dietary_restrictions)}")
        if favorite_cuisines:
            dietary_info.append(f"Preferred cuisines: {', '.join(favorite_cuisines)}")
        if allergies:
            dietary_info.append(f"Allergies: {', '.join(allergies)}")
        if weekly_budget:
            dietary_info.append(f"Weekly budget: ${weekly_budget}")
        if serving_amount:
            dietary_info.append(f"Serving {serving_amount} people")
        
        dietary_text = '. '.join(dietary_info) if dietary_info else "No specific dietary restrictions"
        
        # Build budget and serving context
        budget_context = ""
        if weekly_budget:
            budget_context = f"Keep the total estimated cost under ${weekly_budget} for the week. "
        
        serving_context = ""
        if serving_amount:
            serving_context = f"Scale all recipes to serve {serving_amount} people. "
        
        prompt = f"""Create a 7-day meal plan. {dietary_text}.

{budget_context}{serving_context}Focus on affordable, nutritious ingredients that provide good value.

Return ONLY valid JSON in this format:
{{
  "days": [
    {{
      "day": "Monday",
      "breakfast": {{"name": "Oatmeal with Berries", "ingredients": ["oats", "berries", "milk"]}},
      "lunch": {{"name": "Quinoa Salad", "ingredients": ["quinoa", "vegetables", "olive oil"]}},
      "dinner": {{"name": "Pasta Primavera", "ingredients": ["pasta", "vegetables", "herbs"]}}
    }},
    {{
      "day": "Tuesday",
      "breakfast": {{"name": "Avocado Toast", "ingredients": ["bread", "avocado", "tomato"]}},
      "lunch": {{"name": "Vegetable Soup", "ingredients": ["vegetables", "broth", "herbs"]}},
      "dinner": {{"name": "Stir Fry", "ingredients": ["vegetables", "rice", "sauce"]}}
    }}
  ],
  "shopping_list": ["oats", "berries", "milk", "quinoa", "vegetables", "olive oil", "pasta", "herbs", "bread", "avocado", "tomato", "broth", "rice", "sauce"],
  "estimated_cost": "$45"
}}

Generate all 7 days (Monday through Sunday) with breakfast, lunch, and dinner for each day. Make sure all meals follow the dietary requirements and budget constraints."""
        
        return prompt
    
    def _convert_simple_to_full_format(self, simple_plan: Dict[str, Any], preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Convert simple LLM response format to full expected format"""
        try:
            from datetime import datetime, timedelta
            
            # Get the days from the simple plan
            days_data = simple_plan.get('days', [])
            shopping_list = simple_plan.get('shopping_list', [])
            estimated_cost = simple_plan.get('estimated_cost', '$45-60')
            
            # Get budget and serving from preferences
            weekly_budget = preferences.get('weekly_budget', preferences.get('weeklyBudget', ''))
            serving_amount = preferences.get('serving_amount', preferences.get('servingAmount', '2'))
            
            # Convert each day to full format
            full_days = []
            today = datetime.now()
            
            for i, day_data in enumerate(days_data):
                day_name = day_data.get('day', f'Day {i+1}')
                day_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
                
                # Convert meals to full format
                meals = {}
                for meal_type in ['breakfast', 'lunch', 'dinner']:
                    if meal_type in day_data:
                        simple_meal = day_data[meal_type]
                        meals[meal_type] = {
                            "name": simple_meal.get('name', f'Meal {i+1}'),
                            "cuisine": "International",
                            "prep_time": "15 minutes",
                            "cook_time": "20 minutes", 
                            "difficulty": "Easy",
                            "servings": int(serving_amount) if serving_amount else 2,
                            "ingredients": simple_meal.get('ingredients', []),
                            "instructions": [f"Prepare {simple_meal.get('name', 'the meal')} with the listed ingredients"],
                            "nutritional_highlights": ["Balanced nutrition"],
                            "tags": ["healthy"]
                        }
                
                full_days.append({
                    "day": day_name,
                    "date": day_date,
                    "meals": meals,
                    "daily_notes": f"LLM-generated meal plan for {day_name}"
                })
            
            # Create full format response
            full_plan = {
                "week_summary": {
                    "theme": "LLM-Generated Weekly Meals",
                    "total_recipes": len(full_days) * 3,
                    "prep_tips": [
                        "Prep ingredients in advance",
                        "Cook grains in batches",
                        "Use fresh ingredients when possible"
                    ],
                    "shopping_highlights": ["Fresh ingredients", "Balanced nutrition"]
                },
                "days": full_days,
                "weekly_shopping_list": {
                    "all_ingredients": shopping_list,
                    "proteins": [item for item in shopping_list if item in ['chicken', 'fish', 'tofu', 'beans', 'lentils', 'quinoa']],
                    "vegetables": [item for item in shopping_list if item in ['vegetables', 'broccoli', 'spinach', 'tomato', 'avocado']],
                    "grains": [item for item in shopping_list if item in ['oats', 'rice', 'pasta', 'bread', 'quinoa']],
                    "dairy": [item for item in shopping_list if item in ['milk', 'yogurt', 'cheese']],
                    "pantry": [item for item in shopping_list if item in ['olive oil', 'herbs', 'spices', 'sauce']],
                    "estimated_cost": estimated_cost if estimated_cost else (f"${weekly_budget}" if weekly_budget else "$45-60")
                },
                "nutritional_summary": {
                    "weekly_highlights": ["Variety of meals", "Balanced nutrition", "Fresh ingredients"],
                    "variety_score": "Good",
                    "health_rating": "Excellent"
                },
                "generated_at": datetime.now().isoformat(),
                "preferences_used": preferences,
                "plan_type": "llm_generated"
            }
            
            return full_plan
            
        except Exception as e:
            print(f'🔥 CONVERT_FORMAT: Error converting format: {e}')
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
Make the meals healthy, varied, and follow the dietary restrictions."""
    
    def _parse_generated_text_to_meal_plan(self, text: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Parse generated text into a structured meal plan"""
        # This is a simplified parser - in a real implementation, you'd use more sophisticated NLP
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        today = datetime.now()
        
        meal_plan_days = []
        for i, day in enumerate(days):
            day_date = today + timedelta(days=i)
            
            # Simple meal suggestions based on preferences
            dietary_restrictions = preferences.get('dietary_restrictions', [])
            is_vegetarian = 'vegetarian' in [r.lower() for r in dietary_restrictions]
            
            meals = {
                "breakfast": {
                    "name": "Healthy Breakfast Bowl",
                    "cuisine": "American",
                    "prep_time": "10 minutes",
                    "cook_time": "5 minutes",
                    "difficulty": "Easy",
                    "servings": 2,
                    "ingredients": ["oats", "fruits", "nuts", "yogurt"],
                    "instructions": ["Mix oats with yogurt", "Add fruits and nuts", "Serve fresh"],
                    "nutritional_highlights": ["High fiber", "Protein"],
                    "tags": ["healthy", "quick"]
                },
                "lunch": {
                    "name": "Mediterranean Salad" if not is_vegetarian else "Quinoa Power Bowl",
                    "cuisine": "Mediterranean",
                    "prep_time": "15 minutes",
                    "cook_time": "10 minutes",
                    "difficulty": "Easy",
                    "servings": 2,
                    "ingredients": ["quinoa", "vegetables", "olive oil", "herbs"],
                    "instructions": ["Cook quinoa", "Chop vegetables", "Mix with dressing"],
                    "nutritional_highlights": ["Complete protein", "Vitamins"],
                    "tags": ["vegetarian", "filling"]
                },
                "dinner": {
                    "name": "Grilled Chicken with Vegetables" if not is_vegetarian else "Lentil Curry",
                    "cuisine": "American" if not is_vegetarian else "Indian",
                    "prep_time": "15 minutes",
                    "cook_time": "30 minutes",
                    "difficulty": "Medium",
                    "servings": 2,
                    "ingredients": ["chicken", "vegetables", "spices"] if not is_vegetarian else ["lentils", "curry spices", "vegetables"],
                    "instructions": ["Season protein", "Cook with vegetables", "Serve hot"],
                    "nutritional_highlights": ["High protein", "Balanced nutrition"],
                    "tags": ["satisfying", "healthy"]
                }
            }
            
            meal_plan_days.append({
                "day": day,
                "date": day_date.strftime("%Y-%m-%d"),
                "meals": meals,
                "daily_notes": f"AI-generated meal plan for {day}"
            })
        
        return {
            "week_summary": {
                "theme": "AI-Generated Healthy Week",
                "total_recipes": 21,
                "prep_tips": [
                    "Prep vegetables in advance",
                    "Cook grains in batches",
                    "Plan your shopping list"
                ],
                "shopping_highlights": ["Fresh vegetables", "Whole grains", "Lean proteins"]
            },
            "days": meal_plan_days,
            "weekly_shopping_list": {
                "proteins": ["chicken", "lentils", "quinoa"] if not is_vegetarian else ["lentils", "quinoa", "tofu"],
                "vegetables": ["broccoli", "spinach", "bell peppers", "onions"],
                "grains": ["oats", "quinoa", "brown rice"],
                "dairy": ["yogurt", "milk"] if 'vegan' not in [r.lower() for r in dietary_restrictions] else [],
                "pantry": ["olive oil", "spices", "herbs", "nuts"],
                "estimated_cost": "$50-65"
            },
            "nutritional_summary": {
                "weekly_highlights": ["Balanced macronutrients", "Variety of vegetables", "Adequate protein"],
                "variety_score": "Good",
                "health_rating": "Excellent"
            },
            "generated_at": datetime.now().isoformat(),
            "preferences_used": preferences,
            "plan_type": "llm_generated"
        }
    
    def _generate_fallback_meal_plan(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a basic fallback meal plan when LLM is not available"""
        print(f'🔥 FALLBACK: Generating fallback meal plan')
        print(f'🔥 FALLBACK: Preferences received: {preferences}')
        
        from datetime import datetime, timedelta
        
        # Get current date
        today = datetime.now()
        
        # Extract preferences
        dietary_restrictions = preferences.get('dietary_restrictions', preferences.get('dietaryRestrictions', []))
        favorite_cuisines = preferences.get('favorite_cuisines', preferences.get('favoriteCuisines', []))
        cooking_skill = preferences.get('cooking_skill_level', preferences.get('cookingSkillLevel', 'intermediate'))
        max_time = preferences.get('max_cooking_time', preferences.get('maxCookingTime', '30 minutes'))
        
        is_vegetarian = 'vegetarian' in [r.lower() for r in dietary_restrictions]
        is_vegan = 'vegan' in [r.lower() for r in dietary_restrictions]
        
        print(f'🔥 FALLBACK: Dietary restrictions: {dietary_restrictions}')
        print(f'🔥 FALLBACK: Favorite cuisines: {favorite_cuisines}')
        print(f'🔥 FALLBACK: Is vegetarian: {is_vegetarian}')
        print(f'🔥 FALLBACK: Is vegan: {is_vegan}')
        
        # Cuisine-specific meal templates
        cuisine_meals = {
            "indian": {
                "breakfast": [
                    {"name": "Masala Chai with Paratha", "cuisine": "Indian", "vegetarian": True, "vegan": False},
                    {"name": "Poha (Flattened Rice)", "cuisine": "Indian", "vegetarian": True, "vegan": True},
                    {"name": "Upma with Vegetables", "cuisine": "Indian", "vegetarian": True, "vegan": True},
                    {"name": "Idli with Sambar", "cuisine": "Indian", "vegetarian": True, "vegan": True},
                ],
                "lunch": [
                    {"name": "Dal Rice with Pickle", "cuisine": "Indian", "vegetarian": True, "vegan": True},
                    {"name": "Chana Masala with Roti", "cuisine": "Indian", "vegetarian": True, "vegan": True},
                    {"name": "Vegetable Biryani", "cuisine": "Indian", "vegetarian": True, "vegan": True},
                    {"name": "Rajma with Basmati Rice", "cuisine": "Indian", "vegetarian": True, "vegan": True},
                ],
                "dinner": [
                    {"name": "Palak Paneer with Naan", "cuisine": "Indian", "vegetarian": True, "vegan": False},
                    {"name": "Aloo Gobi with Chapati", "cuisine": "Indian", "vegetarian": True, "vegan": True},
                    {"name": "Mixed Vegetable Curry", "cuisine": "Indian", "vegetarian": True, "vegan": True},
                    {"name": "Dal Tadka with Rice", "cuisine": "Indian", "vegetarian": True, "vegan": True},
                ]
            },
            "italian": {
                "breakfast": [
                    {"name": "Cappuccino with Cornetto", "cuisine": "Italian", "vegetarian": True, "vegan": False},
                    {"name": "Italian Toast with Tomato", "cuisine": "Italian", "vegetarian": True, "vegan": True},
                    {"name": "Ricotta Pancakes", "cuisine": "Italian", "vegetarian": True, "vegan": False},
                ],
                "lunch": [
                    {"name": "Margherita Pizza", "cuisine": "Italian", "vegetarian": True, "vegan": False},
                    {"name": "Pasta Aglio e Olio", "cuisine": "Italian", "vegetarian": True, "vegan": True},
                    {"name": "Caprese Salad", "cuisine": "Italian", "vegetarian": True, "vegan": False},
                    {"name": "Minestrone Soup", "cuisine": "Italian", "vegetarian": True, "vegan": True},
                ],
                "dinner": [
                    {"name": "Spaghetti Carbonara", "cuisine": "Italian", "vegetarian": False, "vegan": False},
                    {"name": "Eggplant Parmigiana", "cuisine": "Italian", "vegetarian": True, "vegan": False},
                    {"name": "Pasta Primavera", "cuisine": "Italian", "vegetarian": True, "vegan": False},
                    {"name": "Risotto with Mushrooms", "cuisine": "Italian", "vegetarian": True, "vegan": False},
                ]
            },
            "mediterranean": {
                "breakfast": [
                    {"name": "Greek Yogurt with Honey", "cuisine": "Mediterranean", "vegetarian": True, "vegan": False},
                    {"name": "Avocado Toast with Feta", "cuisine": "Mediterranean", "vegetarian": True, "vegan": False},
                    {"name": "Mediterranean Smoothie Bowl", "cuisine": "Mediterranean", "vegetarian": True, "vegan": True},
                ],
                "lunch": [
                    {"name": "Greek Salad", "cuisine": "Mediterranean", "vegetarian": True, "vegan": False},
                    {"name": "Hummus with Pita", "cuisine": "Mediterranean", "vegetarian": True, "vegan": True},
                    {"name": "Mediterranean Wrap", "cuisine": "Mediterranean", "vegetarian": True, "vegan": False},
                    {"name": "Lentil Soup", "cuisine": "Mediterranean", "vegetarian": True, "vegan": True},
                ],
                "dinner": [
                    {"name": "Grilled Vegetables with Quinoa", "cuisine": "Mediterranean", "vegetarian": True, "vegan": True},
                    {"name": "Stuffed Bell Peppers", "cuisine": "Mediterranean", "vegetarian": True, "vegan": True},
                    {"name": "Mediterranean Pasta", "cuisine": "Mediterranean", "vegetarian": True, "vegan": False},
                    {"name": "Falafel with Tahini", "cuisine": "Mediterranean", "vegetarian": True, "vegan": True},
                ]
            },
            "american": {
                "breakfast": [
                    {"name": "Pancakes with Syrup", "cuisine": "American", "vegetarian": True, "vegan": False},
                    {"name": "Avocado Toast", "cuisine": "American", "vegetarian": True, "vegan": True},
                    {"name": "Overnight Oats", "cuisine": "American", "vegetarian": True, "vegan": True},
                    {"name": "Smoothie Bowl", "cuisine": "American", "vegetarian": True, "vegan": True},
                ],
                "lunch": [
                    {"name": "Quinoa Buddha Bowl", "cuisine": "American", "vegetarian": True, "vegan": True},
                    {"name": "Grilled Cheese Sandwich", "cuisine": "American", "vegetarian": True, "vegan": False},
                    {"name": "Caesar Salad", "cuisine": "American", "vegetarian": True, "vegan": False},
                    {"name": "Veggie Burger", "cuisine": "American", "vegetarian": True, "vegan": True},
                ],
                "dinner": [
                    {"name": "Grilled Portobello Mushroom", "cuisine": "American", "vegetarian": True, "vegan": True},
                    {"name": "Mac and Cheese", "cuisine": "American", "vegetarian": True, "vegan": False},
                    {"name": "BBQ Jackfruit Sandwich", "cuisine": "American", "vegetarian": True, "vegan": True},
                    {"name": "Stuffed Sweet Potato", "cuisine": "American", "vegetarian": True, "vegan": True},
                ]
            }
        }
        
        # Default fallback meals if no specific cuisine is found
        default_meals = {
            "breakfast": [
                {"name": "Overnight Oats", "cuisine": "International", "vegetarian": True, "vegan": True},
                {"name": "Avocado Toast", "cuisine": "International", "vegetarian": True, "vegan": True},
                {"name": "Smoothie Bowl", "cuisine": "International", "vegetarian": True, "vegan": True},
                {"name": "Greek Yogurt Parfait", "cuisine": "International", "vegetarian": True, "vegan": False},
            ],
            "lunch": [
                {"name": "Quinoa Buddha Bowl", "cuisine": "International", "vegetarian": True, "vegan": True},
                {"name": "Lentil Soup", "cuisine": "International", "vegetarian": True, "vegan": True},
                {"name": "Veggie Wrap", "cuisine": "International", "vegetarian": True, "vegan": True},
                {"name": "Mixed Green Salad", "cuisine": "International", "vegetarian": True, "vegan": True},
            ],
            "dinner": [
                {"name": "Vegetable Stir-Fry", "cuisine": "International", "vegetarian": True, "vegan": True},
                {"name": "Stuffed Bell Peppers", "cuisine": "International", "vegetarian": True, "vegan": True},
                {"name": "Mushroom Risotto", "cuisine": "International", "vegetarian": True, "vegan": False},
                {"name": "Roasted Vegetable Bowl", "cuisine": "International", "vegetarian": True, "vegan": True},
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
        
        for i, day in enumerate(days):
            day_date = today + timedelta(days=i)
            
            day_meals = {}
            for meal_type in ["breakfast", "lunch", "dinner"]:
                available_for_meal = available_meals[meal_type]
                
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
                selected_meal = filtered_meals[i % len(filtered_meals)]
                
                day_meals[meal_type] = {
                    "name": selected_meal["name"],
                    "ingredients": ["ingredients vary"],  # Simplified for fallback
                    "cuisine": selected_meal["cuisine"]
                }
            
            weekly_plan.append({
                "day": day,
                "date": day_date.strftime("%Y-%m-%d"),
                **day_meals
            })
        
        # Generate shopping list based on cuisine
        shopping_list = self._generate_cuisine_shopping_list(favorite_cuisines, dietary_restrictions)
        
        return {
            "week_summary": f"Fallback meal plan focusing on {', '.join(favorite_cuisines) if favorite_cuisines else 'varied'} cuisine",
            "days": weekly_plan,
            "weekly_shopping_list": shopping_list,
            "nutritional_summary": {
                "focus": "Balanced nutrition with emphasis on fresh ingredients",
                "dietary_accommodations": dietary_restrictions
            },
            "generated_at": datetime.now().isoformat(),
            "preferences_used": preferences,
            "plan_type": "fallback_cuisine_focused"
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
        print(f'🔥 TEXT_EXTRACTOR: Attempting to extract meal plan from text')
        
        favorite_cuisines = preferences.get('favorite_cuisines', preferences.get('favoriteCuisines', []))
        
        # Look for day patterns
        import re
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        extracted_days = []
        for day in days:
            # Look for day patterns in text
            day_pattern = rf"{day}[:\s]*.*?(?=(?:{'|'.join(days)})|$)"
            day_match = re.search(day_pattern, text, re.IGNORECASE | re.DOTALL)
            
            if day_match:
                day_text = day_match.group(0)
                
                # Extract meals from day text
                meals = {}
                meal_types = ["breakfast", "lunch", "dinner"]
                
                for meal_type in meal_types:
                    meal_pattern = rf"{meal_type}[:\s]*([^,\n]*)"
                    meal_match = re.search(meal_pattern, day_text, re.IGNORECASE)
                    
                    if meal_match:
                        meal_name = meal_match.group(1).strip()
                        # Clean up the meal name
                        meal_name = re.sub(r'^["\s]*|["\s]*$', '', meal_name)
                        meal_name = re.sub(r'[{}"\[\]]', '', meal_name)
                        
                        if meal_name:
                            meals[meal_type] = {
                                "name": meal_name,
                                "ingredients": ["ingredients vary"],
                                "cuisine": favorite_cuisines[0] if favorite_cuisines else "International"
                            }
                
                if meals:
                    extracted_days.append({
                        "day": day,
                        "date": "",  # Will be filled later
                        **meals
                    })
        
        if extracted_days:
            print(f'🔥 TEXT_EXTRACTOR: Successfully extracted {len(extracted_days)} days')
            
            # Fill in dates
            from datetime import datetime, timedelta
            today = datetime.now()
            for i, day_plan in enumerate(extracted_days):
                day_plan["date"] = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            
            return {
                "week_summary": f"LLM-generated meal plan focusing on {', '.join(favorite_cuisines) if favorite_cuisines else 'varied'} cuisine",
                "days": extracted_days,
                "weekly_shopping_list": self._generate_cuisine_shopping_list(favorite_cuisines, preferences.get('dietary_restrictions', [])),
                "nutritional_summary": {
                    "focus": "LLM-generated with preference-based nutrition",
                    "dietary_accommodations": preferences.get('dietary_restrictions', [])
                },
                "generated_at": datetime.now().isoformat(),
                "preferences_used": preferences,
                "plan_type": "llm_text_extracted"
            }
        
        print(f'🔥 TEXT_EXTRACTOR: Failed to extract meaningful meal plan')
        return None
    
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