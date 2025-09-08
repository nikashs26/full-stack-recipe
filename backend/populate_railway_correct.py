#!/usr/bin/env python3
"""
Populate Railway with correct recipe data from local sync_data.json
This script uploads the correct sync data and populates Railway properly
"""

import requests
import json
import time
import os

def upload_sync_data_to_railway():
    """Upload the correct sync data to Railway"""
    railway_url = "https://full-stack-recipe-production.up.railway.app"
    
    # Read the local sync data
    with open('backend/sync_data.json', 'r') as f:
        sync_data = f.read()
    
    print(f"📤 Uploading sync data to Railway...")
    print(f"   Data size: {len(sync_data)} bytes")
    
    # Upload the sync data
    files = {'file': ('sync_data.json', sync_data, 'application/json')}
    response = requests.post(f"{railway_url}/api/upload-sync", files=files, timeout=60)
    
    if response.status_code == 200:
        print("✅ Sync data uploaded successfully")
        return True
    else:
        print(f"❌ Failed to upload sync data: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def trigger_railway_population():
    """Trigger Railway to populate from the uploaded sync data"""
    railway_url = "https://full-stack-recipe-production.up.railway.app"
    
    print("🚀 Triggering Railway population...")
    
    # Trigger population
    response = requests.post(f"{railway_url}/api/populate-async", timeout=30)
    
    if response.status_code == 202:
        print("✅ Population started successfully")
        return True
    else:
        print(f"❌ Failed to start population: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def monitor_population():
    """Monitor the population progress"""
    railway_url = "https://full-stack-recipe-production.up.railway.app"
    
    print("⏳ Monitoring population progress...")
    
    max_wait = 300  # 5 minutes max
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{railway_url}/api/populate-status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            population = data.get('population', {})
            recipe_count = data.get('recipe_count', {})
            
            print(f"   Status: {population.get('message', 'Unknown')}")
            print(f"   Recipe count: {recipe_count.get('total', 0)}")
            
            if not population.get('running', False):
                if population.get('success', False):
                    print("✅ Population completed successfully!")
                    return True
                else:
                    print(f"❌ Population failed: {population.get('message', 'Unknown error')}")
                    return False
        
        time.sleep(10)
    
    print("⏰ Population monitoring timed out")
    return False

def verify_population():
    """Verify that the population worked correctly"""
    railway_url = "https://full-stack-recipe-production.up.railway.app"
    
    print("🔍 Verifying population results...")
    
    # Check recipe count
    response = requests.get(f"{railway_url}/api/debug-recipes", timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        count = data.get('recipe_collection_count', 0)
        sample_recipes = data.get('sample_recipes', [])
        
        print(f"   Total recipes: {count}")
        
        if sample_recipes:
            print("   Sample recipes:")
            for i, recipe in enumerate(sample_recipes[:3]):
                title = recipe.get('title', 'No title')
                cuisine = recipe.get('cuisine', 'No cuisine')
                cuisines = recipe.get('cuisines', 'No cuisines')
                print(f"     {i+1}. \"{title}\" - Cuisine: \"{cuisine}\" - Cuisines: \"{cuisines}\"")
        
        # Check if we have proper titles and cuisines
        has_proper_titles = any(
            recipe.get('title', '') != 'Untitled Recipe' 
            for recipe in sample_recipes
        )
        has_proper_cuisines = any(
            recipe.get('cuisine', '').lower() not in ['', 'other', 'none', 'null']
            for recipe in sample_recipes
        )
        
        if has_proper_titles and has_proper_cuisines:
            print("✅ Population verification successful - recipes have proper titles and cuisines!")
            return True
        else:
            print("❌ Population verification failed - recipes still have generic titles/cuisines")
            return False
    else:
        print(f"❌ Failed to verify population: {response.status_code}")
        return False

def main():
    """Main function to populate Railway with correct data"""
    print("🚀 Starting Railway population with correct recipe data...")
    print("=" * 60)
    
    # Step 1: Upload sync data
    if not upload_sync_data_to_railway():
        return False
    
    # Step 2: Trigger population
    if not trigger_railway_population():
        return False
    
    # Step 3: Monitor progress
    if not monitor_population():
        return False
    
    # Step 4: Verify results
    if not verify_population():
        return False
    
    print("🎉 Railway population completed successfully!")
    print("   Your recipes should now have proper titles and cuisine tags.")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
