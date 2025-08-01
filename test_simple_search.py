#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_search_service import RecipeSearchService

def test_simple_search():
    """Test simple search functionality"""
    
    print("Testing simple search...")
    
    search_service = RecipeSearchService()
    
    # Test a very simple search
    try:
        print("Testing search for 'chicken'...")
        results = search_service.semantic_search("chicken", limit=5)
        print(f"Search for 'chicken' returned {len(results)} results")
        
        if results:
            print("\nTop results:")
            for i, recipe in enumerate(results[:3], 1):
                title = recipe.get('title', recipe.get('name', 'No title'))
                cuisine = recipe.get('cuisine', 'Unknown')
                print(f"{i}. {title} - {cuisine}")
        else:
            print("No results found!")
            
        # Test another simple search
        print("\nTesting search for 'pasta'...")
        results = search_service.semantic_search("pasta", limit=5)
        print(f"Search for 'pasta' returned {len(results)} results")
        
        if results:
            print("\nTop results:")
            for i, recipe in enumerate(results[:3], 1):
                title = recipe.get('title', recipe.get('name', 'No title'))
                cuisine = recipe.get('cuisine', 'Unknown')
                print(f"{i}. {title} - {cuisine}")
        else:
            print("No results found!")
            
    except Exception as e:
        print(f"Error in simple search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_search() 