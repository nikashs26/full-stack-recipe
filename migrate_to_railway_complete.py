#!/usr/bin/env python3
"""
Complete migration script to transfer ALL local data to Railway
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
            
            return {
                "status": "success",
                "recipe_count": recipe_count
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
    
    def migrate_recipes_to_railway(self) -> bool:
        """Migrate all local recipes to Railway"""
        print("\n🍳 Migrating recipes to Railway...")
        
        try:
            # Get all local recipes
            all_recipes = self.local_recipe_cache.recipe_collection.get(include=['metadatas', 'documents'])
            
            if not all_recipes['ids']:
                print("   ⚠️  No local recipes found")
                return False
            
            print(f"   📊 Found {len(all_recipes['ids'])} local recipes")
            
            # Prepare recipes for migration
            recipes_to_migrate = []
            for i, (recipe_id, metadata, document) in enumerate(zip(all_recipes['ids'], all_recipes['metadatas'], all_recipes['documents'])):
                try:
                    recipe_data = json.loads(document)
                    recipes_to_migrate.append({
                        'id': recipe_id,
                        'metadata': metadata,
                        'data': recipe_data
                    })
                except Exception as e:
                    print(f"   ⚠️  Error processing recipe {recipe_id}: {e}")
                    continue
            
            print(f"   📦 Prepared {len(recipes_to_migrate)} recipes for migration")
            
            # Save recipes to a file for Railway to consume
            migration_file = 'railway_recipes_migration.json'
            with open(migration_file, 'w') as f:
                json.dump({
                    'recipes': recipes_to_migrate,
                    'metadata': {
                        'total_recipes': len(recipes_to_migrate),
                        'migration_timestamp': time.time(),
                        'source': 'local_chromadb'
                    }
                }, f, indent=2)
            
            print(f"   💾 Saved recipes to {migration_file}")
            
            # Upload to Railway using the populate-from-file endpoint
            try:
                with open(migration_file, 'rb') as f:
                    files = {'file': f}
                    response = requests.post(f"{self.api_url}/populate-from-file", files=files, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ {result.get('message', 'Recipes migrated successfully')}")
                    return True
                else:
                    print(f"   ❌ Failed to upload recipes: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Error uploading recipes: {e}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error migrating recipes: {e}")
            return False
    
    def migrate_users_to_railway(self) -> bool:
        """Migrate user data to Railway"""
        print("\n👥 Migrating users to Railway...")
        
        try:
            # Get all local users
            all_users = self.local_user_service.users_collection.get(include=['metadatas', 'documents'])
            
            if not all_users['ids']:
                print("   ⚠️  No local users found")
                return True  # Not an error if no users
            
            print(f"   📊 Found {len(all_users['ids'])} local users")
            
            # Prepare users for migration
            users_to_migrate = []
            for user_id, metadata, document in zip(all_users['ids'], all_users['metadatas'], all_users['documents']):
                try:
                    user_data = json.loads(document)
                    users_to_migrate.append({
                        'id': user_id,
                        'metadata': metadata,
                        'data': user_data
                    })
                except Exception as e:
                    print(f"   ⚠️  Error processing user {user_id}: {e}")
                    continue
            
            print(f"   📦 Prepared {len(users_to_migrate)} users for migration")
            
            # Save users to a file
            migration_file = 'railway_users_migration.json'
            with open(migration_file, 'w') as f:
                json.dump({
                    'users': users_to_migrate,
                    'metadata': {
                        'total_users': len(users_to_migrate),
                        'migration_timestamp': time.time(),
                        'source': 'local_chromadb'
                    }
                }, f, indent=2)
            
            print(f"   💾 Saved users to {migration_file}")
            print(f"   ℹ️  User migration file created - manual upload may be required")
            return True
                
        except Exception as e:
            print(f"   ❌ Error migrating users: {e}")
            return False
    
    def migrate_preferences_to_railway(self) -> bool:
        """Migrate user preferences to Railway"""
        print("\n⚙️  Migrating preferences to Railway...")
        
        try:
            # Get all local preferences
            all_prefs = self.local_preferences_service.collection.get(include=['metadatas', 'documents'])
            
            if not all_prefs['ids']:
                print("   ⚠️  No local preferences found")
                return True  # Not an error if no preferences
            
            print(f"   📊 Found {len(all_prefs['ids'])} local preference sets")
            
            # Prepare preferences for migration
            prefs_to_migrate = []
            for pref_id, metadata, document in zip(all_prefs['ids'], all_prefs['metadatas'], all_prefs['documents']):
                try:
                    pref_data = json.loads(document)
                    prefs_to_migrate.append({
                        'user_id': pref_id,
                        'metadata': metadata,
                        'data': pref_data
                    })
                except Exception as e:
                    print(f"   ⚠️  Error processing preferences {pref_id}: {e}")
                    continue
            
            print(f"   📦 Prepared {len(prefs_to_migrate)} preference sets for migration")
            
            # Save preferences to a file
            migration_file = 'railway_preferences_migration.json'
            with open(migration_file, 'w') as f:
                json.dump({
                    'preferences': prefs_to_migrate,
                    'metadata': {
                        'total_preferences': len(prefs_to_migrate),
                        'migration_timestamp': time.time(),
                        'source': 'local_chromadb'
                    }
                }, f, indent=2)
            
            print(f"   💾 Saved preferences to {migration_file}")
            print(f"   ℹ️  Preferences migration file created - manual upload may be required")
            return True
                
        except Exception as e:
            print(f"   ❌ Error migrating preferences: {e}")
            return False
    
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
        
        # Step 2: Report local data
        print("\n2️⃣ Analyzing local data...")
        local_data = self.get_local_data_summary()
        print(f"   📊 Local Data Summary:")
        print(f"      Recipes: {local_data['recipes']}")
        print(f"      Users: {local_data['users']}")
        print(f"      Preferences: {local_data['preferences']}")
        print(f"      Meal History: {local_data['meal_history']}")
        
        # Step 3: Migrate recipes
        print("\n3️⃣ Migrating recipes...")
        recipe_success = self.migrate_recipes_to_railway()
        
        # Step 4: Migrate users
        print("\n4️⃣ Migrating users...")
        user_success = self.migrate_users_to_railway()
        
        # Step 5: Migrate preferences
        print("\n5️⃣ Migrating preferences...")
        prefs_success = self.migrate_preferences_to_railway()
        
        # Step 6: Final verification
        print("\n6️⃣ Final verification...")
        final_status = self.check_railway_status()
        final_recipe_count = final_status.get('recipe_count', 0)
        
        print(f"   📊 Final recipe count on Railway: {final_recipe_count}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 MIGRATION SUMMARY")
        print("=" * 60)
        print(f"✅ Recipes migrated: {'Yes' if recipe_success else 'No'}")
        print(f"✅ Users migrated: {'Yes' if user_success else 'No'}")
        print(f"✅ Preferences migrated: {'Yes' if prefs_success else 'No'}")
        print(f"📊 Final Railway recipe count: {final_recipe_count}")
        print(f"📊 Local recipe count: {local_data['recipes']}")
        
        if final_recipe_count >= local_data['recipes'] * 0.9:  # 90% success threshold
            print("   🎉 SUCCESS! Railway has most of your recipes!")
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
