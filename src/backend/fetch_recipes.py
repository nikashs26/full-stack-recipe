import os
import json
import time
import requests
import re
from dotenv import load_dotenv
from services.recipe_cache_service import RecipeCacheService

# Load environment variables
load_dotenv()

# Initialize ChromaDB
recipe_cache = RecipeCacheService()

# Spoonacular API configuration
SPOONACULAR_API_KEY = os.getenv('SPOONACULAR_API_KEY', 'fe61cea1027f4164a8fbf96fe54fdbb4')
BASE_URL = 'https://api.spoonacular.com/recipes'

def parse_instructions(instructions_text: str) -> list:
    """Parse recipe instructions into individual steps"""
    if not instructions_text:
        return ['No instructions provided.']
    
    # Clean up the instructions - preserve original structure but normalize whitespace
    instructions_text = instructions_text.replace('\r\n', '\n').replace('\r', '\n')
    
    # First, try to split by actual numbered steps (e.g., "1.", "1)", "Step 1:")
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

def format_instructions(recipe_data):
    """Format recipe instructions properly"""
    # First try to use analyzedInstructions if available (Spoonacular's structured format)
    if recipe_data.get('analyzedInstructions') and isinstance(recipe_data['analyzedInstructions'], list):
        instructions = []
        for instruction_set in recipe_data['analyzedInstructions']:
            if instruction_set.get('steps') and isinstance(instruction_set['steps'], list):
                for step in instruction_set['steps']:
                    if step.get('step'):
                        instructions.append(step['step'].strip())
        
        if instructions:
            return instructions
    
    # Fallback to parsing the instructions field
    if recipe_data.get('instructions'):
        return parse_instructions(recipe_data['instructions'])
    
    return ['No instructions provided.']

def fetch_recipes_from_spoonacular(limit=500):
    """Fetch recipes from Spoonacular API with comprehensive details"""
    print(f"\nFetching {limit} recipes from Spoonacular API...")
    
    # First, get recipe IDs with basic info
    search_url = f"{BASE_URL}/complexSearch"
    params = {
        'apiKey': SPOONACULAR_API_KEY,
        'number': limit,
        'addRecipeInformation': 'true',
        'fillIngredients': 'true',
        'instructionsRequired': 'true',
        'addRecipeNutrition': 'true',
        'sort': 'popularity',
        'sortDirection': 'desc'
    }
    
    try:
        # Get list of recipes with basic info
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'results' not in data or not data['results']:
            print("No recipes found in the response")
            return []
            
        recipes = []
        total_recipes = len(data['results'])
        print(f"Found {total_recipes} recipes. Fetching detailed information...")
        
        # Process each recipe to get detailed information
        for i, recipe in enumerate(data['results'], 1):
            try:
                recipe_id = recipe['id']
                print(f"\nProcessing recipe {i}/{total_recipes}: ID {recipe_id}")
                
                # Get detailed recipe information
                detail_url = f"{BASE_URL}/{recipe_id}/information"
                detail_params = {
                    'apiKey': SPOONACULAR_API_KEY,
                    'includeNutrition': 'true'
                }
                
                detail_response = requests.get(detail_url, params=detail_params)
                detail_response.raise_for_status()
                detailed_recipe = detail_response.json()
                
                # Format instructions properly
                instructions = format_instructions(detailed_recipe)
                
                # Extract and format recipe data
                formatted_recipe = {
                    'id': str(detailed_recipe['id']),
                    'title': detailed_recipe.get('title', 'Untitled Recipe'),
                    'image': detailed_recipe.get('image', ''),
                    'servings': detailed_recipe.get('servings', 2),
                    'readyInMinutes': detailed_recipe.get('readyInMinutes', 30),
                    'sourceUrl': detailed_recipe.get('sourceUrl', ''),
                    'sourceName': detailed_recipe.get('sourceName', ''),
                    'summary': detailed_recipe.get('summary', ''),
                    'cuisines': detailed_recipe.get('cuisines', []),
                    'diets': detailed_recipe.get('diets', []),
                    'dishTypes': detailed_recipe.get('dishTypes', []),
                    'instructions': instructions,  # Use properly formatted instructions
                    'ingredients': [
                        {
                            'id': ing.get('id'),
                            'name': ing.get('name', '').lower(),
                            'amount': ing.get('measures', {}).get('metric', {}).get('amount', 0),
                            'unit': ing.get('measures', {}).get('metric', {}).get('unitShort', ''),
                            'original': ing.get('original', '')
                        }
                        for ing in detailed_recipe.get('extendedIngredients', [])
                    ],
                    'nutrition': {
                        'calories': next(
                            (n['amount'] for n in detailed_recipe.get('nutrition', {}).get('nutrients', [])
                             if n['name'] == 'Calories'), 0
                        ),
                        'protein': next(
                            (n['amount'] for n in detailed_recipe.get('nutrition', {}).get('nutrients', [])
                             if n['name'] == 'Protein'), 0
                        ),
                        'carbs': next(
                            (n['amount'] for n in detailed_recipe.get('nutrition', {}).get('nutrients', [])
                             if n['name'] == 'Carbohydrates'), 0
                        ),
                        'fat': next(
                            (n['amount'] for n in detailed_recipe.get('nutrition', {}).get('nutrients', [])
                             if n['name'] == 'Fat'), 0
                        )
                    },
                    'analyzedInstructions': detailed_recipe.get('analyzedInstructions', [])
                }
                
                recipes.append(formatted_recipe)
                print(f"✅ Processed: {formatted_recipe['title']}")
                
                # Be nice to the API - add a small delay between requests
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error processing recipe {recipe_id}: {str(e)}")
                continue
                
        return recipes
        
    except Exception as e:
        print(f"Error fetching recipes: {str(e)}")
        return []

