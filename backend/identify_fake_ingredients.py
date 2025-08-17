#!/usr/bin/env python3
"""
Identify recipes with generic/fake ingredients
"""

import chromadb
import json
from collections import defaultdict

def identify_fake_ingredients():
    """Identify recipes that have generic/fake ingredients"""
    
    print("🔍 Identifying recipes with generic/fake ingredients...")
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('recipe_details_cache')
        
        total_recipes = collection.count()
        print(f"📊 Total recipes in ChromaDB: {total_recipes}")
        
        # Get all recipes
        results = collection.get(limit=total_recipes)
        
        # Track fake ingredients
        fake_ingredient_recipes = []
        real_ingredient_recipes = []
        generic_patterns = [
            'salt to taste',
            'black pepper to taste', 
            '2 tablespoons olive oil',
            'to taste',
            'pieces',
            'medium',
            'cloves'
        ]
        
        print("\n📋 Analyzing recipe ingredients...")
        
        for i, doc in enumerate(results['documents']):
            try:
                recipe = json.loads(doc)
                title = recipe.get('title', 'Unknown')
                ingredients = recipe.get('ingredients', [])
                recipe_id = recipe.get('id', 'unknown')
                
                if not ingredients:
                    continue
                
                # Check if ingredients look generic
                is_fake = False
                generic_count = 0
                
                for ing in ingredients:
                    if isinstance(ing, dict):
                        original = ing.get('original', '').lower()
                        name = ing.get('name', '').lower()
                        
                        # Check for generic patterns
                        for pattern in generic_patterns:
                            if pattern in original or pattern in name:
                                generic_count += 1
                                break
                        
                        # Check for very generic measurements
                        if ing.get('measure') in ['to taste', 'pieces', 'medium']:
                            generic_count += 1
                
                # If more than 50% of ingredients are generic, mark as fake
                if generic_count > len(ingredients) * 0.5:
                    is_fake = True
                    fake_ingredient_recipes.append({
                        'id': recipe_id,
                        'title': title,
                        'ingredients': ingredients,
                        'generic_count': generic_count,
                        'total_ingredients': len(ingredients)
                    })
                else:
                    real_ingredient_recipes.append({
                        'id': recipe_id,
                        'title': title,
                        'ingredients': ingredients
                    })
                
                # Progress indicator
                if (i + 1) % 100 == 0:
                    print(f"   Processed {i + 1}/{total_recipes} recipes...")
                    
            except Exception as e:
                print(f"Error processing recipe {i}: {e}")
        
        print("\n" + "=" * 60)
        print("📊 FAKE INGREDIENT ANALYSIS RESULTS")
        print("=" * 60)
        print(f"Total recipes: {total_recipes}")
        print(f"✅ Recipes with real ingredients: {len(real_ingredient_recipes)}")
        print(f"❌ Recipes with fake ingredients: {len(fake_ingredient_recipes)}")
        print(f"📈 Real ingredient coverage: {(len(real_ingredient_recipes)/total_recipes)*100:.1f}%")
        
        if fake_ingredient_recipes:
            print(f"\n📋 Sample recipes with fake ingredients:")
            for i, recipe in enumerate(fake_ingredient_recipes[:10], 1):
                print(f"   {i}. {recipe['title']} (ID: {recipe['id']})")
                print(f"      Generic: {recipe['generic_count']}/{recipe['total_ingredients']} ingredients")
                print(f"      Sample: {recipe['ingredients'][:2]}")
                print()
            
            if len(fake_ingredient_recipes) > 10:
                print(f"   ... and {len(fake_ingredient_recipes) - 10} more")
        
        # Analyze by source
        print(f"\n🔍 Analysis by recipe source:")
        mealdb_fake = 0
        spoonacular_fake = 0
        unknown_fake = 0
        
        for recipe in fake_ingredient_recipes:
            recipe_id = recipe['id']
            if 'mealdb' in str(recipe_id).lower():
                mealdb_fake += 1
            elif str(recipe_id).isdigit() and len(str(recipe_id)) > 6:
                spoonacular_fake += 1
            else:
                unknown_fake += 1
        
        print(f"   TheMealDB recipes with fake ingredients: {mealdb_fake}")
        print(f"   Spoonacular recipes with fake ingredients: {spoonacular_fake}")
        print(f"   Unknown source recipes with fake ingredients: {unknown_fake}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if fake_ingredient_recipes:
            print(f"   ⚠️  {len(fake_ingredient_recipes)} recipes have generic/fake ingredients")
            print(f"   🔑 Get a Spoonacular API key to fetch real ingredients for {spoonacular_fake} recipes")
            print(f"   🗑️  Or remove fake ingredients to show users that data is missing")
            print(f"   📚 Consider re-importing recipes from original sources")
        
        return {
            'total_recipes': total_recipes,
            'real_ingredient_recipes': len(real_ingredient_recipes),
            'fake_ingredient_recipes': len(fake_ingredient_recipes),
            'fake_recipes': fake_ingredient_recipes
        }
        
    except Exception as e:
        print(f"❌ Error analyzing recipes: {e}")
        return None

if __name__ == "__main__":
    identify_fake_ingredients()
