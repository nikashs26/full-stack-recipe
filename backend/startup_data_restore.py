#!/usr/bin/env python3
"""
Startup Data Restore for Railway
This script runs on Railway startup to ensure data is always available
"""

import os
import json
import sys
import time
import requests
from pathlib import Path

def check_railway_data():
    """Check if Railway has data"""
    try:
        api_url = "https://full-stack-recipe-production.up.railway.app/api"
        response = requests.get(f"{api_url}/recipe-counts", timeout=10)
        if response.status_code == 200:
            data = response.json()
            recipe_count = data.get('total_recipes', 0)
            return recipe_count > 0
        return False
    except:
        return False

def restore_data_from_file():
    """Restore data from a pre-populated file"""
    try:
        # Check if we have a data file
        data_file = Path("/app/data/railway_sync_data.json")
        if not data_file.exists():
            print("No data file found for restoration")
            return False
        
        print("Found data file, restoring...")
        
        # Upload data to Railway
        with open(data_file, 'r') as f:
            sync_data = json.load(f)
        
        api_url = "https://full-stack-recipe-production.up.railway.app/api"
        
        # Upload sync data
        upload_response = requests.post(
            f"{api_url}/upload-sync",
            json=sync_data,
            timeout=120
        )
        
        if upload_response.status_code not in [200, 201]:
            print(f"Upload failed: {upload_response.status_code}")
            return False
        
        print("Data uploaded successfully")
        
        # Trigger population
        populate_response = requests.post(f"{api_url}/populate-async", timeout=60)
        
        if populate_response.status_code not in [200, 202]:
            print(f"Population trigger failed: {populate_response.status_code}")
            return False
        
        print("Population triggered successfully")
        return True
        
    except Exception as e:
        print(f"Error restoring data: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 Railway startup data restore...")
    
    # Wait a bit for the app to start
    time.sleep(10)
    
    # Check if we already have data
    if check_railway_data():
        print("✅ Railway already has data")
        return
    
    print("⚠️ Railway missing data, attempting restore...")
    
    # Try to restore from file
    if restore_data_from_file():
        print("✅ Data restored successfully")
    else:
        print("❌ Failed to restore data")

if __name__ == "__main__":
    main()
