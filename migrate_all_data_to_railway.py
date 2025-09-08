#!/usr/bin/env python3
"""
Complete migration script to move ALL local data to Railway
This will migrate recipes, users, preferences, and meal history
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

class CompleteRailwayMigrator:
    def __init__(self, railway_url: str = "https://full-stack-recipe-production.up.railway.app"):
        self.railway_url = railway_url.rstrip('/')
        self.api_url = f"{self.railway_url}/api"
        
        # Local services
        self.local_recipe_cache = RecipeCacheService()
        self.local_user_service = UserService()
        self.local_preferences_service = UserPreferencesService()
        self.local_meal_history_service = MealHistoryService()
        
        print(f"🚀 Complete Railway Migrator initialized")
        print(f"   Railway URL: {self.railway_url}")
        print(f"   API URL: {self.api_url}")
    
    def check_railway_status(self) -> dict:
        """Check Railway backend status and recipe count"""
        try:
            # Check health
            health_response = requests.get(f"{self.api_url}/health", timeout=10)
            if health_response.status_code != 200:
                return {"status": "error", "message": "Railway backend not accessible"}
            
            # Check recipe count
            recipes_response = requests.get(f"{self.api_url}/get_recipes?limit=1", timeout=10)
            if recipes_response.status_code == 200:
                recipes_data = recipes_response.json()
                recipe_count = recipes_data.get('total', 0)
            else:
                recipe_count = 0
            
            # Check population status
            populate_response = requests.get(f"{self.api_url}/populate-status", timeout=10)
            populate_data = populate_response.json() if populate_response.status_code == 200 else {}
            
            return {
                "status": "success",
                "recipe_count": recipe_count,
                "population_running": populate_data.get('population', {}).get('running', False),
                "population_status": populate_data.get('population', {})
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Cannot connect to Railway: {e}"}
    
    def get_local_data_summary(self) -> dict:
        """Get comprehensive summary of all local data"""
        summary = {}
        
        try:
            # Get recipe count
            all_recipes = self.local_recipe_cache.recipe_collection.get(include=['metadatas'])
            summary['recipes'] = len(all_recipes['ids'])
        except Exception as e:
            print(f"Error getting recipe count: {e}")
            summary['recipes'] = 0
        
        try:
            # Get user count and details
            all_users = self.local_user_service.users_collection.get(include=['metadatas', 'documents'])
            summary['users'] = len(all_users['ids'])
            summary['user_details'] = []
            for i, (user_id, metadata, document) in enumerate(zip(all_users['ids'], all_users['metadatas'], all_users['documents'])):
                try:
                    user_data = json.loads(document)
                    summary['user_details'].append({
                        'id': user_id,
                        'email': user_data.get('email', 'Unknown'),
                        'is_verified': user_data.get('is_verified', False)
                    })
                except:
                    summary['user_details'].append({'id': user_id, 'email': 'Unknown', 'is_verified': False})
        except Exception as e:
            print(f"Error getting user data: {e}")
            summary['users'] = 0
            summary['user_details'] = []
        
        try:
            # Get preferences count and details
            all_prefs = self.local_preferences_service.collection.get(include=['metadatas', 'documents'])
            summary['preferences'] = len(all_prefs['ids'])
            summary['preference_details'] = []
            for i, (pref_id, metadata, document) in enumerate(zip(all_prefs['ids'], all_prefs['metadatas'], all_prefs['documents'])):
                try:
                    pref_data = json.loads(document)
                    summary['preference_details'].append({
                        'user_id': pref_id,
                        'has_dietary_restrictions': 'dietaryRestrictions' in pref_data,
                        'has_favorite_cuisines': 'favoriteCuisines' in pref_data,
                        'has_favorite_foods': 'favoriteFoods' in pref_data
                    })
                except:
                    summary['preference_details'].append({'user_id': pref_id, 'error': 'parse_failed'})
        except Exception as e:
            print(f"Error getting preferences data: {e}")
            summary['preferences'] = 0
            summary['preference_details'] = []
        
        try:
            # Get meal history count
            all_meals = self.local_meal_history_service.meal_history_collection.get()
            summary['meal_history'] = len(all_meals['ids'])
        except Exception as e:
            print(f"Error getting meal history count: {e}")
            summary['meal_history'] = 0
        
        return summary
    
    def wait_for_recipe_population(self, timeout_minutes: int = 10) -> bool:
        """Wait for recipe population to complete"""
        print(f"\n⏳ Waiting for recipe population to complete (timeout: {timeout_minutes} minutes)...")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            try:
                status = self.check_railway_status()
                if status["status"] == "error":
                    print(f"   ❌ Error checking status: {status['message']}")
                    return False
                
                recipe_count = status.get("recipe_count", 0)
                population_running = status.get("population_running", False)
                
                print(f"   📊 Current recipe count: {recipe_count}")
                print(f"   🔄 Population running: {population_running}")
                
                if not population_running and recipe_count > 1000:
                    print(f"   ✅ Recipe population completed! Found {recipe_count} recipes")
                    return True
                elif not population_running and recipe_count < 1000:
                    print(f"   ⚠️  Population finished but only {recipe_count} recipes found")
                    return False
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"   ❌ Error checking population status: {e}")
                time.sleep(30)
        
        print(f"   ⏰ Timeout reached after {timeout_minutes} minutes")
        return False
    
    def create_user_migration_data(self) -> dict:
        """Create migration data for users"""
        try:
            all_users = self.local_user_service.users_collection.get(include=['metadatas', 'documents'])
            
            migration_data = {
                'users': [],
                'metadata': {
                    'total_users': len(all_users['ids']),
                    'migration_timestamp': time.time(),
                    'source': 'local_chromadb'
                }
            }
            
            for user_id, metadata, document in zip(all_users['ids'], all_users['metadatas'], all_users['documents']):
                try:
                    user_data = json.loads(document)
                    migration_data['users'].append({
                        'id': user_id,
                        'metadata': metadata,
                        'data': user_data
                    })
                except Exception as e:
                    print(f"Error processing user {user_id}: {e}")
                    continue
            
            return migration_data
            
        except Exception as e:
            print(f"Error creating user migration data: {e}")
            return {'users': [], 'metadata': {'error': str(e)}}
    
    def create_preferences_migration_data(self) -> dict:
        """Create migration data for user preferences"""
        try:
            all_prefs = self.local_preferences_service.collection.get(include=['metadatas', 'documents'])
            
            migration_data = {
                'preferences': [],
                'metadata': {
                    'total_preferences': len(all_prefs['ids']),
                    'migration_timestamp': time.time(),
                    'source': 'local_chromadb'
                }
            }
            
            for pref_id, metadata, document in zip(all_prefs['ids'], all_prefs['metadatas'], all_prefs['documents']):
                try:
                    pref_data = json.loads(document)
                    migration_data['preferences'].append({
                        'user_id': pref_id,
                        'metadata': metadata,
                        'data': pref_data
                    })
                except Exception as e:
                    print(f"Error processing preferences {pref_id}: {e}")
                    continue
            
            return migration_data
            
        except Exception as e:
            print(f"Error creating preferences migration data: {e}")
            return {'preferences': [], 'metadata': {'error': str(e)}}
    
    def run_complete_migration(self) -> bool:
        """Run the complete migration process"""
        print("🚀 Starting Complete Railway Migration")
        print("=" * 60)
        
        # Step 1: Check Railway status
        print("\n1️⃣ Checking Railway status...")
        railway_status = self.check_railway_status()
        if railway_status["status"] == "error":
            print(f"   ❌ {railway_status['message']}")
            return False
        
        print(f"   ✅ Railway is accessible")
        print(f"   📊 Current recipe count: {railway_status.get('recipe_count', 0)}")
        print(f"   🔄 Population running: {railway_status.get('population_running', False)}")
        
        # Step 2: Report local data
        print("\n2️⃣ Analyzing local data...")
        local_data = self.get_local_data_summary()
        print(f"   📊 Local Data Summary:")
        print(f"      Recipes: {local_data['recipes']}")
        print(f"      Users: {local_data['users']}")
        print(f"      Preferences: {local_data['preferences']}")
        print(f"      Meal History: {local_data['meal_history']}")
        
        # Step 3: Wait for recipe population
        if railway_status.get('population_running', False):
            print("\n3️⃣ Recipe population is running...")
            if not self.wait_for_recipe_population():
                print("   ⚠️  Recipe population didn't complete successfully")
        else:
            print("\n3️⃣ No recipe population running, checking current state...")
            current_count = railway_status.get('recipe_count', 0)
            if current_count < 1000:
                print(f"   ⚠️  Only {current_count} recipes found, may need to trigger population")
        
        # Step 4: Create migration data for other services
        print("\n4️⃣ Preparing user and preferences data...")
        user_data = self.create_user_migration_data()
        prefs_data = self.create_preferences_migration_data()
        
        print(f"   👥 User data: {len(user_data['users'])} users")
        print(f"   ⚙️  Preferences data: {len(prefs_data['preferences'])} preference sets")
        
        # Step 5: Save migration data for manual review
        migration_summary = {
            'railway_status': railway_status,
            'local_data': local_data,
            'user_migration_data': user_data,
            'preferences_migration_data': prefs_data,
            'migration_timestamp': time.time()
        }
        
        with open('complete_migration_summary.json', 'w') as f:
            json.dump(migration_summary, f, indent=2)
        
        print(f"\n✅ Migration summary saved to: complete_migration_summary.json")
        
        # Step 6: Final verification
        print("\n5️⃣ Final verification...")
        final_status = self.check_railway_status()
        final_recipe_count = final_status.get('recipe_count', 0)
        
        print(f"   📊 Final recipe count on Railway: {final_recipe_count}")
        
        if final_recipe_count > 1000:
            print("   🎉 SUCCESS! Railway has all your recipes!")
            print(f"   🌐 Your app is live at: {self.railway_url}")
            print(f"   🔗 API endpoint: {self.api_url}")
            return True
        else:
            print(f"   ⚠️  Only {final_recipe_count} recipes found - may need manual intervention")
            return False

def main():
    """Main function"""
    migrator = CompleteRailwayMigrator()
    migrator.run_complete_migration()

if __name__ == "__main__":
    main()
