#!/usr/bin/env python3
"""
ChromaDB Setup Script for Recipe App

This script initializes ChromaDB collections and indexes sample data
to get you started with the intelligent features.
"""

import sys
import os
import json
from typing import List, Dict, Any

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.recipe_search_service import RecipeSearchService
from services.meal_history_service import MealHistoryService
from services.smart_shopping_service import SmartShoppingService
from services.user_preferences_service import UserPreferencesService

def create_sample_recipes() -> List[Dict[str, Any]]:
    """Create sample recipes for indexing"""
    return [
        {
            "id": "recipe_1",
            "name": "Mediterranean Quinoa Bowl",
            "cuisine": "Mediterranean",
            "ingredients": [
                "quinoa", "chickpeas", "cucumber", "cherry tomatoes",
                "red onion", "feta cheese", "olive oil", "lemon juice",
                "oregano", "salt", "pepper"
            ],
            "instructions": [
                "Cook quinoa according to package instructions",
                "Dice cucumber, tomatoes, and red onion",
                "Drain and rinse chickpeas",
                "Whisk together olive oil, lemon juice, oregano, salt, and pepper",
                "Combine all ingredients and toss with dressing",
                "Top with crumbled feta cheese"
            ],
            "dietaryRestrictions": ["vegetarian", "gluten-free"],
            "difficulty": "easy",
            "mealType": "lunch",
            "cookingTime": "25 minutes",
            "ratings": [4.5, 4.8, 4.2, 4.7],
            "comments": []
        },
        {
            "id": "recipe_2",
            "name": "Cozy Chicken Stew",
            "cuisine": "American",
            "ingredients": [
                "chicken breast", "carrots", "celery", "onion",
                "potatoes", "chicken broth", "thyme", "bay leaves",
                "garlic", "flour", "butter", "salt", "pepper"
            ],
            "instructions": [
                "Cut chicken into bite-sized pieces",
                "Chop vegetables into chunks",
                "Sauté onion and garlic in butter",
                "Add chicken and brown on all sides",
                "Add vegetables and seasonings",
                "Pour in broth and simmer for 45 minutes",
                "Thicken with flour if desired"
            ],
            "dietaryRestrictions": [],
            "difficulty": "intermediate",
            "mealType": "dinner",
            "cookingTime": "60 minutes",
            "ratings": [4.6, 4.9, 4.4, 4.8, 4.7],
            "comments": []
        },
        {
            "id": "recipe_3",
            "name": "Quick Avocado Toast",
            "cuisine": "Modern",
            "ingredients": [
                "whole grain bread", "avocado", "lime juice",
                "cherry tomatoes", "red pepper flakes", "salt",
                "hemp seeds", "olive oil"
            ],
            "instructions": [
                "Toast bread until golden",
                "Mash avocado with lime juice and salt",
                "Spread avocado mixture on toast",
                "Top with halved cherry tomatoes",
                "Sprinkle with red pepper flakes and hemp seeds",
                "Drizzle with olive oil"
            ],
            "dietaryRestrictions": ["vegetarian", "vegan"],
            "difficulty": "easy",
            "mealType": "breakfast",
            "cookingTime": "10 minutes",
            "ratings": [4.3, 4.1, 4.5, 4.2],
            "comments": []
        },
        {
            "id": "recipe_4",
            "name": "Spicy Thai Curry",
            "cuisine": "Thai",
            "ingredients": [
                "coconut milk", "red curry paste", "chicken thighs",
                "bell peppers", "bamboo shoots", "Thai basil",
                "fish sauce", "brown sugar", "lime juice",
                "jasmine rice", "garlic", "ginger"
            ],
            "instructions": [
                "Cook jasmine rice",
                "Heat coconut milk in a wok",
                "Add curry paste and cook until fragrant",
                "Add chicken and cook until done",
                "Add vegetables and simmer",
                "Season with fish sauce, sugar, and lime juice",
                "Garnish with Thai basil and serve over rice"
            ],
            "dietaryRestrictions": ["gluten-free"],
            "difficulty": "intermediate",
            "mealType": "dinner",
            "cookingTime": "35 minutes",
            "ratings": [4.8, 4.9, 4.6, 4.7, 4.8],
            "comments": []
        },
        {
            "id": "recipe_5",
            "name": "Protein Power Smoothie",
            "cuisine": "Modern",
            "ingredients": [
                "banana", "spinach", "protein powder", "almond milk",
                "peanut butter", "chia seeds", "honey", "ice cubes"
            ],
            "instructions": [
                "Add all ingredients to blender",
                "Blend until smooth and creamy",
                "Add more almond milk if needed",
                "Serve immediately"
            ],
            "dietaryRestrictions": ["vegetarian", "gluten-free"],
            "difficulty": "easy",
            "mealType": "breakfast",
            "cookingTime": "5 minutes",
            "ratings": [4.4, 4.6, 4.3, 4.5],
            "comments": []
        }
    ]

def create_sample_preferences() -> Dict[str, Any]:
    """Create sample user preferences"""
    return {
        "dietaryRestrictions": ["vegetarian"],
        "favoriteCuisines": ["Mediterranean", "Asian", "Modern"],
        "allergens": ["nuts"],
        "cookingSkillLevel": "intermediate",
        "healthGoals": ["weight loss", "general wellness"],
        "maxCookingTime": "45 minutes"
    }

