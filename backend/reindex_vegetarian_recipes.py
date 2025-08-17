#!/usr/bin/env python3
"""
Script to reindex all existing recipes with the new vegetarian detection logic
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add the current directory to the path so we can import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.recipe_search_service import RecipeSearchService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def reindex_vegetarian_recipes():
    """Reindex all recipes with the new vegetarian detection logic"""
    
    print("🔄 Starting vegetarian recipe reindex...")
    
    try:
        # Initialize the search service
        search_service = RecipeSearchService()
        print("✅ RecipeSearchService initialized successfully")
        
        # Get all existing recipes
        print("📊 Fetching all existing recipes...")
        all_recipes = search_service.semantic_search("", limit=2000)
        print(f"📈 Found {len(all_recipes)} recipes to reindex")
        
        # Count vegetarian recipes before reindexing
        vegetarian_before = 0
        for recipe in all_recipes:
            is_vegetarian = (
                "vegetarian" in recipe.get("dietaryRestrictions", []) or
                recipe.get("vegetarian", False) or
                recipe.get("diets") == "vegetarian" or
                (isinstance(recipe.get("diets"), list) and "vegetarian" in recipe.get("diets", []))
            )
            if is_vegetarian:
                vegetarian_before += 1
        
        print(f"🥗 Vegetarian recipes before reindexing: {vegetarian_before}")
        
        # Reindex each recipe
        print("🔄 Reindexing recipes...")
        reindexed_count = 0
        
        for i, recipe in enumerate(all_recipes):
            try:
                # Reindex the recipe with the new logic
                search_service.index_recipe(recipe)
                reindexed_count += 1
                
                if (i + 1) % 100 == 0:
                    print(f"   Progress: {i + 1}/{len(all_recipes)} recipes reindexed")
                    
            except Exception as e:
                logger.error(f"Failed to reindex recipe {recipe.get('title', 'Unknown')}: {e}")
        
        print(f"✅ Successfully reindexed {reindexed_count} recipes")
        
        # Test the vegetarian filter after reindexing
        print("\n🧪 Testing vegetarian filter after reindexing...")
        
        filters = {"is_vegetarian": True}
        vegetarian_filtered = search_service.semantic_search("", filters=filters, limit=2000)
        
        print(f"🔍 Recipes returned with vegetarian filter: {len(vegetarian_filtered)}")
        
        if len(vegetarian_filtered) == vegetarian_before:
            print("✅ Vegetarian filter is now working correctly!")
        else:
            print(f"⚠️  Still not working correctly. Expected {vegetarian_before}, got {len(vegetarian_filtered)}")
        
        # Show some sample results
        if vegetarian_filtered:
            print("\n📝 Sample vegetarian recipes from filter:")
            for i, recipe in enumerate(vegetarian_filtered[:5]):
                print(f"  {i+1}. {recipe.get('title') or recipe.get('name')}")
        
    except Exception as e:
        logger.error(f"Error during reindexing: {e}")
        print(f"❌ Reindexing failed: {e}")
        return
    
    print("\n🏁 Reindexing completed!")

if __name__ == "__main__":
    reindex_vegetarian_recipes()
