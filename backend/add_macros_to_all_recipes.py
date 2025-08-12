import asyncio
import chromadb
import json
from services.nutrition_analysis_agent import NutritionAnalysisAgent

async def add_macros_to_all_recipes():
    """Run once to add macronutrient info to all recipes in ChromaDB"""
    
    print("🚀 Starting macronutrient analysis for all recipes...")
    
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
    
    # Process each recipe
    for i, doc in enumerate(results['documents']):
        try:
            recipe_id = results['metadatas'][i].get('id', f'recipe_{i}')
            recipe_title = results['metadatas'][i].get('title', f'Recipe {i}')
            
            print(f"\n🍽️  Analyzing {i+1}/{len(results['documents'])}: {recipe_title}")
            
            # Prepare recipe data
            recipe_data = {
                'id': recipe_id,
                'title': recipe_title,
                'ingredients': results['metadatas'][i].get('ingredients', ''),
                'instructions': doc if doc else ''
            }
            
            # Analyze nutrition
            result = await nutrition_agent.analyze_recipe_nutrition(recipe_data)
            
            if result['status'] == 'success':
                nutrition = result['nutrition']
                
                # Update the recipe in ChromaDB with nutrition data
                updated_metadata = results['metadatas'][i].copy()
                updated_metadata.update({
                    'calories': nutrition.get('calories', 0),
                    'protein': nutrition.get('protein', 0),
                    'carbs': nutrition.get('carbohydrates', 0),
                    'fat': nutrition.get('fat', 0),
                    'nutrition_analyzed': True,
                    'nutrition_analyzed_at': result['analyzed_at']
                })
                
                # Also update the document to include nutrition data in the recipe object
                try:
                    # Parse the existing document if it's JSON
                    if doc and doc.strip():
                        recipe_doc = json.loads(doc)
                        # Add nutrition data to the recipe object
                        recipe_doc['nutrition'] = {
                            'calories': nutrition.get('calories', 0),
                            'protein': nutrition.get('protein', 0),
                            'carbs': nutrition.get('carbohydrates', 0),
                            'fat': nutrition.get('fat', 0)
                        }
                        # Also add top-level nutrition fields for compatibility
                        recipe_doc['calories'] = nutrition.get('calories', 0)
                        recipe_doc['protein'] = nutrition.get('protein', 0)
                        recipe_doc['carbs'] = nutrition.get('carbohydrates', 0)
                        recipe_doc['fat'] = nutrition.get('fat', 0)
                        
                        updated_doc = json.dumps(recipe_doc)
                    else:
                        # If no document, create a basic one with nutrition
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
                except:
                    # If parsing fails, create a simple document with nutrition
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
                success_count += 1
                
            else:
                print(f"   ❌ Analysis failed: {result.get('error', 'Unknown error')}")
                error_count += 1
                
        except Exception as e:
            print(f"   ❌ Error processing recipe {i}: {e}")
            error_count += 1
            continue
    
    print(f"\n🎉 Macronutrient analysis complete!")
    print(f"📊 Results:")
    print(f"   ✅ Successful: {success_count} recipes")
    print(f"   ❌ Failed: {error_count} recipes")
    print(f"   📈 Success rate: {(success_count/(success_count+error_count)*100):.1f}%")
    
    if success_count > 0:
        print(f"\n✅ Your recipes now have macronutrient info! Check your app to see the macro data.")
    else:
        print(f"\n❌ No recipes were updated. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(add_macros_to_all_recipes()) 