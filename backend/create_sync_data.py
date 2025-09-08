#!/usr/bin/env python3
"""
Create sync data programmatically for Railway deployment
"""

import json
import os

def create_sync_data():
    """Create sync data with sample recipes for Railway"""
    
    # Sample recipes - you can expand this list
    sample_recipes = [
        {
            "id": "sample_1",
            "title": "Classic Spaghetti Carbonara",
            "description": "A traditional Italian pasta dish with eggs, cheese, and pancetta",
            "ingredients": [
                {"name": "spaghetti", "measure": "400g", "original": "400g spaghetti"},
                {"name": "eggs", "measure": "4 large", "original": "4 large eggs"},
                {"name": "parmesan cheese", "measure": "100g", "original": "100g parmesan cheese"},
                {"name": "pancetta", "measure": "150g", "original": "150g pancetta"},
                {"name": "black pepper", "measure": "1 tsp", "original": "1 tsp black pepper"},
                {"name": "salt", "measure": "to taste", "original": "salt to taste"}
            ],
            "instructions": "Cook spaghetti, mix with beaten eggs and cheese, add pancetta",
            "prep_time": 15,
            "cook_time": 20,
            "servings": 4,
            "cuisine": "Italian",
            "dietary_tags": ["vegetarian"],
            "difficulty": "medium",
            "image_url": "https://example.com/carbonara.jpg",
            "nutrition": {
                "calories": 450,
                "protein": 18,
                "carbs": 35,
                "fat": 25
            }
        },
        {
            "id": "sample_2",
            "title": "Chicken Stir Fry",
            "description": "Quick and healthy chicken stir fry with vegetables",
            "ingredients": [
                {"name": "chicken breast", "measure": "500g", "original": "500g chicken breast"},
                {"name": "bell peppers", "measure": "2", "original": "2 bell peppers"},
                {"name": "broccoli", "measure": "200g", "original": "200g broccoli"},
                {"name": "soy sauce", "measure": "3 tbsp", "original": "3 tbsp soy sauce"},
                {"name": "garlic", "measure": "3 cloves", "original": "3 cloves garlic"},
                {"name": "ginger", "measure": "1 inch", "original": "1 inch ginger"},
                {"name": "rice", "measure": "300g", "original": "300g rice"}
            ],
            "instructions": "Cut chicken, stir fry with vegetables, add sauce, serve over rice",
            "prep_time": 10,
            "cook_time": 15,
            "servings": 3,
            "cuisine": "Asian",
            "dietary_tags": ["gluten-free"],
            "difficulty": "easy",
            "image_url": "https://example.com/stirfry.jpg",
            "nutrition": {
                "calories": 320,
                "protein": 28,
                "carbs": 25,
                "fat": 12
            }
        }
    ]
    
    # Create sync data structure
    sync_data = {
        "sync_timestamp": "2025-09-08T06:00:00.000000",
        "recipes": sample_recipes
    }
    
    # Write to file
    sync_file_path = "/app/railway_sync_data.json"
    with open(sync_file_path, 'w') as f:
        json.dump(sync_data, f, indent=2)
    
    print(f"✓ Created sync data with {len(sample_recipes)} recipes at {sync_file_path}")
    return sync_file_path

if __name__ == "__main__":
    create_sync_data()
