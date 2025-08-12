import requests
from services.recipe_cache_service import RecipeCacheService
from typing import List
import re
import logging

logger = logging.getLogger(__name__)

# Initialize ChromaDB
recipe_cache = RecipeCacheService()

# TheMealDB API endpoints
MEALDB_SEARCH_URL = "https://www.themealdb.com/api/json/v1/1/search.php"
MEALDB_LOOKUP_URL = "https://www.themealdb.com/api/json/v1/1/lookup.php"
MEALDB_LIST_AREAS = "https://www.themealdb.com/api/json/v1/1/list.php?a=list"

def parse_instructions(instructions_text: str) -> List[str]:
    """Parse recipe instructions into individual steps"""
    if not instructions_text:
        return ['No instructions provided.']
    
    # Clean up the instructions - preserve original structure but normalize whitespace
    instructions_text = instructions_text.replace('\r\n', '\n').replace('\r', '\n')
    
    # First, try to split by actual numbered steps (e.g., "1.", "1)", "Step 1:")
    import re
    
    # Look for actual step numbers at the beginning of lines or after periods
    # This pattern is more conservative and won't split on measurements
    step_pattern = r'(?:\n\s*\d+[.)]|\A\s*\d+[.)])'
    
    # Split by the step pattern
    raw_steps = re.split(f'({step_pattern})', instructions_text, flags=re.MULTILINE)
    
    # Clean up the split results
    steps = []
    current_step = ''
    
    for i, part in enumerate(raw_steps):
        part = part.strip()
        if not part:
            continue
            
        # If this part is a step number/indicator
        if re.match(f'^{step_pattern}$', part, flags=re.MULTILINE):
            if current_step:  # Save the previous step if exists
                steps.append(current_step.strip())
            current_step = part + ' '  # Start new step with the number
        else:
            current_step += part + ' '
    
    # Add the last step if it exists
    if current_step.strip():
        steps.append(current_step.strip())
    
    # If we couldn't split by numbers, try other methods
    if len(steps) <= 1:
        # Try splitting by double newlines first (preserve natural paragraph breaks)
        steps = [s.strip() for s in instructions_text.split('\n\n') if s.strip()]
        
        # If that doesn't work, try splitting by single newlines that look like step separators
        if len(steps) <= 1:
            # Look for newlines that are followed by capital letters (likely new steps)
            steps = [s.strip() for s in re.split(r'\n(?=\s*[A-Z])', instructions_text) if s.strip()]
    
    # Clean up each step - remove leading numbers and normalize
    cleaned_steps = []
    for step in steps:
        if step:
            # Remove leading step numbers
            cleaned_step = re.sub(r'^\s*\d+[.)]?\s*', '', step).strip()
            if cleaned_step:
                # Normalize whitespace within the step
                cleaned_step = ' '.join(cleaned_step.split())
                cleaned_steps.append(cleaned_step)
    
    # If we still don't have multiple steps, try to split by cooking action keywords
    if len(cleaned_steps) <= 1 and instructions_text:
        # Look for common cooking instruction patterns that indicate new steps
        cooking_keywords = [
            'preheat', 'heat', 'add', 'stir', 'mix', 'combine', 'pour', 'bake', 'cook', 'fry',
            'grill', 'roast', 'boil', 'simmer', 'season', 'salt', 'pepper', 'drain', 'remove',
            'serve', 'garnish', 'decorate', 'cool', 'chill', 'refrigerate', 'freeze', 'place',
            'transfer', 'return', 'bring', 'lower', 'cover', 'uncover', 'flip', 'turn'
        ]
        
        # Split by sentences that contain cooking keywords
        sentences = re.split(r'[.!?]+', instructions_text)
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 15:  # Only meaningful sentences
                # Check if sentence contains cooking keywords
                if any(keyword in sentence.lower() for keyword in cooking_keywords):
                    cleaned_steps.append(sentence)
    
    # If all else fails, try to split by periods that end sentences
    if len(cleaned_steps) <= 1:
        # More intelligent sentence splitting that doesn't break on measurements
        # Look for periods followed by space and capital letter, but avoid breaking on measurements
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z][a-z])', instructions_text)
        cleaned_steps = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
    
    # Ensure we have at least one step
    if not cleaned_steps:
        cleaned_steps = [instructions_text.strip()]
    
    return cleaned_steps

async def fetch_all_meals():
    """Fetch all meals from TheMealDB"""
    all_meals = []
    base_url = "https://www.themealdb.com/api/json/v1/1"

    # Fetch meals by category
    categories = [
        "Beef", "Chicken", "Dessert", "Lamb", "Miscellaneous", 
        "Pasta", "Pork", "Seafood", "Side", "Starter", "Vegan", "Vegetarian"
    ]
    
    for category in categories:
        try:
            response = requests.get(f"{base_url}/filter.php?c={category}")
            response.raise_for_status()
            data = response.json()
            
            if data.get('meals'):
                # Fetch detailed info for each meal
                for meal in data['meals'][:5]:  # Limit to 5 meals per category
                    try:
                        meal_response = requests.get(f"{base_url}/lookup.php?i={meal['idMeal']}")
                        meal_response.raise_for_status()
                        meal_data = meal_response.json()
                        
                        if meal_data.get('meals') and meal_data['meals'][0]:
                            meal_info = meal_data['meals'][0]
                            
                            # Parse instructions properly
                            if meal_info.get('strInstructions'):
                                instructions = parse_instructions(meal_info['strInstructions'])
                            else:
                                instructions = []
                            
                            meal_info['instructions'] = instructions
                            all_meals.append(meal_info)
                            
                    except Exception as e:
                        logger.error(f"Error fetching meal {meal['idMeal']}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error fetching category {category}: {e}")
            continue
    
    logger.info(f"Total meals fetched: {len(all_meals)}")
    return all_meals

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
