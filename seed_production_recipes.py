#!/usr/bin/env python3
"""
Production Recipe Seeding Script
Seeds recipes into ChromaDB for production deployment
"""

import sys
import os
import requests
import json
import time
from typing import List, Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def seed_recipes():
    """Seed recipes from TheMealDB and curated recipes"""
    try:
        # Initialize recipe cache service
        from services.recipe_cache_service import RecipeCacheService
        recipe_cache = RecipeCacheService()
        
        print("🍳 Production Recipe Seeding Script")
        print("=" * 50)
        
        # Check current recipe count
        try:
            count_result = recipe_cache.get_recipe_count()
            if isinstance(count_result, dict):
                current_count = count_result.get('total', 0)
            else:
                current_count = count_result
            print(f"📊 Current recipes in ChromaDB: {current_count}")
        except:
            current_count = 0
            print("📊 ChromaDB appears empty")
        
        if current_count > 0:
            user_input = input(f"ChromaDB already has {current_count} recipes. Continue? (y/N): ")
            if user_input.lower() != 'y':
                print("❌ Seeding cancelled")
                return
        
        print("\n🌱 Starting recipe seeding...")
        
        # Get recipes from TheMealDB (free API)
        categories = ['Seafood', 'Chicken', 'Beef', 'Pasta', 'Vegetarian', 'Dessert']
        total_added = 0
        
        for category in categories:
            try:
                print(f"\n📡 Fetching {category} recipes...")
                response = requests.get(f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category}", timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    meals = data.get('meals', [])[:12]  # Get 12 per category
                    
                    for i, meal in enumerate(meals):
                        print(f"  Processing {i+1}/{len(meals)}: {meal.get('strMeal', 'Unknown')}")
                        
                        # Get detailed recipe info
                        detail_response = requests.get(f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal['idMeal']}", timeout=10)
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            detailed_meal = detail_data.get('meals', [{}])[0]
                            
                            # Extract ingredients
                            ingredients = []
                            for j in range(1, 21):
                                ingredient = detailed_meal.get(f'strIngredient{j}', '').strip()
                                measure = detailed_meal.get(f'strMeasure{j}', '').strip()
                                if ingredient and ingredient.lower() != 'null':
                                    ingredients.append(f"{measure} {ingredient}".strip())
                            
                            # Format recipe for ChromaDB
                            recipe = {
                                'id': f"themealdb_{meal['idMeal']}",
                                'title': detailed_meal.get('strMeal', 'Unknown Recipe'),
                                'image': detailed_meal.get('strMealThumb', ''),
                                'cuisine': detailed_meal.get('strArea', category),
                                'cuisines': [detailed_meal.get('strArea', category)],
                                'ingredients': ingredients,
                                'instructions': detailed_meal.get('strInstructions', '').split('. ') if detailed_meal.get('strInstructions') else [],
                                'source': 'TheMealDB',
                                'category': category,
                                'diets': ['vegetarian'] if category == 'Vegetarian' else [],
                                'tags': [category.lower(), detailed_meal.get('strArea', '').lower()],
                                'ready_in_minutes': 45,
                                'difficulty': 'medium',
                                'description': f"Delicious {category.lower()} recipe from {detailed_meal.get('strArea', 'international')} cuisine."
                            }
                            
                            # Add to ChromaDB
                            try:
                                recipe_cache.cache_recipe(recipe['id'], recipe)
                                total_added += 1
                                print(f"    ✅ Added: {recipe['title']}")
                            except Exception as e:
                                print(f"    ❌ Failed to add {recipe['title']}: {e}")
                        
                        # Rate limiting
                        time.sleep(0.2)
                        
                else:
                    print(f"    ❌ Failed to fetch {category} recipes: {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Error fetching {category} recipes: {e}")
                continue
        
        # Add curated recipes
        print(f"\n🎨 Adding curated recipes...")
        curated_recipes = [
            {
                'id': 'curated_french_toast',
                'title': 'Classic French Toast',
                'image': 'https://images.unsplash.com/photo-1484723091739-30a097e8f929?w=500',
                'cuisine': 'French',
                'cuisines': ['French', 'Breakfast'],
                'ingredients': ['4 slices thick bread', '3 large eggs', '1/2 cup milk', '1 tsp vanilla extract', '1/2 tsp cinnamon', '2 tbsp butter', 'maple syrup'],
                'instructions': ['Whisk eggs, milk, vanilla, and cinnamon in a shallow dish', 'Dip each bread slice in mixture, coating both sides', 'Heat butter in a large skillet over medium heat', 'Cook bread slices until golden brown, about 3-4 minutes per side', 'Serve hot with maple syrup'],
                'source': 'Assistant',
                'diets': ['vegetarian'],
                'tags': ['breakfast', 'french', 'sweet'],
                'ready_in_minutes': 15,
                'difficulty': 'easy',
                'description': 'A classic breakfast favorite with crispy exterior and custardy interior.'
            },
            {
                'id': 'curated_avocado_toast',
                'title': 'Avocado Toast Supreme',
                'image': 'https://images.unsplash.com/photo-1541519227354-08fa5d50c44d?w=500',
                'cuisine': 'Modern',
                'cuisines': ['Modern', 'Healthy'],
                'ingredients': ['2 slices sourdough bread', '1 ripe avocado', '1 tbsp lemon juice', 'salt to taste', 'black pepper to taste', '1 tbsp olive oil', '1 medium tomato, sliced'],
                'instructions': ['Toast bread slices until golden', 'Mash avocado with lemon juice, salt, and pepper', 'Spread avocado mixture evenly on toast', 'Top with tomato slices', 'Drizzle with olive oil and season with additional salt and pepper'],
                'source': 'Assistant',
                'diets': ['vegetarian', 'vegan', 'healthy'],
                'tags': ['breakfast', 'healthy', 'quick'],
                'ready_in_minutes': 10,
                'difficulty': 'easy',
                'description': 'A nutritious and Instagram-worthy breakfast packed with healthy fats.'
            },
            {
                'id': 'curated_chicken_tikka_masala',
                'title': 'Chicken Tikka Masala',
                'image': 'https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=500',
                'cuisine': 'Indian',
                'cuisines': ['Indian', 'Asian'],
                'ingredients': ['1 lb chicken breast, cubed', '1 cup yogurt', '2 tbsp tikka masala spice', '1 onion, diced', '3 cloves garlic', '1 can tomato sauce', '1/2 cup heavy cream', 'basmati rice'],
                'instructions': ['Marinate chicken in yogurt and spices for 30 minutes', 'Cook chicken in a pan until golden', 'Sauté onion and garlic', 'Add tomato sauce and simmer', 'Add cooked chicken and cream', 'Serve over basmati rice'],
                'source': 'Assistant',
                'diets': [],
                'tags': ['indian', 'curry', 'dinner'],
                'ready_in_minutes': 60,
                'difficulty': 'medium',
                'description': 'A creamy, aromatic curry that\'s a favorite in Indian restaurants worldwide.'
            }
        ]
        
        for recipe in curated_recipes:
            try:
                recipe_cache.cache_recipe(recipe['id'], recipe)
                total_added += 1
                print(f"✅ Added curated: {recipe['title']}")
            except Exception as e:
                print(f"❌ Failed to add curated {recipe['title']}: {e}")
        
        print(f"\n🎉 Seeding complete!")
        print(f"📊 Total recipes added: {total_added}")
        
        # Verify final count
        try:
            final_count = recipe_cache.get_recipe_count()
            print(f"📊 Final recipes in ChromaDB: {final_count}")
        except Exception as e:
            print(f"⚠️ Could not verify final count: {e}")
        
        print("\n✅ Production seeding successful! Your app now has recipes.")
        return total_added
        
    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    seed_recipes()