def store_recipes_in_chromadb(recipes):
    """Store recipes in ChromaDB"""
    if not recipes:
        print("No recipes to store")
        return
    
    print(f"\nStoring {len(recipes)} recipes in ChromaDB...")
    
    try:
        # Check existing recipes to avoid duplicates
        print("Checking existing recipes in cache...")
        existing_recipes = recipe_cache.get_all_recipes()
        existing_ids = set()
        
        if existing_recipes:
            for recipe in existing_recipes:
                if isinstance(recipe, dict) and 'id' in recipe:
                    existing_ids.add(str(recipe['id']))
            print(f"Found {len(existing_ids)} existing recipes in cache")
        
        # Filter out recipes that already exist
        new_recipes = []
        duplicate_count = 0
        
        for recipe in recipes:
            recipe_id = str(recipe['id'])
            if recipe_id in existing_ids:
                duplicate_count += 1
                continue
            new_recipes.append(recipe)
        
        if duplicate_count > 0:
            print(f"Skipping {duplicate_count} duplicate recipes")
        
        if not new_recipes:
            print("No new recipes to add - all recipes already exist in cache")
            return
        
        print(f"Adding {len(new_recipes)} new recipes to cache...")
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        search_texts = []
        
        for recipe in new_recipes:
            recipe_id = str(recipe['id'])
            ids.append(recipe_id)
            
            # Store the full recipe as a JSON string
            documents.append(json.dumps(recipe))
            
            # Create metadata
            metadata = {
                'id': recipe_id,
                'title': recipe['title'],
                'cuisine': recipe['cuisines'][0] if recipe.get('cuisines') else 'International',
                'diet': recipe['diets'][0] if recipe.get('diets') else 'None',
                'calories': recipe.get('nutrition', {}).get('calories', 0),
                'readyInMinutes': recipe.get('readyInMinutes', 30),
                'ingredients_count': len(recipe.get('ingredients', [])),
                'cached_at': str(int(time.time()))
            }
            metadatas.append(metadata)
            
            # Create search text
            search_terms = [
                recipe['title'],
                *[ing['name'] for ing in recipe.get('ingredients', [])],
                *recipe.get('cuisines', []),
                *recipe.get('diets', []),
                *recipe.get('dishTypes', [])
            ]
            search_text = ' '.join(filter(None, search_terms)).lower()
            search_texts.append(search_text)
        
        # Store in recipe collection
        recipe_cache.recipe_collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        # Store in search collection
        recipe_cache.search_collection.upsert(
            ids=ids,
            documents=search_texts,
            metadatas=metadatas
        )
        
        print(f"✓ Successfully added {len(new_recipes)} new recipes to ChromaDB")
        
    except Exception as e:
        print(f"Error storing recipes in ChromaDB: {str(e)}")
        raise

def main():
    print("Starting recipe import process...")
    
    # Fetch recipes from Spoonacular
    recipes = fetch_recipes_from_spoonacular(limit=500)
    
    if recipes:
        # Store recipes in ChromaDB
        store_recipes_in_chromadb(recipes)
        
        # Verify the count
        count = len(recipe_cache.recipe_collection.get()['documents'])
        print(f"\nTotal recipes in ChromaDB: {count}")
    else:
        print("No recipes were fetched. Please check the API key and try again.")

if __name__ == "__main__":
    main()
