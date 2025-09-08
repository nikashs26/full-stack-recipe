#!/usr/bin/env python3
"""
Update cuisine tags for recipes on Railway
This script connects to Railway and updates recipes that have missing or generic cuisine tags
"""

import requests
import json
import time
from typing import Dict, List, Any

class RailwayCuisineUpdater:
    def __init__(self, railway_url: str = "https://full-stack-recipe-production.up.railway.app"):
        self.railway_url = railway_url.rstrip('/')
        self.api_url = f"{self.railway_url}/api"
        
    def get_all_recipes(self) -> List[Dict[str, Any]]:
        """Get all recipes from Railway"""
        try:
            # Get recipes in batches
            all_recipes = []
            offset = 0
            limit = 100
            
            while True:
                response = requests.get(
                    f"{self.api_url}/get_recipes",
                    params={"limit": limit, "offset": offset},
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"❌ Error fetching recipes: {response.status_code}")
                    break
                
                data = response.json()
                recipes = data.get('results', [])
                
                if not recipes:
                    break
                    
                all_recipes.extend(recipes)
                print(f"📥 Fetched {len(recipes)} recipes (total: {len(all_recipes)})")
                
                if len(recipes) < limit:
                    break
                    
                offset += limit
                time.sleep(0.5)  # Rate limiting
                
            return all_recipes
            
        except Exception as e:
            print(f"❌ Error getting recipes: {e}")
            return []
    
    def normalize_cuisine(self, recipe: Dict[str, Any]) -> str:
        """Normalize cuisine based on recipe data"""
        title = recipe.get('title', '').lower()
        ingredients = recipe.get('ingredients', '').lower()
        
        # Cuisine detection based on title and ingredients
        if any(word in title for word in ['pasta', 'risotto', 'parmesan', 'italian', 'pizza', 'lasagna']):
            return 'Italian'
        elif any(word in title for word in ['curry', 'tandoori', 'biryani', 'dal', 'naan', 'indian']):
            return 'Indian'
        elif any(word in title for word in ['sushi', 'ramen', 'teriyaki', 'japanese', 'tempura']):
            return 'Japanese'
        elif any(word in title for word in ['taco', 'burrito', 'enchilada', 'mexican', 'quesadilla']):
            return 'Mexican'
        elif any(word in title for word in ['pad thai', 'tom yum', 'thai', 'green curry', 'red curry']):
            return 'Thai'
        elif any(word in title for word in ['pho', 'vietnamese', 'banh mi', 'spring roll']):
            return 'Vietnamese'
        elif any(word in title for word in ['kimchi', 'korean', 'bulgogi', 'bibimbap']):
            return 'Korean'
        elif any(word in title for word in ['chinese', 'kung pao', 'lo mein', 'fried rice']):
            return 'Chinese'
        elif any(word in title for word in ['french', 'ratatouille', 'coq au vin', 'bouillabaisse']):
            return 'French'
        elif any(word in title for word in ['greek', 'moussaka', 'tzatziki', 'gyro']):
            return 'Greek'
        elif any(word in title for word in ['spanish', 'paella', 'gazpacho', 'tapas']):
            return 'Spanish'
        elif any(word in title for word in ['american', 'burger', 'bbq', 'southern', 'cajun']):
            return 'American'
        elif any(word in title for word in ['british', 'fish and chips', 'shepherd', 'english']):
            return 'British'
        elif any(word in title for word in ['german', 'sauerkraut', 'bratwurst', 'schnitzel']):
            return 'German'
        elif any(word in title for word in ['russian', 'borscht', 'pelmeni', 'blini']):
            return 'Russian'
        elif any(word in title for word in ['mexican', 'tortilla', 'salsa', 'guacamole']):
            return 'Mexican'
        elif any(word in title for word in ['mediterranean', 'olive', 'feta', 'hummus']):
            return 'Mediterranean'
        elif any(word in title for word in ['middle eastern', 'falafel', 'tahini', 'zaatar']):
            return 'Middle Eastern'
        elif any(word in title for word in ['caribbean', 'jamaican', 'jerk', 'plantain']):
            return 'Caribbean'
        elif any(word in title for word in ['african', 'ethiopian', 'moroccan', 'tagine']):
            return 'African'
        elif any(word in title for word in ['latin american', 'brazilian', 'peruvian', 'argentinian']):
            return 'Latin American'
        
        # Check ingredients for cuisine clues
        if any(ingredient in ingredients for ingredient in ['soy sauce', 'hoisin', 'oyster sauce', 'ginger', 'garlic']):
            return 'Chinese'
        elif any(ingredient in ingredients for ingredient in ['curry powder', 'garam masala', 'tandoori', 'cardamom']):
            return 'Indian'
        elif any(ingredient in ingredients for ingredient in ['miso', 'wasabi', 'sake', 'mirin']):
            return 'Japanese'
        elif any(ingredient in ingredients for ingredient in ['cilantro', 'lime', 'jalapeno', 'cumin']):
            return 'Mexican'
        elif any(ingredient in ingredients for ingredient in ['lemongrass', 'fish sauce', 'coconut milk', 'kaffir lime']):
            return 'Thai'
        elif any(ingredient in ingredients for ingredient in ['gochujang', 'kimchi', 'sesame oil', 'soy sauce']):
            return 'Korean'
        elif any(ingredient in ingredients for ingredient in ['olive oil', 'feta', 'oregano', 'basil']):
            return 'Mediterranean'
        elif any(ingredient in ingredients for ingredient in ['tahini', 'sumac', 'zaatar', 'pomegranate']):
            return 'Middle Eastern'
        
        # Default fallback
        return 'International'
    
    def update_recipe_cuisine(self, recipe_id: str, new_cuisine: str) -> bool:
        """Update a single recipe's cuisine on Railway"""
        try:
            # This would need to be implemented as an API endpoint on Railway
            # For now, we'll just print what would be updated
            print(f"🔄 Would update recipe {recipe_id} to cuisine: {new_cuisine}")
            return True
        except Exception as e:
            print(f"❌ Error updating recipe {recipe_id}: {e}")
            return False
    
    def update_cuisines(self):
        """Main function to update cuisines for all recipes"""
        print("🚀 Starting Railway cuisine update...")
        
        # Get all recipes
        recipes = self.get_all_recipes()
        if not recipes:
            print("❌ No recipes found")
            return
        
        print(f"📊 Found {len(recipes)} recipes to check")
        
        updated_count = 0
        needs_update = []
        
        # Find recipes that need cuisine updates
        for recipe in recipes:
            # Extract recipe data from the nested structure
            recipe_data = recipe.get('data', {})
            metadata = recipe.get('metadata', {})
            
            # Get cuisine from metadata
            current_cuisine = metadata.get('cuisine', '').lower()
            title = metadata.get('title', recipe_data.get('title', ''))
            
            # Skip if already has a specific cuisine
            if current_cuisine and current_cuisine not in ['', 'other', 'none', 'null', 'international']:
                continue
            
            # Determine new cuisine
            new_cuisine = self.normalize_cuisine({
                'title': title,
                'ingredients': metadata.get('ingredients', '')
            })
            
            if new_cuisine and new_cuisine != current_cuisine:
                needs_update.append({
                    'id': recipe.get('id'),
                    'title': title,
                    'current_cuisine': current_cuisine,
                    'new_cuisine': new_cuisine
                })
        
        print(f"🔍 Found {len(needs_update)} recipes that need cuisine updates")
        
        # Show what would be updated
        for recipe in needs_update[:10]:  # Show first 10
            print(f"   - {recipe['title']}: '{recipe['current_cuisine']}' → '{recipe['new_cuisine']}'")
        
        if len(needs_update) > 10:
            print(f"   ... and {len(needs_update) - 10} more")
        
        print(f"\n✅ Analysis complete. {len(needs_update)} recipes need cuisine updates.")
        print("Note: This script identifies recipes that need updates but doesn't actually update them yet.")
        print("The Railway backend would need an update endpoint to modify recipe cuisines.")

if __name__ == "__main__":
    updater = RailwayCuisineUpdater()
    updater.update_cuisines()
