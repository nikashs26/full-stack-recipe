import requests
import time
import json
from backend.services.recipe_cache_service import RecipeCacheService

# Initialize ChromaDB service
recipe_cache = RecipeCacheService()

# TheMealDB API endpoints
MEALDB_LIST_URL = "https://www.themealdb.com/api/json/v1/1/filter.php?a={area}"
MEALDB_LOOKUP_URL = "https://www.themealdb.com/api/json/v1/1/lookup.php?i={id}"

# Cuisines to fetch
CUISINES = [
    "Italian", "Chinese", "Mexican", "Indian", "French", 
    "Thai", "Japanese", "American", "Spanish", "Moroccan", 
    "Greek", "Turkish"
]

def detect_cuisine_from_recipe(recipe):
    """Detect cuisine from recipe details and map to country"""
    if not isinstance(recipe, dict):
        return 'american'  # Default fallback
    
    # Map of cuisines to their countries
    CUISINE_TO_COUNTRY = {
        # Italian
        'italian': 'italian', 'tuscan': 'italian', 'sicilian': 'italian', 'roman': 'italian',
        'venetian': 'italian', 'neapolitan': 'italian', 'lombard': 'italian',
        
        # Asian
        'chinese': 'chinese', 'sichuan': 'chinese', 'cantonese': 'chinese', 'hunan': 'chinese',
        'japanese': 'japanese', 'korean': 'korean', 'thai': 'thai', 'vietnamese': 'vietnamese',
        'indian': 'indian', 'punjabi': 'indian', 'south indian': 'indian', 'bengali': 'indian',
        'indonesian': 'indonesian', 'malaysian': 'malaysian', 'filipino': 'filipino',
        
        # European
        'french': 'french', 'provencal': 'french', 'spanish': 'spanish', 'catalan': 'spanish',
        'german': 'german', 'greek': 'greek', 'portuguese': 'portuguese', 'british': 'british',
        'irish': 'irish', 'scottish': 'scottish', 'swedish': 'swedish', 'norwegian': 'norwegian',
        'danish': 'danish', 'dutch': 'dutch', 'belgian': 'belgian', 'swiss': 'swiss',
        'austrian': 'austrian', 'russian': 'russian', 'polish': 'polish', 'hungarian': 'hungarian',
        
        # American
        'american': 'american', 'southern': 'american', 'cajun': 'american', 'creole': 'american',
        'soul food': 'american', 'tex-mex': 'american', 'southwestern': 'american',
        
        # Latin American
        'mexican': 'mexican', 'caribbean': 'caribbean', 'jamaican': 'jamaican',
        'brazilian': 'brazilian', 'peruvian': 'peruvian', 'argentinian': 'argentinian',
        'cuban': 'cuban', 'puerto rican': 'puerto rican',
        
        # Middle Eastern/African
        'moroccan': 'moroccan', 'lebanese': 'lebanese', 'turkish': 'turkish', 'israeli': 'israeli',
        'egyptian': 'egyptian', 'ethiopian': 'ethiopian', 'south african': 'south african',
        
        # Other
        'australian': 'australian', 'new zealand': 'new zealand'
    }
    
    # Map of ingredients to their most likely country
    INGREDIENT_TO_COUNTRY = {
        # Italian
        'pasta': 'italian', 'risotto': 'italian', 'prosciutto': 'italian', 'parmesan': 'italian',
        'mozzarella': 'italian', 'basil': 'italian', 'oregano': 'italian', 'pesto': 'italian',
        
        # Mexican
        'taco': 'mexican', 'tortilla': 'mexican', 'salsa': 'mexican', 'guacamole': 'mexican',
        'queso': 'mexican', 'cilantro': 'mexican', 'jalapeno': 'mexican', 'enchilada': 'mexican',
        
        # Chinese
        'soy sauce': 'chinese', 'hoisin': 'chinese', 'szechuan': 'chinese', 'wok': 'chinese',
        'stir-fry': 'chinese', 'dumpling': 'chinese', 'bok choy': 'chinese',
        
        # Indian
        'curry': 'indian', 'masala': 'indian', 'tikka': 'indian', 'naan': 'indian',
        'samosas': 'indian', 'tandoori': 'indian', 'garam masala': 'indian',
        
        # Thai
        'thai': 'thai', 'lemongrass': 'thai', 'fish sauce': 'thai', 'pad thai': 'thai',
        'kaeng': 'thai', 'tom yum': 'thai', 'thai basil': 'thai',
        
        # Japanese
        'sushi': 'japanese', 'ramen': 'japanese', 'miso': 'japanese', 'wasabi': 'japanese',
        'teriyaki': 'japanese', 'tempura': 'japanese', 'dashi': 'japanese',
        
        # French
        'baguette': 'french', 'brie': 'french', 'provençal': 'french', 'ratatouille': 'french',
        'béchamel': 'french', 'au vin': 'french', 'coq au vin': 'french',
        
        # Greek
        'feta': 'greek', 'tzatziki': 'greek', 'gyro': 'greek', 'dolma': 'greek',
        'moussaka': 'greek', 'kalamata': 'greek',
        
        # Spanish
        'paella': 'spanish', 'chorizo': 'spanish', 'saffron': 'spanish', 'tapas': 'spanish',
        'manchego': 'spanish', 'gazpacho': 'spanish',
        
        # Vietnamese
        'pho': 'vietnamese', 'banh mi': 'vietnamese', 'fish sauce': 'vietnamese',
        'lemongrass': 'vietnamese', 'rice paper': 'vietnamese', 'hoisin': 'vietnamese',
        
        # Korean
        'kimchi': 'korean', 'gochujang': 'korean', 'bulgogi': 'korean', 'bibimbap': 'korean',
        'korean bbq': 'korean', 'soju': 'korean',
        
        # American
        'burger': 'american', 'hot dog': 'american', 'barbecue': 'american',
        'mac and cheese': 'american', 'apple pie': 'american', 'buffalo wings': 'american'
    }
    
    # Safely get text to analyze
    def safe_get(d, key, default=''):
        value = d.get(key, default)
        return str(value).lower() if value is not None else ''
    
    # Build text from recipe fields
    text_parts = [
        safe_get(recipe, 'strMeal'),
        safe_get(recipe, 'strInstructions'),
        safe_get(recipe, 'strArea', '')
    ]
    
    # Add ingredients
    for i in range(1, 21):
        ingredient = safe_get(recipe, f'strIngredient{i}')
        if ingredient and ingredient != 'none' and ingredient != '':
            text_parts.append(ingredient)
    
    text = ' '.join(text_parts)
    
    # First, check if we have a direct cuisine match in the recipe's area or cuisine field
    if 'strArea' in recipe and recipe['strArea']:
        area = recipe['strArea'].lower()
        if area in CUISINE_TO_COUNTRY:
            return CUISINE_TO_COUNTRY[area]
    
    # Check if we have a cuisine field that maps to a country
    if 'strTags' in recipe and recipe['strTags']:
        tags = [t.strip().lower() for t in recipe['strTags'].split(',')]
        for tag in tags:
            if tag in CUISINE_TO_COUNTRY:
                return CUISINE_TO_COUNTRY[tag]
    
    # Analyze ingredients and recipe name to determine cuisine
    text_lower = text.lower()
    cuisine_scores = {}
    
    # Check for ingredient matches
    for ingredient, country in INGREDIENT_TO_COUNTRY.items():
        if ingredient in text_lower:
            cuisine_scores[country] = cuisine_scores.get(country, 0) + 1
    
    # Check for cuisine name matches in the recipe text
    for cuisine, country in CUISINE_TO_COUNTRY.items():
        if cuisine in text_lower and cuisine != country:  # Avoid double counting
            cuisine_scores[country] = cuisine_scores.get(country, 0) + 2  # Higher weight for direct matches
    
    # If we found matches, return the most likely country
    if cuisine_scores:
        best_match = max(cuisine_scores.items(), key=lambda x: x[1])
        return best_match[0]
    
    # If we still don't have a match, look for any country name in the recipe text
    country_names = set(CUISINE_TO_COUNTRY.values())
    for country in country_names:
        if f' {country} ' in f' {text_lower} ':
            return country
    
    # Final fallback to american if we can't determine the cuisine
    return 'american'

