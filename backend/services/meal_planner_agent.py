import random
from typing import List, Dict, Any, Optional
from services.user_preferences_service import UserPreferencesService

# Placeholder for recipe data (replace with actual database/API calls)
# In a real scenario, this would fetch recipes from MongoDB or an external API.
class RecipeServicePlaceholder:
    def get_all_recipes(self) -> List[Dict[str, Any]]:
        # This should return a list of recipe dictionaries with relevant fields
        # For now, a mock list
        return [
            {
                "id": "rec1", "name": "Spaghetti Bolognese", "cuisine": "Italian",
                "dietaryRestrictions": [], "difficulty": "intermediate", "ingredients": ["pasta", "meat", "tomato"]
            },
            {
                "id": "rec2", "name": "Vegetable Stir-fry", "cuisine": "Asian",
                "dietaryRestrictions": ["vegetarian", "vegan"], "difficulty": "beginner", "ingredients": ["broccoli", "carrot", "tofu"]
            },
            {
                "id": "rec3", "name": "Gluten-Free Chicken Curry", "cuisine": "Indian",
                "dietaryRestrictions": ["gluten-free"], "difficulty": "intermediate", "ingredients": ["chicken", "curry powder", "rice"]
            },
            {
                "id": "rec4", "name": "Classic Beef Tacos", "cuisine": "Mexican",
                "dietaryRestrictions": [], "difficulty": "beginner", "ingredients": ["beef", "tortillas", "salsa"]
            },
            {
                "id": "rec5", "name": "Lentil Soup", "cuisine": "Mediterranean",
                "dietaryRestrictions": ["vegetarian", "vegan"], "difficulty": "beginner", "ingredients": ["lentils", "vegetables"]
            },
            {
                "id": "rec6", "name": "Keto Salmon with Asparagus", "cuisine": "American",
                "dietaryRestrictions": ["keto"], "difficulty": "intermediate", "ingredients": ["salmon", "asparagus", "butter"]
            },
            {
                "id": "rec7", "name": "Vegan Lasagna", "cuisine": "Italian",
                "dietaryRestrictions": ["vegan"], "difficulty": "advanced", "ingredients": ["pasta", "vegan cheese", "tomato"]
            },
            {
                "id": "rec8", "name": "Carnivore Steak and Eggs", "cuisine": "American",
                "dietaryRestrictions": ["carnivore"], "difficulty": "beginner", "ingredients": ["steak", "eggs"]
            },
            # Add more diverse mock recipes
            {
                "id": "rec9", "name": "Sushi Rolls", "cuisine": "Japanese",
                "dietaryRestrictions": [], "difficulty": "advanced", "ingredients": ["rice", "fish", "seaweed"]
            },
            {
                "id": "rec10", "name": "Thai Green Curry", "cuisine": "Thai",
                "dietaryRestrictions": ["vegan"], "difficulty": "intermediate", "ingredients": ["coconut milk", "curry paste", "vegetables"]
            },
        ]

