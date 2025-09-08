#!/usr/bin/env python3
"""
Railway Data Sync Script

This script extracts data from your local ChromaDB and syncs it to your Railway production deployment.
It handles recipes, user preferences, meal plans, and other data that your local environment has.
"""

import os
import sys
import json
import requests
import chromadb
from datetime import datetime
from typing import Dict, List, Any, Optional
import time

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from services.recipe_search_service import RecipeSearchService
    from services.meal_history_service import MealHistoryService
    from services.smart_shopping_service import SmartShoppingService
    from services.user_preferences_service import UserPreferencesService
    from services.recipe_cache_service import RecipeCacheService
except ImportError as e:
    print(f"⚠️ Could not import services: {e}")
    print("This script should be run from the backend directory")
    sys.exit(1)

class RailwayDataSyncer:
    def __init__(self, railway_url: str):
        self.railway_url = railway_url.rstrip('/')
        self.local_client = chromadb.PersistentClient(path="./chroma_db")
        self.session = requests.Session()
        self.session.timeout = 30
        
    def test_railway_connection(self) -> bool:
        """Test if Railway backend is accessible"""
        try:
            print(f"🔍 Testing Railway connection: {self.railway_url}")
            response = self.session.get(f"{self.railway_url}/api/health")
            if response.status_code == 200:
                print("✅ Railway connection successful")
                return True
            else:
                print(f"❌ Railway health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to Railway: {e}")
            return False
    
    def extract_local_recipes(self) -> List[Dict[str, Any]]:
        """Extract all recipes from local ChromaDB"""
        print("📚 Extracting recipes from local ChromaDB...")
        
        recipes = []
        collections_to_check = [
            "recipe_details_cache",
            "recipe_search_cache", 
            "recipes"
        ]
        
        for collection_name in collections_to_check:
            try:
                collection = self.local_client.get_collection(collection_name)
                count = collection.count()
                print(f"📊 Found {count} recipes in '{collection_name}' collection")
                
                if count > 0:
                    # Get all documents from this collection
                    results = collection.get(include=['documents', 'metadatas'])
                    
                    for i, (doc_id, document, metadata) in enumerate(zip(
                        results['ids'], 
                        results['documents'], 
                        results['metadatas']
                    )):
                        try:
                            if isinstance(document, str):
                                recipe_data = json.loads(document)
                            else:
                                recipe_data = document
                            
                            # Ensure it's a valid recipe
                            if isinstance(recipe_data, dict) and recipe_data.get('id'):
                                # Add collection source for tracking
                                recipe_data['_source_collection'] = collection_name
                                recipes.append(recipe_data)
                                
                        except Exception as e:
                            print(f"⚠️ Error processing recipe {i} from {collection_name}: {e}")
                            continue
                            
            except Exception as e:
                print(f"⚠️ Could not access collection '{collection_name}': {e}")
                continue
        
        # Remove duplicates based on recipe ID
        unique_recipes = {}
        for recipe in recipes:
            recipe_id = recipe.get('id')
            if recipe_id and recipe_id not in unique_recipes:
                unique_recipes[recipe_id] = recipe
        
        final_recipes = list(unique_recipes.values())
        print(f"✅ Extracted {len(final_recipes)} unique recipes")
        return final_recipes
    
    def extract_user_preferences(self) -> List[Dict[str, Any]]:
        """Extract user preferences from local ChromaDB"""
        print("👤 Extracting user preferences...")
        
        preferences = []
        try:
            collection = self.local_client.get_collection("user_preferences")
            count = collection.count()
            print(f"📊 Found {count} user preferences")
            
            if count > 0:
                results = collection.get(include=['documents', 'metadatas'])
                
                for doc_id, document, metadata in zip(
                    results['ids'], 
                    results['documents'], 
                    results['metadatas']
                ):
                    try:
                        if isinstance(document, str):
                            pref_data = json.loads(document)
                        else:
                            pref_data = document
                        
                        if isinstance(pref_data, dict):
                            pref_data['_id'] = doc_id
                            preferences.append(pref_data)
                            
                    except Exception as e:
                        print(f"⚠️ Error processing preference {doc_id}: {e}")
                        continue
                        
        except Exception as e:
            print(f"⚠️ Could not access user preferences: {e}")
        
        print(f"✅ Extracted {len(preferences)} user preferences")
        return preferences
    
    def extract_meal_plans(self) -> List[Dict[str, Any]]:
        """Extract meal plans from local ChromaDB"""
        print("🍽️ Extracting meal plans...")
        
        meal_plans = []
        try:
            collection = self.local_client.get_collection("meal_plans")
            count = collection.count()
            print(f"📊 Found {count} meal plans")
            
            if count > 0:
                results = collection.get(include=['documents', 'metadatas'])
                
                for doc_id, document, metadata in zip(
                    results['ids'], 
                    results['documents'], 
                    results['metadatas']
                ):
                    try:
                        if isinstance(document, str):
                            plan_data = json.loads(document)
                        else:
                            plan_data = document
                        
                        if isinstance(plan_data, dict):
                            plan_data['_id'] = doc_id
                            meal_plans.append(plan_data)
                            
                    except Exception as e:
                        print(f"⚠️ Error processing meal plan {doc_id}: {e}")
                        continue
                        
        except Exception as e:
            print(f"⚠️ Could not access meal plans: {e}")
        
        print(f"✅ Extracted {len(meal_plans)} meal plans")
        return meal_plans
    
    def sync_recipes_to_railway(self, recipes: List[Dict[str, Any]]) -> bool:
        """Sync recipes to Railway via API"""
        print(f"🚀 Syncing {len(recipes)} recipes to Railway...")
        
        # For now, we'll create a backup file that can be uploaded to Railway
        # This is because Railway doesn't have direct ChromaDB access in the same way
        
        backup_data = {
            "sync_timestamp": datetime.now().isoformat(),
            "total_recipes": len(recipes),
            "recipes": recipes
        }
        
        # Save to file for manual upload
        backup_filename = f"railway_recipes_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Recipe data saved to: {backup_filename}")
        print("📤 This file can be uploaded to Railway or used to populate the production database")
        
        return True
    
    def create_railway_population_script(self, recipes: List[Dict[str, Any]], 
                                       preferences: List[Dict[str, Any]], 
                                       meal_plans: List[Dict[str, Any]]) -> str:
        """Create a script that can be run on Railway to populate the data"""
        
        script_content = f'''#!/usr/bin/env python3
"""
Railway Data Population Script
Generated on {datetime.now().isoformat()}

This script populates Railway ChromaDB with data from your local environment.
Run this script on Railway after deployment to sync your data.
"""

import json
import chromadb
from services.recipe_search_service import RecipeSearchService
from services.meal_history_service import MealHistoryService
from services.smart_shopping_service import SmartShoppingService
from services.user_preferences_service import UserPreferencesService

def populate_railway_data():
    """Populate Railway ChromaDB with synced data"""
    print("🚀 Populating Railway ChromaDB...")
    
    # Initialize services
    recipe_search_service = RecipeSearchService()
    meal_history_service = MealHistoryService()
    smart_shopping_service = SmartShoppingService()
    user_preferences_service = UserPreferencesService()
    
    # Load synced data
    recipes = {json.dumps(recipes, indent=2)}
    preferences = {json.dumps(preferences, indent=2)}
    meal_plans = {json.dumps(meal_plans, indent=2)}
    
    # Index recipes
    print(f"📚 Indexing {{len(recipes)}} recipes...")
    recipe_search_service.bulk_index_recipes(recipes)
    
    # Save user preferences
    print(f"👤 Saving {{len(preferences)}} user preferences...")
    for pref in preferences:
        user_id = pref.get('_id', 'default_user')
        pref_data = {{k: v for k, v in pref.items() if k != '_id'}}
        user_preferences_service.save_preferences(user_id, pref_data)
    
    # Save meal plans
    print(f"🍽️ Saving {{len(meal_plans)}} meal plans...")
    for plan in meal_plans:
        plan_id = plan.get('_id', 'default_plan')
        plan_data = {{k: v for k, v in plan.items() if k != '_id'}}
        # You'll need to implement meal plan saving in your service
        print(f"Meal plan {{plan_id}}: {{plan_data.get('title', 'Untitled')}}")
    
    print("✅ Railway data population complete!")

if __name__ == "__main__":
    populate_railway_data()
'''
        
        script_filename = f"populate_railway_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        with open(script_filename, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"📝 Railway population script created: {script_filename}")
        return script_filename
    
    def sync_all_data(self) -> bool:
        """Sync all data from local to Railway"""
        print("🔄 Starting complete data sync to Railway...")
        
        # Test connection first
        if not self.test_railway_connection():
            return False
        
        # Extract all data
        recipes = self.extract_local_recipes()
        preferences = self.extract_user_preferences()
        meal_plans = self.extract_meal_plans()
        
        if not recipes and not preferences and not meal_plans:
            print("❌ No data found to sync")
            return False
        
        # Sync recipes
        if recipes:
            self.sync_recipes_to_railway(recipes)
        
        # Create population script
        script_file = self.create_railway_population_script(recipes, preferences, meal_plans)
        
        print("\n" + "="*60)
        print("🎉 Data sync preparation complete!")
        print("="*60)
        print(f"📊 Data extracted:")
        print(f"   - {len(recipes)} recipes")
        print(f"   - {len(preferences)} user preferences") 
        print(f"   - {len(meal_plans)} meal plans")
        print(f"\n📁 Files created:")
        print(f"   - Recipe backup: railway_recipes_sync_*.json")
        print(f"   - Population script: {script_file}")
        print(f"\n🚀 Next steps:")
        print(f"   1. Upload the population script to your Railway deployment")
        print(f"   2. Run the script on Railway to populate the database")
        print(f"   3. Verify your Netlify frontend can access the data")
        
        return True

def main():
    """Main function"""
    print("🚀 Railway Data Sync Tool")
    print("=" * 50)
    
    # Get Railway URL
    railway_url = os.environ.get('RAILWAY_URL')
    if not railway_url:
        railway_url = input("Enter your Railway URL (e.g., https://your-app.up.railway.app): ").strip()
        if not railway_url:
            print("❌ No Railway URL provided")
            return
    
    # Create syncer
    syncer = RailwayDataSyncer(railway_url)
    
    # Perform sync
    success = syncer.sync_all_data()
    
    if success:
        print("\n✅ Sync preparation completed successfully!")
    else:
        print("\n❌ Sync preparation failed")

if __name__ == "__main__":
    main()
