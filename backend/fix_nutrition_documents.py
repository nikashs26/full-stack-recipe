import chromadb
import json

def fix_nutrition_documents():
    """Fix recipe documents by copying nutrition data from metadata"""
    
    print("🔧 Fixing recipe documents with nutrition data...")
    
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
    for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
        try:
            recipe_id = meta.get('id', f'recipe_{i}')
            recipe_title = meta.get('title', f'Recipe {i}')
            
            # Check if we have nutrition data in metadata
            if 'calories' in meta and meta['calories'] != 0:
                print(f"🍽️  Fixing nutrition in document: {recipe_title}")
                
                calories = meta.get('calories', 0)
                protein = meta.get('protein', 0)
                carbs = meta.get('carbs', 0)
                fat = meta.get('fat', 0)
                
                # Create updated document with nutrition data
                try:
                    if doc and doc.strip():
                        recipe_doc = json.loads(doc)
                    else:
                        recipe_doc = {}
                    
                    # Add nutrition data to the recipe document
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
                
                # Update the recipe document
                recipe_collection.update(
                    ids=[recipe_id],
                    documents=[updated_doc]
                )
                
                print(f"   ✅ Fixed document: {calories} cal, {protein}g protein, {carbs}g carbs, {fat}g fat")
                updated_count += 1
                
        except Exception as e:
            print(f"   ❌ Error updating recipe {i}: {e}")
            continue
    
    print(f"\n🎉 Nutrition document fix complete!")
    print(f"📊 Updated {updated_count} recipe documents")
    print(f"✅ Your app should now show the correct, varied macros!")
    print(f"🔍 Check your app - recipes should now display different nutrition values!")

if __name__ == "__main__":
    fix_nutrition_documents() 