#!/usr/bin/env python3
"""
Export Recipes for Production
Exports all recipes from local ChromaDB to JSON for production deployment
"""

import sys
import os
import json
from typing import List, Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def export_all_recipes():
    """Export all recipes from ChromaDB to JSON file"""
    try:
        from services.recipe_cache_service import RecipeCacheService
        
        print("📦 Exporting All Recipes for Production")
        print("=" * 50)
        
        # Initialize recipe cache
        recipe_cache = RecipeCacheService()
        
        # Get current count
        count_result = recipe_cache.get_recipe_count()
        if isinstance(count_result, dict):
            total_count = count_result.get('total', 0)
        else:
            total_count = count_result
        
        print(f"📊 Found {total_count} recipes to export")
        
        if total_count == 0:
            print("❌ No recipes found to export")
            return
        
        # Export all recipes
        print("📦 Exporting recipes...")
        all_recipes = recipe_cache.get_cached_recipes("", "", {})
        
        print(f"✅ Retrieved {len(all_recipes)} recipes")
        
        # Clean up recipes for JSON serialization
        cleaned_recipes = []
        for recipe in all_recipes:
            # Ensure all values are JSON serializable
            cleaned_recipe = {}
            for key, value in recipe.items():
                if value is not None:
                    if isinstance(value, (str, int, float, bool, list, dict)):
                        cleaned_recipe[key] = value
                    else:
                        cleaned_recipe[key] = str(value)
            cleaned_recipes.append(cleaned_recipe)
        
        # Save to JSON file
        export_file = "production_recipes_backup.json"
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump({
                "export_timestamp": "2025-09-12",
                "total_recipes": len(cleaned_recipes),
                "recipes": cleaned_recipes
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported {len(cleaned_recipes)} recipes to {export_file}")
        print(f"📁 File size: {os.path.getsize(export_file) / 1024 / 1024:.2f} MB")
        
        # Also create a smaller backup with just essential fields
        essential_recipes = []
        for recipe in cleaned_recipes:
            essential = {
                'id': recipe.get('id'),
                'title': recipe.get('title', recipe.get('name')),
                'image': recipe.get('image', recipe.get('imageUrl')),
                'cuisine': recipe.get('cuisine'),
                'cuisines': recipe.get('cuisines', []),
                'ingredients': recipe.get('ingredients', []),
                'instructions': recipe.get('instructions', []),
                'source': recipe.get('source', 'imported'),
                'diets': recipe.get('diets', []),
                'tags': recipe.get('tags', []),
                'ready_in_minutes': recipe.get('ready_in_minutes', 30),
                'difficulty': recipe.get('difficulty', 'medium'),
                'description': recipe.get('description', ''),
                'calories': recipe.get('calories'),
                'protein': recipe.get('protein'),
                'carbs': recipe.get('carbs'),
                'fat': recipe.get('fat')
            }
            essential_recipes.append(essential)
        
        essential_file = "production_recipes_essential.json"
        with open(essential_file, 'w', encoding='utf-8') as f:
            json.dump({
                "export_timestamp": "2025-09-12",
                "total_recipes": len(essential_recipes),
                "recipes": essential_recipes
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created essential backup: {essential_file}")
        print(f"📁 Essential file size: {os.path.getsize(essential_file) / 1024 / 1024:.2f} MB")
        
        print(f"\n🎯 Next steps:")
        print(f"1. Commit these JSON files to your repo")
        print(f"2. Deploy to Render - the auto-seeding will use these files")
        print(f"3. Your 1,333 recipes will be restored on production!")
        
        return len(cleaned_recipes)
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    export_all_recipes()
