#!/usr/bin/env python3
"""
Railway Data Restore - Ensure data persists after deployments
"""

import sys
import os
import json
import requests
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

class RailwayDataRestore:
    def __init__(self):
        self.api_url = "https://full-stack-recipe-production.up.railway.app/api"
        self.recipe_cache = RecipeCacheService()
        
    def check_railway_data(self):
        """Check if Railway has data"""
        try:
            # Check recipe count
            count_response = requests.get(f"{self.api_url}/recipe-counts", timeout=10)
            if count_response.status_code == 200:
                count_data = count_response.json()
                recipe_count = count_data.get('total_recipes', 0)
                print(f"📊 Railway has {recipe_count} recipes")
                return recipe_count > 0
            else:
                print(f"❌ Failed to get recipe count: {count_response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error checking Railway data: {e}")
            return False
    
    def restore_data_to_railway(self):
        """Restore all data to Railway"""
        print("🔄 Restoring data to Railway...")
        
        # Get all local recipes
        all_recipes = self.recipe_cache.get_cached_recipes()
        print(f"📚 Found {len(all_recipes)} local recipes")
        
        if not all_recipes:
            print("❌ No local recipes found")
            return False
        
        # Create sync data
        sync_data = {
            "recipes": [],
            "users": [],
            "preferences": [],
            "meal_history": []
        }
        
        # Process recipes
        for recipe in all_recipes:
            try:
                recipe_id = recipe.get('id')
                if not recipe_id:
                    continue
                
                # Get metadata
                result = self.recipe_cache.recipe_collection.get(
                    ids=[recipe_id],
                    include=['metadatas']
                )
                
                metadata = result['metadatas'][0] if result['metadatas'] else {}
                
                # Create merged recipe data
                merged_recipe = recipe.copy()
                for key, value in metadata.items():
                    if key not in merged_recipe or merged_recipe[key] is None or merged_recipe[key] == '':
                        merged_recipe[key] = value
                
                sync_data['recipes'].append({
                    'id': recipe_id,
                    'metadata': metadata,
                    'data': merged_recipe,
                    'document': json.dumps(merged_recipe)
                })
                
            except Exception as e:
                print(f"   ⚠️ Error processing recipe {recipe.get('id', 'unknown')}: {e}")
                continue
        
        print(f"📤 Uploading {len(sync_data['recipes'])} recipes to Railway...")
        
        # Upload to Railway
        try:
            upload_response = requests.post(
                f"{self.api_url}/upload-sync",
                json=sync_data,
                timeout=120
            )
            
            if upload_response.status_code not in [200, 201]:
                print(f"❌ Upload failed: {upload_response.status_code}")
                print(f"Response: {upload_response.text}")
                return False
            
            print("✅ Upload successful")
            
            # Trigger population
            print("🔄 Triggering population...")
            populate_response = requests.post(f"{self.api_url}/populate-async", timeout=60)
            
            if populate_response.status_code not in [200, 202]:
                print(f"❌ Population trigger failed: {populate_response.status_code}")
                return False
            
            print("✅ Population triggered successfully")
            
            # Monitor population
            return self.monitor_population()
            
        except Exception as e:
            print(f"❌ Error uploading data: {e}")
            return False
    
    def monitor_population(self):
        """Monitor population progress"""
        print("📊 Monitoring population progress...")
        max_attempts = 60  # 5 minutes max
        attempt = 0
        
        while attempt < max_attempts:
            try:
                response = requests.get(f"{self.api_url}/populate-status", timeout=30)
                if response.status_code == 200:
                    status = response.json()
                    recipe_count = status.get('recipe_count', {}).get('total', 0)
                    population = status.get('population', {})
                    
                    print(f"   Recipes processed: {recipe_count}")
                    
                    if population.get('running'):
                        print(f"   Status: {population.get('message', 'Processing...')}")
                    elif population.get('finished_at'):
                        print(f"   ✅ Population completed at {population.get('finished_at')}")
                        return True
                    else:
                        print(f"   Status: {population.get('message', 'Unknown')}")
                
                attempt += 1
                if attempt < max_attempts:
                    print("   Waiting 5 seconds...")
                    time.sleep(5)
                    
            except Exception as e:
                print(f"   Error checking status: {e}")
                attempt += 1
                if attempt < max_attempts:
                    time.sleep(5)
        
        print("⚠️ Population monitoring timed out")
        return False
    
    def test_railway_endpoints(self):
        """Test if Railway endpoints are working"""
        print("🧪 Testing Railway endpoints...")
        
        # Test search endpoint
        try:
            search_response = requests.get(f"{self.api_url}/recipes?query=pasta&limit=5", timeout=10)
            if search_response.status_code == 200:
                data = search_response.json()
                recipe_count = len(data.get('results', []))
                print(f"✅ Search endpoint working: {recipe_count} recipes found")
                return True
            else:
                print(f"❌ Search endpoint failed: {search_response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Search endpoint error: {e}")
            return False
    
    def run_restore(self):
        """Run the complete restore process"""
        print("🚀 Starting Railway data restore...")
        
        # Check if Railway has data
        if self.check_railway_data():
            print("✅ Railway already has data")
            if self.test_railway_endpoints():
                print("✅ Railway endpoints are working")
                return True
            else:
                print("⚠️ Railway has data but endpoints not working")
        
        # Restore data
        if self.restore_data_to_railway():
            print("✅ Data restored successfully")
            
            # Test endpoints
            if self.test_railway_endpoints():
                print("✅ All Railway endpoints are working")
                return True
            else:
                print("❌ Endpoints still not working after restore")
                return False
        else:
            print("❌ Failed to restore data")
            return False

def main():
    restorer = RailwayDataRestore()
    success = restorer.run_restore()
    
    if success:
        print("\n🎉 Railway data restore completed successfully!")
        print("🌐 Your Netlify site should now have working search and filters")
    else:
        print("\n❌ Railway data restore failed")
        print("💡 Check Railway logs for more details")

if __name__ == "__main__":
    main()
