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
    """Parse recipe instructions into individual steps with intelligent splitting"""
    if not instructions_text:
        return ['No instructions provided.']
    
    # Clean up the instructions - preserve original structure but normalize whitespace
    instructions_text = instructions_text.replace('\r\n', '\n').replace('\r', '\n')
    
    # First, try to find actual numbered steps that are clearly recipe steps
    # Look for patterns like "1.", "1)", "Step 1:", etc. at the beginning of lines
    # But avoid splitting on measurements like "1 tablespoon", "2 minutes", etc.
    
    # More intelligent step detection - look for step numbers that are followed by cooking actions
    # and not by measurements or ingredient amounts
    step_pattern = r'(?:\n\s*|^)\s*(\d+)[.)]\s*(?=[A-Z][a-z]+)'
    
    # Find all potential step numbers and their positions
    step_matches = list(re.finditer(step_pattern, instructions_text, re.MULTILINE))
    
    if len(step_matches) > 1:
        # We found multiple step numbers, split on them
        steps = []
        last_end = 0
        
        for match in step_matches:
            step_num = match.group(1)
            step_start = match.start()
            
            # Get the text from the last step to this one
            if step_start > last_end:
                step_text = instructions_text[last_end:step_start].strip()
                if step_text:
                    steps.append(step_text)
            
            # Start new step with the step number
            last_end = step_start
        
        # Add the last step
        if last_end < len(instructions_text):
            last_step = instructions_text[last_end:].strip()
            if last_step:
                steps.append(last_step)
        
        # Clean up steps
        cleaned_steps = []
        for step in steps:
            if step:
                # Remove leading step numbers and clean up
                cleaned_step = re.sub(r'^\s*\d+[.)]?\s*', '', step).strip()
                if cleaned_step:
                    # Normalize whitespace within the step
                    cleaned_step = ' '.join(cleaned_step.split())
                    cleaned_steps.append(cleaned_step)
        
        if cleaned_steps:
            return cleaned_steps
    
    # If we couldn't find clear step numbers, try other methods
    # Try splitting by double newlines first (preserve natural paragraph breaks)
    steps = [s.strip() for s in instructions_text.split('\n\n') if s.strip()]
    
    if len(steps) > 1:
        # Clean up and return
        return [' '.join(step.split()) for step in steps if step.strip()]
    
    # Try splitting by single newlines that look like step separators
    # Look for newlines that are followed by capital letters (likely new steps)
    steps = [s.strip() for s in re.split(r'\n(?=\s*[A-Z])', instructions_text) if s.strip()]
    
    if len(steps) > 1:
        # Clean up and return
        return [' '.join(step.split()) for step in steps if step.strip()]
    
    # If all else fails, try intelligent sentence splitting
    # Split by periods that end sentences, but avoid breaking on measurements
    # Look for periods followed by space and capital letter
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z][a-z])', instructions_text)
    cleaned_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and len(sentence) > 20:  # Only meaningful sentences
            # Clean up whitespace
            cleaned_sentence = ' '.join(sentence.split())
            cleaned_sentences.append(cleaned_sentence)
    
    if len(cleaned_sentences) > 1:
        return cleaned_sentences
    
    # If we still can't split meaningfully, return the original text as a single step
    return [' '.join(instructions_text.split())]

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
