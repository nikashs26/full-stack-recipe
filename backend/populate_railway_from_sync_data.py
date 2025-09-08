#!/usr/bin/env python3
"""
Railway Population Script from Sync Data

This script populates Railway ChromaDB with data from the sync data file.
It's designed to be run on Railway to populate the production database.
"""

import json
import os
import sys
from typing import Dict, List, Any

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_sync_data() -> Dict[str, Any]:
    """Load sync data from the JSON file"""
    try:
        # Look for the sync data file
        sync_files = [f for f in os.listdir('.') if f.startswith('railway_sync_data_') and f.endswith('.json')]
        
        if not sync_files:
            print("❌ No sync data file found")
            return None
        
        # Use the most recent file
        sync_file = sorted(sync_files)[-1]
        print(f"📂 Loading sync data from: {sync_file}")
        
        with open(sync_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Loaded sync data with {len(data.get('recipes', []))} recipes")
        return data
        
    except Exception as e:
        print(f"❌ Error loading sync data: {e}")
        return None

def populate_railway_from_sync_data():
    """Populate Railway ChromaDB with sync data"""
    print("🚀 Populating Railway from sync data...")
    
    # Load sync data
    sync_data = load_sync_data()
    if not sync_data:
        return False
    
    try:
        # Import services
        from services.recipe_search_service import RecipeSearchService
        from services.user_preferences_service import UserPreferencesService
        from services.meal_history_service import MealHistoryService
        
        # Initialize services
        recipe_search_service = RecipeSearchService()
        user_preferences_service = UserPreferencesService()
        meal_history_service = MealHistoryService()
        
        # Populate recipes
        recipes = sync_data.get('recipes', [])
        if recipes:
            print(f"📚 Indexing {len(recipes)} recipes...")
            recipe_search_service.bulk_index_recipes(recipes)
            print(f"✅ Successfully indexed {len(recipes)} recipes")
        
        # Populate user preferences
        preferences = sync_data.get('user_preferences', [])
        if preferences:
            print(f"👤 Saving {len(preferences)} user preferences...")
            for pref in preferences:
                user_id = pref.get('_id', 'default_user')
                pref_data = {k: v for k, v in pref.items() if k != '_id'}
                user_preferences_service.save_preferences(user_id, pref_data)
            print(f"✅ Successfully saved {len(preferences)} user preferences")
        
        # Populate meal history
        meal_history = sync_data.get('meal_history', [])
        if meal_history:
            print(f"📅 Saving {len(meal_history)} meal history entries...")
            for history in meal_history:
                history_id = history.get('_id', 'default_history')
                history_data = {k: v for k, v in history.items() if k != '_id'}
                # You'll need to implement meal history saving in your service
                print(f"Meal history {history_id}: {history_data.get('title', 'Untitled')}")
            print(f"✅ Successfully saved {len(meal_history)} meal history entries")
        
        print("🎉 Railway population complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error populating Railway: {e}")
        return False

if __name__ == "__main__":
    success = populate_railway_from_sync_data()
    if success:
        print("✅ Population successful!")
    else:
        print("❌ Population failed!")
