#!/usr/bin/env python3
"""
Script to count recipes with specific default macro values
"""

import json

def count_default_macros():
    """Count recipes with the specific default macro values"""
    
    # Load the nutrition analysis results
    with open('backend/nutrition_analysis_results_1333_recipes.json', 'r') as f:
        data = json.load(f)
    
    print(f"📊 Analyzing {data['total_recipes']} recipes for default macro values...")
    
    # Default macro values to look for
    default_calories = 300
    default_protein = 15
    default_carbs = 60
    default_fat = 12
    
    # Counters
    exact_defaults = 0  # All macros match defaults
    partial_defaults = 0  # At least one macro matches default
    recipes_with_defaults = []
    
    for recipe in data['results']:
        if recipe['status'] == 'success':
            nutrition = recipe['nutrition']
            
            calories = nutrition.get('calories', 0)
            protein = nutrition.get('protein', 0)
            carbs = nutrition.get('carbohydrates', 0)
            fat = nutrition.get('fat', 0)
            
            # Check if this recipe has any default values
            has_default = False
            default_macros = []
            
            if calories == default_calories:
                has_default = True
                default_macros.append(f"calories: {calories}")
            
            if protein == default_protein:
                has_default = True
                default_macros.append(f"protein: {protein}g")
            
            if carbs == default_carbs:
                has_default = True
                default_macros.append(f"carbs: {carbs}g")
            
            if fat == default_fat:
                has_default = True
                default_macros.append(f"fat: {fat}g")
            
            if has_default:
                partial_defaults += 1
                recipes_with_defaults.append({
                    'id': recipe['recipe_id'],
                    'title': recipe['title'],
                    'nutrition': nutrition,
                    'default_macros': default_macros
                })
                
                # Check if ALL macros match defaults
                if (calories == default_calories and 
                    protein == default_protein and 
                    carbs == default_carbs and 
                    fat == default_fat):
                    exact_defaults += 1
    
    print(f"\n🎯 Results for default macro values:")
    print(f"   Default calories: {default_calories}")
    print(f"   Default protein: {default_protein}g")
    print(f"   Default carbs: {default_carbs}g")
    print(f"   Default fat: {default_fat}g")
    
    print(f"\n📈 Summary:")
    print(f"   Total recipes analyzed: {data['total_recipes']}")
    print(f"   Recipes with at least one default macro: {partial_defaults}")
    print(f"   Recipes with ALL default macros: {exact_defaults}")
    print(f"   Percentage with any defaults: {(partial_defaults/data['total_recipes'])*100:.1f}%")
    print(f"   Percentage with all defaults: {(exact_defaults/data['total_recipes'])*100:.1f}%")
    
    # Show breakdown by macro type
    calories_default = sum(1 for r in recipes_with_defaults if r['nutrition'].get('calories') == default_calories)
    protein_default = sum(1 for r in recipes_with_defaults if r['nutrition'].get('protein') == default_protein)
    carbs_default = sum(1 for r in recipes_with_defaults if r['nutrition'].get('carbohydrates') == default_carbs)
    fat_default = sum(1 for r in recipes_with_defaults if r['nutrition'].get('fat') == default_fat)
    
    print(f"\n🔍 Breakdown by macro type:")
    print(f"   Recipes with default calories ({default_calories}): {calories_default}")
    print(f"   Recipes with default protein ({default_protein}g): {protein_default}")
    print(f"   Recipes with default carbs ({default_carbs}g): {carbs_default}")
    print(f"   Recipes with default fat ({default_fat}g): {fat_default}")
    
    # Show examples of recipes with defaults
    print(f"\n📋 Examples of recipes with default macros:")
    for i, recipe in enumerate(recipes_with_defaults[:10]):
        print(f"   {i+1}. {recipe['title']}")
        print(f"      Calories: {recipe['nutrition'].get('calories', 0)}, Protein: {recipe['nutrition'].get('protein', 0)}g, Carbs: {recipe['nutrition'].get('carbohydrates', 0)}g, Fat: {recipe['nutrition'].get('fat', 0)}g")
        print(f"      Default macros: {', '.join(recipe['default_macros'])}")

if __name__ == "__main__":
    count_default_macros() 