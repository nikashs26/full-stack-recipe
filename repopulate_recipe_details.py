#!/usr/bin/env python3
"""
Repopulate recipe details (ingredients and instructions) from the original API
"""

import sys
import os
import json
import requests
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

class RecipeDetailRepopulator:
    def __init__(self):
        self.recipe_cache = RecipeCacheService()
        self.spoonacular_api_key = os.environ.get('SPOONACULAR_API_KEY', 'your-api-key-here')
        
    def fetch_recipe_details_from_spoonacular(self, recipe_id):
        """Fetch detailed recipe information from Spoonacular API"""
        try:
            # Spoonacular API endpoint for recipe details
            url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
            params = {
                'apiKey': self.spoonacular_api_key,
                'includeNutrition': True
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"   API error for recipe {recipe_id}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   Error fetching recipe {recipe_id}: {e}")
            return None
    
    def extract_ingredients_from_api_data(self, api_data):
        """Extract ingredients from Spoonacular API data"""
        ingredients = []
        
        for ing in api_data.get('extendedIngredients', []):
            try:
                amount = ing.get('amount', 0)
                unit = ing.get('unit', '').strip()
                name = ing.get('name', '').strip()
                
                if name:
                    ingredient = {
                        'name': name,
                        'amount': amount,
                        'unit': unit,
                        'original': f"{amount} {unit} {name}".strip()
                    }
                    ingredients.append(ingredient)
            except Exception as e:
                print(f"   Error processing ingredient: {e}")
                continue
        
        return ingredients
    
    def extract_instructions_from_api_data(self, api_data):
        """Extract instructions from Spoonacular API data"""
        instructions = []
        
        # Try analyzed instructions first
        for instruction in api_data.get('analyzedInstructions', []):
            for step in instruction.get('steps', []):
                if step.get('step'):
                    instructions.append(step['step'].strip())
        
        # Fallback to plain instructions
        if not instructions and 'instructions' in api_data and api_data['instructions']:
            instructions = [s.strip() for s in api_data['instructions'].split('\n') if s.strip()]
        
        return instructions or ['No instructions provided.']
    
    def update_recipe_details(self, recipe_id, ingredients, instructions):
        """Update recipe with ingredients and instructions"""
        try:
            # Get current recipe data
            result = self.recipe_cache.recipe_collection.get(
                ids=[recipe_id],
                include=['documents', 'metadatas']
            )
            
            if not result['ids']:
                print(f"   Recipe {recipe_id} not found in cache")
                return False
            
            # Parse current data
            document = json.loads(result['documents'][0])
            metadata = result['metadatas'][0]
            
            # Update with new details
            document['ingredients'] = ingredients
            document['instructions'] = instructions
            
            # Update metadata
            metadata['ingredients'] = json.dumps(ingredients)
            metadata['instructions'] = json.dumps(instructions)
            
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
    
    def repopulate_all_recipes(self):
        """Repopulate all recipes with detailed information"""
        print("🔄 Starting recipe detail repopulation...")
        
        # Get all recipes
        all_recipes = self.recipe_cache.recipe_collection.get(
            include=['documents', 'metadatas'],
            limit=None
        )
        
        recipe_count = len(all_recipes['ids'])
        print(f"📊 Found {recipe_count} recipes to update")
        
        success_count = 0
        failed_count = 0
        
        for i, (recipe_id, metadata, document) in enumerate(zip(
            all_recipes['ids'], 
            all_recipes['metadatas'], 
            all_recipes['documents']
        )):
            try:
                doc = json.loads(document)
                title = doc.get('title', 'Unknown')
                
                print(f"   Processing {i+1}/{recipe_count}: {title} (ID: {recipe_id})")
                
                # Check if already has ingredients and instructions
                has_ingredients = doc.get('ingredients') and len(doc.get('ingredients', [])) > 0
                has_instructions = doc.get('instructions') and len(doc.get('instructions', [])) > 0
                
                if has_ingredients and has_instructions:
                    print(f"   ✅ Already has details, skipping")
                    continue
                
                # Fetch from API
                api_data = self.fetch_recipe_details_from_spoonacular(recipe_id)
                if not api_data:
                    print(f"   ❌ Failed to fetch from API")
                    failed_count += 1
                    continue
                
                # Extract details
                ingredients = self.extract_ingredients_from_api_data(api_data)
                instructions = self.extract_instructions_from_api_data(api_data)
                
                # Update recipe
                if self.update_recipe_details(recipe_id, ingredients, instructions):
                    print(f"   ✅ Updated with {len(ingredients)} ingredients and {len(instructions)} instructions")
                    success_count += 1
                else:
                    print(f"   ❌ Failed to update")
                    failed_count += 1
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"   ❌ Error processing recipe {recipe_id}: {e}")
                failed_count += 1
                continue
        
        print(f"\n📊 Repopulation Summary:")
        print(f"   Total recipes: {recipe_count}")
        print(f"   Successfully updated: {success_count}")
        print(f"   Failed: {failed_count}")
        
        return success_count > 0

def main():
    repopulator = RecipeDetailRepopulator()
    
    # Check if API key is available
    if repopulator.spoonacular_api_key == 'your-api-key-here':
        print("❌ Please set SPOONACULAR_API_KEY environment variable")
        print("   You can get a free API key from https://spoonacular.com/food-api")
        return
    
    success = repopulator.repopulate_all_recipes()
    
    if success:
        print("\n✅ Recipe details repopulation completed!")
        print("🌐 Your recipes now have ingredients and instructions")
    else:
        print("\n❌ Recipe details repopulation failed")

if __name__ == "__main__":
    main()
