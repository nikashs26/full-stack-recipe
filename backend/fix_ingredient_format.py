#!/usr/bin/env python3
"""
Fix Ingredient Format in Database

This script converts the complex Spoonacular ingredient format to a simple
format that the frontend can display properly without showing [object Object].
"""

import chromadb
import json
from datetime import datetime

def fix_ingredient_format():
    """Fix ingredient format in the database"""
    
    print("🔧 Fixing ingredient format in database...")
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('recipe_details_cache')
        
        total_recipes = collection.count()
        print(f"📊 Total recipes in ChromaDB: {total_recipes}")
        
        # Get all recipes
        results = collection.get(limit=total_recipes)
        
        # Track changes
        recipes_updated = 0
        ingredients_fixed = 0
        
        for i, (recipe_id, metadata, document) in enumerate(zip(
            results['ids'], results['metadatas'], results['documents']
        )):
            if i % 100 == 0:
                print(f"   Processed {i}/{total_recipes} recipes...")
            
            recipe = json.loads(document)
            ingredients = recipe.get('ingredients', [])
            
            if not ingredients:
                continue
            
            # Check if ingredients need fixing
            needs_fixing = False
            for ing in ingredients:
                if isinstance(ing, dict) and 'amount' in ing and isinstance(ing['amount'], dict):
                    needs_fixing = True
                    break
            
            if not needs_fixing:
                continue
            
            # Fix ingredients
            fixed_ingredients = []
            for ing in ingredients:
                if isinstance(ing, dict):
                    name = ing.get('name', 'Unknown')
                    amount = ing.get('amount')
                    unit = ing.get('unit', '')
                    
                    # Handle complex amount structure
                    if isinstance(amount, dict):
                        # Prefer US measurements, fallback to metric
                        if 'us' in amount and 'value' in amount['us']:
                            amount_value = amount['us']['value']
                            unit = amount['us'].get('unit', unit)
                        elif 'metric' in amount and 'value' in amount['metric']:
                            amount_value = amount['metric']['value']
                            unit = amount['metric'].get('unit', unit)
                        else:
                            amount_value = None
                    else:
                        amount_value = amount
                    
                    # Format the ingredient
                    if amount_value is not None and unit:
                        formatted_amount = f"{amount_value} {unit}".strip()
                    elif amount_value is not None:
                        formatted_amount = str(amount_value)
                    else:
                        formatted_amount = ""
                    
                    fixed_ingredients.append({
                        "name": name,
                        "amount": formatted_amount,
                        "unit": unit
                    })
                    
                    ingredients_fixed += 1
                else:
                    # Keep string ingredients as-is
                    fixed_ingredients.append(ing)
            
            # Update the recipe
            recipe['ingredients'] = fixed_ingredients
            recipe['updated_at'] = datetime.now().isoformat()
            recipe['ingredients_formatted'] = True
            
            # Update in ChromaDB
            collection.update(
                ids=[recipe_id],
                documents=[json.dumps(recipe)],
                metadatas=[metadata]
            )
            
            recipes_updated += 1
        
        # Summary
        print(f"\n🎉 Ingredient format fixing completed!")
        print(f"   Recipes updated: {recipes_updated}")
        print(f"   Ingredients fixed: {ingredients_fixed}")
        print(f"   Total recipes processed: {total_recipes}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    fix_ingredient_format()
