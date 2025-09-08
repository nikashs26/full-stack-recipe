#!/usr/bin/env python3
"""
Comprehensive script to sync all local data to Railway
This will migrate recipes, users, preferences, and meal history to Railway
"""

import os
import sys
import json
import requests
import time
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService
from services.user_service import UserService
from services.user_preferences_service import UserPreferencesService
from services.meal_history_service import MealHistoryService

class RailwayDataSyncer:
    def __init__(self, railway_url: str = "https://full-stack-recipe-production.up.railway.app"):
        self.railway_url = railway_url.rstrip('/')
        self.api_url = f"{self.railway_url}/api"
        
        # Local services
        self.local_recipe_cache = RecipeCacheService()
        self.local_user_service = UserService()
        self.local_preferences_service = UserPreferencesService()
        self.local_meal_history_service = MealHistoryService()
        
        print(f"🚀 Railway Data Syncer initialized")
        print(f"   Railway URL: {self.railway_url}")
        print(f"   API URL: {self.api_url}")
    
    def test_railway_connection(self) -> bool:
        """Test if Railway backend is accessible"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Railway backend is accessible")
                return True
            else:
                print(f"❌ Railway backend returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to Railway backend: {e}")
            return False
    
    def get_local_data_summary(self) -> dict:
        """Get summary of local data"""
        summary = {}
        
        try:
            # Get recipe count
            all_recipes = self.local_recipe_cache.recipe_collection.get(include=['metadatas'])
            summary['recipes'] = len(all_recipes['ids'])
        except Exception as e:
            print(f"Error getting recipe count: {e}")
            summary['recipes'] = 0
        
        try:
            # Get user count
            all_users = self.local_user_service.users_collection.get()
            summary['users'] = len(all_users['ids'])
        except Exception as e:
            print(f"Error getting user count: {e}")
            summary['users'] = 0
        
        try:
            # Get preferences count
            all_prefs = self.local_preferences_service.collection.get()
            summary['preferences'] = len(all_prefs['ids'])
        except Exception as e:
            print(f"Error getting preferences count: {e}")
            summary['preferences'] = 0
        
        try:
            # Get meal history count
            all_meals = self.local_meal_history_service.meal_history_collection.get()
            summary['meal_history'] = len(all_meals['ids'])
        except Exception as e:
            print(f"Error getting meal history count: {e}")
            summary['meal_history'] = 0
        
        return summary
    
    def sync_recipes_to_railway(self) -> bool:
        """Sync all recipes to Railway using the existing sync script"""
        print("\n🍳 Syncing recipes to Railway...")
        
        try:
            # Get all local recipes
            all_recipes = self.local_recipe_cache.recipe_collection.get(
                include=['metadatas', 'documents']
            )
            
            recipe_count = len(all_recipes['ids'])
            print(f"   Found {recipe_count} local recipes")
            
            if recipe_count == 0:
                print("   No recipes to sync")
                return True
            
            # Create a sync data file
            sync_data = {
                'recipes': [],
                'metadata': {
                    'total_recipes': recipe_count,
                    'sync_timestamp': time.time(),
                    'source': 'local_chromadb'
                }
            }
            
            # Convert recipes to sync format
            for i, (recipe_id, metadata, document) in enumerate(zip(
                all_recipes['ids'], 
                all_recipes['metadatas'], 
                all_recipes['documents']
            )):
                try:
                    recipe_data = json.loads(document)
                    sync_data['recipes'].append({
                        'id': recipe_id,
                        'metadata': metadata,
                        'data': recipe_data
                    })
                    
                    if (i + 1) % 100 == 0:
                        print(f"   Processed {i + 1}/{recipe_count} recipes...")
                        
                except Exception as e:
                    print(f"   Error processing recipe {recipe_id}: {e}")
                    continue
            
            # Save sync data to file
            sync_file = 'railway_sync_data.json'
            with open(sync_file, 'w') as f:
                json.dump(sync_data, f, indent=2)
            
            print(f"   ✅ Created sync file: {sync_file}")
            print(f"   📊 Sync data contains {len(sync_data['recipes'])} recipes")
            
            # Upload to Railway
            print("   📤 Uploading to Railway...")
            with open(sync_file, 'rb') as f:
                files = {'file': (sync_file, f, 'application/json')}
                response = requests.post(f"{self.api_url}/upload-sync", files=files)
            
            if response.status_code == 200:
                print("   ✅ Successfully uploaded to Railway")
                
                # Trigger population from the uploaded file
                print("   🔄 Triggering population on Railway...")
                populate_response = requests.post(f"{self.api_url}/populate-from-file")
                
                if populate_response.status_code == 200:
                    print("   ✅ Successfully populated Railway with recipes")
                    return True
                else:
                    print(f"   ❌ Failed to populate Railway: {populate_response.status_code}")
                    print(f"   Response: {populate_response.text}")
                    return False
            else:
                print(f"   ❌ Failed to upload to Railway: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error syncing recipes: {e}")
            return False
    
    def verify_railway_recipes(self) -> bool:
        """Verify that recipes are properly synced to Railway"""
        print("\n🔍 Verifying Railway recipes...")
        
        try:
            # Test basic recipe endpoint
            response = requests.get(f"{self.api_url}/get_recipes?limit=1")
            if response.status_code == 200:
                data = response.json()
                recipe_count = data.get('total', 0)
                print(f"   ✅ Railway has {recipe_count} recipes")
                
                if recipe_count > 0:
                    # Test recipe search
                    search_response = requests.get(f"{self.api_url}/get_recipes?query=pasta&limit=5")
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        search_count = len(search_data.get('results', []))
                        print(f"   ✅ Recipe search working: found {search_count} results for 'pasta'")
                        return True
                    else:
                        print(f"   ⚠️  Recipe search not working: {search_response.status_code}")
                        return False
                else:
                    print("   ❌ No recipes found on Railway")
                    return False
            else:
                print(f"   ❌ Cannot verify recipes: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error verifying Railway recipes: {e}")
            return False
    
    def sync_users_to_railway(self) -> bool:
        """Sync users to Railway (placeholder for now)"""
        print("\n👥 Syncing users to Railway...")
        
        try:
            # Get all local users
            all_users = self.local_user_service.users_collection.get(
                include=['metadatas', 'documents']
            )
            
            user_count = len(all_users['ids'])
            print(f"   Found {user_count} local users")
            
            if user_count == 0:
                print("   No users to sync")
                return True
            
            print(f"   ℹ️  User sync requires API endpoint implementation")
            print(f"   ℹ️  Found {user_count} users locally")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error syncing users: {e}")
            return False
    
    def sync_preferences_to_railway(self) -> bool:
        """Sync user preferences to Railway (placeholder for now)"""
        print("\n⚙️  Syncing user preferences to Railway...")
        
        try:
            # Get all local preferences
            all_prefs = self.local_preferences_service.collection.get(
                include=['metadatas', 'documents']
            )
            
            pref_count = len(all_prefs['ids'])
            print(f"   Found {pref_count} local preference sets")
            
            if pref_count == 0:
                print("   No preferences to sync")
                return True
            
            print(f"   ℹ️  Preferences sync requires API endpoint implementation")
            print(f"   ℹ️  Found {pref_count} preference sets locally")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error syncing preferences: {e}")
            return False
    
    def run_sync(self) -> bool:
        """Run the complete sync process"""
        print("🚀 Starting Railway Data Sync")
        print("=" * 50)
        
        # Step 1: Test connection
        if not self.test_railway_connection():
            print("❌ Cannot proceed without Railway connection")
            return False
        
        # Step 2: Report local data
        print("\n📊 Local Data Summary:")
        local_data = self.get_local_data_summary()
        for key, value in local_data.items():
            print(f"   {key.capitalize()}: {value}")
        
        # Step 3: Sync data
        success = True
        success &= self.sync_recipes_to_railway()
        
        if success:
            success &= self.verify_railway_recipes()
        
        # Step 4: Sync other data (placeholders for now)
        self.sync_users_to_railway()
        self.sync_preferences_to_railway()
        
        # Step 5: Report results
        print("\n" + "=" * 50)
        if success:
            print("🎉 Recipe sync completed successfully!")
            print(f"🌐 Your app is now live at: {self.railway_url}")
            print(f"🔗 API endpoint: {self.api_url}")
        else:
            print("❌ Sync had some issues - check the logs above")
        
        return success

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync all local data to Railway')
    parser.add_argument('--railway-url', default='https://full-stack-recipe-production.up.railway.app',
                       help='Railway deployment URL')
    
    args = parser.parse_args()
    
    syncer = RailwayDataSyncer(args.railway_url)
    syncer.run_sync()

if __name__ == "__main__":
    main()
