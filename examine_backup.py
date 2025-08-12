#!/usr/bin/env python3
"""
Script to examine the backup data and see what recipes we can recover
"""

import json

def examine_backup():
    """Examine the backup data to see what we can recover"""
    
    print("🔍 Examining backup data for recoverable recipes...")
    
    try:
        # Load the backup
        with open('recipe_backup_20250812_155632_202_recipes.json', 'r') as f:
            backup = json.load(f)
        
        print(f"📊 Backup created: {backup['backup_created']}")
        print(f"📊 Total recipes in backup: {len(backup['recipes'])}")
        
        # Find recipes with actual content
        recipes_with_ingredients = []
        recipes_with_instructions = []
        
        for recipe in backup['recipes']:
            data = recipe['data']
            
            # Check for ingredients
            if 'ingredients' in data and data['ingredients']:
                if isinstance(data['ingredients'], list) and len(data['ingredients']) > 0:
                    recipes_with_ingredients.append(recipe)
                elif isinstance(data['ingredients'], str) and data['ingredients'].strip():
                    recipes_with_ingredients.append(recipe)
            
            # Check for instructions
            if 'instructions' in data and data['instructions']:
                if isinstance(data['instructions'], list) and len(data['instructions']) > 0:
                    recipes_with_instructions.append(recipe)
                elif isinstance(data['instructions'], str) and data['instructions'].strip():
                    recipes_with_instructions.append(recipe)
        
        print(f"\n📋 Recipes with ingredients: {len(recipes_with_ingredients)}")
        print(f"📋 Recipes with instructions: {len(recipes_with_instructions)}")
        
        # Show sample of recipes with content
        if recipes_with_ingredients:
            print(f"\n🍽️  Sample recipe with ingredients:")
            sample = recipes_with_ingredients[0]
            print(f"   ID: {sample['id']}")
            print(f"   Title: {sample['data'].get('title', 'No title')}")
            
            ingredients = sample['data']['ingredients']
            if isinstance(ingredients, list):
                print(f"   Ingredients: {len(ingredients)} items")
                for i, ing in enumerate(ingredients[:3]):  # Show first 3
                    print(f"     {i+1}. {ing}")
                if len(ingredients) > 3:
                    print(f"     ... and {len(ingredients) - 3} more")
            else:
                print(f"   Ingredients: {ingredients[:100]}...")
            
            instructions = sample['data'].get('instructions', [])
            if isinstance(instructions, list):
                print(f"   Instructions: {len(instructions)} steps")
                for i, step in enumerate(instructions[:2]):  # Show first 2
                    print(f"     {i+1}. {step[:100]}...")
                if len(instructions) > 2:
                    print(f"     ... and {len(instructions) - 2} more")
            elif isinstance(instructions, str):
                print(f"   Instructions: {instructions[:100]}...")
        
        # Check what fields are available
        all_fields = set()
        for recipe in backup['recipes']:
            all_fields.update(recipe['data'].keys())
        
        print(f"\n📊 All available fields in backup:")
        for field in sorted(all_fields):
            print(f"   - {field}")
        
        return recipes_with_ingredients, recipes_with_instructions
        
    except Exception as e:
        print(f"❌ Error examining backup: {e}")
        return [], []

if __name__ == "__main__":
    examine_backup() 