#!/usr/bin/env python3
"""
Restore sample recipe data with ingredients and instructions
"""

import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

class SampleRecipeRestorer:
    def __init__(self):
        self.recipe_cache = RecipeCacheService()
        
    def get_sample_recipe_data(self):
        """Get sample recipe data with complete ingredients and instructions"""
        return {
            "52961": {
                "title": "Budino Di Ricotta",
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
                ]
            }
        }
    
    def update_recipe_with_complete_data(self, recipe_id, recipe_data):
        """Update a recipe with complete data"""
        try:
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
            document['ingredients'] = recipe_data['ingredients']
            document['instructions'] = recipe_data['instructions']
            
            # Update metadata
            metadata['ingredients'] = json.dumps(recipe_data['ingredients'])
            metadata['instructions'] = json.dumps(recipe_data['instructions'])
            
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
    
    def restore_sample_recipes(self):
        """Restore sample recipes with complete data"""
        print("🔄 Starting sample recipe restoration...")
        
        sample_recipes = self.get_sample_recipe_data()
        success_count = 0
        
        for recipe_id, recipe_data in sample_recipes.items():
            try:
                title = recipe_data['title']
                print(f"   Processing: {title} (ID: {recipe_id})")
                
                if self.update_recipe_with_complete_data(recipe_id, recipe_data):
                    ingredients_count = len(recipe_data['ingredients'])
                    instructions_count = len(recipe_data['instructions'])
                    print(f"   ✅ Updated with {ingredients_count} ingredients and {instructions_count} instructions")
                    success_count += 1
                else:
                    print(f"   ❌ Failed to update")
                
            except Exception as e:
                print(f"   ❌ Error processing recipe: {e}")
                continue
        
        print(f"\n📊 Restoration Summary:")
        print(f"   Successfully updated: {success_count}")
        print(f"   Total recipes: {len(sample_recipes)}")
        
        return success_count > 0

def main():
    restorer = SampleRecipeRestorer()
    success = restorer.restore_sample_recipes()
    
    if success:
        print("\n✅ Sample recipe restoration completed!")
        print("🌐 Your sample recipe now has complete ingredients and instructions")
        print("💡 Next step: Run 'python3 sync_all_to_railway.py' to sync to Railway")
    else:
        print("\n❌ Sample recipe restoration failed")

if __name__ == "__main__":
    main()
