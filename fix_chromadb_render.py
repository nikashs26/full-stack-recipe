#!/usr/bin/env python3
"""
Quick fix script to test ChromaDB on Render
This script will help identify and fix the ChromaDB issue
"""

import requests
import json
import os

def test_chromadb_import():
    """Test if ChromaDB can be imported and used"""
    print("🔍 Testing ChromaDB Import and Usage")
    print("=" * 40)
    
    try:
        import chromadb
        print("✅ ChromaDB imported successfully")
        
        # Test basic ChromaDB functionality
        print("🔧 Testing ChromaDB client creation...")
        
        # Test with different paths
        test_paths = [
            './chroma_db',
            '/opt/render/project/src/chroma_db',
            '/tmp/chroma_db_test'
        ]
        
        for path in test_paths:
            try:
                print(f"   Testing path: {path}")
                client = chromadb.PersistentClient(path=path)
                collection = client.get_or_create_collection("test_collection")
                print(f"   ✅ Success with path: {path}")
                
                # Test basic operations
                collection.add(
                    documents=["test document"],
                    metadatas=[{"test": True}],
                    ids=["test_id"]
                )
                
                results = collection.get(ids=["test_id"])
                if results['documents']:
                    print(f"   ✅ Basic operations work with path: {path}")
                    return path
                else:
                    print(f"   ❌ Basic operations failed with path: {path}")
                    
            except Exception as e:
                print(f"   ❌ Failed with path {path}: {e}")
        
        return None
        
    except ImportError as e:
        print(f"❌ ChromaDB import failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def test_render_environment():
    """Test Render environment variables"""
    print("\n🌐 Testing Render Environment")
    print("=" * 40)
    
    base_url = os.getenv('RENDER_URL', 'https://dietary-delight.onrender.com')
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/api/health", timeout=10)
        print(f"Health check: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"Health response: {health_data}")
            
            # Check if there's a ChromaDB health endpoint
            if 'services' in health_data and 'chromadb' in health_data['services']:
                chromadb_health_url = f"{base_url}{health_data['services']['chromadb']}"
                print(f"ChromaDB health URL: {chromadb_health_url}")
                
                try:
                    chromadb_response = requests.get(chromadb_health_url, timeout=10)
                    print(f"ChromaDB health: {chromadb_response.status_code}")
                    if chromadb_response.status_code == 200:
                        print(f"ChromaDB health data: {chromadb_response.json()}")
                    else:
                        print(f"ChromaDB health error: {chromadb_response.text}")
                except Exception as e:
                    print(f"ChromaDB health check failed: {e}")
        
    except Exception as e:
        print(f"❌ Render connection failed: {e}")

def create_minimal_user_service():
    """Create a minimal UserService that should work on Render"""
    print("\n🔧 Creating Minimal UserService Fix")
    print("=" * 40)
    
    fix_code = '''
# Minimal UserService fix for Render
import os
import json
import uuid
from datetime import datetime

# Force ChromaDB import
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

class MinimalUserService:
    def __init__(self):
        if not CHROMADB_AVAILABLE:
            print("❌ ChromaDB not available")
            self.users_collection = None
            return
        
        # Try multiple paths
        possible_paths = [
            os.environ.get('CHROMA_DB_PATH', './chroma_db'),
            '/opt/render/project/src/chroma_db',
            './chroma_db',
            '/tmp/chroma_db'
        ]
        
        for path in possible_paths:
            try:
                print(f"Trying ChromaDB path: {path}")
                os.makedirs(path, exist_ok=True)
                client = chromadb.PersistentClient(path=path)
                self.users_collection = client.get_or_create_collection("users")
                print(f"✅ ChromaDB initialized at: {path}")
                return
            except Exception as e:
                print(f"❌ Failed with path {path}: {e}")
                continue
        
        print("❌ All ChromaDB paths failed")
        self.users_collection = None
    
    def register_user(self, email, password, full_name=""):
        if not self.users_collection:
            return {"success": False, "error": "Database not available"}
        
        try:
            # Simple registration logic
            user_id = f"user_{str(uuid.uuid4())}"
            user_data = {
                "user_id": user_id,
                "email": email,
                "password_hash": password,  # In real app, hash this
                "full_name": full_name,
                "is_verified": True,  # Skip verification for testing
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.users_collection.upsert(
                documents=[json.dumps(user_data)],
                metadatas=[{"email": email, "user_id": user_id}],
                ids=[user_id]
            )
            
            return {"success": True, "user_id": user_id, "email": email}
        except Exception as e:
            return {"success": False, "error": str(e)}
'''
    
    with open('minimal_user_service.py', 'w') as f:
        f.write(fix_code)
    
    print("✅ Created minimal_user_service.py")
    print("   This can be used as a temporary fix for Render")

if __name__ == "__main__":
    print("🚀 ChromaDB Render Fix Diagnostic")
    print("=" * 50)
    
    # Test local ChromaDB
    working_path = test_chromadb_import()
    
    # Test Render environment
    test_render_environment()
    
    # Create minimal fix
    create_minimal_user_service()
    
    if working_path:
        print(f"\n✅ Local ChromaDB works with path: {working_path}")
        print("   This path should work on Render too")
    else:
        print("\n❌ Local ChromaDB test failed")
        print("   Check your ChromaDB installation")
    
    print("\n📝 Next steps:")
    print("1. Deploy the updated UserService to Render")
    print("2. Check Render logs for ChromaDB initialization messages")
    print("3. Test with the setup script again")