def normalize_recipe(recipe):
    """Normalize recipe data for storage"""
    # Detect cuisine from recipe details
    detected_cuisine = detect_cuisine_from_recipe(recipe)
    
    normalized = {
        'id': recipe['idMeal'],
        'title': recipe['strMeal'],
        'cuisine': detected_cuisine,
        'image': recipe['strMealThumb'],
        'instructions': recipe['strInstructions'],
        'ingredients': [],
        'cuisines': [detected_cuisine],
        'diets': [],
        'readyInMinutes': 30  # Default value
    }
    
    # Extract ingredients
    for i in range(1, 21):
        ingredient = recipe.get(f'strIngredient{i}')
        measure = recipe.get(f'strMeasure{i}')
        if ingredient and ingredient.strip():
            normalized['ingredients'].append({
                'name': ingredient.strip(),
                'amount': measure.strip() if measure else ''
            })
    
    # Infer dietary restrictions
    ingredients_lower = [ing['name'].lower() for ing in normalized['ingredients']]
    if not any(meat in ' '.join(ingredients_lower) for meat in ['chicken', 'beef', 'pork', 'fish', 'meat']):
        normalized['diets'].append('vegetarian')
    
    return normalized

def fetch_recipes_by_cuisine(cuisine, max_per_cuisine=100):
    """Fetch recipes for a specific cuisine with enhanced cuisine detection"""
    print(f"Fetching recipes for {cuisine} cuisine...")
    recipes = []
    
    try:
        # First try to fetch by area (more reliable)
        response = requests.get(MEALDB_LIST_URL.format(area=cuisine))
        data = response.json()
        
        if data and 'meals' in data and data['meals']:
            # Limit the number of recipes per cuisine
            for meal in data['meals'][:max_per_cuisine]:
                try:
                    # Get full recipe details
                    meal_detail = requests.get(MEALDB_LOOKUP_URL.format(id=meal['idMeal'])).json()
                    if meal_detail and 'meals' in meal_detail and meal_detail['meals']:
                        recipe = meal_detail['meals'][0]
                        # Add cuisine info if not present
                        if 'strArea' in recipe and not recipe['strArea']:
                            recipe['strArea'] = cuisine
                        recipes.append(recipe)
                except Exception as e:
                    print(f"Error fetching recipe {meal.get('idMeal')}: {e}")
                    continue
                    
    except Exception as e:
        print(f"Error fetching {cuisine} recipes: {e}")
    
    print(f"Found {len(recipes)} recipes for {cuisine}")
    return recipes

def fetch_and_store_recipes():
    """Fetch recipes from TheMealDB and store in ChromaDB"""
    all_recipes = []
    
    # Fetch recipes for each cuisine
    for cuisine in CUISINES:
        recipes = fetch_recipes_by_cuisine(cuisine, max_per_cuisine=100)
        all_recipes.extend(recipes)
        
    # Remove duplicates by recipe ID
    unique_recipes = {recipe['idMeal']: recipe for recipe in all_recipes}.values()
    print(f"Total unique recipes: {len(unique_recipes)}")
    
    # Normalize and cache recipes
    normalized_recipes = [normalize_recipe(recipe) for recipe in unique_recipes]
    
    # Cache all recipes
    if normalized_recipes:
        recipe_cache.cache_recipes(normalized_recipes)
        print(f"Successfully cached {len(normalized_recipes)} recipes")
    else:
        print("No recipes to cache")

if __name__ == "__main__":
    fetch_and_store_recipes()