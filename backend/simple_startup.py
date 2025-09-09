#!/usr/bin/env python3
"""
Simple startup script for Railway
This creates sample data without relying on persistent volumes
"""

import os
import sys
import json
import time
from pathlib import Path

def create_sample_data():
    """Create sample recipe data"""
    try:
        print("📁 Creating sample recipe data...")
        
        # Sample recipe data with complete information
        sample_recipes = [
            {
                "id": "52961",
                "title": "Budino Di Ricotta",
                "cuisine": "Italian",
                "cuisines": ["italian"],
                "diets": "vegetarian",
                "ingredients": [
                    {"name": "Ricotta", "measure": "500g", "original": "500g Ricotta"},
                    {"name": "Eggs", "measure": "4 large", "original": "4 large Eggs"},
                    {"name": "Flour", "measure": "3 tbs", "original": "3 tbs Flour"},
                    {"name": "Sugar", "measure": "250g", "original": "250g Sugar"},
                    {"name": "Cinnamon", "measure": "1 tsp", "original": "1 tsp Cinnamon"},
                    {"name": "Grated Zest of 2 Lemons", "measure": "", "original": "Grated Zest of 2 Lemons"},
                    {"name": "Dark Rum", "measure": "5 tbs", "original": "5 tbs Dark Rum"},
                    {"name": "Icing Sugar", "measure": "sprinkling", "original": "sprinkling Icing Sugar"}
                ],
                "instructions": [
                    "Mash the ricotta and beat well with the egg yolks, stir in the flour, sugar, cinnamon, grated lemon rind and the rum and mix well. You can do this in a food processor. Beat the egg whites until stiff, fold in and pour into a buttered and floured 25cm cake tin. Bake in the oven at 180ºC/160ºC fan/gas.",
                    "For about.",
                    "Minutes, or until it is firm. Serve hot or cold dusted with icing sugar."
                ],
                "calories": 350,
                "protein": 12,
                "carbs": 44,
                "fat": 14,
                "image": "https://www.themealdb.com/images/media/meals/1549542877.jpg"
            },
            {
                "id": "52772",
                "title": "Teriyaki Chicken Casserole",
                "cuisine": "Japanese",
                "cuisines": ["japanese"],
                "diets": "gluten free",
                "ingredients": [
                    {"name": "Chicken Thighs", "measure": "6", "original": "6 Chicken Thighs"},
                    {"name": "Soy Sauce", "measure": "1/2 cup", "original": "1/2 cup Soy Sauce"},
                    {"name": "Brown Sugar", "measure": "1/2 cup", "original": "1/2 cup Brown Sugar"},
                    {"name": "Garlic", "measure": "3 cloves", "original": "3 cloves Garlic"},
                    {"name": "Ginger", "measure": "1 inch", "original": "1 inch Ginger"},
                    {"name": "Rice", "measure": "2 cups", "original": "2 cups Rice"}
                ],
                "instructions": [
                    "Preheat oven to 350°F. Place chicken thighs in a baking dish.",
                    "Mix soy sauce, brown sugar, garlic, and ginger in a bowl.",
                    "Pour sauce over chicken and bake for 45 minutes.",
                    "Serve over rice."
                ],
                "calories": 420,
                "protein": 28,
                "carbs": 35,
                "fat": 18,
                "image": "https://www.themealdb.com/images/media/meals/wvpsxx1468256321.jpg"
            },
            {
                "id": "52773",
                "title": "Beef and Mushroom Stew",
                "cuisine": "American",
                "cuisines": ["american"],
                "diets": "gluten free",
                "ingredients": [
                    {"name": "Beef Chuck", "measure": "2 lbs", "original": "2 lbs Beef Chuck"},
                    {"name": "Mushrooms", "measure": "1 lb", "original": "1 lb Mushrooms"},
                    {"name": "Onions", "measure": "2 large", "original": "2 large Onions"},
                    {"name": "Carrots", "measure": "4", "original": "4 Carrots"},
                    {"name": "Beef Broth", "measure": "4 cups", "original": "4 cups Beef Broth"},
                    {"name": "Red Wine", "measure": "1 cup", "original": "1 cup Red Wine"}
                ],
                "instructions": [
                    "Cut beef into 1-inch cubes and season with salt and pepper.",
                    "Brown beef in batches in a large pot over medium-high heat.",
                    "Add onions and carrots, cook until softened.",
                    "Add mushrooms, broth, and wine. Bring to a boil, then simmer for 2 hours.",
                    "Serve hot with crusty bread."
                ],
                "calories": 380,
                "protein": 32,
                "carbs": 18,
                "fat": 22,
                "image": "https://www.themealdb.com/images/media/meals/1529444830.jpg"
            }
        ]
        
        # Save to a simple JSON file
        data_file = Path("sample_recipes.json")
        with open(data_file, 'w') as f:
            json.dump(sample_recipes, f, indent=2)
        
        print(f"✅ Created {len(sample_recipes)} sample recipes")
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 Simple Railway startup...")
    
    # Create sample data
    if create_sample_data():
        print("✅ Sample data created successfully")
    else:
        print("❌ Failed to create sample data")

if __name__ == "__main__":
    main()
