#!/usr/bin/env python3
"""
Script to integrate existing nutrition analysis results into ChromaDB
This will make all the analyzed nutrition data available to the frontend
"""

import chromadb
import json
import os
from datetime import datetime

def integrate_nutrition_results():
    """Integrate nutrition analysis results into ChromaDB collection"""
    
    print("🔧 Integrating nutrition analysis results into ChromaDB...")
    
    # Load the nutrition analysis results
    nutrition_file = "nutrition_analysis_results_1333_recipes.json"
    if not os.path.exists(nutrition_file):
        print(f"❌ Nutrition analysis file not found: {nutrition_file}")
        print("💡 Make sure you're running this from the backend directory")
        return
    
    print(f"📊 Loading nutrition data from: {nutrition_file}")
    
    with open(nutrition_file, 'r') as f:
        nutrition_data = json.load(f)
    
    print(f"✅ Loaded {nutrition_data['total_recipes']} nutrition records")
    print(f"📈 Success rate: {nutrition_data['success_rate']*100:.1f}%")
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path="../chroma_db")
    recipe_collection = client.get_collection("recipe_details_cache")
    
    print(f"📊 Total recipes in ChromaDB: {recipe_collection.count()}")
    
    # Get all recipes from ChromaDB
    results = recipe_collection.get(include=['documents', 'metadatas'])
    
    if not results['documents']:
        print("❌ No recipes found in ChromaDB")
        return
    
    # Create a lookup dictionary for nutrition data
    nutrition_lookup = {}
    for recipe in nutrition_data['results']:
        if recipe['status'] == 'success':
            # Try multiple ID formats for matching
            recipe_id = recipe['recipe_id']
            nutrition_lookup[recipe_id] = recipe['nutrition']
            
            # Also try without prefix for matching
            if recipe_id.startswith('mealdb_'):
                short_id = recipe_id[7:]  # Remove 'mealdb_' prefix
                nutrition_lookup[short_id] = recipe['nutrition']
            elif recipe_id.startswith('spoonacular_'):
                short_id = recipe_id[12:]  # Remove 'spoonacular_' prefix
                nutrition_lookup[short_id] = recipe['nutrition']
    
    print(f"🔍 Created nutrition lookup with {len(nutrition_lookup)} entries")
    
    # Track statistics
    updated_count = 0
    not_found_count = 0
    already_updated_count = 0
    
    # Process each recipe in ChromaDB
    for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
        try:
            recipe_id = meta.get('id', f'recipe_{i}')
            recipe_title = meta.get('title', f'Recipe {i}')
            
            # Check if we already have nutrition data
            if (meta.get('calories', 0) != 0 and 
                meta.get('protein', 0) != 0 and 
                meta.get('carbs', 0) != 0 and 
                meta.get('fat', 0) != 0):
                already_updated_count += 1
                continue
            
            # Try to find nutrition data for this recipe
            nutrition = None
            
            # Try exact ID match first
            if recipe_id in nutrition_lookup:
                nutrition = nutrition_lookup[recipe_id]
            else:
                # Try to find by title (case-insensitive)
                title_lower = recipe_title.lower()
                for n_id, n_data in nutrition_lookup.items():
                    # This is a simple title matching - could be enhanced
                    if title_lower in n_id.lower() or n_id.lower() in title_lower:
                        nutrition = n_data
                        break
            
            if nutrition:
                print(f"🍽️  Updating nutrition for: {recipe_title}")
                
                calories = nutrition.get('calories', 0)
                protein = nutrition.get('protein', 0)
                carbs = nutrition.get('carbohydrates', 0)
                fat = nutrition.get('fat', 0)
                
                # Update metadata
                updated_metadata = meta.copy()
                updated_metadata.update({
                    'calories': calories,
                    'protein': protein,
                    'carbs': carbs,
                    'fat': fat,
                    'nutrition_integrated': True,
                    'nutrition_integrated_at': datetime.now().isoformat()
                })
                
                # Update document
                try:
                    if doc and doc.strip():
                        recipe_doc = json.loads(doc)
                    else:
                        recipe_doc = {}
                    
                    # Add nutrition data to the recipe document
                    recipe_doc['nutrition'] = {
                        'calories': calories,
                        'protein': protein,
                        'carbohydrates': carbs,
                        'fat': fat
                    }
                    
                    # Also add top-level fields for direct access
                    recipe_doc['calories'] = calories
                    recipe_doc['protein'] = protein
                    recipe_doc['carbs'] = carbs
                    recipe_doc['fat'] = fat
                    
                    # Add macrosPerServing for RecipeCard compatibility
                    recipe_doc['macrosPerServing'] = {
                        'calories': calories,
                        'protein': protein,
                        'carbs': carbs,
                        'fat': fat
                    }
                    
                    updated_doc = json.dumps(recipe_doc)
                    
                except Exception as e:
                    # If parsing fails, create simple document
                    updated_doc = json.dumps({
                        'title': recipe_title,
                        'nutrition': {
                            'calories': calories,
                            'protein': protein,
                            'carbohydrates': carbs,
                            'fat': fat
                        },
                        'calories': calories,
                        'protein': protein,
                        'carbs': carbs,
                        'fat': fat,
                        'macrosPerServing': {
                            'calories': calories,
                            'protein': protein,
                            'carbs': carbs,
                            'fat': fat
                        }
                    })
                
                # Update the recipe in ChromaDB
                recipe_collection.update(
                    ids=[recipe_id],
                    documents=[updated_doc],
                    metadatas=[updated_metadata]
                )
                
                print(f"   ✅ Updated: {calories} cal, {protein}g protein, {carbs}g carbs, {fat}g fat")
                updated_count += 1
                
            else:
                not_found_count += 1
                if not_found_count <= 5:  # Only show first few for brevity
                    print(f"   ❓ No nutrition data found for: {recipe_title}")
                
        except Exception as e:
            print(f"   ❌ Error updating recipe {i}: {e}")
            continue
    
    # Print summary
    print(f"\n" + "="*50)
    print(f"📋 INTEGRATION COMPLETE")
    print(f"="*50)
    print(f"📊 Results:")
    print(f"   ✅ Updated: {updated_count} recipes")
    print(f"   🔄 Already had nutrition: {already_updated_count} recipes")
    print(f"   ❓ No nutrition data found: {not_found_count} recipes")
    print(f"   📈 Total processed: {updated_count + already_updated_count + not_found_count}")
    
    if updated_count > 0:
        print(f"\n🎉 Successfully integrated nutrition data for {updated_count} recipes!")
        print(f"💡 Your app should now show varied, realistic macro values instead of defaults")
        print(f"🔍 Check your app - recipes should display different nutrition values!")
    else:
        print(f"\n⚠️  No recipes were updated. This might mean:")
        print(f"   - All recipes already have nutrition data")
        print(f"   - The nutrition analysis results don't match your current recipes")
        print(f"   - There's a mismatch in recipe IDs between the analysis and ChromaDB")

if __name__ == "__main__":
    integrate_nutrition_results() 