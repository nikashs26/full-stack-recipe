#!/usr/bin/env python3
"""
Script to analyze how many recipes have default macro values
"""

import json
from collections import defaultdict, Counter

def analyze_default_macros():
    """Analyze the nutrition analysis results to find recipes with default macro values"""
    
    # Load the nutrition analysis results
    with open('backend/nutrition_analysis_results_1333_recipes.json', 'r') as f:
        data = json.load(f)
    
    print(f"📊 Analyzing {data['total_recipes']} recipes...")
    
    # Track macro values
    calorie_counts = Counter()
    protein_counts = Counter()
    carbs_counts = Counter()
    fat_counts = Counter()
    
    # Track recipes with potential default values
    potential_defaults = []
    
    for recipe in data['results']:
        if recipe['status'] == 'success':
            nutrition = recipe['nutrition']
            
            calories = nutrition.get('calories', 0)
            protein = nutrition.get('protein', 0)
            carbs = nutrition.get('carbohydrates', 0)
            fat = nutrition.get('fat', 0)
            
            # Count occurrences
            calorie_counts[calories] += 1
            protein_counts[protein] += 1
            carbs_counts[carbs] += 1
            fat_counts[fat] += 1
            
            # Check for suspicious patterns (very common values)
            if (calories in [300, 0] or 
                protein in [15, 0] or 
                carbs in [60, 0] or 
                fat in [12, 0]):
                potential_defaults.append({
                    'id': recipe['recipe_id'],
                    'title': recipe['title'],
                    'nutrition': nutrition
                })
    
    print(f"\n🔍 Most common calorie values:")
    for calories, count in calorie_counts.most_common(10):
        print(f"   {calories} calories: {count} recipes")
    
    print(f"\n🔍 Most common protein values:")
    for protein, count in protein_counts.most_common(10):
        print(f"   {protein}g protein: {count} recipes")
    
    print(f"\n🔍 Most common carb values:")
    for carbs, count in carbs_counts.most_common(10):
        print(f"   {carbs}g carbs: {count} recipes")
    
    print(f"\n🔍 Most common fat values:")
    for fat, count in fat_counts.most_common(10):
        print(f"   {fat}g fat: {count} recipes")
    
    # Identify likely default values
    likely_defaults = []
    for calories, count in calorie_counts.items():
        if count > 50:  # If more than 50 recipes have the same value, it's suspicious
            likely_defaults.append(('calories', calories, count))
    
    for protein, count in protein_counts.items():
        if count > 50:
            likely_defaults.append(('protein', protein, count))
    
    for carbs, count in carbs_counts.items():
        if count > 50:
            likely_defaults.append(('carbs', carbs, count))
    
    for fat, count in fat_counts.items():
        if count > 50:
            likely_defaults.append(('fat', fat, count))
    
    print(f"\n🚨 Likely default macro values (appearing in >50 recipes):")
    for macro, value, count in likely_defaults:
        print(f"   {macro}: {value} ({count} recipes)")
    
    # Count recipes that have at least one likely default value
    recipes_with_defaults = set()
    for recipe in data['results']:
        if recipe['status'] == 'success':
            nutrition = recipe['nutrition']
            calories = nutrition.get('calories', 0)
            protein = nutrition.get('protein', 0)
            carbs = nutrition.get('carbohydrates', 0)
            fat = nutrition.get('fat', 0)
            
            # Check if any macro is a likely default
            if (calories in [300] or 
                protein in [15] or 
                carbs in [60] or 
                fat in [12]):
                recipes_with_defaults.add(recipe['recipe_id'])
    
    print(f"\n📈 Summary:")
    print(f"   Total recipes analyzed: {data['total_recipes']}")
    print(f"   Successful analyses: {data['successful_analyses']}")
    print(f"   Recipes with likely default macros: {len(recipes_with_defaults)}")
    print(f"   Percentage with defaults: {(len(recipes_with_defaults)/data['total_recipes'])*100:.1f}%")
    
    # Show some examples of recipes with defaults
    print(f"\n📋 Examples of recipes with likely default macros:")
    for i, recipe_id in enumerate(list(recipes_with_defaults)[:10]):
        recipe = next(r for r in data['results'] if r['recipe_id'] == recipe_id)
        nutrition = recipe['nutrition']
        print(f"   {i+1}. {recipe['title']}")
        print(f"      Calories: {nutrition.get('calories', 0)}, Protein: {nutrition.get('protein', 0)}g, Carbs: {nutrition.get('carbohydrates', 0)}g, Fat: {nutrition.get('fat', 0)}g")

if __name__ == "__main__":
    analyze_default_macros() 