def setup_chromadb():
    """Initialize ChromaDB collections and index sample data"""
    print("🚀 Setting up ChromaDB for Recipe App...")
    
    try:
        # Initialize services
        print("📊 Initializing services...")
        recipe_search_service = RecipeSearchService()
        meal_history_service = MealHistoryService()
        smart_shopping_service = SmartShoppingService()
        user_preferences_service = UserPreferencesService()
        
        # Create sample data
        print("📝 Creating sample data...")
        sample_recipes = create_sample_recipes()
        sample_preferences = create_sample_preferences()
        
        # Index sample recipes
        print("🔍 Indexing sample recipes for semantic search...")
        recipe_search_service.bulk_index_recipes(sample_recipes)
        print(f"✅ Indexed {len(sample_recipes)} recipes")
        
        # Save sample user preferences
        print("👤 Setting up demo user preferences...")
        user_preferences_service.save_preferences("demo_user", sample_preferences)
        print("✅ Demo user preferences saved")
        
        # Create sample meal plan for testing
        print("🍽️ Creating sample meal plan...")
        sample_meal_plan = {
            "monday": {
                "breakfast": {
                    "id": "recipe_3",
                    "name": "Quick Avocado Toast",
                    "cuisine": "Modern",
                    "ingredients": ["whole grain bread", "avocado", "lime juice"],
                    "difficulty": "easy"
                },
                "lunch": {
                    "id": "recipe_1",
                    "name": "Mediterranean Quinoa Bowl",
                    "cuisine": "Mediterranean",
                    "ingredients": ["quinoa", "chickpeas", "cucumber"],
                    "difficulty": "easy"
                },
                "dinner": {
                    "id": "recipe_2",
                    "name": "Cozy Chicken Stew",
                    "cuisine": "American",
                    "ingredients": ["chicken breast", "carrots", "celery"],
                    "difficulty": "intermediate"
                }
            }
        }
        
        # Log sample meal generation
        meal_history_service.log_meal_generated("demo_user", sample_meal_plan, sample_preferences)
        print("✅ Sample meal plan logged")
        
        # Add sample feedback
        print("📊 Adding sample feedback...")
        meal_history_service.log_meal_feedback("demo_user", "recipe_1", "liked", 5, "Loved this healthy bowl!")
        meal_history_service.log_meal_feedback("demo_user", "recipe_2", "cooked", 4, "Very comforting")
        meal_history_service.log_meal_feedback("demo_user", "recipe_3", "liked", 4)
        print("✅ Sample feedback added")
        
        # Test semantic search
        print("🔍 Testing semantic search...")
        search_results = recipe_search_service.semantic_search("healthy lunch bowl", limit=3)
        print(f"✅ Semantic search test: found {len(search_results)} results")
        
        # Test recommendations
        print("🎯 Testing personalized recommendations...")
        recommendations = recipe_search_service.get_recipe_recommendations(sample_preferences, limit=3)
        print(f"✅ Recommendations test: found {len(recommendations)} recommendations")
        
        # Test smart shopping list
        print("🛒 Testing smart shopping list...")
        shopping_list = smart_shopping_service.create_smart_shopping_list(
            "demo_user", 
            [sample_meal_plan], 
            sample_preferences.get("dietaryRestrictions", [])
        )
        print(f"✅ Smart shopping list created with {shopping_list['total_items']} items")
        
        print("\n🎉 ChromaDB setup completed successfully!")
        print("\n📋 What's been set up:")
        print("   • Recipe semantic search with 5 sample recipes")
        print("   • Demo user with preferences")
        print("   • Sample meal history and feedback")
        print("   • Ingredient knowledge base")
        print("   • Smart shopping list capabilities")
        
        print("\n🚀 Try these API endpoints:")
        print("   • POST /api/search/semantic - Semantic recipe search")
        print("   • GET /api/recommendations - Personalized recommendations")
        print("   • GET /api/meal-history/patterns/demo_user - User patterns")
        print("   • POST /api/shopping/smart-list - Smart shopping lists")
        
        print("\n💡 Example semantic searches to try:")
        print("   • 'comfort food for cold weather'")
        print("   • 'healthy breakfast with protein'")
        print("   • 'quick vegetarian lunch'")
        print("   • 'spicy dinner with vegetables'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up ChromaDB: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_chromadb_features():
    """Test ChromaDB features to ensure they're working"""
    print("\n🧪 Testing ChromaDB features...")
    
    try:
        recipe_search_service = RecipeSearchService()
        
        # Test 1: Semantic search
        print("Test 1: Semantic search for 'healthy bowl'")
        results = recipe_search_service.semantic_search("healthy bowl", limit=2)
        print(f"   ✅ Found {len(results)} results")
        
        # Test 2: Similar recipes
        print("Test 2: Find similar recipes to recipe_1")
        similar = recipe_search_service.find_similar_recipes("recipe_1", limit=2)
        print(f"   ✅ Found {len(similar)} similar recipes")
        
        # Test 3: User patterns
        print("Test 3: Get user meal patterns")
        meal_history_service = MealHistoryService()
        patterns = meal_history_service.get_user_meal_patterns("demo_user")
        print(f"   ✅ Found patterns for {len(patterns.get('preferred_cuisines', {}))} cuisines")
        
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔮 ChromaDB Setup Script for Recipe App")
    print("=" * 50)
    
    # Setup ChromaDB
    success = setup_chromadb()
    
    if success:
        # Run tests
        test_success = test_chromadb_features()
        
        if test_success:
            print("\n🎯 Setup completed successfully!")
            print("Your recipe app now has intelligent ChromaDB features!")
        else:
            print("\n⚠️  Setup completed but some tests failed.")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        sys.exit(1) 