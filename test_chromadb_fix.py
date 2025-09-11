#!/usr/bin/env python3
"""
Test ChromaDB fix with correct NumPy version
"""

import subprocess
import sys

def install_correct_versions():
    """Install ChromaDB with correct NumPy version"""
    print("🔧 Installing ChromaDB with correct NumPy version...")
    
    packages = [
        "numpy==1.24.3",
        "chromadb==0.4.18"
    ]
    
    for package in packages:
        try:
            print(f"📦 Installing {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package, "--force-reinstall"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ {package} installed successfully")
            else:
                print(f"❌ Failed to install {package}")
                print(f"   Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error installing {package}: {e}")
            return False
    
    return True

def test_chromadb():
    """Test ChromaDB functionality"""
    print("\n🧪 Testing ChromaDB...")
    
    try:
        import chromadb
        import numpy as np
        print(f"✅ ChromaDB imported successfully")
        print(f"✅ NumPy version: {np.__version__}")
        
        # Test basic functionality
        client = chromadb.PersistentClient(path="./test_chroma_db")
        collection = client.get_or_create_collection("test_collection")
        
        # Test adding and retrieving data
        collection.add(
            documents=["test document"],
            metadatas=[{"test": True}],
            ids=["test_id"]
        )
        
        results = collection.get(ids=["test_id"])
        if results['documents']:
            print("✅ ChromaDB basic operations working")
            
            # Test user service functionality
            print("\n👤 Testing UserService with ChromaDB...")
            sys.path.append('backend')
            from backend.services.user_service import UserService
            
            user_service = UserService()
            if user_service.users_collection:
                print("✅ UserService ChromaDB collections available")
                
                # Test user registration
                result = user_service.register_user(
                    email="test@example.com",
                    password="TestPassword123!",
                    full_name="Test User"
                )
                
                if result["success"]:
                    print("✅ User registration with ChromaDB working")
                    return True
                else:
                    print(f"❌ User registration failed: {result['error']}")
                    return False
            else:
                print("❌ UserService ChromaDB collections not available")
                return False
        else:
            print("❌ ChromaDB operations failed")
            return False
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main test process"""
    print("🚀 ChromaDB Fix Test")
    print("=" * 25)
    
    if install_correct_versions():
        if test_chromadb():
            print("\n🎉 ChromaDB is working perfectly!")
            print("This configuration should work on Render!")
            return True
        else:
            print("\n❌ ChromaDB test failed")
            return False
    else:
        print("\n❌ Installation failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
