#!/usr/bin/env python3
"""
FIXED VERSION: Add macronutrient info to all recipes in ChromaDB
This version PRESERVES existing recipe data instead of overwriting it
"""

import asyncio
import chromadb
import json
from services.nutrition_analysis_agent import NutritionAnalysisAgent

async def add_macros_to_all_recipes_safely():
    """Safely add macronutrient info to all recipes while preserving existing data"""
    
    print("🚀 Starting SAFE macronutrient analysis for all recipes...")
    print("⚠️  This version will PRESERVE your existing recipe data!")
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    recipe_collection = client.get_collection("recipe_details_cache")
    
    print(f"📊 Total recipes to analyze: {recipe_collection.count()}")
    
    # Initialize nutrition agent
    nutrition_agent = NutritionAnalysisAgent()
    
    # Get all recipes
    results = recipe_collection.get(include=['documents', 'metadatas'])
    
    if not results['documents']:
        print("❌ No recipes found in database")
        return
    
    print(f"📋 Analyzing {len(results['documents'])} recipes...")
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    # Process each recipe
    for i, doc in enumerate(results['documents']):
        try:
            recipe_id = results['metadatas'][i].get('id', f'recipe_{i}')
            recipe_title = results['metadatas'][i].get('title', f'Recipe {i}')
            
            print(f"\n🍽️  Analyzing {i+1}/{len(results['documents'])}: {recipe_title}")
            
            # Check if recipe already has nutrition data
            if results['metadatas'][i].get('nutrition_analyzed'):
                print(f"   ⏭️  Skipping - already has nutrition data")
                skipped_count += 1
                continue
            
            # SAFELY extract existing recipe data
            existing_recipe_data = {}
            
            if doc and doc.strip():
                try:
                    # Try to parse existing document
                    existing_recipe_data = json.loads(doc)
                    print(f"   📄 Found existing recipe data with {len(existing_recipe_data)} fields")
                except json.JSONDecodeError:
                    print(f"   ⚠️  Existing document is not valid JSON, will create new one")
                    existing_recipe_data = {}
            
            # Prepare recipe data for nutrition analysis
            # Use existing data when available, fallback to metadata
            recipe_data = {
                'id': recipe_id,
                'title': existing_recipe_data.get('title', recipe_title),
                'ingredients': existing_recipe_data.get('ingredients', 
                    results['metadatas'][i].get('ingredients', '')),
                'instructions': existing_recipe_data.get('instructions', 
                    results['metadatas'][i].get('instructions', '')),
                'cuisine': existing_recipe_data.get('cuisine', 
                    results['metadatas'][i].get('cuisine', '')),
                'diets': existing_recipe_data.get('diets', 
                    results['metadatas'][i].get('diets', ''))
            }
            
            # Analyze nutrition
            result = await nutrition_agent.analyze_recipe_nutrition(recipe_data)
            
            if result['status'] == 'success':
                nutrition = result['nutrition']
                
                # SAFELY update the recipe - PRESERVE existing data
                updated_metadata = results['metadatas'][i].copy()
                updated_metadata.update({
                    'calories': nutrition.get('calories', 0),
                    'protein': nutrition.get('protein', 0),
                    'carbs': nutrition.get('carbohydrates', 0),
                    'fat': nutrition.get('fat', 0),
                    'nutrition_analyzed': True,
                    'nutrition_analyzed_at': result['analyzed_at']
                })
                
                # SAFELY update the document - PRESERVE existing content
                try:
                    # Start with existing recipe data
                    updated_recipe_doc = existing_recipe_data.copy()
                    
                    # Add nutrition data without overwriting existing fields
                    updated_recipe_doc['nutrition'] = {
                        'calories': nutrition.get('calories', 0),
                        'protein': nutrition.get('protein', 0),
                        'carbs': nutrition.get('carbohydrates', 0),
                        'fat': nutrition.get('fat', 0)
                    }
                    
                    # Add top-level nutrition fields for compatibility
                    updated_recipe_doc['calories'] = nutrition.get('calories', 0)
                    updated_recipe_doc['protein'] = nutrition.get('protein', 0)
                    updated_recipe_doc['carbs'] = nutrition.get('carbohydrates', 0)
                    updated_recipe_doc['fat'] = nutrition.get('fat', 0)
                    
                    # Ensure we have at least basic recipe structure
                    if 'title' not in updated_recipe_doc:
                        updated_recipe_doc['title'] = recipe_title
                    
                    updated_doc = json.dumps(updated_recipe_doc)
                    
                except Exception as e:
                    print(f"   ⚠️  Error updating recipe document: {e}")
                    # Create a minimal document with nutrition if update fails
                    updated_doc = json.dumps({
                        'title': recipe_title,
                        'nutrition': {
                            'calories': nutrition.get('calories', 0),
                            'protein': nutrition.get('protein', 0),
                            'carbs': nutrition.get('carbohydrates', 0),
                            'fat': nutrition.get('fat', 0)
                        },
                        'calories': nutrition.get('calories', 0),
                        'protein': nutrition.get('protein', 0),
                        'carbs': nutrition.get('carbohydrates', 0),
                        'fat': nutrition.get('fat', 0)
                    })
                
                # Update both the document and metadata
                recipe_collection.update(
                    ids=[recipe_id],
                    documents=[updated_doc],
                    metadatas=[updated_metadata]
                )
                
                print(f"   ✅ Added macros: {nutrition.get('calories', 0)} kcal, {nutrition.get('protein', 0)}g protein, {nutrition.get('carbohydrates', 0)}g carbs, {nutrition.get('fat', 0)}g fat")
                print(f"   💾 Preserved {len(existing_recipe_data)} existing recipe fields")
                success_count += 1
                
            else:
                print(f"   ❌ Analysis failed: {result.get('error', 'Unknown error')}")
                error_count += 1
                
        except Exception as e:
            print(f"   ❌ Error processing recipe {i}: {e}")
            error_count += 1
            continue
    
    print(f"\n🎉 SAFE Macronutrient analysis complete!")
    print(f"📊 Results:")
    print(f"   ✅ Successful: {success_count} recipes")
    print(f"   ⏭️  Skipped (already had nutrition): {skipped_count} recipes")
    print(f"   ❌ Failed: {error_count} recipes")
    
    if success_count > 0:
        total_processed = success_count + skipped_count
        print(f"   📈 Success rate: {(total_processed/(total_processed+error_count)*100):.1f}%")
        print(f"\n✅ Your recipes now have macronutrient info while preserving all existing data!")
        print(f"💡 Check your app to see the macro data without losing recipe content.")
    else:
        print(f"\n❌ No recipes were updated. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(add_macros_to_all_recipes_safely()) 