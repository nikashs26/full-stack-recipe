#!/usr/bin/env python3
"""
Restore complete recipe data from the populate_railway_20250907_210446.py file
"""

import sys
import os
import json
import re

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

class RecipeDataRestorer:
    def __init__(self):
        self.recipe_cache = RecipeCacheService()
        self.populate_file = 'backend/populate_railway_20250907_210446.py'
        
    def extract_recipes_from_populate_file(self):
        """Extract recipe data from the populate file"""
        print("📖 Reading recipe data from populate file...")
        
        try:
            with open(self.populate_file, 'r') as f:
                content = f.read()
            
            # Find the recipes array in the file
            # Look for the line that starts with "recipes = ["
            start_pattern = r'recipes = \['
            start_match = re.search(start_pattern, content)
            
            if not start_match:
                print("❌ Could not find recipes array in populate file")
                return []
            
            # Find the end of the recipes array
            start_pos = start_match.end()
            
            # Count brackets to find the end
            bracket_count = 1
            pos = start_pos
            while pos < len(content) and bracket_count > 0:
                if content[pos] == '[':
                    bracket_count += 1
                elif content[pos] == ']':
                    bracket_count -= 1
                pos += 1
            
            if bracket_count != 0:
                print("❌ Could not find end of recipes array")
                return []
            
            # Extract the recipes array
            recipes_text = content[start_pos:pos-1]
            
            # Parse as Python list
            recipes = eval(recipes_text)
            
            print(f"✅ Found {len(recipes)} recipes in populate file")
            return recipes
            
        except Exception as e:
            print(f"❌ Error reading populate file: {e}")
            return []
    
    def update_recipe_with_complete_data(self, recipe_data):
        """Update a recipe with complete data from populate file"""
        try:
            recipe_id = recipe_data['id']
            title = recipe_data['title']
            ingredients = recipe_data.get('ingredients', [])
            instructions = recipe_data.get('instructions', [])
            
            # Get current recipe data
            result = self.recipe_cache.recipe_collection.get(
                ids=[recipe_id],
                include=['documents', 'metadatas']
            )
            
            if not result['ids']:
                print(f"   Recipe {recipe_id} not found in current database")
                return False
            
            # Parse current data
            document = json.loads(result['documents'][0])
            metadata = result['metadatas'][0]
            
            # Update with complete data
            document['ingredients'] = ingredients
            document['instructions'] = instructions
            document['description'] = recipe_data.get('description', '')
            
            # Update metadata
            metadata['ingredients'] = json.dumps(ingredients)
            metadata['instructions'] = json.dumps(instructions)
            metadata['description'] = recipe_data.get('description', '')
            
            # Store updated data
            self.recipe_cache.recipe_collection.upsert(
                ids=[recipe_id],
                documents=[json.dumps(document)],
                metadatas=[metadata]
            )
            
            return True
            
        except Exception as e:
            print(f"   Error updating recipe {recipe_id}: {e}")
            return False
    
    def restore_all_recipes(self):
        """Restore all recipes with complete data"""
        print("🔄 Starting recipe data restoration...")
        
        # Extract recipes from populate file
        recipes = self.extract_recipes_from_populate_file()
        if not recipes:
            return False
        
        success_count = 0
        failed_count = 0
        not_found_count = 0
        
        for i, recipe_data in enumerate(recipes):
            try:
                recipe_id = recipe_data['id']
                title = recipe_data['title']
                
                print(f"   Processing {i+1}/{len(recipes)}: {title} (ID: {recipe_id})")
                
                # Check if recipe exists in current database
                result = self.recipe_cache.recipe_collection.get(ids=[recipe_id])
                if not result['ids']:
                    print(f"   ⚠️ Recipe not found in current database, skipping")
                    not_found_count += 1
                    continue
                
                # Update with complete data
                if self.update_recipe_with_complete_data(recipe_data):
                    ingredients_count = len(recipe_data.get('ingredients', []))
                    instructions_count = len(recipe_data.get('instructions', []))
                    print(f"   ✅ Updated with {ingredients_count} ingredients and {instructions_count} instructions")
                    success_count += 1
                else:
                    print(f"   ❌ Failed to update")
                    failed_count += 1
                
            except Exception as e:
                print(f"   ❌ Error processing recipe: {e}")
                failed_count += 1
                continue
        
        print(f"\n📊 Restoration Summary:")
        print(f"   Total recipes in populate file: {len(recipes)}")
        print(f"   Successfully updated: {success_count}")
        print(f"   Not found in current DB: {not_found_count}")
        print(f"   Failed: {failed_count}")
        
        return success_count > 0

def main():
    restorer = RecipeDataRestorer()
    success = restorer.restore_all_recipes()
    
    if success:
        print("\n✅ Recipe data restoration completed!")
        print("🌐 Your recipes now have complete ingredients and instructions")
        print("💡 Next step: Run 'python3 sync_all_to_railway.py' to sync to Railway")
    else:
        print("\n❌ Recipe data restoration failed")

if __name__ == "__main__":
    main()
