import os
import json
import requests
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AIRecipeGenerator:
    """
    AI-powered recipe generator that creates diverse, fresh recipes using LLMs
    instead of relying on hardcoded recipe data
    """
    
    def __init__(self):
        self.huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY', '')
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        
        # Recipe generation parameters
        self.trending_topics = [
            "air fryer recipes", "meal prep friendly", "one pot meals", 
            "plant-based protein", "keto-friendly", "anti-inflammatory",
            "gut health focused", "high fiber", "quick 15-minute meals",
            "fermented foods", "seasonal produce", "comfort food makeovers"
        ]
        
        self.seasonal_ingredients = {
            "spring": ["asparagus", "peas", "artichokes", "fresh herbs", "strawberries", "rhubarb"],
            "summer": ["tomatoes", "zucchini", "corn", "berries", "stone fruits", "fresh basil"],
            "fall": ["pumpkin", "squash", "apples", "Brussels sprouts", "sweet potatoes", "cranberries"],
            "winter": ["root vegetables", "citrus fruits", "cabbage", "pomegranate", "winter greens", "warming spices"]
        }
        
        self.cuisine_styles = [
            "Mediterranean", "Asian Fusion", "Latin American", "Middle Eastern",
            "Nordic", "African", "Caribbean", "Indian", "Thai", "Mexican",
            "Italian", "French", "Japanese", "Korean", "Vietnamese", "Ethiopian"
        ]
        
        self.cooking_techniques = [
            "grilling", "roasting", "stir-frying", "braising", "steaming",
            "fermentation", "smoking", "sous vide", "pressure cooking", "air frying"
        ]
        
        # Determine LLM service
        self.service = self._determine_service()
        logger.info(f"AI Recipe Generator using: {self.service}")
    
    def _determine_service(self) -> str:
        """Determine which LLM service to use for recipe generation"""
        # Try Ollama first (local, free)
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                return 'ollama'
        except:
            pass
        
        # Try Hugging Face
        if self.huggingface_api_key:
            return 'huggingface'
        
        # Fallback to rule-based generation
        return 'rule_based'
    
    def generate_trending_recipes(self, count: int = 20, user_preferences: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Generate recipes based on current food trends and user preferences"""
        recipes = []
        
        # Select trending topics
        selected_trends = random.sample(self.trending_topics, min(count//2, len(self.trending_topics)))
        
        for trend in selected_trends:
            try:
                recipe = self._generate_recipe_for_trend(trend, user_preferences)
                if recipe:
                    recipes.append(recipe)
                    
                # Generate a variation of the same trend
                if len(recipes) < count:
                    variation = self._generate_recipe_variation(recipe, user_preferences)
                    if variation:
                        recipes.append(variation)
                        
            except Exception as e:
                logger.warning(f"Failed to generate recipe for trend '{trend}': {e}")
                continue
        
        # Fill remaining slots with cuisine-based recipes
        while len(recipes) < count:
            try:
                cuisine = random.choice(self.cuisine_styles)
                technique = random.choice(self.cooking_techniques)
                recipe = self._generate_cuisine_recipe(cuisine, technique, user_preferences)
                if recipe and not self._is_duplicate(recipe, recipes):
                    recipes.append(recipe)
                else:
                    break  # Prevent infinite loop
            except Exception as e:
                logger.warning(f"Failed to generate cuisine recipe: {e}")
                break
        
        return recipes[:count]
    
    def generate_seasonal_recipes(self, season: str = None, count: int = 15) -> List[Dict[str, Any]]:
        """Generate recipes using seasonal ingredients"""
        if not season:
            # Auto-detect season based on current month
            month = datetime.now().month
            if month in [3, 4, 5]:
                season = "spring"
            elif month in [6, 7, 8]:
                season = "summer"
            elif month in [9, 10, 11]:
                season = "fall"
            else:
                season = "winter"
        
        seasonal_ingredients = self.seasonal_ingredients.get(season, [])
        recipes = []
        
        for _ in range(count):
            try:
                # Select 2-3 seasonal ingredients
                ingredients = random.sample(seasonal_ingredients, min(3, len(seasonal_ingredients)))
                cuisine = random.choice(self.cuisine_styles)
                
                recipe = self._generate_seasonal_recipe(ingredients, cuisine, season)
                if recipe and not self._is_duplicate(recipe, recipes):
                    recipes.append(recipe)
            except Exception as e:
                logger.warning(f"Failed to generate seasonal recipe: {e}")
                continue
        
        return recipes
    
    def generate_personalized_recipes(self, user_preferences: Dict[str, Any], count: int = 10) -> List[Dict[str, Any]]:
        """Generate highly personalized recipes based on detailed user preferences"""
        recipes = []
        
        dietary_restrictions = user_preferences.get('dietaryRestrictions', [])
        favorite_cuisines = user_preferences.get('favoriteCuisines', [])
        cooking_skill = user_preferences.get('cookingSkillLevel', 'intermediate')
        max_time = user_preferences.get('maxCookingTime', '30 minutes')
        health_goals = user_preferences.get('healthGoals', [])
        
        # Generate recipes for each favorite cuisine
        for cuisine in favorite_cuisines[:count//2]:
            try:
                recipe = self._generate_personalized_cuisine_recipe(
                    cuisine, dietary_restrictions, cooking_skill, max_time, health_goals
                )
                if recipe:
                    recipes.append(recipe)
            except Exception as e:
                logger.warning(f"Failed to generate personalized {cuisine} recipe: {e}")
                continue
        
        # Generate recipes based on health goals
        for goal in health_goals[:count//3]:
            try:
                recipe = self._generate_health_focused_recipe(
                    goal, dietary_restrictions, cooking_skill, max_time
                )
                if recipe:
                    recipes.append(recipe)
            except Exception as e:
                logger.warning(f"Failed to generate health-focused recipe for '{goal}': {e}")
                continue
        
        # Fill remaining with trending recipes that match preferences
        while len(recipes) < count:
            try:
                trend = random.choice(self.trending_topics)
                recipe = self._generate_recipe_for_trend(trend, user_preferences)
                if recipe and not self._is_duplicate(recipe, recipes):
                    recipes.append(recipe)
                else:
                    break
            except Exception as e:
                logger.warning(f"Failed to generate trending recipe: {e}")
                break
        
        return recipes[:count]
    
    def _generate_recipe_for_trend(self, trend: str, user_preferences: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Generate a recipe based on a specific food trend"""
        if self.service == 'ollama':
            return self._generate_with_ollama_trend(trend, user_preferences)
        elif self.service == 'huggingface':
            return self._generate_with_huggingface_trend(trend, user_preferences)
        else:
            return self._generate_rule_based_trend_recipe(trend, user_preferences)
    
    def _generate_with_ollama_trend(self, trend: str, user_preferences: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Generate recipe using Ollama LLM"""
        try:
            # Build preference context
            pref_context = ""
            if user_preferences:
                dietary = user_preferences.get('dietaryRestrictions', [])
                cuisines = user_preferences.get('favoriteCuisines', [])
                if dietary:
                    pref_context += f"Must be {', '.join(dietary)}. "
                if cuisines:
                    pref_context += f"Preferably {', '.join(cuisines)} style. "
            
            prompt = f"""Create a unique, creative recipe that focuses on "{trend}". {pref_context}

Requirements:
- Original recipe name (not a copy of existing recipes)
- Innovative approach to the trend
- Realistic ingredients and instructions
- Modern cooking techniques
- Health-conscious when possible

Respond with ONLY a JSON object in this format:
{{
  "title": "Unique Recipe Name",
  "summary": "Brief description (1-2 sentences)",
  "cuisine": ["Primary cuisine"],
  "diets": ["dietary tags like vegetarian, gluten-free"],
  "readyInMinutes": 30,
  "servings": 4,
  "difficulty": "Easy/Medium/Hard",
  "ingredients": [
    {{"name": "ingredient", "amount": "1", "unit": "cup"}},
    {{"name": "ingredient2", "amount": "2", "unit": "tbsp"}}
  ],
  "instructions": [
    "Step 1 instruction",
    "Step 2 instruction"
  ],
  "nutritionalHighlights": ["benefit1", "benefit2"],
  "tags": ["tag1", "tag2", "tag3"],
  "trendFocus": "{trend}"
}}"""

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2:latest",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.8, "top_p": 0.9}
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '')
                
                # Extract JSON from response
                try:
                    start_idx = generated_text.find('{')
                    end_idx = generated_text.rfind('}') + 1
                    if start_idx != -1 and end_idx != -1:
                        json_str = generated_text[start_idx:end_idx]
                        recipe_data = json.loads(json_str)
                        
                        # Add metadata
                        recipe_data['id'] = f"ai_trend_{hash(recipe_data['title'])}_{int(datetime.now().timestamp())}"
                        recipe_data['source'] = 'AI Generated'
                        recipe_data['generatedAt'] = datetime.now().isoformat()
                        recipe_data['generationType'] = 'trend_based'
                        recipe_data['image'] = self._generate_recipe_image_url(recipe_data['title'])
                        
                        return recipe_data
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse Ollama JSON response for trend: {trend}")
                    
        except Exception as e:
            logger.warning(f"Ollama generation failed for trend '{trend}': {e}")
        
        return None
    
    def _generate_with_huggingface_trend(self, trend: str, user_preferences: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Generate recipe using Hugging Face API"""
        try:
            pref_context = ""
            if user_preferences:
                dietary = user_preferences.get('dietaryRestrictions', [])
                if dietary:
                    pref_context = f"Make it {', '.join(dietary)}. "
            
            prompt = f"Create a {trend} recipe. {pref_context}Include ingredients and cooking steps."
            
            headers = {"Authorization": f"Bearer {self.huggingface_api_key}"}
            
            response = requests.post(
                "https://api-inference.huggingface.co/models/gpt2",
                headers=headers,
                json={"inputs": prompt, "parameters": {"max_length": 500, "temperature": 0.8}},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get('generated_text', '')
                    return self._parse_generated_text_to_recipe(generated_text, trend)
                    
        except Exception as e:
            logger.warning(f"Hugging Face generation failed for trend '{trend}': {e}")
        
        return None
    
    def _generate_rule_based_trend_recipe(self, trend: str, user_preferences: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate recipe using rule-based approach with templates"""
        
        # Recipe templates based on trends
        trend_templates = {
            "air fryer recipes": {
                "techniques": ["air fry", "crisp", "roast in air fryer"],
                "base_ingredients": ["chicken", "vegetables", "potatoes", "fish"],
                "cooking_time": 20
            },
            "meal prep friendly": {
                "techniques": ["batch cook", "store well", "reheat easily"],
                "base_ingredients": ["grains", "protein", "roasted vegetables"],
                "cooking_time": 45
            },
            "one pot meals": {
                "techniques": ["simmer", "braise", "one-pot cooking"],
                "base_ingredients": ["pasta", "rice", "protein", "vegetables", "broth"],
                "cooking_time": 35
            },
            "plant-based protein": {
                "techniques": ["marinate", "season", "sauté"],
                "base_ingredients": ["lentils", "chickpeas", "tofu", "tempeh", "quinoa"],
                "cooking_time": 25
            }
        }
        
        template = trend_templates.get(trend, {
            "techniques": ["cook", "prepare", "season"],
            "base_ingredients": ["vegetables", "herbs", "spices"],
            "cooking_time": 30
        })
        
        # Apply user preferences
        dietary_restrictions = user_preferences.get('dietaryRestrictions', []) if user_preferences else []
        favorite_cuisines = user_preferences.get('favoriteCuisines', ['International']) if user_preferences else ['International']
        
        # Filter ingredients based on dietary restrictions
        ingredients = template['base_ingredients'].copy()
        if 'vegan' in dietary_restrictions:
            ingredients = [ing for ing in ingredients if ing not in ['chicken', 'fish', 'cheese', 'eggs']]
            ingredients.extend(['nutritional yeast', 'tahini', 'cashews'])
        
        # Select cuisine influence
        cuisine = random.choice(favorite_cuisines) if favorite_cuisines else "International"
        
        # Generate recipe
        recipe_title = self._generate_trend_title(trend, cuisine, ingredients)
        
        return {
            'id': f"ai_rule_{hash(recipe_title)}_{int(datetime.now().timestamp())}",
            'title': recipe_title,
            'summary': f"A delicious {trend} recipe with {cuisine.lower()} influences",
            'cuisine': [cuisine],
            'diets': dietary_restrictions,
            'readyInMinutes': template['cooking_time'],
            'servings': 4,
            'difficulty': 'Medium',
            'ingredients': self._generate_ingredients_list(ingredients, dietary_restrictions),
            'instructions': self._generate_cooking_instructions(template['techniques'], ingredients),
            'nutritionalHighlights': self._generate_nutritional_highlights(trend, ingredients),
            'tags': [trend, cuisine.lower(), 'ai-generated'],
            'source': 'AI Generated',
            'generatedAt': datetime.now().isoformat(),
            'generationType': 'rule_based_trend',
            'image': self._generate_recipe_image_url(recipe_title),
            'trendFocus': trend
        }
    
    def _generate_cuisine_recipe(self, cuisine: str, technique: str, user_preferences: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate a recipe for specific cuisine and cooking technique"""
        
        cuisine_ingredients = {
            "Mediterranean": ["olive oil", "tomatoes", "herbs", "garlic", "lemon", "olives"],
            "Asian Fusion": ["soy sauce", "ginger", "sesame oil", "rice vinegar", "scallions"],
            "Mexican": ["cumin", "chili peppers", "lime", "cilantro", "avocado", "beans"],
            "Indian": ["turmeric", "garam masala", "coconut milk", "curry leaves", "ginger"],
            "Italian": ["basil", "parmesan", "tomatoes", "garlic", "olive oil", "pasta"],
        }
        
        base_ingredients = cuisine_ingredients.get(cuisine, ["herbs", "spices", "vegetables"])
        dietary_restrictions = user_preferences.get('dietaryRestrictions', []) if user_preferences else []
        
        # Filter ingredients based on dietary restrictions
        if 'vegan' in dietary_restrictions:
            base_ingredients = [ing for ing in base_ingredients if ing not in ['parmesan', 'cheese']]
        
        recipe_title = f"{technique.title()} {cuisine} Bowl"
        
        return {
            'id': f"ai_cuisine_{hash(recipe_title)}_{int(datetime.now().timestamp())}",
            'title': recipe_title,
            'summary': f"Authentic {cuisine} flavors using {technique} cooking technique",
            'cuisine': [cuisine],
            'diets': dietary_restrictions,
            'readyInMinutes': 35,
            'servings': 4,
            'difficulty': 'Medium',
            'ingredients': self._generate_ingredients_list(base_ingredients, dietary_restrictions),
            'instructions': self._generate_cooking_instructions([technique], base_ingredients),
            'nutritionalHighlights': ["Traditional flavors", "Balanced nutrition"],
            'tags': [cuisine.lower(), technique, 'authentic'],
            'source': 'AI Generated',
            'generatedAt': datetime.now().isoformat(),
            'generationType': 'cuisine_based',
            'image': self._generate_recipe_image_url(recipe_title)
        }
    
    def _generate_ingredients_list(self, base_ingredients: List[str], dietary_restrictions: List[str]) -> List[Dict[str, Any]]:
        """Generate detailed ingredients list"""
        ingredients = []
        
        for ingredient in base_ingredients[:6]:  # Limit to 6 main ingredients
            amount = random.choice(["1", "2", "1/2", "1/4", "3"])
            unit = random.choice(["cup", "tbsp", "tsp", "cloves", "pieces"])
            
            ingredients.append({
                "name": ingredient,
                "amount": amount,
                "unit": unit
            })
        
        # Add common ingredients
        ingredients.extend([
            {"name": "salt", "amount": "to taste", "unit": ""},
            {"name": "black pepper", "amount": "to taste", "unit": ""},
            {"name": "cooking oil", "amount": "2", "unit": "tbsp"}
        ])
        
        return ingredients
    
    def _generate_cooking_instructions(self, techniques: List[str], ingredients: List[str]) -> List[str]:
        """Generate cooking instructions"""
        instructions = [
            "Prepare all ingredients by washing and chopping as needed.",
            f"Heat cooking oil in a large pan suitable for {techniques[0]}.",
            f"Add the main ingredients and {techniques[0]} for 5-7 minutes.",
            "Season with salt, pepper, and additional spices to taste.",
            "Continue cooking until ingredients are tender and flavors are well combined.",
            "Adjust seasoning if needed and serve hot."
        ]
        
        return instructions
    
    def _generate_nutritional_highlights(self, trend: str, ingredients: List[str]) -> List[str]:
        """Generate nutritional benefits"""
        highlights = []
        
        if "plant-based" in trend:
            highlights.extend(["High in plant protein", "Rich in fiber"])
        if "healthy" in trend:
            highlights.extend(["Low in saturated fat", "Nutrient dense"])
        if any(veg in ingredients for veg in ["vegetables", "herbs", "greens"]):
            highlights.append("Rich in vitamins and minerals")
        
        # Add generic benefits if none found
        if not highlights:
            highlights = ["Balanced nutrition", "Fresh ingredients", "Wholesome meal"]
        
        return highlights[:3]  # Limit to 3 highlights
    
    def _generate_trend_title(self, trend: str, cuisine: str, ingredients: List[str]) -> str:
        """Generate creative recipe title"""
        titles = [
            f"{cuisine} {trend.title()} Bowl",
            f"Modern {trend} with {cuisine} Twist",
            f"{cuisine}-Inspired {trend}",
            f"Healthy {cuisine} {trend}",
            f"Creative {trend} - {cuisine} Style"
        ]
        
        return random.choice(titles)
    
    def _generate_recipe_image_url(self, title: str) -> str:
        """Generate a placeholder image URL based on recipe title"""
        # Use food-related stock photo services
        base_urls = [
            "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=400",  # Food
            "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400",  # Cooking
            "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400",  # Healthy food
            "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400",  # Bowl food
        ]
        
        return random.choice(base_urls)
    
    def _is_duplicate(self, recipe: Dict[str, Any], existing_recipes: List[Dict[str, Any]]) -> bool:
        """Check if recipe is duplicate"""
        recipe_title = recipe.get('title', '').lower()
        for existing in existing_recipes:
            if recipe_title == existing.get('title', '').lower():
                return True
        return False
    
    def _generate_seasonal_recipe(self, ingredients: List[str], cuisine: str, season: str) -> Dict[str, Any]:
        """Generate recipe using seasonal ingredients"""
        title = f"Seasonal {season.title()} {cuisine} with {ingredients[0].title()}"
        
        return {
            'id': f"ai_seasonal_{hash(title)}_{int(datetime.now().timestamp())}",
            'title': title,
            'summary': f"Fresh {season} recipe featuring {', '.join(ingredients)}",
            'cuisine': [cuisine],
            'diets': [],
            'readyInMinutes': 30,
            'servings': 4,
            'difficulty': 'Medium',
            'ingredients': self._generate_ingredients_list(ingredients, []),
            'instructions': self._generate_cooking_instructions(["seasonal cooking"], ingredients),
            'nutritionalHighlights': ["Seasonal produce", "Fresh ingredients", "Nutrient-rich"],
            'tags': [season, cuisine.lower(), 'seasonal'],
            'source': 'AI Generated',
            'generatedAt': datetime.now().isoformat(),
            'generationType': 'seasonal',
            'image': self._generate_recipe_image_url(title),
            'season': season
        }
    
    def _generate_recipe_variation(self, base_recipe: Dict[str, Any], user_preferences: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Generate a variation of an existing recipe"""
        if not base_recipe:
            return None
        
        # Create variation by modifying technique or ingredients
        variation_types = ["technique", "ingredient", "cuisine_fusion"]
        variation_type = random.choice(variation_types)
        
        new_recipe = base_recipe.copy()
        new_recipe['id'] = f"ai_var_{hash(base_recipe['title'])}_{int(datetime.now().timestamp())}"
        
        if variation_type == "technique":
            new_technique = random.choice(self.cooking_techniques)
            new_recipe['title'] = f"{new_technique.title()} {base_recipe['title']}"
            
        elif variation_type == "ingredient":
            new_recipe['title'] = f"Alternative {base_recipe['title']}"
            
        elif variation_type == "cuisine_fusion":
            new_cuisine = random.choice(self.cuisine_styles)
            new_recipe['title'] = f"{new_cuisine} {base_recipe['title']}"
            new_recipe['cuisine'] = [new_cuisine]
        
        new_recipe['generationType'] = f"variation_{variation_type}"
        new_recipe['baseRecipe'] = base_recipe['id']
        
        return new_recipe
    
    def _generate_personalized_cuisine_recipe(self, cuisine: str, dietary_restrictions: List[str], 
                                            cooking_skill: str, max_time: str, health_goals: List[str]) -> Dict[str, Any]:
        """Generate highly personalized recipe for specific cuisine"""
        
        # Adjust complexity based on cooking skill
        difficulty_map = {"beginner": "Easy", "intermediate": "Medium", "expert": "Hard"}
        difficulty = difficulty_map.get(cooking_skill, "Medium")
        
        # Adjust time based on max_time
        time_value = 30  # default
        if "15" in max_time:
            time_value = 15
        elif "45" in max_time:
            time_value = 45
        elif "60" in max_time:
            time_value = 60
        
        title = f"Personalized {cuisine} {health_goals[0] if health_goals else 'Healthy'} Recipe"
        
        return {
            'id': f"ai_personal_{hash(title)}_{int(datetime.now().timestamp())}",
            'title': title,
            'summary': f"Customized {cuisine} recipe for your preferences and {cooking_skill} skill level",
            'cuisine': [cuisine],
            'diets': dietary_restrictions,
            'readyInMinutes': time_value,
            'servings': 4,
            'difficulty': difficulty,
            'ingredients': self._generate_ingredients_list([cuisine.lower()], dietary_restrictions),
            'instructions': self._generate_cooking_instructions([f"{cooking_skill} cooking"], []),
            'nutritionalHighlights': health_goals[:3] if health_goals else ["Balanced nutrition"],
            'tags': [cuisine.lower(), cooking_skill, 'personalized'],
            'source': 'AI Generated',
            'generatedAt': datetime.now().isoformat(),
            'generationType': 'personalized',
            'image': self._generate_recipe_image_url(title),
            'personalizedFor': {
                'cookingSkill': cooking_skill,
                'maxTime': max_time,
                'healthGoals': health_goals,
                'dietaryRestrictions': dietary_restrictions
            }
        }
    
    def _generate_health_focused_recipe(self, health_goal: str, dietary_restrictions: List[str], 
                                      cooking_skill: str, max_time: str) -> Dict[str, Any]:
        """Generate recipe focused on specific health goals"""
        
        health_ingredients = {
            "Weight loss": ["lean protein", "vegetables", "whole grains", "healthy fats"],
            "Heart health": ["omega-3 rich fish", "nuts", "berries", "leafy greens"],
            "Energy boost": ["complex carbs", "B vitamins", "iron-rich foods"],
            "Immune support": ["vitamin C foods", "garlic", "ginger", "turmeric"],
            "General wellness": ["colorful vegetables", "whole foods", "lean proteins"]
        }
        
        ingredients = health_ingredients.get(health_goal, health_ingredients["General wellness"])
        title = f"{health_goal} Focused Healthy Bowl"
        
        return {
            'id': f"ai_health_{hash(title)}_{int(datetime.now().timestamp())}",
            'title': title,
            'summary': f"Nutritious recipe designed to support {health_goal.lower()}",
            'cuisine': ["Healthy"],
            'diets': dietary_restrictions,
            'readyInMinutes': 25,
            'servings': 4,
            'difficulty': 'Easy',
            'ingredients': self._generate_ingredients_list(ingredients, dietary_restrictions),
            'instructions': self._generate_cooking_instructions(["healthy cooking"], ingredients),
            'nutritionalHighlights': [health_goal, "Nutrient dense", "Whole foods"],
            'tags': ['healthy', health_goal.lower().replace(' ', '-'), 'wellness'],
            'source': 'AI Generated',
            'generatedAt': datetime.now().isoformat(),
            'generationType': 'health_focused',
            'image': self._generate_recipe_image_url(title),
            'healthFocus': health_goal
        }
    
    def _parse_generated_text_to_recipe(self, text: str, trend: str) -> Dict[str, Any]:
        """Parse free-form generated text into structured recipe"""
        # This is a simplified parser - could be enhanced with NLP
        title = f"AI Generated {trend.title()} Recipe"
        
        return {
            'id': f"ai_parsed_{hash(title)}_{int(datetime.now().timestamp())}",
            'title': title,
            'summary': text[:100] + "..." if len(text) > 100 else text,
            'cuisine': ["International"],
            'diets': [],
            'readyInMinutes': 30,
            'servings': 4,
            'difficulty': 'Medium',
            'ingredients': [{"name": "mixed ingredients", "amount": "as needed", "unit": ""}],
            'instructions': [text],
            'nutritionalHighlights': ["AI generated", "Creative"],
            'tags': [trend, 'ai-generated'],
            'source': 'AI Generated',
            'generatedAt': datetime.now().isoformat(),
            'generationType': 'text_parsed',
            'image': self._generate_recipe_image_url(title),
            'rawGeneratedText': text
        } 