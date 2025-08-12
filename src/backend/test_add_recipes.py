import requests
from services.recipe_cache_service import RecipeCacheService
from typing import List
import re

# Initialize ChromaDB
recipe_cache = RecipeCacheService()

# TheMealDB API endpoints
MEALDB_LOOKUP_URL = "https://www.themealdb.com/api/json/v1/1/lookup.php?i={id}"

# Two specific recipe IDs from TheMealDB
RECIPE_IDS = ["52772", "52959"]  # Teriyaki Chicken Casserole and Baked salmon with fennel & tomatoes

def parse_instructions(instructions_text: str) -> List[str]:
    """Parse recipe instructions into individual steps"""
    if not instructions_text:
        return ['No instructions provided.']
    
    # Clean up the instructions first
    instructions_text = ' '.join(instructions_text.split())  # Normalize whitespace
    
    # First try to split by actual step numbers (not just any number)
    # Look for numbers at the beginning of lines or after periods, but not in the middle of sentences
    step_pattern = r'(?:\b(?:Step\s*)?\d+[.)]|\n\s*\d+[.)]|\A\s*\d+[.)])'
    steps_pattern1 = re.split(f'({step_pattern})', instructions_text, flags=re.IGNORECASE | re.MULTILINE)
    
    # Clean up the split results
    steps = []
    current_step = ''
    
    for i, part in enumerate(steps_pattern1):
        part = part.strip()
        if not part:
            continue
            
        # If this part is a step number/indicator
        if re.match(f'^{step_pattern}$', part, flags=re.IGNORECASE | re.MULTILINE):
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
        # Try splitting by double newlines first
        steps = [s.strip() for s in instructions_text.split('\n\n') if s.strip()]
        
        # If that doesn't work, try splitting by periods that end a sentence
        if len(steps) <= 1:
            # More intelligent sentence splitting that doesn't break on measurements
            # Look for periods followed by space and capital letter, but avoid breaking on measurements
            sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z][a-z])', instructions_text)
            steps = [s for s in sentences if s.strip()]
    
    # Clean up each step
    steps = [re.sub(r'^\s*\d+[.)]?\s*', '', s).strip() for s in steps if s.strip()]
    
    # If we still don't have multiple steps, try to split by common cooking instruction keywords
    if len(steps) <= 1 and instructions_text:
        # Look for common cooking instruction patterns
        cooking_keywords = [
            'preheat', 'heat', 'add', 'stir', 'mix', 'combine', 'pour', 'bake', 'cook', 'fry',
            'grill', 'roast', 'boil', 'simmer', 'season', 'salt', 'pepper', 'drain', 'remove',
            'serve', 'garnish', 'decorate', 'cool', 'chill', 'refrigerate', 'freeze'
        ]
        
        # Split by sentences that contain cooking keywords
        sentences = re.split(r'[.!?]+', instructions_text)
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Only meaningful sentences
                # Check if sentence contains cooking keywords
                if any(keyword in sentence.lower() for keyword in cooking_keywords):
                    steps.append(sentence)
    
    # If all else fails, just split by periods and clean up
    if len(steps) <= 1:
        sentences = re.split(r'[.!?]+', instructions_text)
        steps = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    # Ensure we have at least one step
    if not steps:
        steps = [instructions_text.strip()]
    
    return steps

def fetch_and_store_recipes():
    """Fetch specific recipes and store them in ChromaDB"""
    
    for recipe_id in RECIPE_IDS:
        print(f"\nFetching recipe {recipe_id}...")
        
        # Get recipe from TheMealDB
        response = requests.get(MEALDB_LOOKUP_URL.format(id=recipe_id))
        if response.ok and response.json()['meals']:
            meal_data = response.json()['meals'][0]
            
            # Extract ingredients
            ingredients = []
            for i in range(1, 21):
                ingredient = meal_data.get(f'strIngredient{i}')
                measure = meal_data.get(f'strMeasure{i}')
                if ingredient and ingredient.strip():
                    ingredients.append({
                        'name': ingredient.strip(),
                        'amount': measure.strip() if measure else ''
                    })
            
            # Normalize recipe data
            recipe = {
                'id': meal_data['idMeal'],
                'title': meal_data['strMeal'],
                'cuisine': meal_data.get('strArea', 'International'),
                'cuisines': [meal_data.get('strArea', 'International')],
                'image': meal_data['strMealThumb'],
                'instructions': parse_instructions(meal_data['strInstructions']) if meal_data.get('strInstructions') else [],
                'ingredients': ingredients,
                'diets': []  # TheMealDB doesn't provide dietary info
            }
            
            # Store in ChromaDB
            recipe_id = str(recipe['id'])
            metadata = {
                "id": recipe_id,
                "title": recipe['title'],
                "cuisine": recipe['cuisine'],
                "cached_at": str(int(time.time()))
            }
            
            # Create search text
            search_terms = [
                recipe['title'],
                recipe['cuisine'],
                *[ing['name'] for ing in recipe['ingredients']]
            ]
            search_text = ' '.join(filter(None, search_terms))
            
            # Store in both collections
            recipe_cache.recipe_collection.upsert(
                ids=[recipe_id],
                documents=[json.dumps(recipe)],
                metadatas=[metadata]
            )
            
            recipe_cache.search_collection.upsert(
                ids=[recipe_id],
                documents=[search_text],
                metadatas=[metadata]
            )
            
            print(f"✅ Added recipe: {recipe['title']}")
        else:
            print(f"❌ Failed to fetch recipe {recipe_id}")

if __name__ == "__main__":
    import time
    import json
    
    print("Starting recipe import process...")
    
    # Clear existing data
    try:
        print("Clearing existing cache...")
        recipe_cache.clear_cache()
        print("✓ Cache cleared successfully")
    except Exception as e:
        print(f"⚠️ Error clearing cache: {e}")
    
    # Add new recipes
    print("\nAdding new recipes to ChromaDB...")
    fetch_and_store_recipes()
    
    # Verify recipes were added
    print("\nVerifying recipes in ChromaDB...")
    try:
        results = recipe_cache.recipe_collection.get()
        if not results or 'documents' not in results or not results['documents']:
            print("❌ No recipes found in ChromaDB")
        else:
            print(f"✓ Found {len(results['documents'])} recipes in ChromaDB:")
            for i, doc in enumerate(results['documents'], 1):
                try:
                    recipe = json.loads(doc)
                    print(f"\nRecipe {i}:")
                    print(f"  ID: {recipe.get('id', 'N/A')}")
                    print(f"  Title: {recipe.get('title', 'N/A')}")
                    print(f"  Cuisine: {recipe.get('cuisine', 'N/A')}")
                    print(f"  Ingredients: {len(recipe.get('ingredients', []))}")
                except json.JSONDecodeError as e:
                    print(f"  ❌ Error parsing recipe {i}: {e}")
                    print(f"  Raw document: {doc[:200]}...")
    except Exception as e:
        print(f"❌ Error querying ChromaDB: {e}")
    
    print("\nVerification complete!")
    
    # Print a summary of all recipes
    try:
        if results and 'documents' in results and results['documents']:
            print("\nSummary of all recipes in ChromaDB:")
            for doc in results['documents']:
                try:
                    recipe = json.loads(doc)
                    print(f"- {recipe.get('title', 'Untitled')} (ID: {recipe.get('id', 'N/A')}, Cuisine: {recipe.get('cuisine', 'N/A')})")
                except json.JSONDecodeError:
                    print("- [Error parsing recipe]")
    except Exception as e:
        print(f"Error generating recipe summary: {e}")