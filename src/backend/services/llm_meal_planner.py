import os
import json
import openai
from typing import Dict, List, Any, Optional
from services.user_preferences_service import UserPreferencesService
from dotenv import load_dotenv

load_dotenv()

class LLMMealPlanner:
    def __init__(self, user_preferences_service: UserPreferencesService):
        self.user_preferences_service = user_preferences_service
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def generate_weekly_meal_plan(self, user_id: str) -> Dict[str, Any]:
        """Generate a weekly meal plan using LLM based on user preferences"""
        try:
            # Get user preferences
            preferences = self.user_preferences_service.get_preferences(user_id)
            if not preferences:
                return {"error": "User preferences not found. Please set your preferences first."}
            
            # Create the prompt for the LLM
            prompt = self._create_meal_plan_prompt(preferences)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using the more cost-effective model
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional nutritionist and meal planning expert. Generate balanced, varied, and delicious meal plans based on user preferences. Always provide exactly 3 meals per day for 7 days (21 meals total). Ensure meals are practical, nutritious, and follow the user's dietary restrictions and preferences."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            meal_plan_text = response.choices[0].message.content
            meal_plan_data = json.loads(meal_plan_text)
            
            # Validate and format the response
            formatted_plan = self._format_meal_plan(meal_plan_data)
            
            return {
                "success": True,
                "plan": formatted_plan,
                "preferences_used": preferences
            }
            
        except openai.OpenAIError as e:
            return {"error": f"OpenAI API error: {str(e)}"}
        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse meal plan response: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def _create_meal_plan_prompt(self, preferences: Dict[str, Any]) -> str:
        """Create a detailed prompt for the LLM based on user preferences"""
        
        # Extract preference details
        dietary_restrictions = preferences.get("dietaryRestrictions", [])
        favorite_cuisines = preferences.get("favoriteCuisines", [])
        allergens = preferences.get("allergens", [])
        cooking_skill = preferences.get("cookingSkillLevel", "beginner")
        health_goals = preferences.get("healthGoals", [])
        meal_prep_time = preferences.get("maxCookingTime", "30 minutes")
        
        prompt = f"""
Please create a comprehensive weekly meal plan with exactly 3 meals per day for 7 days (Monday through Sunday).

USER PREFERENCES:
- Dietary Restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
- Favorite Cuisines: {', '.join(favorite_cuisines) if favorite_cuisines else 'Any'}
- Allergens to Avoid: {', '.join(allergens) if allergens else 'None'}
- Cooking Skill Level: {cooking_skill}
- Health Goals: {', '.join(health_goals) if health_goals else 'General wellness'}
- Maximum Cooking Time: {meal_prep_time}

REQUIREMENTS:
1. Provide exactly 3 meals per day (breakfast, lunch, dinner) for 7 days
2. Ensure nutritional balance across the week
3. Vary cuisines and ingredients to prevent monotony
4. Consider the cooking skill level for recipe complexity
5. Respect all dietary restrictions and allergens
6. Include a mix of cooking methods (grilling, baking, stir-frying, etc.)
7. Make meals practical for the specified cooking time limit

RESPONSE FORMAT:
Please respond with a JSON object in this exact format:
{{
  "monday": {{
    "breakfast": {{
      "id": "unique_id_1",
      "name": "Meal Name",
      "description": "Brief description of the dish",
      "cuisine": "Cuisine type",
      "cookingTime": "X minutes",
      "difficulty": "beginner/intermediate/advanced",
      "ingredients": ["ingredient1", "ingredient2", "ingredient3"],
      "instructions": "Brief cooking instructions"
    }},
    "lunch": {{
      "id": "unique_id_2",
      "name": "Meal Name",
      "description": "Brief description",
      "cuisine": "Cuisine type",
      "cookingTime": "X minutes",
      "difficulty": "beginner/intermediate/advanced",
      "ingredients": ["ingredient1", "ingredient2"],
      "instructions": "Brief cooking instructions"
    }},
    "dinner": {{
      "id": "unique_id_3",
      "name": "Meal Name",
      "description": "Brief description",
      "cuisine": "Cuisine type",
      "cookingTime": "X minutes",
      "difficulty": "beginner/intermediate/advanced",
      "ingredients": ["ingredient1", "ingredient2"],
      "instructions": "Brief cooking instructions"
    }}
  }},
  "tuesday": {{
    ... (same structure for all 7 days)
  }},
  ... (continue for all days of the week)
}}

Make sure each meal has a unique ID and follows the user's preferences strictly.
"""
        
        return prompt
    
    def _format_meal_plan(self, meal_plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format and validate the meal plan data"""
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        meal_types = ["breakfast", "lunch", "dinner"]
        
        formatted_plan = {}
        
        for day in days:
            if day not in meal_plan_data:
                raise ValueError(f"Missing day: {day}")
            
            formatted_plan[day] = {}
            
            for meal_type in meal_types:
                if meal_type not in meal_plan_data[day]:
                    raise ValueError(f"Missing {meal_type} for {day}")
                
                meal = meal_plan_data[day][meal_type]
                
                # Ensure required fields are present
                required_fields = ["id", "name", "description", "cuisine", "cookingTime", "difficulty", "ingredients", "instructions"]
                for field in required_fields:
                    if field not in meal:
                        meal[field] = f"Not specified" if field != "ingredients" else []
                
                formatted_plan[day][meal_type] = meal
        
        return formatted_plan
    
    def regenerate_specific_meal(self, user_id: str, day: str, meal_type: str, current_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Regenerate a specific meal in the plan"""
        try:
            preferences = self.user_preferences_service.get_preferences(user_id)
            if not preferences:
                return {"error": "User preferences not found"}
            
            # Create a prompt for regenerating just one meal
            prompt = self._create_single_meal_prompt(preferences, day, meal_type, current_plan)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional nutritionist. Generate a single meal replacement that fits the user's preferences and complements their existing meal plan."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,  # Higher temperature for more variety
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            meal_data = json.loads(response.choices[0].message.content)
            
            return {
                "success": True,
                "meal": meal_data["meal"]
            }
            
        except Exception as e:
            return {"error": f"Failed to regenerate meal: {str(e)}"}
    
    def _create_single_meal_prompt(self, preferences: Dict[str, Any], day: str, meal_type: str, current_plan: Dict[str, Any]) -> str:
        """Create a prompt for regenerating a single meal"""
        
        dietary_restrictions = preferences.get("dietaryRestrictions", [])
        favorite_cuisines = preferences.get("favoriteCuisines", [])
        allergens = preferences.get("allergens", [])
        cooking_skill = preferences.get("cookingSkillLevel", "beginner")
        
        # Get other meals from the current plan to avoid repetition
        other_meals = []
        for d in current_plan:
            for m in current_plan[d]:
                if not (d == day and m == meal_type):
                    other_meals.append(current_plan[d][m]["name"])
        
        prompt = f"""
Please create a single {meal_type} meal for {day} that fits these preferences:

USER PREFERENCES:
- Dietary Restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
- Favorite Cuisines: {', '.join(favorite_cuisines) if favorite_cuisines else 'Any'}
- Allergens to Avoid: {', '.join(allergens) if allergens else 'None'}
- Cooking Skill Level: {cooking_skill}

AVOID REPETITION:
The user already has these meals in their plan: {', '.join(other_meals[:10])}
Please create something different.

RESPONSE FORMAT:
{{
  "meal": {{
    "id": "unique_id",
    "name": "Meal Name",
    "description": "Brief description",
    "cuisine": "Cuisine type",
    "cookingTime": "X minutes",
    "difficulty": "beginner/intermediate/advanced",
    "ingredients": ["ingredient1", "ingredient2", "ingredient3"],
    "instructions": "Brief cooking instructions"
  }}
}}
"""
        
        return prompt 