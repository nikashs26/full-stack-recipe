#!/usr/bin/env python3
"""
Simple ChromaDB fix for Render
This script tries multiple approaches to get ChromaDB working
"""

import subprocess
import sys
import os

def try_chromadb_install():
    """Try different ChromaDB installation approaches"""
    print("🔧 Attempting ChromaDB installation for Render...")
    
    approaches = [
        {
            "name": "Minimal ChromaDB",
            "command": [sys.executable, "-m", "pip", "install", "chromadb==0.4.18", "--no-deps"],
            "deps": ["numpy", "sqlalchemy", "pydantic", "typing-extensions"]
        },
        {
            "name": "ChromaDB with core deps",
            "command": [sys.executable, "-m", "pip", "install", "chromadb==0.4.18", "numpy", "sqlalchemy", "pydantic"],
            "deps": []
        },
        {
            "name": "ChromaDB latest",
            "command": [sys.executable, "-m", "pip", "install", "chromadb"],
            "deps": []
        }
    ]
    
    for approach in approaches:
        print(f"\n📦 Trying: {approach['name']}")
        
        try:
            # Install main package
            result = subprocess.run(
                approach["command"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print(f"✅ {approach['name']} installed successfully")
                
                # Install dependencies if needed
                for dep in approach["deps"]:
                    try:
                        subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                                     capture_output=True, text=True, timeout=60)
                        print(f"✅ Dependency {dep} installed")
                    except:
                        print(f"⚠️ Dependency {dep} failed, but continuing...")
                
                # Test if it works
                if test_chromadb_import():
                    print(f"🎉 {approach['name']} is working!")
                    return True
                else:
                    print(f"❌ {approach['name']} installed but not working")
            else:
                print(f"❌ {approach['name']} failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {approach['name']} timed out")
        except Exception as e:
            print(f"❌ {approach['name']} error: {e}")
    
    return False

def test_chromadb_import():
    """Test if ChromaDB can be imported and used"""
    try:
        import chromadb
        print("✅ ChromaDB imported successfully")
        
        # Test basic client creation
        client = chromadb.PersistentClient(path="./test_chroma")
        print("✅ ChromaDB client created")
        
        # Test collection creation
        collection = client.get_or_create_collection("test")
        print("✅ ChromaDB collection created")
        
        # Test basic operations
        collection.add(
            documents=["test"],
            metadatas=[{"test": True}],
            ids=["test_id"]
        )
        
        results = collection.get(ids=["test_id"])
        if results['documents']:
            print("✅ ChromaDB operations working")
            return True
        else:
            print("❌ ChromaDB operations failed")
            return False
            
    except ImportError as e:
        print(f"❌ ChromaDB import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ ChromaDB test failed: {e}")
        return False

def create_chromadb_health_check():
    """Create a health check script for ChromaDB"""
    health_script = '''
import os
import sys

def check_chromadb_health():
    try:
        import chromadb
        print("ChromaDB: Available")
        
        # Test basic functionality
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_or_create_collection("health_check")
        
        # Test operations
        collection.add(
            documents=["health check"],
            metadatas=[{"type": "health"}],
            ids=["health_id"]
        )
        
        results = collection.get(ids=["health_id"])
        if results['documents']:
            print("ChromaDB: Working")
            return True
        else:
            print("ChromaDB: Not working")
            return False
            
    except ImportError:
        print("ChromaDB: Not installed")
        return False
    except Exception as e:
        print(f"ChromaDB: Error - {e}")
        return False

if __name__ == "__main__":
    check_chromadb_health()
'''
    
    with open('chromadb_health.py', 'w') as f:
        f.write(health_script)
    
    print("✅ Created chromadb_health.py")

def main():
    """Main fix process"""
    print("🚀 ChromaDB Fix for Render")
    print("=" * 30)
    
    # Try installation
    if try_chromadb_install():
        print("\n🎉 ChromaDB is now working!")
        
        # Create health check
        create_chromadb_health_check()
        
        print("\n📝 Next steps:")
        print("1. Deploy this to Render")
        print("2. Check Render logs for ChromaDB status")
        print("3. Test with: python chromadb_health.py")
        
        return True
    else:
        print("\n❌ All ChromaDB installation attempts failed")
        print("The fallback system will be used instead")
        return False

if __name__ == "__main__":
    main()
