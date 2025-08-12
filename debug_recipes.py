#!/usr/bin/env python3
"""
Debug script to check why recipes aren't showing up in the app
"""

import chromadb
import json

def debug_recipes():
    """Debug recipe storage and retrieval"""
    
    print("🔍 Debugging Recipe Storage and Retrieval")
    print("=" * 50)
    
    try:
        # Initialize ChromaDB
        client = chromadb.PersistentClient(path="./chroma_db")
        
        # Check collections
        collections = client.list_collections()
        print(f"📚 Collections found: {[c.name for c in collections]}")
        
        # Check recipe_details_cache collection
        recipe_collection = client.get_collection("recipe_details_cache")
        print(f"\n📊 Recipe Details Cache:")
        print(f"   Total recipes: {recipe_collection.count()}")
        
        # Get sample recipes
        results = recipe_collection.get(limit=5, include=['documents', 'metadatas'])
        
        print(f"\n📋 Sample Recipes:")
        for i in range(len(results['ids'])):
            recipe_id = results['ids'][i]
            metadata = results['metadatas'][i]
            document = results['documents'][i]
            
            print(f"\n   Recipe {i+1}:")
            print(f"      ID: {recipe_id}")
            print(f"      Title: {metadata.get('title', 'No title')}")
            print(f"      Document type: {type(document)}")
            print(f"      Document length: {len(str(document)) if document else 0}")
            
            # Try to parse the document
            if document and isinstance(document, str):
                try:
                    recipe_data = json.loads(document)
                    print(f"      Parsed successfully: ✅")
                    print(f"      Recipe keys: {list(recipe_data.keys())}")
                    print(f"      Has title: {'title' in recipe_data}")
                    print(f"      Has ingredients: {'ingredients' in recipe_data}")
                    print(f"      Has instructions: {'instructions' in recipe_data}")
                except json.JSONDecodeError as e:
                    print(f"      JSON parse error: ❌ {e}")
            elif document and isinstance(document, dict):
                print(f"      Already a dict: ✅")
                print(f"      Recipe keys: {list(document.keys())}")
            else:
                print(f"      Invalid document: ❌")
        
        # Check if recipes have proper structure
        print(f"\n🔍 Checking Recipe Structure...")
        all_results = recipe_collection.get(include=['documents', 'metadatas'])
        
        valid_recipes = 0
        invalid_recipes = 0
        
        for i, doc in enumerate(all_results['documents']):
            try:
                if isinstance(doc, str):
                    recipe = json.loads(doc)
                else:
                    recipe = doc
                
                if isinstance(recipe, dict) and recipe.get('id') and recipe.get('title'):
                    valid_recipes += 1
                else:
                    invalid_recipes += 1
                    
            except:
                invalid_recipes += 1
        
        print(f"   Valid recipes: {valid_recipes}")
        print(f"   Invalid recipes: {invalid_recipes}")
        
        # Test the cache service method
        print(f"\n🧪 Testing Cache Service Method...")
        try:
            from backend.services.recipe_cache_service import RecipeCacheService
            cache_service = RecipeCacheService()
            cached_recipes = cache_service._get_all_recipes_from_cache()
            print(f"   Cache service returned: {len(cached_recipes)} recipes")
            
            if cached_recipes:
                sample_recipe = cached_recipes[0]
                print(f"   Sample recipe from cache service:")
                print(f"      ID: {sample_recipe.get('id')}")
                print(f"      Title: {sample_recipe.get('title')}")
                print(f"      Type: {type(sample_recipe)}")
        except Exception as e:
            print(f"   Cache service error: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_recipes()