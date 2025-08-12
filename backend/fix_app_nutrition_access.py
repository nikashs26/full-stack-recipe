import chromadb
import json

def fix_app_nutrition_access():
    """Fix how the app accesses nutrition data by storing it in the right format"""
    
    print("🔧 Fixing app nutrition data access...")
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    recipe_collection = client.get_collection("recipe_details_cache")
    
    print(f"📊 Total recipes: {recipe_collection.count()}")
    
    # Get all recipes
    results = recipe_collection.get(include=['documents', 'metadatas'])
    
    if not results['documents']:
        print("❌ No recipes found")
        return
    
    updated_count = 0
    
    # Process each recipe
    for i, doc in enumerate(results['documents']):
        try:
            recipe_id = results['metadatas'][i].get('id', f'recipe_{i}')
            recipe_title = results['metadatas'][i].get('title', f'Recipe {i}')
            metadata = results['metadatas'][i]
            
            # Check if we have nutrition data in metadata
            if 'calories' in metadata and metadata['calories'] != 0:
                print(f"🍽️  Fixing nutrition access for: {recipe_title}")
                
                calories = metadata.get('calories', 0)
                protein = metadata.get('protein', 0)
                carbs = metadata.get('carbs', 0)
                fat = metadata.get('fat', 0)
                
                # Create updated document with nutrition data in the right format
                try:
                    if doc and doc.strip():
                        recipe_doc = json.loads(doc)
                    else:
                        recipe_doc = {}
                    
                    # Add nutrition data in the format your app expects
                    recipe_doc['nutrition'] = {
                        'calories': calories,
                        'protein': protein,
                        'carbs': carbs,
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
                    
                except:
                    # If parsing fails, create simple document
                    updated_doc = json.dumps({
                        'title': recipe_title,
                        'nutrition': {
                            'calories': calories,
                            'protein': protein,
                            'carbs': carbs,
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
                
                # Update the recipe with the new document
                recipe_collection.update(
                    ids=[recipe_id],
                    documents=[updated_doc]
                )
                
                print(f"   ✅ Fixed: {calories} cal, {protein}g protein, {carbs}g carbs, {fat}g fat")
                updated_count += 1
                
        except Exception as e:
            print(f"   ❌ Error updating recipe {i}: {e}")
            continue
    
    print(f"\n🎉 App nutrition access fix complete!")
    print(f"📊 Updated {updated_count} recipes")
    print(f"✅ Your app should now display real macros instead of ~300 cal, ~15g protein!")
    print(f"🔍 Check your app - recipes should now show the actual calculated nutrition values!")

if __name__ == "__main__":
    fix_app_nutrition_access() 