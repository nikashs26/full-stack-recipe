#!/usr/bin/env python3
"""
Remove fake/generic ingredients from recipes
"""

import chromadb
import json
from datetime import datetime

def remove_fake_ingredients():
    """Remove fake/generic ingredients from recipes"""
    
    print("🧹 Removing fake/generic ingredients from recipes...")
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('recipe_details_cache')
        
        total_recipes = collection.count()
        print(f"📊 Total recipes in ChromaDB: {total_recipes}")
        
        # Get all recipes
        results = collection.get(limit=total_recipes)
        
        # Track changes
        recipes_cleaned = 0
        recipes_skipped = 0
        
        # Generic patterns to identify fake ingredients
        generic_patterns = [
            'salt to taste',
            'black pepper to taste', 
            '2 tablespoons olive oil',
            'to taste',
            'pieces',
            'medium',
            'cloves'
        ]
        
        print("\n📋 Analyzing and cleaning recipe ingredients...")
        
        for i, doc in enumerate(results['documents']):
            try:
                recipe = json.loads(doc)
                title = recipe.get('title', 'Unknown')
                ingredients = recipe.get('ingredients', [])
                recipe_id = recipe.get('id', 'unknown')
                
                if not ingredients:
                    continue
                
                # Check if ingredients look generic
                generic_count = 0
                for ing in ingredients:
                    if isinstance(ing, dict):
                        original = ing.get('original', '').lower()
                        name = ing.get('name', '').lower()
                        
                        # Check for generic patterns
                        for pattern in generic_patterns:
                            if pattern in original or pattern in name:
                                generic_count += 1
                                break
                        
                        # Check for very generic measurements
                        if ing.get('measure') in ['to taste', 'pieces', 'medium']:
                            generic_count += 1
                
                # If more than 50% of ingredients are generic, remove them
                if generic_count > len(ingredients) * 0.5:
                    print(f"🧹 Cleaning fake ingredients from: {title}")
                    
                    # Remove ingredients and add note
                    recipe['ingredients'] = []
                    recipe['updated_at'] = datetime.utcnow().isoformat()
                    recipe['metadata'] = recipe.get('metadata', {})
                    recipe['metadata']['ingredients_removed'] = True
                    recipe['metadata']['ingredients_removal_reason'] = 'fake_generic_ingredients'
                    recipe['metadata']['ingredients_removal_date'] = datetime.now().isoformat()
                    
                    # Add a note about missing ingredients
                    if 'notes' not in recipe:
                        recipe['notes'] = []
                    recipe['notes'].append("Ingredients data is missing from the original source. Please check the original recipe for accurate ingredient information.")
                    
                    # Update in ChromaDB
                    updated_doc = json.dumps(recipe)
                    collection.update(
                        ids=[recipe_id],
                        documents=[updated_doc],
                        metadatas=[extract_metadata(recipe)]
                    )
                    
                    recipes_cleaned += 1
                else:
                    recipes_skipped += 1
                
                # Progress indicator
                if (i + 1) % 100 == 0:
                    print(f"   Processed {i + 1}/{total_recipes} recipes...")
                    
            except Exception as e:
                print(f"Error processing recipe {i}: {e}")
        
        print("\n" + "=" * 60)
        print("🧹 FAKE INGREDIENT REMOVAL COMPLETED")
        print("=" * 60)
        print(f"Total recipes processed: {total_recipes}")
        print(f"✅ Recipes cleaned (fake ingredients removed): {recipes_cleaned}")
        print(f"⏭️  Recipes skipped (already had real ingredients): {recipes_skipped}")
        
        if recipes_cleaned > 0:
            print(f"\n💡 What was done:")
            print(f"   - Removed generic ingredients like 'salt to taste', 'black pepper to taste'")
            print(f"   - Added notes explaining that ingredient data is missing")
            print(f"   - Updated metadata to track the cleaning process")
            print(f"\n🔑 Next steps:")
            print(f"   - Get a Spoonacular API key to fetch real ingredients")
            print(f"   - Or investigate original recipe sources")
            print(f"   - Users will now see 'No ingredients' instead of fake data")
        
        return {
            'total_recipes': total_recipes,
            'recipes_cleaned': recipes_cleaned,
            'recipes_skipped': recipes_skipped
        }
        
    except Exception as e:
        print(f"❌ Error cleaning recipes: {e}")
        return None

def extract_metadata(recipe):
    """Extract metadata for ChromaDB"""
    try:
        # Extract cuisines
        cuisines = recipe.get('cuisines', [])
        if isinstance(cuisines, str):
            cuisines = [c.strip() for c in cuisines.split(',') if c.strip()]
        
        # Extract ingredients for metadata
        ingredients = []
        if recipe.get('ingredients'):
            for ing in recipe['ingredients']:
                if isinstance(ing, dict) and 'name' in ing:
                    ingredients.append(ing['name'])
                elif isinstance(ing, str):
                    ingredients.append(ing)
        
        metadata = {
            "id": recipe.get('id', ''),
            "title": recipe.get('title', ''),
            "cuisine": cuisines[0] if cuisines else 'Other',
            "cuisines": ','.join(cuisines) if cuisines else '',
            "ingredients": ','.join(ingredients) if ingredients else '',
            "cached_at": datetime.now().isoformat(),
            "source": recipe.get('source', 'unknown'),
        }
        
        # Add optional fields
        if recipe.get('tags'):
            metadata["tags"] = ','.join(recipe['tags'])
        
        return metadata
        
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return {}

if __name__ == "__main__":
    remove_fake_ingredients()
