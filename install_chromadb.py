#!/usr/bin/env python3
"""
ChromaDB Installation Script for Render
This script ensures ChromaDB is properly installed with all dependencies
"""

import subprocess
import sys
import os

def install_chromadb():
    """Install ChromaDB with all required dependencies"""
    print("🔧 Installing ChromaDB for Render...")
    
    # List of packages to install in order
    packages = [
        "numpy>=1.21.0,<2.0.0",
        "sqlalchemy>=1.4.0,<2.0.0", 
        "pydantic>=1.8.0,<2.0.0",
        "typing-extensions>=4.0.0",
        "psutil>=5.8.0",
        "hnswlib>=0.7.0",
        "httpx>=0.24.0",
        "duckdb>=0.8.0",
        "sentence-transformers>=2.2.0",
        "chromadb==0.4.18"
    ]
    
    for package in packages:
        try:
            print(f"📦 Installing {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package, "--no-cache-dir"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ {package} installed successfully")
            else:
                print(f"❌ Failed to install {package}")
                print(f"   Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout installing {package}")
            return False
        except Exception as e:
            print(f"❌ Error installing {package}: {e}")
            return False
    
    return True

def test_chromadb():
    """Test if ChromaDB is working properly"""
    print("\n🧪 Testing ChromaDB installation...")
    
    try:
        import chromadb
        print("✅ ChromaDB imported successfully")
        
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
            
            # Clean up test data
            client.delete_collection("test_collection")
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

def main():
    """Main installation process"""
    print("🚀 ChromaDB Installation for Render")
    print("=" * 40)
    
    # Check if we're in a Render environment
    if os.environ.get('RENDER_ENVIRONMENT'):
        print("🌐 Running in Render environment")
    else:
        print("💻 Running in local environment")
    
    # Install ChromaDB
    if install_chromadb():
        print("\n✅ ChromaDB installation completed")
        
        # Test installation
        if test_chromadb():
            print("\n🎉 ChromaDB is working perfectly!")
            return True
        else:
            print("\n❌ ChromaDB installation failed tests")
            return False
    else:
        print("\n❌ ChromaDB installation failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
