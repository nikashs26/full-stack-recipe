#!/usr/bin/env python3
"""
Add placeholder ingredients and instructions to recipes that are missing them
"""

import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

class PlaceholderDetailAdder:
    def __init__(self):
        self.recipe_cache = RecipeCacheService()
        
    def generate_placeholder_ingredients(self, recipe_title, cuisine):
        """Generate placeholder ingredients based on recipe title and cuisine"""
        # Basic ingredients that would be common for most recipes
        base_ingredients = [
            {"name": "Salt", "amount": 1, "unit": "tsp", "original": "1 tsp salt"},
            {"name": "Black pepper", "amount": 1, "unit": "tsp", "original": "1 tsp black pepper"},
            {"name": "Olive oil", "amount": 2, "unit": "tbsp", "original": "2 tbsp olive oil"},
        ]
        
        # Add cuisine-specific ingredients
        if cuisine.lower() == 'italian':
            base_ingredients.extend([
                {"name": "Garlic", "amount": 2, "unit": "cloves", "original": "2 cloves garlic"},
                {"name": "Onion", "amount": 1, "unit": "medium", "original": "1 medium onion"},
                {"name": "Tomatoes", "amount": 2, "unit": "cups", "original": "2 cups tomatoes"},
            ])
        elif cuisine.lower() == 'mexican':
            base_ingredients.extend([
                {"name": "Cumin", "amount": 1, "unit": "tsp", "original": "1 tsp cumin"},
                {"name": "Chili powder", "amount": 1, "unit": "tsp", "original": "1 tsp chili powder"},
                {"name": "Lime", "amount": 1, "unit": "medium", "original": "1 medium lime"},
            ])
        elif cuisine.lower() == 'chinese':
            base_ingredients.extend([
                {"name": "Soy sauce", "amount": 2, "unit": "tbsp", "original": "2 tbsp soy sauce"},
                {"name": "Ginger", "amount": 1, "unit": "tbsp", "original": "1 tbsp ginger"},
                {"name": "Sesame oil", "amount": 1, "unit": "tsp", "original": "1 tsp sesame oil"},
            ])
        else:
            base_ingredients.extend([
                {"name": "Herbs", "amount": 1, "unit": "tbsp", "original": "1 tbsp mixed herbs"},
                {"name": "Spices", "amount": 1, "unit": "tsp", "original": "1 tsp mixed spices"},
            ])
        
        return base_ingredients
    
    def generate_placeholder_instructions(self, recipe_title, cuisine):
        """Generate placeholder instructions based on recipe title and cuisine"""
        instructions = [
            "Prepare all ingredients and gather necessary equipment.",
            "Heat a large pan or pot over medium heat.",
            "Add the main ingredients and cook until tender.",
            "Season with salt, pepper, and other spices to taste.",
            "Cook for the recommended time, stirring occasionally.",
            "Taste and adjust seasoning as needed.",
            "Serve hot and enjoy!"
        ]
        
        return instructions
    
    def update_recipe_with_placeholders(self, recipe_id, recipe_title, cuisine):
        """Update recipe with placeholder ingredients and instructions"""
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
            
            # Generate placeholders
            ingredients = self.generate_placeholder_ingredients(recipe_title, cuisine)
            instructions = self.generate_placeholder_instructions(recipe_title, cuisine)
            
            # Update with placeholders
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
    
    def add_placeholders_to_all_recipes(self):
        """Add placeholder details to all recipes missing them"""
        print("🔄 Adding placeholder ingredients and instructions...")
        
        # Get all recipes
        all_recipes = self.recipe_cache.recipe_collection.get(
            include=['documents', 'metadatas'],
            limit=None
        )
        
        recipe_count = len(all_recipes['ids'])
        print(f"📊 Found {recipe_count} recipes to check")
        
        success_count = 0
        skipped_count = 0
        
        for i, (recipe_id, metadata, document) in enumerate(zip(
            all_recipes['ids'], 
            all_recipes['metadatas'], 
            all_recipes['documents']
        )):
            try:
                doc = json.loads(document)
                title = doc.get('title', 'Unknown')
                cuisine = doc.get('cuisine', 'International')
                
                print(f"   Processing {i+1}/{recipe_count}: {title} (ID: {recipe_id})")
                
                # Check if already has ingredients and instructions
                has_ingredients = doc.get('ingredients') and len(doc.get('ingredients', [])) > 0
                has_instructions = doc.get('instructions') and len(doc.get('instructions', [])) > 0
                
                if has_ingredients and has_instructions:
                    print(f"   ✅ Already has details, skipping")
                    skipped_count += 1
                    continue
                
                # Add placeholders
                if self.update_recipe_with_placeholders(recipe_id, title, cuisine):
                    print(f"   ✅ Added placeholder details")
                    success_count += 1
                else:
                    print(f"   ❌ Failed to add placeholders")
                
            except Exception as e:
                print(f"   ❌ Error processing recipe {recipe_id}: {e}")
                continue
        
        print(f"\n📊 Placeholder Addition Summary:")
        print(f"   Total recipes: {recipe_count}")
        print(f"   Successfully updated: {success_count}")
        print(f"   Already had details: {skipped_count}")
        print(f"   Failed: {recipe_count - success_count - skipped_count}")
        
        return success_count > 0

def main():
    adder = PlaceholderDetailAdder()
    success = adder.add_placeholders_to_all_recipes()
    
    if success:
        print("\n✅ Placeholder details added successfully!")
        print("🌐 Your recipes now have ingredients and instructions")
        print("💡 Note: These are placeholder details. For real data, you'll need to:")
        print("   1. Get a Spoonacular API key from https://spoonacular.com/food-api")
        print("   2. Run: python3 repopulate_recipe_details.py")
    else:
        print("\n❌ Failed to add placeholder details")

if __name__ == "__main__":
    main()