class MealPlannerAgent:
    def __init__(self, user_preferences_service: UserPreferencesService, recipe_service: Any):
        self.user_preferences_service = user_preferences_service
        self.recipe_service = recipe_service

    def _filter_recipes(self, all_recipes: List[Dict[str, Any]], preferences: Dict[str, Any], meal_type: Optional[str] = None) -> List[Dict[str, Any]]:
        filtered_recipes = []
        
        dietary_restrictions = preferences.get("dietaryRestrictions", [])
        favorite_cuisines = preferences.get("favoriteCuisines", [])
        allergens = preferences.get("allergens", [])
        cooking_skill_level = preferences.get("cookingSkillLevel", "beginner")

        for recipe in all_recipes:
            # Filter by meal_type if specified
            if meal_type and recipe.get("mealType") and recipe["mealType"].lower() != meal_type.lower():
                continue

            # 1. Dietary Restrictions Check
            recipe_dietary = [d.lower() for d in recipe.get("dietaryRestrictions", [])]
            if dietary_restrictions:
                if not all(res.lower() in recipe_dietary for res in dietary_restrictions):
                    continue # Skip if recipe doesn't meet ALL specified dietary restrictions
            
            # 2. Allergens Check (simplified: checks if any ingredient contains allergen text)
            recipe_ingredients_lower = [ing.lower() for ing in recipe.get("ingredients", [])]
            if any(allergen.lower() in ' '.join(recipe_ingredients_lower) for allergen in allergens):
                continue # Skip if recipe contains any specified allergen
            
            # 3. Cooking Skill Level Check (basic: beginner can do beginner/intermediate, advanced can do all)
            recipe_difficulty = recipe.get("difficulty", "beginner")
            if cooking_skill_level == "beginner" and recipe_difficulty == "advanced":
                continue
            if cooking_skill_level == "intermediate" and recipe_difficulty == "advanced":
                # Intermediate can do intermediate and beginner
                pass # No skip, allow it
            
            filtered_recipes.append(recipe)

        # 4. Prioritize Favorite Cuisines
        if favorite_cuisines:
            prioritized = []
            other = []
            for recipe in filtered_recipes:
                recipe_cuisine_lower = recipe.get("cuisine", "").lower()
                if any(fav_cuisine.lower() == recipe_cuisine_lower for fav_cuisine in favorite_cuisines):
                    prioritized.append(recipe)
                else:
                    other.append(recipe)
            # Shuffle and combine to ensure some variety even if favorites exist
            random.shuffle(prioritized)
            random.shuffle(other)
            filtered_recipes = prioritized + other
        else:
            random.shuffle(filtered_recipes) # Shuffle if no cuisine preference for variety
            
        return filtered_recipes

    def generate_weekly_plan(self, user_id: str) -> Dict[str, Any]:
        preferences = self.user_preferences_service.get_preferences(user_id)
        if not preferences:
            return {"error": "User preferences not found."}

        all_recipes = self.recipe_service.get_all_recipes()
        if not all_recipes:
            return {"error": "No recipes available to generate a plan."}

        eligible_recipes = self._filter_recipes(all_recipes, preferences)
        
        online_recipe_ideas = []
        if not eligible_recipes or len(eligible_recipes) < 7: # If few or no eligible recipes, try web search
            print("Few or no eligible recipes found. Attempting web search for more ideas...")
            search_query_parts = []
            if preferences.get("dietaryRestrictions"):
                search_query_parts.extend(preferences["dietaryRestrictions"])
            if preferences.get("favoriteCuisines"):
                search_query_parts.extend(preferences["favoriteCuisines"])
            # Add cooking skill level to query if available and not beginner
            skill_level = preferences.get("cookingSkillLevel", "beginner")
            if skill_level != "beginner":
                search_query_parts.append(f"{skill_level} difficulty")

            search_query_parts.append("recipe ideas")
            
            search_query = " ".join(search_query_parts)
            online_recipe_ideas = self.recipe_service.search_online_recipe_ideas(search_query)
            print(f"Found {len(online_recipe_ideas)} online recipe ideas.")
            
            # Note: For now, these online ideas are just titles/links. 
            # They cannot be directly added to the meal plan without full recipe data.
            # The frontend can display these as suggestions.

        if not eligible_recipes:
            # If still no eligible recipes even after considering potential web search expansion
            return {
                "error": "No recipes match your preferences. Please adjust them.",
                "online_ideas": online_recipe_ideas # Include ideas if found
            }

        weekly_plan = {
            "monday": {"breakfast": None, "lunch": None, "dinner": None},
            "tuesday": {"breakfast": None, "lunch": None, "dinner": None},
            "wednesday": {"breakfast": None, "lunch": None, "dinner": None},
            "thursday": {"breakfast": None, "lunch": None, "dinner": None},
            "friday": {"breakfast": None, "lunch": None, "dinner": None},
            "saturday": {"breakfast": None, "lunch": None, "dinner": None},
            "sunday": {"breakfast": None, "lunch": None, "dinner": None},
        }

        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        meal_types = ["breakfast", "lunch", "dinner"]

        assigned_recipe_ids = set() # To track recipes used in the *entire* week to avoid direct repetition
        daily_assigned_recipes: Dict[str, set] = {
            day: set() for day in days
        } # To track recipes used on a given day

        for day in days:
            for meal_type in meal_types:
                # Get recipes eligible for the current meal type and user preferences
                # Ensure we don't reuse the exact same recipe multiple times on the same day
                # and try to avoid immediate repetition across days.
                
                # Filter by meal_type first
                eligible_for_meal_type = self._filter_recipes(all_recipes, preferences, meal_type)

                # Further filter to exclude recipes already assigned on this day or recently assigned globally
                # Implement a simple recency check: avoid recipes used in the last 2 days for the same meal type
                recent_global_exclusions = set()
                if len(assigned_recipe_ids) > 0: # Only if recipes have been assigned
                    # This is a very basic heuristic; a more advanced agent would track usage per meal type per day
                    # For now, just avoid recently used recipes globally
                    # In a more complex agent, we'd store a history of chosen recipes
                    pass # We'll manage variety by shuffling and picking from available_for_slot

                available_for_slot = [
                    r for r in eligible_for_meal_type
                    if r["id"] not in daily_assigned_recipes[day] and r["id"] not in assigned_recipe_ids
                ]

                # If not enough variety, allow reuse, but prioritize unused ones
                if not available_for_slot:
                    # Allow recipes not used on this specific day, even if used earlier in the week
                    available_for_slot = [
                        r for r in eligible_for_meal_type
                        if r["id"] not in daily_assigned_recipes[day]
                    ]

                # If still not enough, allow any eligible recipe for the meal type
                if not available_for_slot:
                    available_for_slot = list(eligible_for_meal_type)
                
                if available_for_slot:
                    chosen_recipe = random.choice(available_for_slot)
                    weekly_plan[day][meal_type] = chosen_recipe
                    assigned_recipe_ids.add(chosen_recipe["id"])
                    daily_assigned_recipes[day].add(chosen_recipe["id"])
                else:
                    weekly_plan[day][meal_type] = {"id": "none", "name": f"No {meal_type} recipe found for preferences"}

        return {"plan": weekly_plan} 