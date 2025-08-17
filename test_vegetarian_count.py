#!/usr/bin/env python3
"""
Test script to check vegetarian recipe counts with different filtering approaches
"""
import requests
import json

BASE_URL = "http://localhost:5003"

def test_vegetarian_counts():
    """Test different approaches to find vegetarian recipes"""
    
    print("=== Testing Vegetarian Recipe Counts ===\n")
    
    # Test 1: Check total recipes available
    print("1. Checking total recipes available...")
    response = requests.get(f"{BASE_URL}/get_recipes?limit=1000")
    if response.status_code == 200:
        data = response.json()
        total_recipes = data.get('total', 0)
        print(f"   Total recipes in database: {total_recipes}")
    else:
        print(f"   Error getting total recipes: {response.status_code}")
        return
    
    # Test 2: Check recipes with explicit vegetarian tag
    print("\n2. Checking recipes with explicit 'vegetarian' tag...")
    response = requests.get(f"{BASE_URL}/get_recipes?dietary_restrictions=vegetarian&limit=1000")
    if response.status_code == 200:
        data = response.json()
        explicit_vegetarian = data.get('total', 0)
        print(f"   Recipes with explicit 'vegetarian' tag: {explicit_vegetarian}")
    else:
        print(f"   Error getting vegetarian recipes: {response.status_code}")
    
    # Test 3: Check recipes with 'diets' field containing vegetarian
    print("\n3. Checking recipes with 'diets' field containing vegetarian...")
    response = requests.get(f"{BASE_URL}/get_recipes?limit=1000")
    if response.status_code == 200:
        data = response.json()
        recipes = data.get('results', [])
        
        diets_vegetarian = 0
        for recipe in recipes:
            diets = recipe.get('diets', [])
            if isinstance(diets, list) and 'vegetarian' in [d.lower() for d in diets if d]:
                diets_vegetarian += 1
        
        print(f"   Recipes with 'diets' containing 'vegetarian': {diets_vegetarian}")
    else:
        print(f"   Error getting recipes for analysis: {response.status_code}")
    
    # Test 4: Check recipes with 'dietaryRestrictions' field containing vegetarian
    print("\n4. Checking recipes with 'dietaryRestrictions' field containing vegetarian...")
    if response.status_code == 200:
        dietary_vegetarian = 0
        for recipe in recipes:
            dietary = recipe.get('dietaryRestrictions', [])
            if isinstance(dietary, list) and 'vegetarian' in [d.lower() for d in dietary if d]:
                dietary_vegetarian += 1
        
        print(f"   Recipes with 'dietaryRestrictions' containing 'vegetarian': {dietary_vegetarian}")
    
    # Test 5: Check recipes with vegetarian boolean flag
    print("\n5. Checking recipes with vegetarian=True flag...")
    if response.status_code == 200:
        boolean_vegetarian = 0
        for recipe in recipes:
            if recipe.get('vegetarian') is True:
                boolean_vegetarian += 1
        
        print(f"   Recipes with vegetarian=True: {boolean_vegetarian}")
    
    # Test 6: Check recipes that might be vegetarian by ingredients (no meat)
    print("\n6. Checking recipes that might be vegetarian by ingredients...")
    if response.status_code == 200:
        meat_indicators = [
            'chicken', 'beef', 'pork', 'lamb', 'fish', 'salmon', 'tuna', 'shrimp', 'prawn', 
            'meat', 'bacon', 'ham', 'sausage', 'turkey', 'duck', 'goose', 'venison', 
            'rabbit', 'quail', 'pheasant', 'veal', 'mackerel', 'haddock', 'clam', 'oyster',
            'mussel', 'scallop', 'crab', 'lobster', 'anchovy', 'sardine', 'trout', 'cod',
            'halibut', 'sea bass', 'tilapia', 'catfish', 'swordfish', 'mahi mahi'
        ]
        
        potential_vegetarian = 0
        for recipe in recipes:
            # Get ingredients text
            ingredients_text = ""
            if recipe.get('ingredients'):
                for ing in recipe['ingredients']:
                    if isinstance(ing, dict) and 'name' in ing:
                        ingredients_text += " " + str(ing['name']).lower()
                    elif isinstance(ing, str):
                        ingredients_text += " " + ing.lower()
            
            # Get instructions text
            instructions = recipe.get('instructions', '')
            if isinstance(instructions, list):
                instructions = ' '.join(str(step) for step in instructions)
            instructions = str(instructions).lower()
            
            # Combine all text
            all_text = ingredients_text + " " + instructions
            
            # Check if no meat indicators found
            has_meat = any(meat in all_text for meat in meat_indicators)
            if not has_meat:
                potential_vegetarian += 1
        
        print(f"   Recipes with no meat ingredients (potential vegetarian): {potential_vegetarian}")
    
    print("\n=== Summary ===")
    print(f"Total recipes: {total_recipes}")
    print(f"Explicit vegetarian tag: {explicit_vegetarian}")
    print(f"Potential vegetarian by ingredients: {potential_vegetarian}")
    print(f"Expected vegetarian recipes: ~{potential_vegetarian}")

if __name__ == "__main__":
    test_vegetarian_counts()

