#!/usr/bin/env python3
"""
Analyze missing ingredients in recipes
"""

import chromadb
import json
from collections import defaultdict

def analyze_missing_ingredients():
    """Analyze how many recipes are missing ingredients"""
    
    print("🔍 Analyzing missing ingredients in recipes...")
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('recipe_details_cache')
        
        total_recipes = collection.count()
        print(f"📊 Total recipes in ChromaDB: {total_recipes}")
        
        # Get all recipes
        results = collection.get(limit=total_recipes)
        
        # Analyze ingredients
        missing_ingredients = 0
        empty_ingredients = 0
        recipes_with_ingredients = 0
        ingredient_count_distribution = defaultdict(int)
        
        print("\n📋 Analyzing recipe ingredients...")
        
        for i, doc in enumerate(results['documents']):
            try:
                recipe = json.loads(doc)
                title = recipe.get('title', 'Unknown')
                ingredients = recipe.get('ingredients', [])
                
                # Count ingredients
                ingredient_count = len(ingredients) if ingredients else 0
                ingredient_count_distribution[ingredient_count] += 1
                
                if not ingredients:
                    missing_ingredients += 1
                    if missing_ingredients <= 10:  # Show first 10 missing
                        print(f"❌ Missing ingredients: {title}")
                elif ingredient_count == 0:
                    empty_ingredients += 1
                    if empty_ingredients <= 10:  # Show first 10 empty
                        print(f"⚠️  Empty ingredients: {title}")
                else:
                    recipes_with_ingredients += 1
                    if i < 5:  # Show first 5 with ingredients
                        print(f"✅ Has ingredients ({ingredient_count}): {title}")
                
                # Progress indicator
                if (i + 1) % 100 == 0:
                    print(f"   Processed {i + 1}/{total_recipes} recipes...")
                    
            except Exception as e:
                print(f"Error processing recipe {i}: {e}")
                missing_ingredients += 1
        
        print("\n" + "=" * 60)
        print("📊 INGREDIENT ANALYSIS RESULTS")
        print("=" * 60)
        print(f"Total recipes: {total_recipes}")
        print(f"✅ Recipes with ingredients: {recipes_with_ingredients}")
        print(f"❌ Recipes missing ingredients: {missing_ingredients}")
        print(f"⚠️  Recipes with empty ingredients: {empty_ingredients}")
        print(f"📈 Ingredient coverage: {(recipes_with_ingredients/total_recipes)*100:.1f}%")
        
        print(f"\n📊 Ingredient count distribution:")
        for count in sorted(ingredient_count_distribution.keys()):
            percentage = (ingredient_count_distribution[count] / total_recipes) * 100
            print(f"   {count} ingredients: {ingredient_count_distribution[count]} recipes ({percentage:.1f}%)")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if missing_ingredients > 0:
            print(f"   ⚠️  {missing_ingredients} recipes are missing ingredients")
            print(f"   🔧 Run the fix_missing_ingredients.py script to fix this")
        
        if missing_ingredients > total_recipes * 0.1:
            print(f"   🚨 CRITICAL: More than 10% of recipes are missing ingredients!")
            print(f"   This will significantly impact user experience")
        
        if recipes_with_ingredients < total_recipes * 0.8:
            print(f"   ⚠️  Only {recipes_with_ingredients/total_recipes*100:.1f}% of recipes have ingredients")
            print(f"   Consider running ingredient fix script")
        
        return {
            'total_recipes': total_recipes,
            'recipes_with_ingredients': recipes_with_ingredients,
            'missing_ingredients': missing_ingredients,
            'empty_ingredients': empty_ingredients,
            'coverage_percentage': (recipes_with_ingredients/total_recipes)*100
        }
        
    except Exception as e:
        print(f"❌ Error analyzing recipes: {e}")
        return None

if __name__ == "__main__":
    analyze_missing_ingredients()
