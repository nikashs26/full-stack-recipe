import random
import logging
from typing import List, Dict, Any, Optional
from services.user_preferences_service import UserPreferencesService
from services.llm_meal_planner_agent import LLMMealPlannerAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MealPlannerAgent:
    def __init__(self, user_preferences_service: UserPreferencesService, recipe_service: Any):
        self.user_preferences_service = user_preferences_service
        self.recipe_service = recipe_service
        self.llm_agent = LLMMealPlannerAgent()
        
    def generate_weekly_plan(self, user_id: str) -> Dict[str, Any]:
        """Generate a comprehensive weekly meal plan using LLM with ChromaDB preferences"""
        print(f'🔥 MEAL_PLANNER_AGENT: generate_weekly_plan called for user_id: {user_id}')
        try:
            # Get user preferences from ChromaDB
            print(f'🔥 MEAL_PLANNER_AGENT: Getting preferences from ChromaDB for user_id: {user_id}')
            preferences = self.user_preferences_service.get_preferences(user_id)
            print(f'🔥 MEAL_PLANNER_AGENT: Retrieved preferences: {preferences}')
            
            if not preferences:
                logger.warning(f"No preferences found for user {user_id}")
                print(f'🔥 MEAL_PLANNER_AGENT: No preferences found for user {user_id}')
                return {"error": "User preferences not found. Please set your preferences first."}
            
            logger.info(f"Generating LLM-powered weekly meal plan for user {user_id}")
            print(f'🔥 MEAL_PLANNER_AGENT: Generating meal plan with preferences: {preferences}')
            
            # Use LLM agent to generate comprehensive meal plan
            meal_plan = self.llm_agent.generate_weekly_meal_plan(preferences)
            
            # Add user context and metadata
            meal_plan['user_id'] = user_id
            meal_plan['plan_type'] = 'llm_generated'
            
            return meal_plan
            
        except Exception as e:
            logger.error(f"Error generating weekly plan for user {user_id}: {str(e)}")
            # Fall back to rule-based system
            return self._generate_fallback_plan(user_id)
    
    def generate_meal_plan_with_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a meal plan directly with preferences (for API calls without user ID)"""
        try:
            logger.info("Generating LLM-powered meal plan with provided preferences")
            
            # Use LLM agent to generate comprehensive meal plan
            meal_plan = self.llm_agent.generate_weekly_meal_plan(preferences)
            
            # Add metadata
            meal_plan['plan_type'] = 'llm_generated'
            meal_plan['source'] = 'direct_preferences'
            
            return meal_plan
            
        except Exception as e:
            logger.error(f"Error generating meal plan with preferences: {str(e)}")
            # Fall back to rule-based system
            return self._generate_rule_based_fallback(preferences)
    
    def get_recipe_suggestions(self, meal_type: str, preferences: Dict[str, Any], count: int = 5) -> List[Dict[str, Any]]:
        """Get LLM-powered recipe suggestions for a specific meal type"""
        try:
            logger.info(f"Getting LLM recipe suggestions for {meal_type}")
            return self.llm_agent.get_recipe_suggestions(meal_type, preferences, count)
        except Exception as e:
            logger.error(f"Error getting recipe suggestions: {str(e)}")
            return []
    
    def _generate_fallback_plan(self, user_id: str) -> Dict[str, Any]:
        """Generate a fallback meal plan using rule-based system"""
        try:
            preferences = self.user_preferences_service.get_preferences(user_id)
            if not preferences:
                preferences = self._get_default_preferences()
            
            return self._generate_rule_based_fallback(preferences)
        except Exception as e:
            logger.error(f"Error generating fallback plan: {str(e)}")
            return {"error": "Unable to generate meal plan. Please try again later."}
    
    def _generate_rule_based_fallback(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a basic rule-based meal plan as fallback"""
        from datetime import datetime, timedelta
        
        # Extract preferences
        dietary_restrictions = preferences.get('dietary_restrictions', [])
        favorite_cuisines = preferences.get('favorite_cuisines', [])
        allergies = preferences.get('allergies', [])
        
        # Simple meal templates
        meal_templates = {
            "breakfast": [
                {"name": "Oatmeal with Berries", "cuisine": "American", "time": "10 minutes", "vegetarian": True, "vegan": True},
                {"name": "Avocado Toast", "cuisine": "American", "time": "10 minutes", "vegetarian": True, "vegan": True},
                {"name": "Greek Yogurt Parfait", "cuisine": "Mediterranean", "time": "5 minutes", "vegetarian": True, "vegan": False},
                {"name": "Smoothie Bowl", "cuisine": "American", "time": "10 minutes", "vegetarian": True, "vegan": True},
                {"name": "Scrambled Eggs", "cuisine": "American", "time": "10 minutes", "vegetarian": True, "vegan": False}
            ],
            "lunch": [
                {"name": "Quinoa Buddha Bowl", "cuisine": "American", "time": "25 minutes", "vegetarian": True, "vegan": True},
                {"name": "Mediterranean Wrap", "cuisine": "Mediterranean", "time": "15 minutes", "vegetarian": True, "vegan": False},
                {"name": "Asian Stir-Fry", "cuisine": "Asian", "time": "20 minutes", "vegetarian": True, "vegan": True},
                {"name": "Lentil Soup", "cuisine": "International", "time": "30 minutes", "vegetarian": True, "vegan": True},
                {"name": "Caprese Salad", "cuisine": "Italian", "time": "10 minutes", "vegetarian": True, "vegan": False}
            ],
            "dinner": [
                {"name": "Grilled Salmon with Vegetables", "cuisine": "American", "time": "25 minutes", "vegetarian": False, "vegan": False},
                {"name": "Vegetable Curry", "cuisine": "Indian", "time": "35 minutes", "vegetarian": True, "vegan": True},
                {"name": "Pasta Primavera", "cuisine": "Italian", "time": "30 minutes", "vegetarian": True, "vegan": False},
                {"name": "Thai Green Curry", "cuisine": "Asian", "time": "30 minutes", "vegetarian": True, "vegan": True},
                {"name": "Stuffed Bell Peppers", "cuisine": "Mediterranean", "time": "45 minutes", "vegetarian": True, "vegan": True}
            ]
        }
        
        # Filter recipes based on dietary restrictions
        filtered_meals = {}
        for meal_type, recipes in meal_templates.items():
            filtered_meals[meal_type] = []
            for recipe in recipes:
                if self._is_recipe_compatible_simple(recipe, dietary_restrictions, allergies):
                    filtered_meals[meal_type].append(recipe)
        
        # Generate 7-day plan
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        today = datetime.now()
        
        weekly_plan = []
        for i, day in enumerate(days):
            day_date = today + timedelta(days=i)
            
            day_meals = {}
            for meal_type in ["breakfast", "lunch", "dinner"]:
                available_recipes = filtered_meals.get(meal_type, [])
                if available_recipes:
                    # Prefer favorite cuisines
                    if favorite_cuisines:
                        preferred_recipes = [r for r in available_recipes if r["cuisine"].lower() in [c.lower() for c in favorite_cuisines]]
                        if preferred_recipes:
                            chosen_recipe = random.choice(preferred_recipes)
                        else:
                            chosen_recipe = random.choice(available_recipes)
                    else:
                        chosen_recipe = random.choice(available_recipes)
                    
                    day_meals[meal_type] = {
                        "name": chosen_recipe["name"],
                        "cuisine": chosen_recipe["cuisine"],
                        "prep_time": "10 minutes",
                        "cook_time": chosen_recipe["time"],
                        "difficulty": "Medium",
                        "servings": 2,
                        "ingredients": ["Basic ingredients - see full recipe"],
                        "instructions": [f"Prepare {chosen_recipe['name']} following standard recipe"],
                        "nutritional_highlights": ["Balanced nutrition"],
                        "tags": ["healthy", "balanced"]
                    }
                else:
                    # Fallback meal
                    day_meals[meal_type] = {
                        "name": f"Simple {meal_type.title()}",
                        "cuisine": "International",
                        "prep_time": "10 minutes",
                        "cook_time": "15 minutes",
                        "difficulty": "Easy",
                        "servings": 2,
                        "ingredients": ["Basic ingredients"],
                        "instructions": [f"Prepare a simple {meal_type}"],
                        "nutritional_highlights": ["Balanced nutrition"],
                        "tags": ["quick", "simple"]
                    }
            
            weekly_plan.append({
                "day": day,
                "date": day_date.strftime("%Y-%m-%d"),
                "meals": day_meals,
                "daily_notes": "Rule-based meal plan - consider upgrading to AI-powered planning"
            })
        
        return {
            "week_summary": {
                "theme": "Balanced Weekly Nutrition",
                "total_recipes": 21,
                "prep_tips": [
                    "Prep vegetables in advance for quicker cooking",
                    "Cook grains in larger batches",
                    "Plan your grocery shopping ahead"
                ],
                "shopping_highlights": ["Fresh vegetables", "Whole grains", "Lean proteins"]
            },
            "days": weekly_plan,
            "weekly_shopping_list": {
                "proteins": ["eggs", "tofu", "lentils"] if 'vegetarian' in dietary_restrictions else ["chicken", "salmon", "eggs"],
                "vegetables": ["spinach", "broccoli", "bell peppers", "tomatoes", "onions"],
                "grains": ["quinoa", "brown rice", "oats", "whole wheat bread"],
                "dairy": [] if 'vegan' in dietary_restrictions else ["greek yogurt", "cheese"],
                "pantry": ["olive oil", "spices", "nuts", "seeds", "canned beans"],
                "estimated_cost": "$50-65"
            },
            "nutritional_summary": {
                "weekly_highlights": ["Balanced macronutrients", "Variety of vegetables", "Whole grains"],
                "variety_score": "Good",
                "health_rating": "Good"
            },
            "generated_at": datetime.now().isoformat(),
            "preferences_used": preferences,
            "plan_type": "rule_based_fallback",
            "note": "This is a simplified meal plan. For personalized AI-generated plans with detailed recipes, please ensure your preferences are set and try again."
        }
    
    def _is_recipe_compatible_simple(self, recipe: Dict[str, Any], dietary_restrictions: List[str], allergies: List[str]) -> bool:
        """Simple compatibility check for fallback recipes"""
        # Check dietary restrictions
        for restriction in dietary_restrictions:
            if restriction.lower() == "vegetarian" and not recipe.get("vegetarian", False):
                return False
            if restriction.lower() == "vegan" and not recipe.get("vegan", False):
                return False
        
        # For simplicity, assume other restrictions are handled in recipe selection
        return True
    
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Get default preferences when none are found"""
        return {
            "dietary_restrictions": [],
            "favorite_cuisines": ["American", "Mediterranean", "Italian"],
            "allergies": [],
            "cooking_time": "medium",
            "skill_level": "intermediate",
            "budget_range": "moderate"
        } 