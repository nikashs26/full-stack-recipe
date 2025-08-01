import os
import json
import requests
import re
from typing import Dict, List, Any, Optional
from services.user_preferences_service import UserPreferencesService
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class FreeLLMMealPlannerAgent:
    """
    AI Meal Planning Agent using free LLM options:
    1. Ollama (local models) - Primary choice
    2. Hugging Face Inference API (free tier) - Fallback
    """
    
    def __init__(self, user_preferences_service: UserPreferencesService):
        self.user_preferences_service = user_preferences_service
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.hf_api_key = os.getenv('HUGGING_FACE_API_KEY', '')  # Optional, for higher rate limits
        
    def generate_weekly_meal_plan(self, user_id: str) -> Dict[str, Any]:
        """Generate a weekly meal plan using free LLM options"""
        try:
            print(f"🎯 Generating meal plan for user: {user_id}")
            
            # Get user preferences
            preferences = self.user_preferences_service.get_preferences(user_id)
            if not preferences:
                return {"error": "User preferences not found. Please set your preferences first."}
            
            print(f"📋 User preferences loaded: {list(preferences.keys())}")
            
            # Try Ollama first (local, completely free)
            try:
                print("🤖 Trying Ollama (local LLM)...")
                meal_plan = self._generate_with_ollama(preferences)
                if meal_plan:
                    print("✅ Successfully generated meal plan with Ollama!")
                    return {
                        "success": True,
                        "plan": meal_plan,
                        "preferences_used": preferences,
                        "llm_used": "Ollama (Local)"
                    }
            except Exception as e:
                print(f"❌ Ollama failed: {e}")
            
            # Fallback to Hugging Face
            try:
                print("🌐 Trying Hugging Face...")
                meal_plan = self._generate_with_huggingface(preferences)
                if meal_plan:
                    print("✅ Successfully generated meal plan with Hugging Face!")
                    return {
                        "success": True,
                        "plan": meal_plan,
                        "preferences_used": preferences,
                        "llm_used": "Hugging Face"
                    }
            except Exception as e:
                print(f"❌ Hugging Face failed: {e}")
            
            # If both fail, use rule-based fallback
            print("📋 Using rule-based fallback...")
            meal_plan = self._generate_rule_based_plan(preferences)
            return {
                "success": True,
                "plan": meal_plan,
                "preferences_used": preferences,
                "llm_used": "Rule-based (Fallback)"
            }
            
        except Exception as e:
            print(f"💥 Unexpected error in meal plan generation: {e}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    def _generate_with_ollama(self, preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate meal plan using Ollama (local LLM)"""
        
        print("🤖 Attempting to generate meal plan with Ollama...")
        
        # Check if Ollama is available
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise Exception("Ollama not available")
            print("✅ Ollama server is running")
        except Exception as e:
            print(f"❌ Ollama server not running: {e}")
            raise Exception("Ollama server not running")
        
        prompt = self._create_meal_plan_prompt(preferences)
        print(f"📝 Generated prompt length: {len(prompt)} characters")
        
        payload = {
            "model": "llama3.2:latest",  # Use the available model
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2000
            }
        }
        
        print(f"🚀 Sending request to Ollama with model: {payload['model']}")
        
        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json=payload,
            timeout=120  # Increased timeout for LLM generation
        )
        
        if response.status_code == 200:
            result = response.json()
            meal_plan_text = result.get('response', '')
            print(f"📄 Received response from Ollama ({len(meal_plan_text)} characters)")
            print(f"📝 Response preview: {meal_plan_text[:200]}...")
            
            parsed_plan = self._parse_meal_plan_response(meal_plan_text)
            if parsed_plan:
                print("✅ Successfully parsed meal plan from Ollama response")
                return parsed_plan
            else:
                print("❌ Failed to parse meal plan from Ollama response")
                return None
        else:
            print(f"❌ Ollama request failed with status {response.status_code}")
            print(f"Error response: {response.text}")
            return None
    
    def _generate_with_huggingface(self, preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate meal plan using Hugging Face Inference API"""
        
        # Use a free model like Microsoft DialoGPT or similar
        model_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
        
        headers = {
            "Authorization": f"Bearer {self.hf_api_key}" if self.hf_api_key else "",
            "Content-Type": "application/json"
        }
        
        prompt = self._create_simplified_prompt(preferences)
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1000,
                "temperature": 0.7,
                "return_full_text": False
            }
        }
        
        response = requests.post(model_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                meal_plan_text = result[0].get('generated_text', '')
                return self._parse_meal_plan_response(meal_plan_text)
        
        return None
    
    def _generate_rule_based_plan(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a rule-based meal plan using user preferences"""
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        meal_plan = {"days": {}}
        
        # Get user preferences
        dietary_restrictions = preferences.get('dietaryRestrictions', [])
        favorite_cuisines = preferences.get('favoriteCuisines', ['International'])
        favorite_foods = preferences.get('favoriteFoods', [])
        cooking_skill = preferences.get('cookingSkillLevel', 'beginner')
        include_breakfast = preferences.get('includeBreakfast', True)
        include_lunch = preferences.get('includeLunch', True)
        include_dinner = preferences.get('includeDinner', True)
        include_snacks = preferences.get('includeSnacks', False)
        
        # Get meal templates based on preferences
        meal_templates = self._get_meal_templates(dietary_restrictions, favorite_cuisines, cooking_skill)
        
        for day in days:
            day_plan = {}
            
            if include_breakfast:
                breakfast = self._select_meal_template(meal_templates, 'breakfast', dietary_restrictions)
                day_plan['breakfast'] = breakfast
            
            if include_lunch:
                lunch = self._select_meal_template(meal_templates, 'lunch', dietary_restrictions)
                day_plan['lunch'] = lunch
            
            if include_dinner:
                dinner = self._select_meal_template(meal_templates, 'dinner', dietary_restrictions)
                day_plan['dinner'] = dinner
            
            if include_snacks:
                snack = self._select_meal_template(meal_templates, 'snack', dietary_restrictions)
                day_plan['snack'] = snack
            
            meal_plan["days"][day] = day_plan
        
        # Add metadata
        meal_plan["metadata"] = {
            "generated_at": datetime.utcnow().isoformat(),
            "preferences_used": preferences,
            "method": "rule_based",
            "total_meals": len(days) * (include_breakfast + include_lunch + include_dinner + include_snacks)
        }
        
        return meal_plan
    
    def _create_meal_plan_prompt(self, preferences: Dict[str, Any]) -> str:
        """Create a detailed prompt for LLM meal planning"""
        
        dietary_restrictions = preferences.get("dietaryRestrictions", [])
        favorite_cuisines = preferences.get("favoriteCuisines", [])
        favorite_foods = preferences.get("favoriteFoods", [])
        allergens = preferences.get("allergens", [])
        cooking_skill = preferences.get("cookingSkillLevel", "beginner")
        max_cooking_time = preferences.get("maxCookingTime", "30 minutes")
        
        prompt = f"""You are a professional nutritionist and meal planning expert. Create a weekly meal plan with exactly 3 meals per day for 7 days.

USER PREFERENCES:
- Dietary Restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
- Favorite Cuisines: {', '.join(favorite_cuisines) if favorite_cuisines else 'Any'}
- Favorite Foods: {', '.join(favorite_foods) if favorite_foods else 'Any'}
- Allergens to Avoid: {', '.join(allergens) if allergens else 'None'}
- Cooking Skill Level: {cooking_skill}
- Max Cooking Time: {max_cooking_time}

REQUIREMENTS:
1. Provide exactly 21 meals (3 per day for 7 days)
2. Ensure nutritional balance and variety
3. Respect all dietary restrictions and allergens
4. Match cooking complexity to skill level
5. Include diverse cuisines and cooking methods
6. Incorporate favorite foods when possible
7. Keep cooking time within the specified limit

FORMAT your response as a JSON object with this exact structure:
{{
  "monday": {{
    "breakfast": {{
      "name": "Meal Name",
      "cuisine": "Cuisine Type",
      "ingredients": ["ingredient1", "ingredient2"],
      "instructions": ["step1", "step2"],
      "cooking_time": "30 minutes",
      "difficulty": "beginner"
    }},
    "lunch": {{ ... }},
    "dinner": {{ ... }}
  }},
  "tuesday": {{ ... }},
  "wednesday": {{ ... }},
  "thursday": {{ ... }},
  "friday": {{ ... }},
  "saturday": {{ ... }},
  "sunday": {{ ... }}
}}

Start with Monday and continue through Sunday. Each day should have breakfast, lunch, and dinner.
"""
        
        return prompt
    
    def _create_simplified_prompt(self, preferences: Dict[str, Any]) -> str:
        """Create a simplified prompt for less capable models"""
        
        dietary_restrictions = preferences.get("dietaryRestrictions", [])
        favorite_cuisines = preferences.get("favoriteCuisines", [])
        
        prompt = f"""Create a 7-day meal plan with breakfast, lunch, and dinner.

Preferences:
- Diet: {', '.join(dietary_restrictions) if dietary_restrictions else 'Regular'}
- Cuisines: {', '.join(favorite_cuisines) if favorite_cuisines else 'Any'}

List 21 meals with names and ingredients."""
        
        return prompt
    
    def _parse_meal_plan_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response into structured meal plan"""
        
        print(f"🔍 Parsing LLM response...")
        print(f"📄 Response text length: {len(response_text)}")
        
        try:
            # Try to extract JSON if present
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                print(f"📋 Found JSON match: {json_str[:200]}...")
                parsed_json = json.loads(json_str)
                print(f"✅ Successfully parsed JSON with keys: {list(parsed_json.keys())}")
                return parsed_json
            
            # If no JSON, try to parse as text format
            print("📝 No JSON found, trying text parsing...")
            parsed_text = self._parse_text_meal_plan(response_text)
            if parsed_text:
                print(f"✅ Successfully parsed text format")
                return parsed_text
            
            print("❌ Failed to parse response in any format")
            return None
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            # Try text parsing as fallback
            try:
                parsed_text = self._parse_text_meal_plan(response_text)
                if parsed_text:
                    print(f"✅ Fallback text parsing succeeded")
                    return parsed_text
            except Exception as e2:
                print(f"❌ Text parsing also failed: {e2}")
            return None
        except Exception as e:
            print(f"❌ General parsing error: {e}")
            return None
    
    def _parse_text_meal_plan(self, text: str) -> Dict[str, Any]:
        """Parse text-based meal plan into structured format"""
        
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        meal_types = ["breakfast", "lunch", "dinner"]
        
        plan = {}
        lines = text.split('\n')
        
        current_day = None
        current_meal_type = None
        meal_counter = 1
        
        for line in lines:
            line = line.strip().lower()
            
            # Check for day
            for day in days:
                if day in line:
                    current_day = day
                    plan[day] = {}
                    break
            
            # Check for meal type
            for meal_type in meal_types:
                if meal_type in line and current_day:
                    current_meal_type = meal_type
                    
                    # Extract meal name (simple heuristic)
                    meal_name = line.replace(meal_type, '').strip(' :-')
                    if not meal_name:
                        meal_name = f"Healthy {meal_type.title()}"
                    
                    plan[current_day][current_meal_type] = {
                        "id": f"parsed_{meal_counter}",
                        "name": meal_name.title(),
                        "description": f"Nutritious {meal_type} meal",
                        "cuisine": "International",
                        "cookingTime": "20-30 minutes",
                        "difficulty": "beginner",
                        "ingredients": ["Fresh ingredients", "Seasonings", "Cooking oil"],
                        "instructions": f"Prepare this healthy {meal_type} according to your preferences"
                    }
                    meal_counter += 1
                    break
        
        # Fill in any missing meals
        for day in days:
            if day not in plan:
                plan[day] = {}
            for meal_type in meal_types:
                if meal_type not in plan[day]:
                    plan[day][meal_type] = {
                        "id": f"default_{meal_counter}",
                        "name": f"Healthy {meal_type.title()}",
                        "description": f"Nutritious {meal_type} meal",
                        "cuisine": "International",
                        "cookingTime": "20-30 minutes",
                        "difficulty": "beginner",
                        "ingredients": ["Fresh ingredients", "Seasonings"],
                        "instructions": f"Prepare a healthy {meal_type}"
                    }
                    meal_counter += 1
        
        return plan
    
    def _get_meal_templates(self, dietary_restrictions: List[str], favorite_cuisines: List[str], cooking_skill: str) -> Dict[str, List[Dict]]:
        """Get meal templates based on preferences"""
        
        templates = {
            "breakfast": [
                {
                    "name": "Avocado Toast",
                    "description": "Creamy avocado on whole grain toast",
                    "cuisine": "American",
                    "cookingTime": "10 minutes",
                    "ingredients": ["Whole grain bread", "Avocado", "Lemon juice", "Salt", "Pepper"],
                    "instructions": "Toast bread, mash avocado with lemon juice, season and spread on toast"
                },
                {
                    "name": "Greek Yogurt Bowl",
                    "description": "Protein-rich yogurt with fruits and nuts",
                    "cuisine": "Mediterranean",
                    "cookingTime": "5 minutes",
                    "ingredients": ["Greek yogurt", "Mixed berries", "Granola", "Honey", "Nuts"],
                    "instructions": "Layer yogurt with berries, granola, and nuts. Drizzle with honey"
                },
                {
                    "name": "Vegetable Omelet",
                    "description": "Fluffy eggs with fresh vegetables",
                    "cuisine": "French",
                    "cookingTime": "15 minutes",
                    "ingredients": ["Eggs", "Bell peppers", "Onions", "Cheese", "Herbs"],
                    "instructions": "Beat eggs, sauté vegetables, pour eggs over vegetables, fold omelet"
                }
            ],
            "lunch": [
                {
                    "name": "Quinoa Buddha Bowl",
                    "description": "Nutritious bowl with quinoa and vegetables",
                    "cuisine": "International",
                    "cookingTime": "25 minutes",
                    "ingredients": ["Quinoa", "Roasted vegetables", "Chickpeas", "Tahini", "Greens"],
                    "instructions": "Cook quinoa, roast vegetables, assemble bowl with tahini dressing"
                },
                {
                    "name": "Mediterranean Wrap",
                    "description": "Fresh wrap with Mediterranean flavors",
                    "cuisine": "Mediterranean",
                    "cookingTime": "15 minutes",
                    "ingredients": ["Whole wheat tortilla", "Hummus", "Cucumber", "Tomatoes", "Feta"],
                    "instructions": "Spread hummus on tortilla, add vegetables and cheese, roll tightly"
                },
                {
                    "name": "Asian Stir-Fry",
                    "description": "Quick vegetable stir-fry with protein",
                    "cuisine": "Asian",
                    "cookingTime": "20 minutes",
                    "ingredients": ["Mixed vegetables", "Tofu or chicken", "Soy sauce", "Ginger", "Rice"],
                    "instructions": "Stir-fry vegetables and protein, season with soy sauce and ginger, serve over rice"
                }
            ],
            "dinner": [
                {
                    "name": "Grilled Salmon",
                    "description": "Healthy grilled salmon with vegetables",
                    "cuisine": "American",
                    "cookingTime": "25 minutes",
                    "ingredients": ["Salmon fillet", "Asparagus", "Lemon", "Olive oil", "Herbs"],
                    "instructions": "Season salmon, grill with vegetables, finish with lemon and herbs"
                },
                {
                    "name": "Pasta Primavera",
                    "description": "Light pasta with seasonal vegetables",
                    "cuisine": "Italian",
                    "cookingTime": "30 minutes",
                    "ingredients": ["Whole wheat pasta", "Seasonal vegetables", "Olive oil", "Garlic", "Parmesan"],
                    "instructions": "Cook pasta, sauté vegetables with garlic, toss with pasta and cheese"
                },
                {
                    "name": "Lentil Curry",
                    "description": "Hearty and flavorful lentil curry",
                    "cuisine": "Indian",
                    "cookingTime": "35 minutes",
                    "ingredients": ["Red lentils", "Coconut milk", "Curry spices", "Onions", "Rice"],
                    "instructions": "Cook lentils with spices and coconut milk, serve over rice"
                }
            ]
        }
        
        # Filter templates based on dietary restrictions
        if "vegetarian" in dietary_restrictions or "vegan" in dietary_restrictions:
            # Remove non-vegetarian options
            for meal_type in templates:
                templates[meal_type] = [
                    meal for meal in templates[meal_type] 
                    if not any(ingredient.lower() in ["salmon", "chicken", "fish", "meat"] 
                              for ingredient in meal["ingredients"])
                ]
        
        return templates
    
    def _select_meal_template(self, templates: Dict[str, List[Dict]], meal_type: str, dietary_restrictions: List[str]) -> Dict[str, Any]:
        """Select an appropriate meal template based on preferences"""
        import random
        
        available_templates = templates.get(meal_type, [])
        if not available_templates:
            # Fallback template
            return {
                "id": f"fallback_{meal_type}",
                "name": f"Simple {meal_type.title()}",
                "description": f"A simple and nutritious {meal_type}",
                "cuisine": "International",
                "cookingTime": "20 minutes",
                "difficulty": "beginner",
                "ingredients": ["Basic ingredients"],
                "instructions": ["Follow basic cooking instructions"],
                "nutrition": {
                    "calories": 400,
                    "protein_g": 15,
                    "carbs_g": 50,
                    "fat_g": 15
                }
            }
        
        # Filter by dietary restrictions
        suitable_templates = []
        for template in available_templates:
            template_dietary = template.get('dietaryRestrictions', [])
            if not dietary_restrictions or all(restriction in template_dietary for restriction in dietary_restrictions):
                suitable_templates.append(template)
        
        if not suitable_templates:
            suitable_templates = available_templates  # Use any template if none match dietary restrictions
        
        # Select a random template
        selected = random.choice(suitable_templates)
        
        # Add meal type to the template
        selected['meal_type'] = meal_type
        
        return selected
    
    def regenerate_specific_meal(self, user_id: str, day: str, meal_type: str, current_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Regenerate a specific meal in the plan"""
        
        try:
            preferences = self.user_preferences_service.get_preferences(user_id)
            if not preferences:
                return {"error": "User preferences not found"}
            
            # Get meal templates and select a different one
            dietary_restrictions = preferences.get("dietaryRestrictions", [])
            favorite_cuisines = preferences.get("favoriteCuisines", [])
            cooking_skill = preferences.get("cookingSkillLevel", "beginner")
            
            templates = self._get_meal_templates(dietary_restrictions, favorite_cuisines, cooking_skill)
            new_meal = self._select_meal_template(templates, meal_type, dietary_restrictions)
            
            # Ensure it's different from current meal
            current_meal_name = current_plan.get(day, {}).get(meal_type, {}).get("name", "")
            attempts = 0
            while new_meal["name"] == current_meal_name and attempts < 5:
                new_meal = self._select_meal_template(templates, meal_type, dietary_restrictions)
                attempts += 1
            
            # Add unique ID
            import time
            new_meal["id"] = f"regenerated_{int(time.time())}"
            new_meal["difficulty"] = cooking_skill
            
            return {
                "success": True,
                "meal": new_meal
            }
            
        except Exception as e:
            return {"error": f"Failed to regenerate meal: {str(e)}"} 

    def get_recipe_suggestions(self, meal_type: str, preferences: Dict[str, Any], count: int = 5) -> List[Dict[str, Any]]:
        """Get recipe suggestions for a specific meal type"""
        try:
            # Get meal templates based on preferences
            dietary_restrictions = preferences.get('dietaryRestrictions', [])
            favorite_cuisines = preferences.get('favoriteCuisines', ['International'])
            cooking_skill = preferences.get('cookingSkillLevel', 'beginner')
            
            meal_templates = self._get_meal_templates(dietary_restrictions, favorite_cuisines, cooking_skill)
            
            # Get templates for the specific meal type
            available_templates = meal_templates.get(meal_type, [])
            
            # Filter by dietary restrictions
            suitable_templates = []
            for template in available_templates:
                template_dietary = template.get('dietaryRestrictions', [])
                if not dietary_restrictions or all(restriction in template_dietary for restriction in dietary_restrictions):
                    suitable_templates.append(template)
            
            if not suitable_templates:
                suitable_templates = available_templates
            
            # Return up to the requested count
            return suitable_templates[:count]
            
        except Exception as e:
            print(f"Error getting recipe suggestions: {e}")
            return [] 