import json
from services.recipe_cache_service import RecipeCacheService

# Improved dietary tagging logic
MEAT_INDICATORS = [
    'chicken', 'beef', 'pork', 'lamb', 'fish', 'salmon', 'tuna', 'shrimp', 'prawn', 'meat', 'bacon', 'ham', 'sausage',
    'turkey', 'duck', 'goose', 'venison', 'rabbit', 'quail', 'pheasant', 'veal', 'mackerel', 'haddock', 'clam'
]
ANIMAL_INDICATORS = [
    'milk', 'cheese', 'butter', 'cream', 'egg', 'yogurt', 'honey', 'gelatin', 'lard', 'tallow', 'whey', 'casein',
    'parmesan', 'pecorino', 'mascarpone', 'creme fraiche', 'sour cream', 'condensed milk'
]
GLUTEN_INDICATORS = [
    'flour', 'bread', 'pasta', 'wheat', 'barley', 'rye', 'malt', 'semolina', 'couscous', 'bulgur',
    'spaghetti', 'linguine', 'penne', 'rigatoni', 'fettuccine', 'macaroni', 'muffins', 'buns', 'tortillas'
]
DAIRY_INDICATORS = [
    'milk', 'cheese', 'butter', 'cream', 'yogurt', 'whey', 'casein', 'lactose',
    'parmesan', 'pecorino', 'mascarpone', 'creme fraiche', 'sour cream', 'condensed milk'
]
NUT_INDICATORS = [
    'almond', 'peanut', 'walnut', 'cashew', 'pecan', 'hazelnut', 'pistachio', 'macadamia', 'brazil nut', 'pine nut',
    'cashew nuts', 'peanuts'
]

def infer_diets(ingredients):
    ingredient_names = [ing['name'].lower() for ing in ingredients]
    ingredient_text = ' '.join(ingredient_names)
    diets = []
    
    # Check for meat
    has_meat = any(meat in ingredient_text for meat in MEAT_INDICATORS)
    
    # Check for animal products (but exclude flax eggs which are vegan)
    animal_indicators_filtered = [indicator for indicator in ANIMAL_INDICATORS if indicator != 'egg']
    has_animal_products = any(animal in ingredient_text for animal in animal_indicators_filtered)
    
    # Special case: if recipe has "flax eggs" or "flaxseed", it's likely vegan
    has_flax_eggs = 'flax' in ingredient_text
    if has_flax_eggs:
        has_animal_products = False
    
    # Check for gluten
    has_gluten = any(gluten in ingredient_text for gluten in GLUTEN_INDICATORS)
    
    # Check for dairy
    has_dairy = any(dairy in ingredient_text for dairy in DAIRY_INDICATORS)
    
    # Check for nuts
    has_nuts = any(nut in ingredient_text for nut in NUT_INDICATORS)
    
    # Apply dietary restrictions
    if not has_meat:
        diets.append('vegetarian')
    
    if not has_meat and not has_animal_products:
        diets.append('vegan')
    
    if not has_gluten:
        diets.append('gluten-free')
    
    if not has_dairy:
        diets.append('dairy-free')
    
    if not has_nuts:
        diets.append('nut-free')
    
    return diets

def main():
    recipe_cache = RecipeCacheService()
    results = recipe_cache.recipe_collection.get(include=["documents", "metadatas"])
    
    print(f"Found {len(results['documents'])} recipes in ChromaDB")
    
    # First, let's see what recipes we have
    print("\n=== All Recipes in ChromaDB ===")
    for i, doc in enumerate(results["documents"]):
        try:
            recipe = json.loads(doc)
            title = recipe.get('title', recipe.get('name', 'Untitled'))
            current_diets = recipe.get('diets', [])
            print(f"{i+1}. {title} - Current diets: {current_diets}")
        except Exception as e:
            print(f"Error parsing recipe {i+1}: {e}")
    
    print("\n=== Processing Updates ===")
    updated_count = 0
    for doc, meta in zip(results["documents"], results["metadatas"]):
        try:
            recipe = json.loads(doc)
            title = recipe.get('title', recipe.get('name', 'Untitled'))
            ingredients = recipe.get('ingredients', [])
            
            if not ingredients:
                print(f"Skipping {title}: No ingredients found")
                continue
                
            new_diets = infer_diets(ingredients)
            current_diets = recipe.get('diets', [])
            
            print(f"Processing {title}:")
            print(f"  Current diets: {current_diets}")
            print(f"  New diets: {new_diets}")
            print(f"  Ingredients: {[ing['name'] for ing in ingredients[:5]]}...")
            
            if set(current_diets) != set(new_diets):
                recipe['diets'] = new_diets
                # Upsert updated recipe
                recipe_cache.recipe_collection.upsert(
                    ids=[str(recipe['id'])],
                    documents=[json.dumps(recipe)],
                    metadatas=[meta]
                )
                updated_count += 1
                print(f"  ✅ Updated {title}: {new_diets}")
            else:
                print(f"  ⏭️  No change needed for {title}")
                
        except Exception as e:
            print(f"Error processing recipe: {e}")
    
    print(f"\nUpdated dietary tags for {updated_count} recipes.")

if __name__ == "__main__":
    main() 