#!/usr/bin/env python3
"""
Direct Railway Population Script

This script directly populates your Railway deployment by making API calls.
It extracts data from your local ChromaDB and sends it to Railway via HTTP requests.
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

class DirectRailwayPopulator:
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
    
    def send_recipe_to_railway(self, recipe: Dict[str, Any]) -> bool:
        """Send a single recipe to Railway"""
        try:
            # Clean the recipe for API
            clean_recipe = self.clean_recipe_for_api(recipe)
            
            # Try to add via recipe cache endpoint
            response = self.session.post(
                f"{self.railway_url}/api/recipes/cache",
                json=clean_recipe,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                return True
            else:
                print(f"⚠️ Failed to add recipe {recipe.get('title', 'Unknown')}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"⚠️ Error sending recipe {recipe.get('title', 'Unknown')}: {e}")
            return False
    
    def clean_recipe_for_api(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Clean recipe data for API submission"""
        # Remove any non-serializable fields
        clean_recipe = {}
        
        for key, value in recipe.items():
            if key.startswith('_'):
                continue  # Skip internal fields
                
            try:
                # Test if value is JSON serializable
                json.dumps(value)
                clean_recipe[key] = value
            except (TypeError, ValueError):
                # Convert to string if not serializable
                clean_recipe[key] = str(value)
        
        # Ensure required fields exist
        if 'id' not in clean_recipe:
            clean_recipe['id'] = f"railway-{abs(hash(clean_recipe.get('title', 'unknown')))}"
        
        if 'title' not in clean_recipe:
            clean_recipe['title'] = 'Untitled Recipe'
        
        if 'ingredients' not in clean_recipe:
            clean_recipe['ingredients'] = []
        
        if 'instructions' not in clean_recipe:
            clean_recipe['instructions'] = ['No instructions provided']
        
        return clean_recipe
    
    def populate_railway_recipes(self, recipes: List[Dict[str, Any]]) -> bool:
        """Populate Railway with recipes"""
        print(f"🚀 Populating Railway with {len(recipes)} recipes...")
        
        successful = 0
        failed = 0
        
        # Process in batches to avoid overwhelming the server
        batch_size = 10
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(recipes) + batch_size - 1) // batch_size
            
            print(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} recipes)...")
            
            for recipe in batch:
                if self.send_recipe_to_railway(recipe):
                    successful += 1
                else:
                    failed += 1
                
                # Small delay to avoid overwhelming the server
                time.sleep(0.1)
            
            print(f"📊 Progress: {min(i + batch_size, len(recipes))}/{len(recipes)} recipes processed")
        
        print(f"\n📊 Population Results:")
        print(f"✅ Successfully added: {successful} recipes")
        print(f"❌ Failed: {failed} recipes")
        
        return successful > 0
    
    def verify_railway_data(self) -> bool:
        """Verify that data was successfully added to Railway"""
        try:
            print("🔍 Verifying Railway data...")
            
            # Try to get recipe count
            response = self.session.get(f"{self.railway_url}/api/recipes/count")
            if response.status_code == 200:
                count_data = response.json()
                recipe_count = count_data.get('count', 0)
                print(f"📊 Railway now has {recipe_count} recipes")
                return recipe_count > 0
            else:
                print(f"⚠️ Could not verify recipe count: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"⚠️ Error verifying Railway data: {e}")
            return False
    
    def populate_all_data(self) -> bool:
        """Populate all data to Railway"""
        print("🔄 Starting Railway population...")
        
        # Test connection first
        if not self.test_railway_connection():
            return False
        
        # Extract recipes
        recipes = self.extract_local_recipes()
        if not recipes:
            print("❌ No recipes found to populate")
            return False
        
        # Populate recipes
        success = self.populate_railway_recipes(recipes)
        
        if success:
            # Verify the data
            self.verify_railway_data()
        
        return success

def main():
    """Main function"""
    print("🚀 Direct Railway Population Tool")
    print("=" * 50)
    
    # Get Railway URL
    railway_url = os.environ.get('RAILWAY_URL')
    if not railway_url:
        railway_url = input("Enter your Railway URL (e.g., https://your-app.up.railway.app): ").strip()
        if not railway_url:
            print("❌ No Railway URL provided")
            return
    
    # Create populator
    populator = DirectRailwayPopulator(railway_url)
    
    # Confirm before proceeding
    print(f"\n⚠️ This will populate Railway at: {railway_url}")
    confirm = input("Proceed with population? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Population cancelled")
        return
    
    # Perform population
    success = populator.populate_all_data()
    
    if success:
        print("\n🎉 Railway population completed successfully!")
        print("🌐 Your Netlify frontend should now have access to the recipes!")
    else:
        print("\n❌ Railway population failed")
        print("💡 Check the error messages above for troubleshooting")

if __name__ == "__main__":
    main()
