import requests
import json
import time
from flask import Flask, jsonify
from flask_cors import CORS
from services.recipe_cache_service import RecipeCacheService
from typing import List
import re

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize ChromaDB
recipe_cache = RecipeCacheService()

# TheMealDB API endpoints
MEALDB_LOOKUP_URL = "https://www.themealdb.com/api/json/v1/1/lookup.php?i={id}"

# Recipe IDs from TheMealDB - mix of meat and vegetarian recipes
RECIPE_IDS = ["52772", "52959", "53013", "53016", "53022", "53025", "53026", "53027", "53028", "53029"]

def parse_instructions(instructions_text: str) -> List[str]:
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
                    cleaned_step = ' '.join(step.split())
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

@app.route('/recipes', methods=['GET'])
def get_recipes():
    """Endpoint to get all recipes"""
    try:
        results = recipe_cache.recipe_collection.get(
            include=["documents", "metadatas"]
        )
        recipes = []
        if results and results["documents"]:
            for doc in results["documents"]:
                try:
                    recipe = json.loads(doc)
                    recipes.append(recipe)
                except:
                    pass
        return jsonify({"results": recipes})
    except Exception as e:
        print(f"Error fetching recipes: {e}")
        return jsonify({"results": [], "error": str(e)})

def add_test_recipes():
    """Add test recipes to ChromaDB"""
    for recipe_id in RECIPE_IDS:
        print(f"\nFetching recipe {recipe_id}...")
        
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
                'diets': []
            }
            
            # Infer dietary restrictions based on ingredients
            ingredient_names = [ing['name'].lower() for ing in ingredients]
            ingredient_text = ' '.join(ingredient_names)
            diets = []
            
            # Check for vegetarian (no meat, fish, or poultry)
            meat_indicators = ['chicken', 'beef', 'pork', 'lamb', 'fish', 'salmon', 'tuna', 'shrimp', 'prawn', 'meat', 'bacon', 'ham', 'sausage', 'turkey', 'duck', 'goose', 'venison', 'rabbit', 'quail', 'pheasant']
            has_meat = any(meat in ingredient_text for meat in meat_indicators)
            if not has_meat:
                diets.append('vegetarian')
                print(f"  ✅ Added vegetarian tag for: {recipe['title']}")
            
            # Check for vegan (no animal products)
            animal_indicators = ['milk', 'cheese', 'butter', 'cream', 'egg', 'yogurt', 'honey', 'gelatin', 'lard', 'tallow', 'whey', 'casein']
            has_animal_products = any(animal in ingredient_text for animal in animal_indicators)
            if not has_meat and not has_animal_products:
                diets.append('vegan')
                print(f"  ✅ Added vegan tag for: {recipe['title']}")
            
            # Check for gluten-free
            gluten_indicators = ['flour', 'bread', 'pasta', 'wheat', 'barley', 'rye', 'malt', 'semolina', 'couscous', 'bulgur']
            has_gluten = any(gluten in ingredient_text for gluten in gluten_indicators)
            if not has_gluten:
                diets.append('gluten-free')
                print(f"  ✅ Added gluten-free tag for: {recipe['title']}")
            
            # Check for dairy-free
            dairy_indicators = ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'whey', 'casein', 'lactose']
            has_dairy = any(dairy in ingredient_text for dairy in dairy_indicators)
            if not has_dairy:
                diets.append('dairy-free')
                print(f"  ✅ Added dairy-free tag for: {recipe['title']}")
            
            # Check for nut-free
            nut_indicators = ['almond', 'peanut', 'walnut', 'cashew', 'pecan', 'hazelnut', 'pistachio', 'macadamia', 'brazil nut', 'pine nut']
            has_nuts = any(nut in ingredient_text for nut in nut_indicators)
            if not has_nuts:
                diets.append('nut-free')
                print(f"  ✅ Added nut-free tag for: {recipe['title']}")
            
            print(f"  📋 Dietary tags for {recipe['title']}: {diets}")
            recipe['diets'] = diets
            
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
    # Clear existing data
    try:
        recipe_cache.clear_cache()
        print("Cleared existing cache")
    except:
        pass
    
    # Add test recipes
    add_test_recipes()
    
    # Verify recipes were added
    try:
        results = recipe_cache.recipe_collection.get()
        print(f"\nFound {len(results['documents'])} recipes in ChromaDB:")
        for doc in results['documents']:
            recipe = json.loads(doc)
            print(f"- {recipe['title']} ({recipe['cuisine']})")
    except Exception as e:
        print(f"Error checking recipes: {e}")
    
    print("\nStarting server on http://localhost:8000")
    print("You can now access the recipes in the frontend")
    app.run(host='localhost', port=8000, debug=True) 