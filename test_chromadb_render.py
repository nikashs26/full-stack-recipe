#!/usr/bin/env python3
"""
ChromaDB test script for Render deployment
This script tests if ChromaDB is working properly on Render
"""

import os
import sys

def test_chromadb_import():
    """Test if ChromaDB can be imported"""
    try:
        import chromadb
        print("✅ ChromaDB imported successfully")
        print(f"   ChromaDB version: {chromadb.__version__}")
        return True
    except ImportError as e:
        print(f"❌ ChromaDB import failed: {e}")
        return False

def test_chromadb_functionality():
    """Test ChromaDB basic functionality"""
    try:
        import chromadb
        
        # Test client creation
        chroma_path = os.environ.get('CHROMA_DB_PATH', './chroma_db')
        print(f"🔧 Testing ChromaDB at path: {chroma_path}")
        
        client = chromadb.PersistentClient(path=chroma_path)
        print("✅ ChromaDB client created")
        
        # Test collection creation
        collection = client.get_or_create_collection("test_collection")
        print("✅ ChromaDB collection created")
        
        # Test basic operations
        collection.add(
            documents=["test document"],
            metadatas=[{"test": True, "type": "health_check"}],
            ids=["test_id"]
        )
        print("✅ ChromaDB add operation successful")
        
        # Test retrieval
        results = collection.get(ids=["test_id"])
        if results['documents']:
            print("✅ ChromaDB get operation successful")
            print(f"   Retrieved: {results['documents'][0]}")
        else:
            print("❌ ChromaDB get operation failed")
            return False
        
        # Test user service
        print("\n👤 Testing UserService with ChromaDB...")
        sys.path.append('backend')
        from backend.services.user_service import UserService
        
        user_service = UserService()
        if user_service.users_collection:
            print("✅ UserService ChromaDB collections available")
            
            # Test user registration
            result = user_service.register_user(
                email="render-test@example.com",
                password="TestPassword123!",
                full_name="Render Test User"
            )
            
            if result["success"]:
                print("✅ User registration with ChromaDB working")
                print(f"   User ID: {result['user_id']}")
                return True
            else:
                print(f"❌ User registration failed: {result['error']}")
                return False
        else:
            print("❌ UserService ChromaDB collections not available")
            return False
            
    except Exception as e:
        print(f"❌ ChromaDB functionality test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 ChromaDB Test for Render")
    print("=" * 30)
    
    # Test import
    if not test_chromadb_import():
        print("\n❌ ChromaDB is not available")
        print("The fallback system will be used instead")
        return False
    
    # Test functionality
    if test_chromadb_functionality():
        print("\n🎉 ChromaDB is working perfectly on Render!")
        print("✅ User authentication will use persistent ChromaDB storage")
        return True
    else:
        print("\n❌ ChromaDB functionality test failed")
        print("The fallback system will be used instead")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
