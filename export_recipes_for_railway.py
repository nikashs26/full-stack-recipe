#!/usr/bin/env python3
"""
Export all recipes from local ChromaDB to JSON format for Railway deployment
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

def export_recipes_to_json():
    """Export all recipes from local ChromaDB to JSON file"""
    try:
        print("🔄 Initializing recipe cache service...")
        recipe_cache = RecipeCacheService()
        
        print("📊 Getting all recipes from ChromaDB...")
        all_recipes = recipe_cache.recipe_collection.get(include=['metadatas', 'documents'])
        
        recipe_count = len(all_recipes['ids'])
        print(f"✅ Found {recipe_count} recipes in local ChromaDB")
        
        if recipe_count == 0:
            print("❌ No recipes found in local ChromaDB")
            return False
        
        # Convert to the format expected by Railway
        recipes_data = []
        
        for i, (recipe_id, metadata, document) in enumerate(zip(all_recipes['ids'], all_recipes['metadatas'], all_recipes['documents'])):
            try:
                # Parse the document (recipe data)
                recipe_data = json.loads(document)
                
                # Merge metadata into recipe data for frontend compatibility
                merged_recipe = recipe_data.copy()
                for key, value in metadata.items():
                    if key not in merged_recipe or merged_recipe[key] is None or merged_recipe[key] == '':
                        merged_recipe[key] = value
                
                recipes_data.append(merged_recipe)
                
                if (i + 1) % 100 == 0:
                    print(f"   Processed {i + 1}/{recipe_count} recipes...")
                    
            except Exception as e:
                print(f"   ⚠️ Error processing recipe {recipe_id}: {e}")
                continue
        
        # Save to JSON file
        output_file = 'recipes_data.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(recipes_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully exported {len(recipes_data)} recipes to {output_file}")
        print(f"📁 File size: {os.path.getsize(output_file) / (1024*1024):.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error exporting recipes: {e}")
        return False

if __name__ == "__main__":
    success = export_recipes_to_json()
    if success:
        print("\n🎉 Recipe export completed successfully!")
        print("📤 You can now deploy this to Railway")
    else:
        print("\n❌ Recipe export failed")
        sys.exit(1)
