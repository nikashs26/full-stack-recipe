#!/usr/bin/env python3
"""
Railway Startup Script
This ensures data is always available on Railway
"""

import os
import sys
import json
import time
from pathlib import Path

def ensure_data_directory():
    """Ensure the data directory exists and is writable"""
    data_dir = Path("/app/data")
    chroma_dir = data_dir / "chroma_db"
    
    try:
        # Create directories with proper permissions
        data_dir.mkdir(parents=True, exist_ok=True)
        chroma_dir.mkdir(parents=True, exist_ok=True)
        
        # Test if we can write to the directory
        test_file = data_dir / "test_write.txt"
        test_file.write_text("test")
        test_file.unlink()
        
        print(f"✅ Data directory is writable: {data_dir}")
        print(f"✅ ChromaDB directory created: {chroma_dir}")
        return True
    except Exception as e:
        print(f"❌ Data directory not writable: {e}")
        print(f"   Trying to create with different permissions...")
        
        # Try to create with different approach
        try:
            import subprocess
            subprocess.run(["mkdir", "-p", "/app/data/chroma_db"], check=True)
            subprocess.run(["chmod", "755", "/app/data"], check=True)
            subprocess.run(["chmod", "755", "/app/data/chroma_db"], check=True)
            print(f"✅ Created directories with subprocess")
            return True
        except Exception as e2:
            print(f"❌ Failed to create directories: {e2}")
            return False

def check_chromadb_data():
    """Check if ChromaDB has data"""
    try:
        from services.recipe_cache_service import RecipeCacheService
        recipe_cache = RecipeCacheService()
        
        # Check if we have any recipes
        result = recipe_cache.recipe_collection.get(limit=1)
        recipe_count = len(result['ids']) if result['ids'] else 0
        
        print(f"📊 ChromaDB has {recipe_count} recipes")
        return recipe_count > 0
    except Exception as e:
        print(f"❌ Error checking ChromaDB: {e}")
        return False

def restore_from_sample_data():
    """Restore data from sample recipes"""
    try:
        print("📁 Creating sample recipe data...")
        
        # Sample recipe data with complete information
        sample_recipes = [
            {
                "id": "52961",
                "title": "Budino Di Ricotta",
                "cuisine": "Italian",
                "cuisines": ["italian"],
                "diets": "vegetarian",
                "ingredients": [
                    {"name": "Ricotta", "measure": "500g", "original": "500g Ricotta"},
                    {"name": "Eggs", "measure": "4 large", "original": "4 large Eggs"},
                    {"name": "Flour", "measure": "3 tbs", "original": "3 tbs Flour"},
                    {"name": "Sugar", "measure": "250g", "original": "250g Sugar"},
                    {"name": "Cinnamon", "measure": "1 tsp", "original": "1 tsp Cinnamon"},
                    {"name": "Grated Zest of 2 Lemons", "measure": "", "original": "Grated Zest of 2 Lemons"},
                    {"name": "Dark Rum", "measure": "5 tbs", "original": "5 tbs Dark Rum"},
                    {"name": "Icing Sugar", "measure": "sprinkling", "original": "sprinkling Icing Sugar"}
                ],
                "instructions": [
                    "Mash the ricotta and beat well with the egg yolks, stir in the flour, sugar, cinnamon, grated lemon rind and the rum and mix well. You can do this in a food processor. Beat the egg whites until stiff, fold in and pour into a buttered and floured 25cm cake tin. Bake in the oven at 180ºC/160ºC fan/gas.",
                    "For about.",
                    "Minutes, or until it is firm. Serve hot or cold dusted with icing sugar."
                ],
                "calories": 350,
                "protein": 12,
                "carbs": 44,
                "fat": 14,
                "image": "https://www.themealdb.com/images/media/meals/1549542877.jpg"
            },
            {
                "id": "52772",
                "title": "Teriyaki Chicken Casserole",
                "cuisine": "Japanese",
                "cuisines": ["japanese"],
                "diets": "gluten free",
                "ingredients": [
                    {"name": "Chicken Thighs", "measure": "6", "original": "6 Chicken Thighs"},
                    {"name": "Soy Sauce", "measure": "1/2 cup", "original": "1/2 cup Soy Sauce"},
                    {"name": "Brown Sugar", "measure": "1/2 cup", "original": "1/2 cup Brown Sugar"},
                    {"name": "Garlic", "measure": "3 cloves", "original": "3 cloves Garlic"},
                    {"name": "Ginger", "measure": "1 inch", "original": "1 inch Ginger"},
                    {"name": "Rice", "measure": "2 cups", "original": "2 cups Rice"}
                ],
                "instructions": [
                    "Preheat oven to 350°F. Place chicken thighs in a baking dish.",
                    "Mix soy sauce, brown sugar, garlic, and ginger in a bowl.",
                    "Pour sauce over chicken and bake for 45 minutes.",
                    "Serve over rice."
                ],
                "calories": 420,
                "protein": 28,
                "carbs": 35,
                "fat": 18,
                "image": "https://www.themealdb.com/images/media/meals/wvpsxx1468256321.jpg"
            }
        ]
        
        # Restore to ChromaDB
        from services.recipe_cache_service import RecipeCacheService
        recipe_cache = RecipeCacheService()
        
        restored_count = 0
        for recipe in sample_recipes:
            try:
                recipe_id = recipe['id']
                document = json.dumps(recipe)
                metadata = {
                    'cuisine': recipe.get('cuisine', ''),
                    'cuisines': json.dumps(recipe.get('cuisines', [])),
                    'diets': recipe.get('diets', ''),
                    'ingredients': json.dumps(recipe.get('ingredients', [])),
                    'instructions': json.dumps(recipe.get('instructions', [])),
                    'calories': recipe.get('calories', 0),
                    'protein': recipe.get('protein', 0),
                    'carbs': recipe.get('carbs', 0),
                    'fat': recipe.get('fat', 0)
                }
                
                # Store in ChromaDB
                recipe_cache.recipe_collection.upsert(
                    ids=[recipe_id],
                    documents=[document],
                    metadatas=[metadata]
                )
                restored_count += 1
                
            except Exception as e:
                print(f"   ⚠️ Error restoring recipe {recipe.get('id', 'unknown')}: {e}")
                continue
        
        print(f"✅ Restored {restored_count} sample recipes to ChromaDB")
        return restored_count > 0
        
    except Exception as e:
        print(f"❌ Error restoring sample data: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 Railway startup - ensuring data persistence...")
    
    # Wait a bit for the app to start
    time.sleep(5)
    
    # Ensure data directory exists
    if not ensure_data_directory():
        print("❌ Cannot create data directory")
        return False
    
    # Check if ChromaDB has data
    if check_chromadb_data():
        print("✅ ChromaDB has data - persistence is working")
        return True
    
    print("⚠️ ChromaDB is empty - creating sample data...")
    
    # Try to restore from sample data
    if restore_from_sample_data():
        print("✅ Sample data created successfully")
        return True
    else:
        print("❌ Failed to create sample data")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("🎉 Startup completed successfully")
    else:
        print("⚠️ Startup failed - manual intervention needed")
