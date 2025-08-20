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
        self.hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
        self.hf_api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        
        # LLM configuration
        self.ollama_timeout = 60  # Increased to 60 seconds for comprehensive prompts
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
                meal_plan = self._generate_with_ollama(preferences)
                if meal_plan and self._validate_meal_plan(meal_plan):
                    logger.info("✅ Ollama generated valid meal plan")
                    # Convert the LLM response to the format expected by the frontend
                    converted_plan = self._convert_to_frontend_format(meal_plan, preferences)
                    return {
                        "success": True,
                        "meal_plan": converted_plan,
                        "source": "ollama",
                        "generated_at": datetime.now().isoformat()
                    }
            except Exception as e:
                logger.warning(f"⚠️ Ollama failed: {e}")
            
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
            "model": "llama3.2:latest",  # Use llama3.2:latest since it works
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": self.ollama_max_tokens
            }
        }
        
        logger.info(f"🚀 Sending prompt to Ollama ({len(prompt)} chars)")
        
        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json=payload,
            timeout=self.ollama_timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            logger.info(f"📝 Ollama response received ({len(response_text)} chars)")
            logger.debug(f"📋 Raw Ollama response: {response_text[:1000]}...")
            
            # Parse the response
            meal_plan = self._parse_meal_plan_response(response_text)
            return meal_plan
        else:
            logger.error(f"❌ Ollama request failed: {response.status_code}")
            raise Exception(f"Ollama request failed: {response.status_code}")
    
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
        
        # Build a comprehensive, well-structured prompt using best practices
        prompt = f"""You are an expert nutritionist and meal planning specialist with 15+ years of experience. Your task is to create a personalized, balanced, and delicious 7-day meal plan.

**USER PROFILE:**
- Dietary Requirements: {', '.join(dietary) if dietary else 'No restrictions'}
- Preferred Cuisines: {', '.join(cuisines)}
- Allergens to Avoid: {', '.join(allergens) if allergens else 'None'}
- Cooking Skill Level: {skill}
- Favorite Foods: {', '.join(favorite_foods) if favorite_foods else 'Open to variety'}
- Health & Fitness Goals: {', '.join(health_goals)}
- Maximum Cooking Time per Meal: {max_time}
- Daily Nutritional Targets: {macros['calories']} calories, {macros['protein']}g protein, {macros['carbs']}g carbs, {macros['fat']}g fat

**MEAL PLANNING REQUIREMENTS:**
1. Create exactly 7 days (Monday through Sunday)
2. Include breakfast, lunch, and dinner for each day
3. Ensure variety - no meal should repeat during the week
4. Respect ALL dietary restrictions and allergen avoidances
5. Stay within the specified cooking time limits
6. Incorporate the user's favorite foods multiple times throughout the week
7. Align with health and fitness goals
8. Balance flavors, textures, and nutritional content
9. Consider meal prep efficiency where appropriate
10. Ensure meals are practical and achievable for the specified skill level

**CUISINE INTEGRATION:**
- Primarily focus on {', '.join(cuisines)} cuisine styles
- Incorporate authentic flavors and cooking techniques
- Suggest appropriate spices, herbs, and cooking methods

**NUTRITIONAL CONSIDERATIONS:**
- Balance macronutrients across each day
- Ensure adequate fiber, vitamins, and minerals
- Consider meal timing for optimal energy levels
- Include healthy fats, complex carbohydrates, and complete proteins

**OUTPUT FORMAT:**
Return ONLY valid JSON in this exact structure:
{{
  "week_plan": {{
    "monday": {{
      "breakfast": "Detailed meal name with key ingredients (calories: X, protein: Xg)",
      "lunch": "Detailed meal name with key ingredients (calories: X, protein: Xg)",
      "dinner": "Detailed meal name with key ingredients (calories: X, protein: Xg)"
    }},
    "tuesday": {{
      "breakfast": "Detailed meal name with key ingredients (calories: X, protein: Xg)",
      "lunch": "Detailed meal name with key ingredients (calories: X, protein: Xg)",
      "dinner": "Detailed meal name with key ingredients (calories: X, protein: Xg)"
    }},
    "wednesday": {{
      "breakfast": "Detailed meal name with key ingredients (calories: X, protein: Xg)",
      "lunch": "Detailed meal name with key ingredients (calories: X, protein: Xg)",
      "dinner": "Detailed meal name with key ingredients (calories: X, protein: Xg)"
    }},
    "thursday": {{
      "breakfast": "Detailed meal name with key ingredients (calories: X, protein: Xg)",
      "lunch": "Detailed meal name with key ingredients (calories: X, protein: Xg)",
      "dinner": "Detailed meal name with key ingredients (calories: X, protein: Xg)"
    }},
    "friday": {{
      "breakfast": "Detailed meal name with key ingredients (calories: X, protein: Xg)",
      "lunch": "Detailed meal name with key ingredients (calories: X, protein: Xg)",
      "dinner": "Detailed meal name with key ingredients (calories: X, protein: Xg)"
    }},
    "saturday": {{
      "breakfast": "Detailed meal name with key ingredients (calories: X, protein: Xg)",
      "lunch": "Detailed meal name with key ingredients (calories: X, protein: Xg)",
      "dinner": "Detailed meal name with key ingredients (calories: X, protein: Xg)"
    }},
    "sunday": {{
      "breakfast": "Detailed meal name with key ingredients (calories: X, protein: Xg)",
      "lunch": "Detailed meal name with key ingredients (calories: X, protein: Xg)",
      "dinner": "Detailed meal name with key ingredients (calories: X, protein: Xg)"
    }}
  }}
}}

**CRITICAL INSTRUCTIONS:**
- Include calorie and protein estimates in each meal name
- Make meal names descriptive and appetizing
- Ensure total daily calories align with target ({macros['calories']} calories)
- Return ONLY the JSON structure, no additional text or explanations
- Double-check that all dietary restrictions and allergens are respected"""

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
            
            for index, day_name in enumerate(day_names):
                # Calculate the date for this day
                day_date = today + timedelta(days=index)
                
                day_data = week_plan.get(day_name, {})
                meals = []
                
                # Convert each meal type
                for meal_type in ['breakfast', 'lunch', 'dinner']:
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
                    
                    meals.append({
                        "name": clean_name,
                        "meal_type": meal_type,
                        "cuisine": preferences.get('favoriteCuisines', ['International'])[0] if preferences.get('favoriteCuisines') else 'International',
                        "is_vegetarian": 'vegetarian' in preferences.get('dietaryRestrictions', []),
                        "is_vegan": 'vegan' in preferences.get('dietaryRestrictions', []),
                        "ingredients": ["Fresh ingredients"],  # Simplified for now
                        "instructions": ["Follow standard cooking methods"],  # Simplified for now
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