from services.recipe_cache_service import RecipeCacheService

def check_chroma_contents():
    """Check what recipes are stored in ChromaDB"""
    recipe_cache = RecipeCacheService()
    
    # Get all recipes from recipe collection
    try:
        recipe_results = recipe_cache.recipe_collection.get(
            include=["documents", "metadatas"]
        )
        
        if recipe_results['documents']:
            print(f"\nFound {len(recipe_results['documents'])} recipes in ChromaDB:")
            for i, doc in enumerate(recipe_results['documents']):
                metadata = recipe_results['metadatas'][i]
                print(f"{i+1}. {metadata.get('title', 'Untitled')} ({metadata.get('cuisine', 'Unknown cuisine')})")
        else:
            print("No recipes found in recipe collection")
            
        # Get all search entries
        search_results = recipe_cache.search_collection.get(
            include=["documents", "metadatas"]
        )
        
        if search_results['documents']:
            print(f"\nFound {len(search_results['documents'])} search entries in ChromaDB")
        else:
            print("No search entries found")
            
    except Exception as e:
        print(f"Error checking ChromaDB contents: {e}")

if __name__ == "__main__":
    check_chroma_contents() 