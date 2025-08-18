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
                if meal_plan and self._validate_meal_plan(meal_plan):
                    print("✅ Successfully generated meal plan with Ollama!")
                    return {
                        "success": True,
                        "plan": meal_plan,
                        "preferences_used": preferences,
                        "llm_used": "Ollama (Local)"
                    }
                else:
                    print("❌ Ollama generated invalid meal plan, trying Hugging Face...")
            except Exception as e:
                print(f"❌ Ollama failed: {e}")
            
            # Fallback to Hugging Face
            try:
                print("🌐 Trying Hugging Face...")
                meal_plan = self._generate_with_huggingface(preferences)
                if meal_plan and self._validate_meal_plan(meal_plan):
                    print("✅ Successfully generated meal plan with Hugging Face!")
                    return {
                        "success": True,
                        "plan": meal_plan,
                        "preferences_used": preferences,
                        "llm_used": "Hugging Face"
                    }
                else:
                    print("❌ Hugging Face generated invalid meal plan")
            except Exception as e:
                print(f"❌ Hugging Face failed: {e}")
            
            # If both LLMs fail, try one more time with Ollama using a different model
            try:
                print("🔄 Retrying Ollama with different model...")
                meal_plan = self._generate_with_ollama_fallback(preferences)
                if meal_plan and self._validate_meal_plan(meal_plan):
                    print("✅ Successfully generated meal plan with Ollama fallback!")
                    return {
                        "success": True,
                        "plan": meal_plan,
                        "preferences_used": preferences,
                        "llm_used": "Ollama (Fallback Model)"
                    }
            except Exception as e:
                print(f"❌ Ollama fallback also failed: {e}")
            
            # Only use rule-based fallback as absolute last resort
            print("⚠️ All LLM attempts failed, using rule-based fallback...")
            meal_plan = self._generate_rule_based_plan(preferences)
            return {
                "success": True,
                "plan": meal_plan,
                "preferences_used": preferences,
                "llm_used": "Rule-based (Fallback - LLM Unavailable)",
                "warning": "AI meal planning was unavailable. This is a basic meal plan based on your preferences."
            }
            
        except Exception as e:
            print(f"💥 Unexpected error in meal plan generation: {e}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    def _validate_meal_plan(self, meal_plan: Dict[str, Any]) -> bool:
        """Validate that the generated meal plan has the expected structure"""
        try:
            if not isinstance(meal_plan, dict):
                return False
            
            # Check if it has at least some days
            days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            found_days = 0
            
            for day in days:
                if day in meal_plan and isinstance(meal_plan[day], dict):
                    day_meals = meal_plan[day]
                    # Check if it has at least one meal type
                    meal_types = ["breakfast", "lunch", "dinner"]
                    for meal_type in meal_types:
                        if meal_type in day_meals and isinstance(day_meals[meal_type], dict):
                            meal = day_meals[meal_type]
                            if "name" in meal and meal["name"]:
                                found_days += 1
                                break
            
            # Require at least 3 days with meals to be considered valid
            return found_days >= 3
            
        except Exception as e:
            print(f"❌ Meal plan validation failed: {e}")
            return False
    
    def _generate_with_ollama(self, preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate meal plan using Ollama (local LLM)"""
        
        print("🤖 Attempting to generate meal plan with Ollama...")
        
        # Check if Ollama is available
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code != 200:
                raise Exception(f"Ollama server returned status {response.status_code}")
            print("✅ Ollama server is running")
        except Exception as e:
            print(f"❌ Ollama server not running: {e}")
            raise Exception("Ollama server not running")
        
        prompt = self._create_meal_plan_prompt(preferences)
        print(f"📝 Generated prompt length: {len(prompt)} characters")
        
        # Try multiple models in order of preference
        models_to_try = ["llama3.2:latest", "llama3:latest", "llama2:latest", "mistral:latest", "codellama:latest"]
        
        for model in models_to_try:
            try:
                print(f"🚀 Trying model: {model}")
                
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 3000,  # Increased for better meal plans
                        "num_predict": 2000
                    }
                }
                
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=180  # Increased timeout for LLM generation
                )
                
                if response.status_code == 200:
                    result = response.json()
                    meal_plan_text = result.get('response', '')
                    print(f"📄 Received response from Ollama ({len(meal_plan_text)} characters)")
                    print(f"📝 Response preview: {meal_plan_text[:300]}...")
                    
                    parsed_plan = self._parse_meal_plan_response(meal_plan_text)
                    if parsed_plan and self._validate_meal_plan(parsed_plan):
                        print(f"✅ Successfully generated meal plan with model {model}")
                        return parsed_plan
                    else:
                        print(f"❌ Model {model} generated invalid meal plan, trying next model...")
                        continue
                else:
                    print(f"❌ Ollama request failed with status {response.status_code}")
                    print(f"Error response: {response.text}")
                    continue
                    
            except Exception as e:
                print(f"❌ Error with model {model}: {e}")
                continue
        
        print("❌ All Ollama models failed to generate valid meal plan")
        return None
    
    def _generate_with_ollama_fallback(self, preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate meal plan using Ollama with simplified prompt and different approach"""
        
        print("🔄 Trying Ollama with simplified approach...")
        
        try:
            # Use a much simpler prompt
            simple_prompt = self._create_simple_meal_plan_prompt(preferences)
            
            # Try with a different model and simpler settings
            payload = {
                "model": "mistral:latest",  # Mistral is often more reliable
                "prompt": simple_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.5,  # Lower temperature for more consistent output
                    "top_p": 0.8,
                    "max_tokens": 2000
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                meal_plan_text = result.get('response', '')
                print(f"📄 Received fallback response from Ollama ({len(meal_plan_text)} characters)")
                
                parsed_plan = self._parse_meal_plan_response(meal_plan_text)
                if parsed_plan and self._validate_meal_plan(parsed_plan):
                    print("✅ Fallback Ollama generation succeeded")
                    return parsed_plan
            
        except Exception as e:
            print(f"❌ Ollama fallback failed: {e}")
        
        return None
    
    def _create_simple_meal_plan_prompt(self, preferences: Dict[str, Any]) -> str:
        """Create a very simple prompt for less capable models"""
        
        dietary_restrictions = preferences.get("dietaryRestrictions", [])
        favorite_cuisines = preferences.get("favoriteCuisines", [])
        favorite_foods = preferences.get("favoriteFoods", [])
        
        prompt = f"""Create a simple 7-day meal plan with breakfast, lunch, and dinner.

User preferences:
- Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
- Favorite cuisines: {', '.join(favorite_cuisines) if favorite_cuisines else 'Any'}
- Favorite foods: {', '.join(favorite_foods) if favorite_foods else 'Any'}

Format as JSON:
{{
  "monday": {{
    "breakfast": {{"name": "Meal name", "cuisine": "Cuisine type"}},
    "lunch": {{"name": "Meal name", "cuisine": "Cuisine type"}},
    "dinner": {{"name": "Meal name", "cuisine": "Cuisine type"}}
  }},
  "tuesday": {{ ... }},
  "wednesday": {{ ... }},
  "thursday": {{ ... }},
  "friday": {{ ... }},
  "saturday": {{ ... }},
  "sunday": {{ ... }}
}}

Include favorite foods when possible. Keep it simple and nutritious."""
        
        return prompt
    
    def _generate_with_huggingface(self, preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate meal plan using Hugging Face Inference API"""
        
        print("🌐 Attempting to generate meal plan with Hugging Face...")
        
        # Use a more suitable model for text generation
        model_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
        
        # If no API key, try the free endpoint (may have rate limits)
        if not self.hf_api_key:
            print("⚠️ No Hugging Face API key provided, using free endpoint (may have rate limits)")
            model_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
        else:
            print("🔑 Using Hugging Face API key")
        
        headers = {
            "Authorization": f"Bearer {self.hf_api_key}" if self.hf_api_key else "",
            "Content-Type": "application/json"
        }
        
        # Create a more structured prompt for better results
        prompt = self._create_hf_meal_plan_prompt(preferences)
        print(f"📝 HF prompt length: {len(prompt)} characters")
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1500,
                "temperature": 0.7,
                "return_full_text": False,
                "do_sample": True,
                "top_p": 0.9
            }
        }
        
        try:
            print(f"🚀 Sending request to Hugging Face model...")
            response = requests.post(model_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                print(f"📄 Received response from Hugging Face")
                
                if isinstance(result, list) and len(result) > 0:
                    meal_plan_text = result[0].get('generated_text', '')
                    print(f"📝 Generated text length: {len(meal_plan_text)} characters")
                    print(f"📝 Preview: {meal_plan_text[:300]}...")
                    
                    parsed_plan = self._parse_meal_plan_response(meal_plan_text)
                    if parsed_plan and self._validate_meal_plan(parsed_plan):
                        print("✅ Successfully parsed Hugging Face meal plan")
                        return parsed_plan
                    else:
                        print("❌ Hugging Face generated invalid meal plan")
                        return None
                else:
                    print(f"❌ Unexpected Hugging Face response format: {result}")
                    return None
            else:
                print(f"❌ Hugging Face request failed with status {response.status_code}")
                print(f"Error response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Hugging Face request failed: {e}")
            return None
    
    def _create_hf_meal_plan_prompt(self, preferences: Dict[str, Any]) -> str:
        """Create a prompt specifically designed for Hugging Face models"""
        
        dietary_restrictions = preferences.get("dietaryRestrictions", [])
        favorite_cuisines = preferences.get("favoriteCuisines", [])
        favorite_foods = preferences.get("favoriteFoods", [])
        allergens = preferences.get("allergens", [])
        cooking_skill = preferences.get("cookingSkillLevel", "beginner")
        
        prompt = f"""Create a weekly meal plan for 7 days with breakfast, lunch, and dinner.

User preferences:
- Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
- Favorite cuisines: {', '.join(favorite_cuisines) if favorite_cuisines else 'Any'}
- Favorite foods: {', '.join(favorite_foods) if favorite_foods else 'Any'}
- Allergens to avoid: {', '.join(allergens) if allergens else 'None'}
- Cooking skill: {cooking_skill}

Please provide a meal plan in this JSON format:
{{
  "monday": {{
    "breakfast": {{"name": "Meal name", "cuisine": "Cuisine type"}},
    "lunch": {{"name": "Meal name", "cuisine": "Cuisine type"}},
    "dinner": {{"name": "Meal name", "cuisine": "Cuisine type"}}
  }},
  "tuesday": {{ ... }},
  "wednesday": {{ ... }},
  "thursday": {{ ... }},
  "friday": {{ ... }},
  "saturday": {{ ... }},
  "sunday": {{ ... }}
}}

Focus on including favorite foods and respecting dietary restrictions. Make it nutritious and varied."""
        
        return prompt
    
    def _generate_rule_based_plan(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a rule-based meal plan using user preferences with variety"""
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
        
        # Track used recipes to ensure variety
        used_recipes = set()
        
        for day in days:
            day_plan = {}
            
            if include_breakfast:
                breakfast = self._select_meal_template(meal_templates, 'breakfast', dietary_restrictions, used_recipes)
                day_plan['breakfast'] = breakfast
                used_recipes.add(breakfast["name"])
            
            if include_lunch:
                lunch = self._select_meal_template(meal_templates, 'lunch', dietary_restrictions, used_recipes)
                day_plan['lunch'] = lunch
                used_recipes.add(lunch["name"])
            
            if include_dinner:
                dinner = self._select_meal_template(meal_templates, 'dinner', dietary_restrictions, used_recipes)
                day_plan['dinner'] = dinner
                used_recipes.add(dinner["name"])
            
            if include_snacks:
                snack = self._select_meal_template(meal_templates, 'snack', dietary_restrictions, used_recipes)
                day_plan['snack'] = snack
                used_recipes.add(snack["name"])
            
            meal_plan["days"][day] = day_plan
        
        # Add metadata
        meal_plan["metadata"] = {
            "generated_at": datetime.utcnow().isoformat(),
            "preferences_used": preferences,
            "method": "rule_based",
            "total_meals": len(days) * (include_breakfast + include_lunch + include_dinner + include_snacks),
            "variety_score": len(used_recipes),  # Track how many unique recipes were used
            "cuisines_represented": list(set([meal.get('cuisine', 'Unknown') for day in meal_plan["days"].values() for meal in day.values()]))
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

CRITICAL REQUIREMENTS (in order of priority):
1. FAVORITE FOODS ARE THE HIGHEST PRIORITY - Include user's favorite foods in at least 20% of all meals
2. Don't force cuisine variety if it means excluding favorite foods
3. Provide exactly 21 meals (3 per day for 7 days)
4. Ensure nutritional balance and variety
5. Respect all dietary restrictions and allergens
6. Match cooking complexity to skill level
7. Include diverse cuisines and cooking methods (but secondary to favorite foods)
8. Keep cooking time within the specified limit

IMPORTANT: Generate ONLY valid JSON. Do not include any explanations, markdown formatting, or text outside the JSON structure.

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
    "lunch": {{
      "name": "Meal Name",
      "cuisine": "Cuisine Type",
      "ingredients": ["ingredient1", "ingredient2"],
      "instructions": ["step1", "step2"],
      "cooking_time": "30 minutes",
      "difficulty": "beginner"
    }},
    "dinner": {{
      "name": "Meal Name",
      "cuisine": "Cuisine Type",
      "ingredients": ["ingredient1", "ingredient2"],
      "instructions": ["step1", "step2"],
      "cooking_time": "30 minutes",
      "difficulty": "beginner"
    }}
  }},
  "tuesday": {{
    "breakfast": {{ ... }},
    "lunch": {{ ... }},
    "dinner": {{ ... }}
  }},
  "wednesday": {{
    "breakfast": {{ ... }},
    "lunch": {{ ... }},
    "dinner": {{ ... }}
  }},
  "thursday": {{
    "breakfast": {{ ... }},
    "lunch": {{ ... }},
    "dinner": {{ ... }}
  }},
  "friday": {{
    "breakfast": {{ ... }},
    "lunch": {{ ... }},
    "dinner": {{ ... }}
  }},
  "saturday": {{
    "breakfast": {{ ... }},
    "lunch": {{ ... }},
    "dinner": {{ ... }}
  }},
  "sunday": {{
    "breakfast": {{ ... }},
    "lunch": {{ ... }},
    "dinner": {{ ... }}
  }}
}}

Start with Monday and continue through Sunday. Each day should have breakfast, lunch, and dinner.
REMEMBER: Favorite foods should appear frequently throughout the week, even if it means repeating some cuisines.
Generate ONLY the JSON object, no other text."""
        
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
                
                # Clean up the JSON string
                cleaned_json = self._clean_json_string(json_str)
                
                try:
                    parsed_json = json.loads(cleaned_json)
                    print(f"✅ Successfully parsed JSON with keys: {list(parsed_json.keys())}")
                    return parsed_json
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing failed after cleaning: {e}")
                    # Try to fix common JSON issues
                    fixed_json = self._fix_common_json_issues(cleaned_json)
                    try:
                        parsed_json = json.loads(fixed_json)
                        print(f"✅ Successfully parsed JSON after fixing issues")
                        return parsed_json
                    except json.JSONDecodeError as e2:
                        print(f"❌ JSON parsing still failed after fixes: {e2}")
                        
                        # Try step-by-step repair as last resort
                        print("🔧 Trying step-by-step JSON repair...")
                        repaired_json = self._repair_json_step_by_step(cleaned_json)
                        if repaired_json:
                            print(f"✅ Successfully repaired JSON structure")
                            return repaired_json
            
            # If no JSON or JSON parsing failed, try to parse as text format
            print("📝 No valid JSON found, trying text parsing...")
            parsed_text = self._parse_text_meal_plan(response_text)
            if parsed_text:
                print(f"✅ Successfully parsed text format")
                return parsed_text
            
            print("❌ Failed to parse response in any format")
            return None
            
        except Exception as e:
            print(f"❌ General parsing error: {e}")
            return None
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean up common issues in LLM-generated JSON"""
        
        # Remove markdown code blocks
        json_str = re.sub(r'```json\s*', '', json_str)
        json_str = re.sub(r'```\s*$', '', json_str)
        
        # Remove leading/trailing whitespace and newlines
        json_str = json_str.strip()
        
        # Remove any text before the first {
        first_brace = json_str.find('{')
        if first_brace > 0:
            json_str = json_str[first_brace:]
        
        # Remove any text after the last }
        last_brace = json_str.rfind('}')
        if last_brace > 0:
            json_str = json_str[:last_brace + 1]
        
        # Fix common LLM JSON formatting issues
        json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
        json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
        
        # Fix unquoted keys (common LLM issue)
        json_str = re.sub(r'(\w+):', r'"\1":', json_str)
        
        # Fix single quotes to double quotes
        json_str = json_str.replace("'", '"')
        
        # Fix missing quotes around string values that should be quoted
        # Look for patterns like: "name": Meal Name, -> "name": "Meal Name",
        json_str = re.sub(r':\s*([a-zA-Z][a-zA-Z\s\-&]+)(?=\s*[,}])', r': "\1"', json_str)
        
        # Fix missing quotes around string values in arrays
        json_str = re.sub(r'\[\s*([a-zA-Z][a-zA-Z\s\-&]+)\s*\]', r'["\1"]', json_str)
        
        return json_str
    
    def _fix_common_json_issues(self, json_str: str) -> str:
        """Fix common JSON formatting issues from LLMs"""
        
        try:
            # Try to fix missing quotes around string values
            # This regex looks for unquoted strings after colons
            json_str = re.sub(r':\s*([a-zA-Z][a-zA-Z\s\-&]+)(?=\s*[,}])', r': "\1"', json_str)
            
            # Fix missing quotes around keys
            json_str = re.sub(r'(\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*):', r'\1"\2":', json_str)
            
            # Remove any trailing commas before closing braces/brackets
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            # Try to balance braces and brackets
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            open_brackets = json_str.count('[')
            close_brackets = json_str.count(']')
            
            # Add missing closing braces/brackets if needed
            if open_braces > close_braces:
                json_str += '}' * (open_braces - close_braces)
            if open_brackets > close_brackets:
                json_str += ']' * (open_brackets - close_brackets)
            
            # Fix common array formatting issues
            # Look for patterns like: ["ingredient1", ingredient2, "ingredient3"]
            json_str = re.sub(r',\s*([a-zA-Z][a-zA-Z\s\-&]*)\s*,', r', "\1",', json_str)
            
            # Fix missing quotes at the beginning of arrays
            json_str = re.sub(r'\[\s*([a-zA-Z][a-zA-Z\s\-&]*)', r'["\1"', json_str)
            
            # Fix missing quotes at the end of arrays
            json_str = re.sub(r'([a-zA-Z][a-zA-Z\s\-&]*)\s*\]', r'"\1"]', json_str)
            
            return json_str
            
        except Exception as e:
            print(f"⚠️ Error fixing JSON issues: {e}")
            return json_str
    
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
        """Get comprehensive meal templates with variety and diversity"""
        
        # Extensive recipe database with variety
        templates = {
            "breakfast": [
                # Quick & Easy Breakfasts
                {
                    "name": "Avocado Toast with Poached Eggs",
                    "description": "Creamy avocado on sourdough with perfectly poached eggs",
                    "cuisine": "International",
                    "cookingTime": "15 minutes",
                    "difficulty": "beginner",
                    "ingredients": ["Sourdough bread", "Avocado", "Eggs", "Lemon juice", "Salt", "Pepper", "Red pepper flakes"],
                    "instructions": ["Toast bread until golden", "Mash avocado with lemon juice and seasonings", "Poach eggs in simmering water", "Spread avocado on toast and top with eggs"]
                },
                {
                    "name": "Greek Yogurt Parfait",
                    "description": "Layered yogurt with fresh fruits and crunchy granola",
                    "cuisine": "Mediterranean",
                    "cookingTime": "5 minutes",
                    "difficulty": "beginner",
                    "ingredients": ["Greek yogurt", "Mixed berries", "Granola", "Honey", "Almonds", "Mint leaves"],
                    "instructions": ["Layer yogurt in glass", "Add berries and granola", "Drizzle with honey", "Garnish with almonds and mint"]
                },
                {
                    "name": "Shakshuka",
                    "description": "Middle Eastern eggs poached in spicy tomato sauce",
                    "cuisine": "Middle Eastern",
                    "cookingTime": "25 minutes",
                    "difficulty": "intermediate",
                    "ingredients": ["Eggs", "Tomatoes", "Onion", "Bell peppers", "Garlic", "Cumin", "Paprika", "Feta cheese"],
                    "instructions": ["Sauté onions and peppers", "Add tomatoes and spices", "Create wells for eggs", "Poach eggs in sauce", "Top with feta"]
                },
                {
                    "name": "Japanese Tamago",
                    "description": "Sweet Japanese rolled omelet",
                    "cuisine": "Japanese",
                    "cookingTime": "20 minutes",
                    "difficulty": "advanced",
                    "ingredients": ["Eggs", "Sugar", "Mirin", "Soy sauce", "Dashi stock", "Vegetable oil"],
                    "instructions": ["Beat eggs with seasonings", "Cook thin layers in pan", "Roll each layer carefully", "Slice and serve"]
                },
                {
                    "name": "Mexican Chilaquiles",
                    "description": "Crispy tortillas in spicy sauce with eggs",
                    "cuisine": "Mexican",
                    "cookingTime": "20 minutes",
                    "difficulty": "intermediate",
                    "ingredients": ["Corn tortillas", "Eggs", "Salsa verde", "Queso fresco", "Crema", "Cilantro", "Onion"],
                    "instructions": ["Fry tortillas until crispy", "Simmer in salsa", "Top with fried eggs", "Garnish with cheese and crema"]
                },
                {
                    "name": "French Crepes",
                    "description": "Thin, delicate crepes with sweet or savory fillings",
                    "cuisine": "French",
                    "cookingTime": "30 minutes",
                    "difficulty": "intermediate",
                    "ingredients": ["Flour", "Eggs", "Milk", "Butter", "Sugar", "Vanilla", "Salt"],
                    "instructions": ["Mix batter until smooth", "Rest batter for 30 minutes", "Cook thin crepes in pan", "Fill and fold as desired"]
                },
                {
                    "name": "Indian Masala Dosa",
                    "description": "Crispy rice crepe with spiced potato filling",
                    "cuisine": "Indian",
                    "cookingTime": "45 minutes",
                    "difficulty": "advanced",
                    "ingredients": ["Rice", "Urad dal", "Potatoes", "Onions", "Mustard seeds", "Curry leaves", "Turmeric"],
                    "instructions": ["Soak rice and dal overnight", "Grind to smooth batter", "Ferment for 8 hours", "Make thin crepes", "Fill with spiced potatoes"]
                },
                {
                    "name": "Turkish Menemen",
                    "description": "Scrambled eggs with tomatoes and peppers",
                    "cuisine": "Turkish",
                    "cookingTime": "20 minutes",
                    "difficulty": "beginner",
                    "ingredients": ["Eggs", "Tomatoes", "Green peppers", "Onion", "Olive oil", "Red pepper flakes", "Feta"],
                    "instructions": ["Sauté vegetables in olive oil", "Add tomatoes and cook down", "Scramble eggs into mixture", "Top with feta and herbs"]
                }
            ],
            "lunch": [
                # Light & Fresh Lunches
                {
                    "name": "Vietnamese Pho",
                    "description": "Aromatic rice noodle soup with herbs and protein",
                    "cuisine": "Vietnamese",
                    "cookingTime": "45 minutes",
                    "difficulty": "intermediate",
                    "ingredients": ["Rice noodles", "Beef broth", "Bean sprouts", "Thai basil", "Lime", "Sriracha", "Hoisin sauce"],
                    "instructions": ["Simmer beef broth with spices", "Cook rice noodles", "Assemble with fresh herbs", "Serve with condiments"]
                },
                {
                    "name": "Mediterranean Quinoa Bowl",
                    "description": "Nutritious bowl with Mediterranean flavors",
                    "cuisine": "Mediterranean",
                    "cookingTime": "25 minutes",
                    "difficulty": "beginner",
                    "ingredients": ["Quinoa", "Cherry tomatoes", "Cucumber", "Kalamata olives", "Feta cheese", "Olive oil", "Lemon", "Oregano"],
                    "instructions": ["Cook quinoa according to package", "Chop vegetables", "Mix with olive oil and lemon", "Top with feta and herbs"]
                },
                {
                    "name": "Thai Green Curry",
                    "description": "Spicy coconut curry with vegetables and protein",
                    "cuisine": "Thai",
                    "cookingTime": "30 minutes",
                    "difficulty": "intermediate",
                    "ingredients": ["Green curry paste", "Coconut milk", "Vegetables", "Protein of choice", "Fish sauce", "Palm sugar", "Thai basil"],
                    "instructions": ["Fry curry paste in oil", "Add coconut milk", "Simmer vegetables and protein", "Season with fish sauce and sugar"]
                },
                {
                    "name": "Lebanese Falafel Wrap",
                    "description": "Crispy chickpea fritters in pita with tahini",
                    "cuisine": "Lebanese",
                    "cookingTime": "35 minutes",
                    "difficulty": "intermediate",
                    "ingredients": ["Chickpeas", "Onion", "Garlic", "Parsley", "Cumin", "Coriander", "Pita bread", "Tahini sauce"],
                    "instructions": ["Process chickpeas with herbs", "Form into balls", "Deep fry until golden", "Serve in pita with tahini"]
                },
                {
                    "name": "Korean Bibimbap",
                    "description": "Colorful rice bowl with vegetables and gochujang",
                    "cuisine": "Korean",
                    "cookingTime": "40 minutes",
                    "difficulty": "intermediate",
                    "ingredients": ["Rice", "Spinach", "Carrots", "Bean sprouts", "Eggs", "Gochujang", "Sesame oil", "Sesame seeds"],
                    "instructions": ["Cook rice", "Prepare vegetables separately", "Fry egg sunny-side up", "Assemble bowl and top with gochujang"]
                },
                {
                    "name": "Italian Caprese Salad",
                    "description": "Fresh mozzarella with tomatoes and basil",
                    "cuisine": "Italian",
                    "cookingTime": "10 minutes",
                    "difficulty": "beginner",
                    "ingredients": ["Fresh mozzarella", "Heirloom tomatoes", "Fresh basil", "Balsamic glaze", "Extra virgin olive oil", "Sea salt", "Black pepper"],
                    "instructions": ["Slice mozzarella and tomatoes", "Arrange alternately on plate", "Tear basil leaves", "Drizzle with oil and balsamic"]
                },
                {
                    "name": "Japanese Bento Box",
                    "description": "Beautifully arranged lunch with variety",
                    "cuisine": "Japanese",
                    "cookingTime": "35 minutes",
                    "difficulty": "intermediate",
                    "ingredients": ["Rice", "Salmon", "Tamago", "Vegetables", "Pickled items", "Miso soup"],
                    "instructions": ["Prepare rice", "Cook salmon and tamago", "Steam vegetables", "Arrange beautifully in bento box"]
                },
                {
                    "name": "Mexican Ceviche",
                    "description": "Fresh fish cured in citrus with vegetables",
                    "cuisine": "Mexican",
                    "cookingTime": "20 minutes",
                    "difficulty": "intermediate",
                    "ingredients": ["Fresh fish", "Lime juice", "Onion", "Cilantro", "Jalapeño", "Tomatoes", "Avocado"],
                    "instructions": ["Cube fresh fish", "Marinate in lime juice", "Add vegetables and herbs", "Serve with tortilla chips"]
                }
            ],
            "dinner": [
                # Hearty & Flavorful Dinners
                {
                    "name": "Moroccan Tagine",
                    "description": "Slow-cooked stew with aromatic spices",
                    "cuisine": "Moroccan",
                    "cookingTime": "90 minutes",
                    "difficulty": "intermediate",
                    "ingredients": ["Lamb or chicken", "Onions", "Dried apricots", "Almonds", "Cinnamon", "Cumin", "Coriander", "Couscous"],
                    "instructions": ["Brown meat with spices", "Add vegetables and dried fruits", "Simmer until tender", "Serve over couscous"]
                },
                {
                    "name": "Indian Butter Chicken",
                    "description": "Creamy tomato-based curry with tender chicken",
                    "cuisine": "Indian",
                    "cookingTime": "60 minutes",
                    "difficulty": "intermediate",
                    "ingredients": ["Chicken", "Yogurt", "Tomato sauce", "Heavy cream", "Butter", "Garam masala", "Fenugreek", "Basmati rice"],
                    "instructions": ["Marinate chicken in yogurt", "Grill until charred", "Simmer in tomato sauce", "Finish with cream and butter"]
                },
                {
                    "name": "French Coq au Vin",
                    "description": "Classic French braised chicken in wine",
                    "cuisine": "French",
                    "cookingTime": "120 minutes",
                    "difficulty": "advanced",
                    "ingredients": ["Chicken", "Red wine", "Bacon", "Mushrooms", "Pearl onions", "Carrots", "Herbs de Provence"],
                    "instructions": ["Brown chicken and bacon", "Add wine and vegetables", "Braise until tender", "Reduce sauce and serve"]
                },
                {
                    "name": "Thai Massaman Curry",
                    "description": "Rich peanut curry with tender beef",
                    "cuisine": "Thai",
                    "cookingTime": "90 minutes",
                    "difficulty": "intermediate",
                    "ingredients": ["Beef", "Massaman curry paste", "Coconut milk", "Potatoes", "Peanuts", "Tamarind", "Palm sugar"],
                    "instructions": ["Brown beef with curry paste", "Add coconut milk", "Simmer with potatoes", "Finish with peanuts and tamarind"]
                },
                {
                    "name": "Spanish Paella",
                    "description": "Saffron rice with seafood and chorizo",
                    "cuisine": "Spanish",
                    "cookingTime": "45 minutes",
                    "difficulty": "advanced",
                    "ingredients": ["Arborio rice", "Saffron", "Seafood", "Chorizo", "Bell peppers", "Peas", "Lemon"],
                    "instructions": ["Toast rice with saffron", "Add broth gradually", "Add seafood and vegetables", "Create socarrat at bottom"]
                },
                {
                    "name": "Japanese Ramen",
                    "description": "Rich broth with noodles and toppings",
                    "cuisine": "Japanese",
                    "cookingTime": "120 minutes",
                    "difficulty": "advanced",
                    "ingredients": ["Pork bones", "Noodles", "Chashu pork", "Soft-boiled eggs", "Nori", "Green onions", "Bamboo shoots"],
                    "instructions": ["Simmer pork bones for hours", "Prepare chashu and eggs", "Cook noodles", "Assemble with toppings"]
                },
                {
                    "name": "Greek Moussaka",
                    "description": "Layered eggplant with spiced meat and béchamel",
                    "cuisine": "Greek",
                    "cookingTime": "90 minutes",
                    "difficulty": "advanced",
                    "ingredients": ["Eggplant", "Ground lamb", "Onion", "Cinnamon", "Nutmeg", "Béchamel sauce", "Parmesan"],
                    "instructions": ["Grill eggplant slices", "Cook spiced meat", "Make béchamel sauce", "Layer and bake until golden"]
                },
                {
                    "name": "Ethiopian Doro Wat",
                    "description": "Spicy chicken stew with berbere spice",
                    "cuisine": "Ethiopian",
                    "cookingTime": "75 minutes",
                    "difficulty": "intermediate",
                    "ingredients": ["Chicken", "Berbere spice", "Onions", "Garlic", "Ginger", "Hard-boiled eggs", "Injera bread"],
                    "instructions": ["Sauté onions with berbere", "Add chicken and spices", "Simmer until tender", "Serve with eggs and injera"]
                }
            ]
        }
        
        # Add snack templates if needed
        if "snack" not in templates:
            templates["snack"] = [
                {
                    "name": "Hummus with Vegetables",
                    "description": "Creamy hummus with fresh crudités",
                    "cuisine": "Middle Eastern",
                    "cookingTime": "10 minutes",
                    "difficulty": "beginner",
                    "ingredients": ["Chickpeas", "Tahini", "Lemon", "Garlic", "Olive oil", "Carrots", "Cucumber", "Bell peppers"],
                    "instructions": ["Blend chickpeas with tahini and lemon", "Season with garlic and salt", "Serve with fresh vegetables"]
                },
                {
                    "name": "Greek Tzatziki",
                    "description": "Cool yogurt dip with cucumber and herbs",
                    "cuisine": "Greek",
                    "cookingTime": "15 minutes",
                    "difficulty": "beginner",
                    "ingredients": ["Greek yogurt", "Cucumber", "Garlic", "Dill", "Lemon juice", "Olive oil", "Pita bread"],
                    "instructions": ["Grate and drain cucumber", "Mix with yogurt and herbs", "Season to taste", "Serve with pita"]
                }
            ]
        
        # Filter templates based on dietary restrictions
        if "vegetarian" in dietary_restrictions or "vegan" in dietary_restrictions:
            for meal_type in templates:
                templates[meal_type] = [
                    meal for meal in templates[meal_type] 
                    if not any(ingredient.lower() in ["salmon", "chicken", "fish", "meat", "beef", "lamb", "pork", "bacon", "chorizo"]
                              for ingredient in meal["ingredients"])
                ]
        
        if "vegan" in dietary_restrictions:
            for meal_type in templates:
                templates[meal_type] = [
                    meal for meal in templates[meal_type] 
                    if not any(ingredient.lower() in ["eggs", "yogurt", "cheese", "feta", "mozzarella", "parmesan", "cream", "milk"]
                              for ingredient in meal["ingredients"])
                ]
        
        return templates
    
    def _select_meal_template(self, templates: Dict[str, List[Dict]], meal_type: str, dietary_restrictions: List[str], used_recipes: set = None) -> Dict[str, Any]:
        """Select an appropriate meal template with variety and no repetition"""
        import random
        
        if used_recipes is None:
            used_recipes = set()
        
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
        
        # Prioritize recipes that haven't been used recently
        unused_templates = [t for t in suitable_templates if t["name"] not in used_recipes]
        
        if unused_templates:
            # Use unused recipes first
            selected = random.choice(unused_templates)
        else:
            # If all recipes have been used, reset and use any
            selected = random.choice(suitable_templates)
        
        # Add meal type and unique ID to the template
        selected['meal_type'] = meal_type
        selected['id'] = f"{meal_type}_{selected['name'].lower().replace(' ', '_')}_{random.randint(1000, 9999)}"
        
        # Add difficulty level if not present
        if 'difficulty' not in selected:
            selected['difficulty'] = 'beginner'
        
        return selected
    
    def regenerate_specific_meal(self, user_id: str, day: str, meal_type: str, current_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Regenerate a specific meal in the plan with variety"""
        
        try:
            preferences = self.user_preferences_service.get_preferences(user_id)
            if not preferences:
                return {"error": "User preferences not found"}
            
            # Get meal templates and select a different one
            dietary_restrictions = preferences.get("dietaryRestrictions", [])
            favorite_cuisines = preferences.get("favoriteCuisines", [])
            cooking_skill = preferences.get("cookingSkillLevel", "beginner")
            
            templates = self._get_meal_templates(dietary_restrictions, favorite_cuisines, cooking_skill)
            
            # Collect all currently used recipe names to avoid repetition
            used_recipes = set()
            for plan_day, day_meals in current_plan.items():
                if isinstance(day_meals, dict):
                    for meal_key, meal_data in day_meals.items():
                        if isinstance(meal_data, dict) and 'name' in meal_data:
                            used_recipes.add(meal_data['name'])
            
            # Get current meal name to avoid regenerating the same recipe
            current_meal_name = current_plan.get(day, {}).get(meal_type, {}).get("name", "")
            
            # Try to find a different recipe
            attempts = 0
            max_attempts = 10
            new_meal = None
            
            while attempts < max_attempts:
                new_meal = self._select_meal_template(templates, meal_type, dietary_restrictions, used_recipes)
                
                # If we found a different meal, use it
                if new_meal["name"] != current_meal_name:
                    break
                
                # If we're still getting the same meal, try without the used_recipes filter
                if attempts >= 5:
                    new_meal = self._select_meal_template(templates, meal_type, dietary_restrictions, set())
                    if new_meal["name"] != current_meal_name:
                        break
                
                attempts += 1
            
            # If we still can't find a different meal, create a variation
            if new_meal["name"] == current_meal_name:
                new_meal["name"] = f"{current_meal_name} (Variation)"
                new_meal["description"] = f"A delicious variation of {current_meal_name}"
            
            # Add unique ID and ensure difficulty matches user preference
            import time
            new_meal["id"] = f"regenerated_{meal_type}_{int(time.time())}"
            new_meal["difficulty"] = cooking_skill
            
            return {
                "success": True,
                "meal": new_meal,
                "variety_improvement": True
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

    def _repair_json_step_by_step(self, json_str: str) -> Optional[Dict[str, Any]]:
        """Attempt to repair JSON step by step, trying different approaches"""
        
        print("🔧 Attempting step-by-step JSON repair...")
        
        # Step 1: Try to extract just the basic structure
        try:
            # Look for the main meal plan structure
            pattern = r'\{[^{}]*"monday"[^{}]*\{[^{}]*"breakfast"[^{}]*\{[^{}]*"name"[^{}]*"[^"]*"[^{}]*\}[^{}]*\}[^{}]*\}'
            match = re.search(pattern, json_str, re.DOTALL)
            if match:
                basic_json = match.group() + "}"
                print("📋 Extracted basic structure, attempting to parse...")
                try:
                    return json.loads(basic_json)
                except:
                    pass
        except Exception as e:
            print(f"⚠️ Basic structure extraction failed: {e}")
        
        # Step 2: Try to build a minimal valid JSON
        try:
            print("🔧 Building minimal valid JSON structure...")
            minimal_plan = {}
            days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            
            for day in days:
                day_pattern = r'"' + day + r'"\s*:\s*\{[^{}]*\}'
                day_match = re.search(day_pattern, json_str, re.DOTALL)
                if day_match:
                    day_str = "{" + day_match.group() + "}"
                    try:
                        day_data = json.loads(day_str)
                        if day in day_data:
                            minimal_plan[day] = day_data[day]
                    except:
                        # If parsing fails, create a basic structure
                        minimal_plan[day] = {
                            "breakfast": {"name": f"Healthy {day.title()} Breakfast", "cuisine": "International"},
                            "lunch": {"name": f"Healthy {day.title()} Lunch", "cuisine": "International"},
                            "dinner": {"name": f"Healthy {day.title()} Dinner", "cuisine": "International"}
                        }
                else:
                    # Create default structure for missing days
                    minimal_plan[day] = {
                        "breakfast": {"name": f"Healthy {day.title()} Breakfast", "cuisine": "International"},
                        "lunch": {"name": f"Healthy {day.title()} Lunch", "cuisine": "International"},
                        "dinner": {"name": f"Healthy {day.title()} Dinner", "cuisine": "International"}
                    }
            
            if minimal_plan:
                print("✅ Successfully built minimal meal plan structure")
                return minimal_plan
                
        except Exception as e:
            print(f"⚠️ Minimal structure building failed: {e}")
        
        # Step 3: Try to extract meal names and build structure
        try:
            print("🔧 Extracting meal names and building structure...")
            meal_plan = {}
            days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            meal_types = ["breakfast", "lunch", "dinner"]
            
            for day in days:
                meal_plan[day] = {}
                for meal_type in meal_types:
                    # Look for meal names in the text
                    pattern = r'"' + day + r'"[^{}]*"' + meal_type + r'"[^{}]*"name"[^{}]*"([^"]+)"'
                    match = re.search(pattern, json_str, re.DOTALL)
                    if match:
                        meal_name = match.group(1)
                        meal_plan[day][meal_type] = {
                            "name": meal_name,
                            "cuisine": "International",
                            "ingredients": ["Fresh ingredients", "Seasonings"],
                            "instructions": [f"Prepare {meal_name} according to your preferences"],
                            "cooking_time": "30 minutes",
                            "difficulty": "beginner"
                        }
                    else:
                        # Default meal
                        meal_plan[day][meal_type] = {
                            "name": f"Healthy {meal_type.title()}",
                            "cuisine": "International",
                            "ingredients": ["Fresh ingredients", "Seasonings"],
                            "instructions": [f"Prepare a healthy {meal_type}"],
                            "cooking_time": "30 minutes",
                            "difficulty": "beginner"
                        }
            
            print("✅ Successfully extracted meal names and built structure")
            return meal_plan
            
        except Exception as e:
            print(f"⚠️ Meal name extraction failed: {e}")
        
        return None 