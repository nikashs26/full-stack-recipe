#!/usr/bin/env python3
"""
Complete Railway sync script that ensures exact data structure match
"""

import requests
import json
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

class CompleteRailwaySyncer:
    def __init__(self):
        self.railway_url = "https://full-stack-recipe-production.up.railway.app"
        self.api_url = f"{self.railway_url}/api"
        self.recipe_cache = RecipeCacheService()
        
    def get_all_local_recipes(self):
        """Get all recipes from local cache with exact structure"""
        print("📊 Fetching all local recipes...")
        
        # Get all recipes with both metadata and documents
        all_recipes = self.recipe_cache.recipe_collection.get(
            include=["documents", "metadatas"],
            limit=None  # Get all recipes
        )
        
        recipe_count = len(all_recipes['ids'])
        print(f"   Found {recipe_count} local recipes")
        
        return all_recipes
    
    def create_exact_sync_data(self, all_recipes):
        """Create sync data that preserves exact local structure"""
        print("🔄 Creating exact sync data...")
        
        sync_data = {
            "recipes": [],
            "sync_timestamp": datetime.now().isoformat(),
            "total_recipes": len(all_recipes['ids'])
        }
        
        # Process each recipe to preserve exact structure
        for i, (recipe_id, metadata, document) in enumerate(zip(
            all_recipes['ids'], 
            all_recipes['metadatas'], 
            all_recipes['documents']
        )):
            try:
                # Parse the document
                recipe_data = json.loads(document)
                
                # Create the exact structure that matches local storage
                recipe_entry = {
                    "id": recipe_id,
                    "metadata": metadata,  # Exact metadata from ChromaDB
                    "data": recipe_data,   # Exact document data from ChromaDB
                    # Add any additional fields needed for Railway
                    "source": "local_sync",
                    "sync_timestamp": datetime.now().isoformat()
                }
                
                sync_data['recipes'].append(recipe_entry)
                
                if (i + 1) % 100 == 0:
                    print(f"   Processed {i + 1}/{len(all_recipes['ids'])} recipes...")
                    
            except Exception as e:
                print(f"   Error processing recipe {recipe_id}: {e}")
                continue
        
        print(f"✅ Created sync data with {len(sync_data['recipes'])} recipes")
        return sync_data
    
    def upload_sync_data(self, sync_data):
        """Upload sync data to Railway"""
        print("📤 Uploading sync data to Railway...")
        
        # Save sync data to file
        sync_file = "complete_railway_sync_data.json"
        with open(sync_file, 'w') as f:
            json.dump(sync_data, f, indent=2)
        
        print(f"   Created sync file: {sync_file}")
        print(f"   File size: {os.path.getsize(sync_file) / 1024 / 1024:.2f} MB")
        
        # Upload to Railway
        try:
            with open(sync_file, 'rb') as f:
                files = {'file': (sync_file, f, 'application/json')}
                response = requests.post(f"{self.api_url}/upload-sync", files=files, timeout=300)
            
            if response.status_code == 200:
                print("✅ Successfully uploaded to Railway")
                return True
            else:
                print(f"❌ Upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False
    
    def trigger_railway_population(self):
        """Trigger population on Railway"""
        print("🔄 Triggering Railway population...")
        
        try:
            # Use async population to handle large dataset
            response = requests.post(f"{self.api_url}/populate-async", timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Population started: {result.get('message', 'Unknown status')}")
                return True
            else:
                print(f"❌ Population trigger failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Population error: {e}")
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
                    import time
                    time.sleep(5)
                    
            except Exception as e:
                print(f"   Error checking status: {e}")
                attempt += 1
                if attempt < max_attempts:
                    import time
                    time.sleep(5)
        
        print("⚠️ Population monitoring timed out")
        return False
    
    def verify_sync(self):
        """Verify that sync was successful"""
        print("🔍 Verifying sync...")
        
        try:
            response = requests.get(f"{self.api_url}/debug-recipes", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                recipe_count = data.get('recipe_collection_count', 0)
                print(f"✅ Railway now has {recipe_count} recipes")
                
                # Test a sample recipe
                sample_recipes = data.get('sample_recipes', [])
                if sample_recipes:
                    sample = sample_recipes[0]
                    print(f"   Sample recipe: {sample.get('title', 'Unknown')}")
                    print(f"   Cuisine: {sample.get('cuisine', 'N/A')}")
                    print(f"   Diets: {sample.get('diets', 'N/A')}")
                
                return recipe_count > 1000  # Should have most recipes
            else:
                print(f"❌ Verification failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False
    
    def run_complete_sync(self):
        """Run the complete sync process"""
        print("🚀 Starting Complete Railway Sync")
        print("=" * 50)
        
        # Step 1: Get all local recipes
        all_recipes = self.get_all_local_recipes()
        if not all_recipes['ids']:
            print("❌ No local recipes found")
            return False
        
        # Step 2: Create exact sync data
        sync_data = self.create_exact_sync_data(all_recipes)
        
        # Step 3: Upload to Railway
        if not self.upload_sync_data(sync_data):
            return False
        
        # Step 4: Trigger population
        if not self.trigger_railway_population():
            return False
        
        # Step 5: Monitor progress
        if not self.monitor_population():
            print("⚠️ Population may still be running in background")
        
        # Step 6: Verify sync
        if self.verify_sync():
            print("🎉 Complete sync successful!")
            return True
        else:
            print("⚠️ Sync completed but verification failed")
            return False

def main():
    syncer = CompleteRailwaySyncer()
    success = syncer.run_complete_sync()
    
    if success:
        print("\n✅ All recipes synced successfully!")
        print("🌐 Your Netlify app should now have all recipes with exact local data")
    else:
        print("\n❌ Sync encountered issues")
        print("Check the logs above for details")

if __name__ == "__main__":
    main()
