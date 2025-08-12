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