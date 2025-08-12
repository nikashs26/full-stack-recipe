import requests
import time
import json
import chromadb
from chromadb.utils import embedding_functions

# Initialize ChromaDB directly
client = chromadb.PersistentClient(path="./chroma_db")
embedding_function = embedding_functions.DefaultEmbeddingFunction()

# Get or create the recipe collection
recipe_collection = client.get_or_create_collection(
    name="recipe_details_cache",
    metadata={"description": "Cache for individual recipe details"},
    embedding_function=embedding_function
)

# TheMealDB API endpoints
MEALDB_LIST_URL = "https://www.themealdb.com/api/json/v1/1/filter.php?a={area}"
MEALDB_LOOKUP_URL = "https://www.themealdb.com/api/json/v1/1/lookup.php?i={id}"

# Cuisines to fetch (expanded to get more recipes)
CUISINES = [
    "Italian", "Chinese", "Mexican", "Indian", "French", 
    "Thai", "Japanese", "American", "Spanish", "Moroccan", 
    "Greek", "Turkish", "British", "Irish", "Caribbean",
    "Vietnamese", "Korean", "Indonesian", "Malaysian", "Filipino"
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
    }
    
    # Combine all text for analysis
    text_parts = []
    if recipe.get('strMeal'):
        text_parts.append(recipe['strMeal'].lower())
    if recipe.get('strInstructions'):
        text_parts.append(recipe['strInstructions'].lower())
    if recipe.get('strArea'):
        text_parts.append(recipe['strArea'].lower())
    
    text_lower = ' '.join(text_parts)
    
    # Score cuisines based on ingredient matches
    cuisine_scores = {}
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
            # Get more recipes per cuisine to reach the target of 1,200
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
                        if len(recipes) <= 10:  # Only show first 10 to avoid spam
                            print(f"  - {recipe['strMeal']}")
                        elif len(recipes) == 11:
                            print(f"  ... and {len(data['meals']) - 10} more")
                except Exception as e:
                    print(f"Error fetching recipe {meal.get('idMeal')}: {e}")
                    continue
                    
    except Exception as e:
        print(f"Error fetching {cuisine} recipes: {e}")
    
    print(f"Found {len(recipes)} recipes for {cuisine}")
    return recipes

def add_recipe_to_chroma(recipe):
    """Add a recipe directly to ChromaDB"""
    try:
        # Create document text for embedding
        doc_text = f"{recipe['title']} {recipe.get('cuisine', '')} {' '.join([ing['name'] for ing in recipe.get('ingredients', [])])}"
        
        # Convert lists to strings for ChromaDB compatibility
        diets_str = ', '.join(recipe.get('diets', [])) if recipe.get('diets') else ''
        
        # Add to collection
        recipe_collection.add(
            documents=[doc_text],
            metadatas=[{
                'id': recipe['id'],
                'title': recipe['title'],
                'cuisine': recipe['cuisine'],
                'image': recipe.get('image', ''),
                'diets': diets_str,
                'readyInMinutes': recipe.get('readyInMinutes', 30)
            }],
            ids=[recipe['id']]
        )
        return True
    except Exception as e:
        print(f"Error adding recipe {recipe['id']}: {e}")
        return False

def fetch_and_store_recipes():
    """Fetch recipes from TheMealDB and store in ChromaDB"""
    all_recipes = []
    
    # Fetch recipes for each cuisine
    for cuisine in CUISINES:
        recipes = fetch_recipes_by_cuisine(cuisine, max_per_cuisine=20)
        all_recipes.extend(recipes)
        time.sleep(1)  # Be nice to the API
        
    # Remove duplicates by recipe ID
    unique_recipes = {recipe['idMeal']: recipe for recipe in all_recipes}.values()
    print(f"Total unique recipes: {len(unique_recipes)}")
    
    # Normalize and store recipes
    successful = 0
    for recipe in unique_recipes:
        normalized = normalize_recipe(recipe)
        if add_recipe_to_chroma(normalized):
            successful += 1
    
    print(f"Successfully stored {successful} recipes in ChromaDB")
    return successful

if __name__ == "__main__":
    print("Starting recipe restoration...")
    print("This will fetch recipes from TheMealDB and restore them with proper tags")
    print("=" * 60)
    
    count = fetch_and_store_recipes()
    print(f"\n✅ Recipe restoration complete! Added {count} recipes with proper tags.")
    print("Your recipes should now be visible in the app with all the original formatting and tags.") 