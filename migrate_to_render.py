#!/usr/bin/env python3
"""
Migration script to help transfer data from Railway to Render
"""

import os
import json
import requests
from datetime import datetime

def create_render_sync_data():
    """Create sync data file for Render deployment"""
    
    # Check if we have existing sync data
    sync_files = [
        'complete_sync_data.json',
        'railway_sync_data.json',
        'complete_railway_sync_data.json'
    ]
    
    sync_data = None
    used_file = None
    
    for file_path in sync_files:
        if os.path.exists(file_path):
            print(f"📁 Found existing sync data: {file_path}")
            try:
                with open(file_path, 'r') as f:
                    sync_data = json.load(f)
                used_file = file_path
                break
            except Exception as e:
                print(f"⚠️ Error reading {file_path}: {e}")
                continue
    
    if not sync_data:
        print("❌ No existing sync data found. Please run a backup first.")
        return False
    
    # Create Render-specific sync data
    render_sync_data = {
        'migration_info': {
            'from': 'Railway',
            'to': 'Render',
            'migrated_at': datetime.now().isoformat(),
            'source_file': used_file
        },
        'recipes': sync_data.get('recipes', []),
        'users': sync_data.get('users', []),
        'preferences': sync_data.get('preferences', []),
        'reviews': sync_data.get('reviews', []),
        'folders': sync_data.get('folders', [])
    }
    
    # Save Render sync data
    output_file = 'render_sync_data.json'
    with open(output_file, 'w') as f:
        json.dump(render_sync_data, f, indent=2)
    
    print(f"✅ Created Render sync data: {output_file}")
    print(f"📊 Contains:")
    print(f"   - {len(render_sync_data['recipes'])} recipes")
    print(f"   - {len(render_sync_data['users'])} users")
    print(f"   - {len(render_sync_data['preferences'])} preferences")
    print(f"   - {len(render_sync_data['reviews'])} reviews")
    print(f"   - {len(render_sync_data['folders'])} folders")
    
    return True

def test_render_deployment():
    """Test if Render deployment is working"""
    render_url = "https://dietary-delight.onrender.com"
    
    print(f"🔍 Testing Render deployment at {render_url}...")
    
    try:
        # Test basic health
        response = requests.get(f"{render_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Render deployment is healthy!")
            return True
        else:
            print(f"⚠️ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach Render deployment: {e}")
        return False

def upload_to_render():
    """Upload sync data to Render"""
    render_url = "https://dietary-delight.onrender.com"
    sync_file = "render_sync_data.json"
    
    if not os.path.exists(sync_file):
        print(f"❌ Sync file {sync_file} not found. Run create_render_sync_data() first.")
        return False
    
    print(f"📤 Uploading {sync_file} to Render...")
    
    try:
        with open(sync_file, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{render_url}/api/upload-sync", files=files, timeout=60)
        
        if response.status_code == 200:
            print("✅ Sync data uploaded successfully!")
            return True
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Upload error: {e}")
        return False

def populate_render():
    """Populate Render with uploaded data"""
    render_url = "https://dietary-delight.onrender.com"
    
    print("🔄 Populating Render with uploaded data...")
    
    try:
        response = requests.post(f"{render_url}/api/populate-from-file", timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Population successful: {result.get('message', 'Unknown')}")
            return True
        else:
            print(f"❌ Population failed: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Population error: {e}")
        return False

def main():
    """Main migration process"""
    print("🚀 Starting Railway to Render Migration")
    print("=" * 50)
    
    # Step 1: Create sync data
    print("\n1️⃣ Creating Render sync data...")
    if not create_render_sync_data():
        return
    
    # Step 2: Test Render deployment
    print("\n2️⃣ Testing Render deployment...")
    if not test_render_deployment():
        print("⚠️ Render deployment not ready. Please deploy first.")
        return
    
    # Step 3: Upload data
    print("\n3️⃣ Uploading data to Render...")
    if not upload_to_render():
        return
    
    # Step 4: Populate data
    print("\n4️⃣ Populating Render database...")
    if not populate_render():
        return
    
    print("\n🎉 Migration completed successfully!")
    print("✅ Your backend is now running on Render with all your data!")
    print("🔗 URL: https://dietary-delight.onrender.com")

if __name__ == "__main__":
    main()
