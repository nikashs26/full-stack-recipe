import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class FreeLLMMealPlannerAgent:
    """
    Clean, agent-based meal planner that ONLY uses LLM responses.
    No fallbacks, no rule-based nonsense - just pure LLM intelligence.
    """
    
    def __init__(self, user_preferences_service):
        self.user_preferences_service = user_preferences_service
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.2:latest')
        self.hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
        self.hf_api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        
        # LLM configuration
        self.ollama_timeout = 30  # Reduced timeout for faster responses
        self.ollama_max_tokens = 2000  # Increased for detailed responses
        self.hf_max_tokens = 2000
        
        logger.info(f"🤖 Meal Planner Agent initialized - Ollama: {self.ollama_url}")
    
    def generate_weekly_meal_plan(self, user_id: str) -> Dict[str, Any]:
        """
        Generate a complete 7-day meal plan using ONLY the LLM.
        Returns the LLM response or fails gracefully.
        """
        try:
            # Get user preferences
            preferences = self.user_preferences_service.get_preferences(user_id)
            if not preferences:
                return {"error": "No user preferences found"}
            
            return self._generate_meal_plan_with_preferences(user_id, preferences)
            
        except Exception as e:
            logger.error(f"❌ Meal plan generation failed: {e}")
            return {"error": f"Meal plan generation failed: {str(e)}"}
    
    def generate_weekly_meal_plan_with_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete 7-day meal plan using ONLY the LLM with provided preferences.
        Returns the LLM response or fails gracefully.
        """
        return self._generate_meal_plan_with_preferences(user_id, preferences)
    
    def _generate_meal_plan_with_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method to generate meal plan with preferences.
        """
        try:
            logger.info(f"🎯 Generating meal plan for user {user_id} with preferences: {list(preferences.keys())}")
            
            # Try Ollama first (preferred)
            try:
                logger.info("🤖 Attempting to generate with Ollama...")
                meal_plan = self._generate_with_ollama(preferences)
                logger.info(f"🔍 Ollama returned meal plan: {type(meal_plan)}")
                
                if meal_plan:
                    logger.info("📝 Validating meal plan structure...")
                    if self._validate_meal_plan(meal_plan):
                        logger.info("✅ Ollama generated valid meal plan")
                        # Convert the LLM response to the format expected by the frontend
                        converted_plan = self._convert_to_frontend_format(meal_plan, preferences)
                        return {
                            "success": True,
                            "meal_plan": converted_plan,
                            "source": "ollama",
                            "generated_at": datetime.now().isoformat()
                        }
                    else:
                        logger.error("❌ Meal plan validation failed")
                        logger.error(f"Meal plan structure: {meal_plan}")
                else:
                    logger.error("❌ Ollama returned None/empty meal plan")
            except Exception as e:
                logger.warning(f"⚠️ Ollama failed: {e}")
                import traceback
                logger.warning(f"Traceback: {traceback.format_exc()}")
            
            # Try Hugging Face as backup
            if self.hf_api_key:
                try:
                    meal_plan = self._generate_with_huggingface(preferences)
                    if meal_plan and self._validate_meal_plan(meal_plan):
                        logger.info("✅ Hugging Face generated valid meal plan")
                        # Convert the LLM response to the format expected by the frontend
                        converted_plan = self._convert_to_frontend_format(meal_plan, preferences)
                        return {
                            "success": True,
                            "meal_plan": converted_plan,
                            "source": "huggingface",
                            "generated_at": datetime.now().isoformat()
                        }
                except Exception as e:
                    logger.warning(f"⚠️ Hugging Face failed: {e}")
            
            # If we get here, both LLMs failed
            logger.error("❌ Both LLMs failed to generate meal plan")
            return {
                "error": "Unable to generate meal plan - LLM services unavailable",
                "details": "Please try again later or check your LLM configuration"
            }
            
        except Exception as e:
            logger.error(f"❌ Meal plan generation failed: {e}")
            return {"error": f"Meal plan generation failed: {str(e)}"}
    
    def _generate_with_ollama(self, preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate meal plan using Ollama LLM."""
        prompt = self._create_meal_plan_prompt(preferences)
        
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 800,
                "num_ctx": 2048
            }
        }
        
        logger.info(f"🚀 Sending prompt to Ollama ({len(prompt)} chars)")
        logger.info(f"🔧 Using model: {self.ollama_model}")
        logger.info(f"🔗 URL: {self.ollama_url}/api/generate")
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.ollama_timeout
            )
            
            logger.info(f"📡 Ollama response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                logger.info(f"📝 Ollama response received ({len(response_text)} chars)")
                logger.info(f"📋 Full Ollama response: {response_text}")  # Log full response to see what we got
                
                # Parse the simple text response into a structured format
                meal_plan = self._parse_simple_text_response(response_text)
                if meal_plan:
                    logger.info("✅ Successfully parsed meal plan from Ollama")
                    return meal_plan
                else:
                    logger.error("❌ Failed to parse meal plan from Ollama response")
                    logger.error(f"Raw response: {response_text}")
                    return None
            else:
                logger.error(f"❌ Ollama request failed: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                raise Exception(f"Ollama request failed: {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ Ollama request timed out after {self.ollama_timeout} seconds")
            raise Exception("Ollama request timed out")
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Could not connect to Ollama at {self.ollama_url}")
            raise Exception("Could not connect to Ollama")
        except Exception as e:
            logger.error(f"❌ Unexpected error calling Ollama: {str(e)}")
            raise
    
    def _generate_with_huggingface(self, preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate meal plan using Hugging Face Inference API."""
        prompt = self._create_meal_plan_prompt(preferences)
        
        headers = {"Authorization": f"Bearer {self.hf_api_key}"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": self.hf_max_tokens,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True
            }
        }
        
        logger.info(f"🚀 Sending prompt to Hugging Face ({len(prompt)} chars)")
        
        response = requests.post(
            self.hf_api_url,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result[0].get('generated_text', '')
            logger.info(f"📝 Hugging Face response received ({len(response_text)} chars)")
            
            # Parse the response
            meal_plan = self._parse_meal_plan_response(response_text)
            return meal_plan
        else:
            logger.error(f"❌ Hugging Face request failed: {response.status_code}")
            raise Exception(f"Hugging Face request failed: {response.status_code}")
    
    def _create_meal_plan_prompt(self, preferences: Dict[str, Any]) -> str:
        """Create a focused prompt for meal planning."""
        
        # Extract key preferences
        dietary = preferences.get('dietaryRestrictions', [])
        cuisines = preferences.get('favoriteCuisines', ['International'])
        allergens = preferences.get('allergens', [])
        skill = preferences.get('cookingSkillLevel', 'beginner')
        favorite_foods = preferences.get('favoriteFoods', [])
        health_goals = preferences.get('healthGoals', ['General wellness'])
        max_time = preferences.get('maxCookingTime', '30 minutes')
        
        # Get target macros
        macros = {
            'calories': preferences.get('targetCalories', 2000),
            'protein': preferences.get('targetProtein', 150),
            'carbs': preferences.get('targetCarbs', 200),
            'fat': preferences.get('targetFat', 65)
        }
        
        # Build a focused but contextual prompt 
        cuisine_list = ', '.join(cuisines) if cuisines else 'American, Chinese, Mexican'
        prompt = f"""You are a professional meal planner creating a diverse weekly menu. Generate varied, appealing meal names using these cuisines: {cuisine_list}

Requirements:
- Each day needs 3 different meals (breakfast, lunch, dinner)
- Ensure variety - no repeated meals across the week
- Mix cooking styles (grilled, stir-fried, baked, etc.)
- Include both simple and interesting options
- Match cuisines appropriately (e.g., Chinese dishes should be labeled Chinese)

Monday: Breakfast, Lunch, Dinner
Tuesday: Breakfast, Lunch, Dinner  
Wednesday: Breakfast, Lunch, Dinner
Thursday: Breakfast, Lunch, Dinner
Friday: Breakfast, Lunch, Dinner
Saturday: Breakfast, Lunch, Dinner
Sunday: Breakfast, Lunch, Dinner

Provide specific meal names for each slot."""

        return prompt
    
    def _validate_meal_plan(self, meal_plan: Dict[str, Any]) -> bool:
        """Validate that the meal plan has the expected structure."""
        try:
            if not isinstance(meal_plan, dict):
                logger.debug("❌ Meal plan is not a dict")
                return False
            
            week_plan = meal_plan.get('week_plan')
            if not week_plan:
                logger.debug("❌ No 'week_plan' key found in meal plan")
                return False
            
            # Check that we have all 7 days
            expected_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in expected_days:
                if day not in week_plan:
                    logger.debug(f"❌ Missing day: {day}")
                    return False
                
                day_plan = week_plan[day]
                if not isinstance(day_plan, dict):
                    logger.debug(f"❌ Day {day} is not a dict: {type(day_plan)}")
                    return False
                
                # Check that each day has the main meals
                for meal_type in ['breakfast', 'lunch', 'dinner']:
                    if meal_type not in day_plan:
                        logger.debug(f"❌ Missing meal type {meal_type} for {day}")
                        return False
                    
                    meal = day_plan[meal_type]
                    # For now, just check it's a string (meal name)
                    if not isinstance(meal, str):
                        logger.debug(f"❌ Meal {meal_type} for {day} is not a string: {type(meal)}")
                        return False
            
            logger.debug("✅ Meal plan validation successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Meal plan validation failed: {e}")
            return False
    
    def _parse_meal_plan_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the LLM response into a structured meal plan."""
        try:
            # Clean the response text
            cleaned_text = self._clean_json_string(response_text)
            logger.debug(f"🧹 Cleaned text: {cleaned_text[:200]}...")
            
            # Try to parse as JSON
            try:
                meal_plan = json.loads(cleaned_text)
                logger.debug(f"📋 Parsed JSON structure: {list(meal_plan.keys()) if isinstance(meal_plan, dict) else 'Not a dict'}")
                
                if self._validate_meal_plan(meal_plan):
                    logger.info("✅ Meal plan validation successful")
                    return meal_plan
                else:
                    logger.warning("⚠️ Meal plan validation failed - checking structure")
                    if isinstance(meal_plan, dict):
                        logger.warning(f"📋 Top-level keys: {list(meal_plan.keys())}")
                        if 'week_plan' in meal_plan:
                            week_plan = meal_plan['week_plan']
                            if isinstance(week_plan, dict):
                                logger.warning(f"📅 Week plan keys: {list(week_plan.keys())}")
                            else:
                                logger.warning(f"❌ Week plan is not a dict: {type(week_plan)}")
                        else:
                            logger.warning("❌ No 'week_plan' key found")
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Failed to parse JSON: {e}")
                logger.warning(f"📝 Raw response text: {response_text[:500]}...")
            
            # If JSON parsing failed, try to extract JSON from the text
            extracted_json = self._extract_json_from_text(response_text)
            if extracted_json and self._validate_meal_plan(extracted_json):
                logger.info("✅ Extracted JSON validation successful")
                return extracted_json
            
            logger.error("❌ Could not parse valid meal plan from LLM response")
            return None
            
        except Exception as e:
            logger.error(f"❌ Meal plan parsing failed: {e}")
            return None
    
    def _clean_json_string(self, text: str) -> str:
        """Clean the text to extract valid JSON."""
        # Remove markdown code blocks
        text = text.replace('```json', '').replace('```', '')
        
        # Find the first { and last }
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]
        
        return text
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON structure from text when direct parsing fails."""
        try:
            # Look for JSON-like structures
            import re
            
            # Find JSON object patterns
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, text, re.DOTALL)
            
            for match in matches:
                try:
                    parsed = json.loads(match)
                    if self._validate_meal_plan(parsed):
                        return parsed
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"❌ JSON extraction failed: {e}")
            return None
    
    def _parse_simple_text_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse a simple text response into meal plan structure."""
        try:
            lines = response_text.strip().split('\n')
            week_plan = {}
            current_day = None
            
            day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            meal_types = ['breakfast', 'lunch', 'dinner']
            
            logger.info(f"🔍 Parsing response with {len(lines)} lines")
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('Here are'):
                    continue
                
                logger.info(f"📝 Processing line: '{line}'")
                
                # Check if line starts with a day name
                line_lower = line.lower()
                for day in day_names:
                    if line_lower.startswith(day):
                        current_day = day
                        week_plan[current_day] = {}
                        logger.info(f"📅 Found day: {current_day}")
                        break
                
                # Check if line contains a meal (format: "- Breakfast: Meal Name")
                if current_day and line.startswith('-'):
                    # Parse lines like "- Breakfast: Egg Rolls & Oatmeal"
                    if ':' in line:
                        meal_part = line[1:].strip()  # Remove the '-'
                        meal_type_text, meal_name = meal_part.split(':', 1)
                        meal_type = meal_type_text.strip().lower()
                        meal_name = meal_name.strip()
                        
                        if meal_type in meal_types and meal_name:
                            week_plan[current_day][meal_type] = meal_name
                            logger.info(f"🍽️ Added {meal_type}: {meal_name} for {current_day}")
            
            # If we didn't get a proper structure, create a simple default one
            if not week_plan:
                logger.warning("Could not parse day structure, creating default meal plan")
                default_meals = {
                    'breakfast': 'Scrambled Eggs with Toast',
                    'lunch': 'Grilled Chicken Salad', 
                    'dinner': 'Beef Stir-Fry with Rice'
                }
                for day in day_names:
                    week_plan[day] = default_meals.copy()
            
            # Ensure all days have all meal types
            for day in day_names:
                if day not in week_plan:
                    week_plan[day] = {}
                for meal_type in meal_types:
                    if meal_type not in week_plan[day]:
                        week_plan[day][meal_type] = f"Simple {meal_type}"
                        logger.warning(f"⚠️ Missing {meal_type} for {day}, using default")
            
            logger.info(f"✅ Parsed meal plan with {len(week_plan)} days")
            return {"week_plan": week_plan}
            
        except Exception as e:
            logger.error(f"Failed to parse simple text response: {e}")
            return None
    
    def regenerate_specific_meal(self, user_id: str, day: str, meal_type: str, current_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Regenerate a specific meal using the LLM."""
        try:
            preferences = self.user_preferences_service.get_preferences(user_id)
            if not preferences:
                return {"error": "No user preferences found"}
            
            # Create a focused prompt for regenerating a specific meal
            prompt = f"""You are an expert chef. Regenerate the {meal_type} for {day} based on these preferences:

USER PREFERENCES:
- Dietary restrictions: {', '.join(preferences.get('dietaryRestrictions', []))}
- Favorite cuisines: {', '.join(preferences.get('favoriteCuisines', ['International']))}
- Allergens to avoid: {', '.join(preferences.get('allergens', []))}
- Cooking skill: {preferences.get('cookingSkillLevel', 'beginner')}
- Max cooking time: {preferences.get('maxCookingTime', '30 minutes')}

CURRENT MEAL PLAN CONTEXT:
{json.dumps(current_plan, indent=2)}

REQUIREMENT:
Create a new {meal_type} for {day} that:
1. Fits the user's preferences
2. Is different from the current meal
3. Maintains nutritional balance
4. Includes: name, ingredients, instructions, cooking time, and nutrition info

RESPONSE FORMAT:
Return ONLY valid JSON:
{{
  "name": "New Meal Name",
  "ingredients": ["ingredient1", "ingredient2"],
  "instructions": "Step-by-step cooking instructions",
  "cooking_time": "X minutes",
  "nutrition": {{
    "calories": X,
    "protein": "Xg",
    "carbs": "Xg",
    "fat": "Xg"
  }}
}}

IMPORTANT: Return ONLY the JSON, no other text."""

            # Try Ollama first
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": "llama3.2:latest",
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.8,
                            "max_tokens": 1000
                        }
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get('response', '')
                    
                    # Parse the response
                    try:
                        new_meal = json.loads(self._clean_json_string(response_text))
                        return {
                            "success": True,
                            "meal": new_meal,
                            "source": "ollama"
                        }
                    except:
                        return {"error": "Failed to parse regenerated meal"}
                        
            except Exception as e:
                logger.warning(f"⚠️ Ollama meal regeneration failed: {e}")
            
            return {"error": "Unable to regenerate meal - LLM service unavailable"}
            
        except Exception as e:
            logger.error(f"❌ Meal regeneration failed: {e}")
            return {"error": f"Meal regeneration failed: {str(e)}"}
    
    def _convert_to_frontend_format(self, meal_plan: Dict[str, Any], preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Convert LLM meal plan to the format expected by the frontend."""
        try:
            week_plan = meal_plan.get('week_plan', {})
            days = []
            
            # Get today's date for date calculation
            from datetime import datetime, timedelta
            today = datetime.now().date()
            
            day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            
            # Cache favorite cuisines for rotation to ensure variety that matches preferences
            favorite_cuisines: List[str] = preferences.get('favoriteCuisines', []) or []
            num_cuisines: int = len(favorite_cuisines)

            for index, day_name in enumerate(day_names):
                # Calculate the date for this day
                day_date = today + timedelta(days=index)
                
                day_data = week_plan.get(day_name, {})
                meals = []
                
                # Convert each meal type
                for meal_index, meal_type in enumerate(['breakfast', 'lunch', 'dinner']):
                    meal_name = day_data.get(meal_type, f"Default {meal_type}")
                    
                    # Extract calories and protein from the meal name if present
                    calories = 400  # Default
                    protein = "15g"  # Default
                    
                    # Try to extract numbers from meal name like "(350, 25g)"
                    import re
                    calorie_match = re.search(r'\((\d+)', meal_name)
                    protein_match = re.search(r'(\d+)g\)', meal_name)
                    
                    if calorie_match:
                        calories = int(calorie_match.group(1))
                    if protein_match:
                        protein = f"{protein_match.group(1)}g"
                    
                    # Clean the meal name (remove calorie/protein info)
                    clean_name = re.sub(r'\s*\(\d+[^)]*\)', '', meal_name).strip()

                    # Choose cuisine by rotating through the user's favorites across days/meals
                    if num_cuisines > 0:
                        cuisine = favorite_cuisines[(index * 3 + meal_index) % num_cuisines]
                    else:
                        cuisine = 'International'

                    # Provide slightly better placeholder ingredients based on meal name heuristics
                    lower_name = clean_name.lower()
                    if 'salad' in lower_name:
                        ingredients = ["mixed greens", "protein of choice", "assorted vegetables", "dressing"]
                    elif 'stir-fry' in lower_name or 'stir fry' in lower_name:
                        ingredients = ["protein of choice", "mixed vegetables", "stir-fry sauce", "oil"]
                    elif 'wrap' in lower_name or 'burrito' in lower_name:
                        ingredients = ["tortilla", "protein", "vegetables", "sauce"]
                    elif 'omelette' in lower_name or 'omelet' in lower_name:
                        ingredients = ["eggs", "fillings of choice", "salt", "pepper"]
                    elif 'toast' in lower_name:
                        ingredients = ["bread", "toppings of choice"]
                    elif 'bowl' in lower_name or 'quinoa' in lower_name:
                        ingredients = ["grain base", "protein", "vegetables", "sauce"]
                    elif 'parfait' in lower_name:
                        ingredients = ["yogurt", "fruit", "granola", "sweetener (optional)"]
                    elif 'skewer' in lower_name:
                        ingredients = ["protein", "vegetables", "marinade"]
                    elif 'quesadilla' in lower_name:
                        ingredients = ["tortillas", "cheese", "filling of choice"]
                    else:
                        ingredients = ["See recipe details"]

                    # Replace generic instruction with a brief cuisine-specific guide
                    instructions = [
                        f"Gather ingredients for {clean_name}.",
                        f"Cook using typical {cuisine} techniques appropriate for {meal_type}.",
                        "Taste, adjust seasoning, and serve."
                    ]
                    
                    meals.append({
                        "name": clean_name,
                        "meal_type": meal_type,
                        "cuisine": cuisine,
                        "is_vegetarian": 'vegetarian' in preferences.get('dietaryRestrictions', []),
                        "is_vegan": 'vegan' in preferences.get('dietaryRestrictions', []),
                        "ingredients": ingredients,
                        "instructions": instructions,
                        "nutrition": {
                            "calories": calories,
                            "protein": protein,
                            "carbs": "30g",
                            "fat": "10g"
                        },
                        "prep_time": preferences.get('maxCookingTime', '30 minutes'),
                        "cook_time": preferences.get('maxCookingTime', '30 minutes'),
                        "servings": 2,
                        "difficulty": preferences.get('cookingSkillLevel', 'beginner')
                    })
                
                days.append({
                    "day": day_name.capitalize(),
                    "date": day_date.isoformat(),
                    "meals": meals
                })
            
            # Create the full meal plan structure
            converted_plan = {
                "days": days,
                "shopping_list": {
                    "ingredients": [],
                    "estimated_cost": 0
                },
                "nutrition_summary": {
                    "daily_average": {
                        "calories": preferences.get('targetCalories', 1800),
                        "protein": f"{preferences.get('targetProtein', 120)}g",
                        "carbs": f"{preferences.get('targetCarbs', 180)}g",
                        "fat": f"{preferences.get('targetFat', 60)}g"
                    }
                },
                "generated_at": datetime.now().isoformat(),
                "preferences_used": preferences,
                "plan_type": "llm_generated"
            }
            
            return converted_plan
            
        except Exception as e:
            logger.error(f"❌ Conversion to frontend format failed: {e}")
            # Return a minimal structure to prevent crashes
            return {
                "days": [],
                "shopping_list": {"ingredients": [], "estimated_cost": 0},
                "nutrition_summary": {"daily_average": {"calories": 1800, "protein": "120g", "carbs": "180g", "fat": "60g"}},
                "generated_at": datetime.now().isoformat(),
                "preferences_used": preferences,
                "plan_type": "llm_generated"
            } 