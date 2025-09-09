#!/usr/bin/env python3
"""
Ensure Railway persistence by creating a robust data restoration system
"""

import sys
import os
import json
import requests
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

class RailwayPersistenceManager:
    def __init__(self):
        self.api_url = "https://full-stack-recipe-production.up.railway.app/api"
        self.recipe_cache = RecipeCacheService()
        
    def check_railway_status(self):
        """Check if Railway backend is accessible and has data"""
        try:
            # Check health
            health_response = requests.get(f"{self.api_url}/health", timeout=10)
            if health_response.status_code != 200:
                print(f"❌ Railway health check failed: {health_response.status_code}")
                return False
            
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
            print(f"❌ Error checking Railway status: {e}")
            return False
    
    def restore_railway_data(self):
        """Restore data to Railway if it's missing"""
        print("🔄 Restoring Railway data...")
        
        # Check if we have sync data
        if not os.path.exists('railway_sync_data.json'):
            print("❌ No sync data file found. Run sync_all_to_railway.py first.")
            return False
        
        try:
            # Upload sync data
            with open('railway_sync_data.json', 'r') as f:
                sync_data = json.load(f)
            
            print(f"📤 Uploading {len(sync_data['recipes'])} recipes to Railway...")
            upload_response = requests.post(
                f"{self.api_url}/upload-sync",
                json=sync_data,
                timeout=60
            )
            
            if upload_response.status_code not in [200, 201]:
                print(f"❌ Upload failed: {upload_response.status_code}")
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
            print(f"❌ Error restoring data: {e}")
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
    
    def ensure_persistence(self):
        """Ensure Railway has persistent data"""
        print("🔍 Checking Railway persistence...")
        
        if self.check_railway_status():
            print("✅ Railway has data - persistence is working")
            return True
        else:
            print("⚠️ Railway is missing data - restoring...")
            return self.restore_railway_data()

def main():
    manager = RailwayPersistenceManager()
    success = manager.ensure_persistence()
    
    if success:
        print("\n✅ Railway persistence ensured!")
        print("🌐 Your recipes should now be available on Netlify")
    else:
        print("\n❌ Failed to ensure Railway persistence")
        print("💡 Try running 'python3 sync_all_to_railway.py' first")

if __name__ == "__main__":
    main()
