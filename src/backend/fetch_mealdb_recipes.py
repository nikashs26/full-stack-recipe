import requests
from services.recipe_cache_service import RecipeCacheService

# Initialize ChromaDB
recipe_cache = RecipeCacheService()

# TheMealDB API endpoints
MEALDB_SEARCH_URL = "https://www.themealdb.com/api/json/v1/1/search.php"
MEALDB_LOOKUP_URL = "https://www.themealdb.com/api/json/v1/1/lookup.php"
MEALDB_LIST_AREAS = "https://www.themealdb.com/api/json/v1/1/list.php?a=list"

def get_meal_areas():
    """Get all available cuisine areas from TheMealDB"""
    response = requests.get(MEALDB_LIST_AREAS)
    if response.ok:
        areas = [area['strArea'] for area in response.json().get('meals', [])]
        return areas
    return ["American", "British", "Canadian", "Chinese", "French", "Indian", "Italian", "Japanese", "Mexican", "Spanish"]

def search_mealdb_recipes(search_term=None, cuisine=None, limit=12):
    """Search for recipes in TheMealDB"""
    try:
        # First, get all recipes for the cuisine (if specified)
        if cuisine and cuisine.lower() != 'all':
            response = requests.get(f"{MEALDB_SEARCH_URL}?a={cuisine}")
        # Or search by term if provided
        elif search_term:
            response = requests.get(f"{MEALDB_SEARCH_URL}?s={search_term}")
        # Otherwise, get random recipes
        else:
            response = requests.get("https://www.themealdb.com/api/json/v1/1/random.php")
            
        if not response.ok:
            print(f"Error fetching recipes: {response.status_code}")
            return []
            
        meals = response.json().get('meals', [])
        if not meals:
            return []
            
        # Limit results
        meals = meals[:limit]
        
        # Get detailed information for each recipe
        recipes = []
        for meal in meals:
            recipe = {
                'id': f"mealdb_{meal['idMeal']}",
                'title': meal['strMeal'],
                'cuisine': meal.get('strArea', 'International'),
                'cuisines': [meal.get('strArea', 'International')],
                'image': meal['strMealThumb'],
                'instructions': meal['strInstructions'].split('\r\n') if meal.get('strInstructions') else [],
                'ingredients': [],
                'diets': [],
                'source': 'themealdb',
                'type': 'spoonacular'  # Using spoonacular type for compatibility with existing frontend
            }
            
            # Extract ingredients and measures
            for i in range(1, 21):
                ingredient = meal.get(f'strIngredient{i}')
                measure = meal.get(f'strMeasure{i}')
                if ingredient and ingredient.strip():
                    recipe['ingredients'].append({
                        'name': ingredient.strip(),
                        'amount': measure.strip() if measure else '',
                        'unit': ''
                    })
            
            recipes.append(recipe)
            
        return recipes
        
    except Exception as e:
        print(f"Error in search_mealdb_recipes: {str(e)}")
        return []

def store_recipes_in_chromadb(recipes):
    """Store recipes in ChromaDB"""
    if not recipes:
        return False
        
    try:
        # Prepare documents and metadata for ChromaDB
        documents = []
        metadatas = []
        
        for recipe in recipes:
            # Create a searchable text
            text = f"{recipe['title']} {recipe.get('cuisine', '')} {' '.join(recipe.get('ingredients', []))}"
            
            # Prepare metadata
            metadata = {
                'id': recipe['id'],
                'title': recipe['title'],
                'cuisine': recipe.get('cuisine', ''),
                'image': recipe.get('image', ''),
                'source': 'themealdb',
                'type': 'spoonacular'  # For compatibility with existing frontend
            }
            
            documents.append(text)
            metadatas.append(metadata)
        
        # Add to ChromaDB
        recipe_cache.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=[recipe['id'] for recipe in recipes]
        )
        
        print(f"Successfully stored {len(recipes)} recipes in ChromaDB")
        return True
        
    except Exception as e:
        print(f"Error storing recipes in ChromaDB: {str(e)}")
        return False

def search_and_store_recipes(search_term=None, cuisine=None, limit=12):
    """Search for recipes and store them in ChromaDB"""
    recipes = search_mealdb_recipes(search_term, cuisine, limit)
    if recipes:
        return store_recipes_in_chromadb(recipes)
    return False

if __name__ == "__main__":
    # Example usage
    search_term = input("Enter search term (or press Enter for random recipes): ").strip()
    cuisine = input("Enter cuisine (or press Enter for all): ").strip() or None
    
    if search_term or cuisine:
        search_and_store_recipes(search_term, cuisine)
    else:
        print("Please provide either a search term or cuisine")
