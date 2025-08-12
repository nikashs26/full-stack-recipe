import chromadb
import json

def restore_recipes_to_app():
    """Copy recipes from recipe_search_cache to recipe_details_cache so the app can see them"""
    
    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Get the source collection (where recipes currently are)
    source_collection = client.get_collection("recipe_search_cache")
    print(f"Source collection 'recipe_search_cache' has {source_collection.count()} items")
    
    # Get the target collection (where the app looks for recipes)
    target_collection = client.get_collection("recipe_details_cache")
    print(f"Target collection 'recipe_details_cache' has {target_collection.count()} items")
    
    # Get all recipes from source
    print("Fetching recipes from source collection...")
    source_recipes = source_collection.get(include=['documents', 'metadatas'])
    
    if not source_recipes.get('documents'):
        print("No recipes found in source collection!")
        return
    
    print(f"Found {len(source_recipes['documents'])} recipes to copy")
    
    # Copy recipes to target collection
    copied_count = 0
    for i, doc in enumerate(source_recipes['documents']):
        try:
            if not doc or not isinstance(doc, str):
                continue
                
            # Parse the recipe
            recipe = json.loads(doc)
            if not isinstance(recipe, dict) or not recipe.get('id'):
                continue
            
            # Get metadata
            metadata = source_recipes['metadatas'][i] if i < len(source_recipes['metadatas']) else {}
            
            # Add to target collection
            target_collection.upsert(
                ids=[recipe['id']],
                documents=[doc],
                metadatas=[metadata]
            )
            
            copied_count += 1
            if copied_count % 100 == 0:
                print(f"Copied {copied_count} recipes...")
                
        except Exception as e:
            print(f"Error copying recipe {i}: {e}")
            continue
    
    print(f"Successfully copied {copied_count} recipes!")
    
    # Verify the copy worked
    final_count = target_collection.count()
    print(f"Final count in 'recipe_details_cache': {final_count} items")
    
    if final_count > 1000:
        print("✅ Success! Your app should now see all your recipes!")
    else:
        print("❌ Something went wrong - recipe count is too low")

if __name__ == "__main__":
    restore_recipes_to_app() 