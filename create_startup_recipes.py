#!/usr/bin/env python3
"""
Create a recipes_data.json file for automatic startup loading
This will take recipes from existing data and create a clean startup file
"""

import json
import os

def create_startup_recipes():
    """Create a recipes_data.json file for automatic startup loading"""
    
    # Try to load from the large data file
    source_files = [
        'complete_railway_sync_data.json',
        'batch_1.json', 
        'batch_2.json'
    ]
    
    all_recipes = []
    
    for source_file in source_files:
        if os.path.exists(source_file):
            try:
                print(f"📁 Loading from {source_file}...")
                with open(source_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different data structures
                if isinstance(data, dict):
                    recipes = data.get('recipes', data.get('data', []))
                elif isinstance(data, list):
                    recipes = data
                else:
                    print(f"⚠️ Unknown data structure in {source_file}")
                    continue
                
                print(f"📊 Found {len(recipes)} recipes in {source_file}")
                all_recipes.extend(recipes)
                
                if len(all_recipes) >= 1500:  # Limit for startup
                    break
                    
            except Exception as e:
                print(f"❌ Error loading {source_file}: {e}")
                continue
    
    # Add our curated recipes
    curated_recipes = [
        {
            "id": "curated_french_toast",
            "title": "Perfect French Toast",
            "image": "https://images.unsplash.com/photo-1484723091739-30a097e8f929?w=500",
            "cuisine": "French",
            "cuisines": ["French", "Breakfast"],
            "ingredients": ["4 slices thick bread", "3 large eggs", "1/2 cup milk", "1 tsp vanilla extract", "1 tsp cinnamon", "2 tbsp butter", "maple syrup"],
            "instructions": [
                "Whisk together eggs, milk, vanilla, and cinnamon in a shallow dish",
                "Heat butter in a large skillet over medium heat",
                "Dip each bread slice in egg mixture, coating both sides",
                "Cook in skillet 2-3 minutes per side until golden brown",
                "Serve immediately with maple syrup"
            ],
            "diets": ["vegetarian"],
            "tags": ["breakfast", "easy", "sweet", "comfort food"],
            "ready_in_minutes": 15,
            "difficulty": "easy",
            "servings": 2,
            "source": "curated"
        },
        {
            "id": "curated_overnight_oats",
            "title": "Overnight Oats with Berries",
            "image": "https://images.unsplash.com/photo-1571197119587-cfac4ac57e4a?w=500",
            "cuisine": "American",
            "cuisines": ["American", "Healthy"],
            "ingredients": ["1/2 cup rolled oats", "1/2 cup milk", "1 tbsp chia seeds", "1 tbsp maple syrup", "1/4 cup mixed berries", "1 tbsp almond butter"],
            "instructions": [
                "Combine oats, milk, chia seeds, and maple syrup in a jar",
                "Stir well and refrigerate overnight",
                "In the morning, top with berries and almond butter",
                "Enjoy cold or at room temperature"
            ],
            "diets": ["vegetarian", "healthy", "gluten-free"],
            "tags": ["breakfast", "no-cook", "healthy", "meal-prep"],
            "ready_in_minutes": 5,
            "difficulty": "easy",
            "servings": 1,
            "source": "curated"
        },
        {
            "id": "curated_avocado_toast",
            "title": "Gourmet Avocado Toast",
            "image": "https://images.unsplash.com/photo-1541519227354-08fa5d50c44d?w=500",
            "cuisine": "Modern",
            "cuisines": ["Modern", "Healthy"],
            "ingredients": ["2 slices sourdough bread", "1 ripe avocado", "1 tbsp lime juice", "salt and pepper", "cherry tomatoes", "feta cheese", "olive oil"],
            "instructions": [
                "Toast bread until golden brown",
                "Mash avocado with lime juice, salt, and pepper",
                "Spread avocado mixture on toast",
                "Top with sliced cherry tomatoes and crumbled feta",
                "Drizzle with olive oil and season"
            ],
            "diets": ["vegetarian", "healthy"],
            "tags": ["breakfast", "lunch", "healthy", "quick"],
            "ready_in_minutes": 10,
            "difficulty": "easy",
            "servings": 2,
            "source": "curated"
        },
        {
            "id": "curated_quinoa_bowl",
            "title": "Mediterranean Quinoa Bowl",
            "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500",
            "cuisine": "Mediterranean",
            "cuisines": ["Mediterranean", "Healthy"],
            "ingredients": ["1 cup cooked quinoa", "cucumber", "cherry tomatoes", "red onion", "olives", "feta cheese", "olive oil", "lemon juice", "oregano"],
            "instructions": [
                "Cook quinoa according to package directions",
                "Dice cucumber, tomatoes, and red onion",
                "Combine quinoa with vegetables and olives",
                "Whisk olive oil, lemon juice, and oregano for dressing",
                "Top with feta cheese and serve"
            ],
            "diets": ["vegetarian", "gluten-free", "healthy"],
            "tags": ["lunch", "dinner", "healthy", "protein-rich"],
            "ready_in_minutes": 20,
            "difficulty": "easy",
            "servings": 2,
            "source": "curated"
        },
        {
            "id": "curated_thai_lettuce_wraps",
            "title": "Thai Chicken Lettuce Wraps",
            "image": "https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?w=500",
            "cuisine": "Thai",
            "cuisines": ["Thai", "Asian"],
            "ingredients": ["1 lb ground chicken", "butter lettuce", "carrots", "red bell pepper", "green onions", "cilantro", "peanuts", "soy sauce", "sesame oil", "lime juice", "sriracha"],
            "instructions": [
                "Cook ground chicken in a large skillet",
                "Add diced vegetables and cook until tender",
                "Mix soy sauce, sesame oil, lime juice, and sriracha",
                "Add sauce to chicken mixture",
                "Serve in lettuce cups with peanuts and cilantro"
            ],
            "diets": ["gluten-free", "low-carb"],
            "tags": ["dinner", "appetizer", "healthy", "spicy"],
            "ready_in_minutes": 25,
            "difficulty": "medium",
            "servings": 4,
            "source": "curated"
        }
    ]
    
    # Add curated recipes to the collection
    all_recipes.extend(curated_recipes)
    
    # Take up to 1500 recipes for good variety but not overwhelming startup
    selected_recipes = all_recipes[:1500]
    
    # Create the recipes_data.json file
    startup_data = {
        "recipes": selected_recipes,
        "metadata": {
            "created_at": "2025-09-12",
            "total_recipes": len(selected_recipes),
            "purpose": "Automatic startup loading for Render deployment",
            "sources": source_files
        }
    }
    
    # Write to recipes_data.json
    with open('recipes_data.json', 'w', encoding='utf-8') as f:
        json.dump(startup_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created recipes_data.json with {len(selected_recipes)} recipes")
    print(f"📁 File size: {os.path.getsize('recipes_data.json') / (1024*1024):.1f} MB")
    print(f"🚀 This file will be automatically loaded on startup!")
    
    return len(selected_recipes)

if __name__ == "__main__":
    print("🍳 Creating Startup Recipes File")
    print("=" * 40)
    
    recipe_count = create_startup_recipes()
    
    print("\n" + "=" * 40)
    print(f"🎉 Successfully created startup file with {recipe_count} recipes!")
    print("🚀 Deploy to see recipes automatically loaded!")
