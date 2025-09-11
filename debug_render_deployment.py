#!/usr/bin/env python3
"""
Debug script for Render deployment issues
"""

import os
import sys
import json
import traceback

def check_environment():
    """Check environment variables and system info"""
    print("🔍 Environment Check")
    print("=" * 40)
    
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    
    print("\nEnvironment variables:")
    env_vars = [
        'CHROMA_DB_PATH',
        'RENDER_ENVIRONMENT', 
        'RAILWAY_ENVIRONMENT',
        'FLASK_ENV',
        'PYTHON_VERSION',
        'PORT',
        'CHROMA_SERVER_HOST',
        'CHROMA_SERVER_HTTP_PORT',
        'CHROMA_DB_IMPL'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        print(f"  {var}: {value}")
    
    print(f"\nDirectory contents:")
    try:
        for item in os.listdir('.'):
            print(f"  {item}")
    except Exception as e:
        print(f"  Error listing directory: {e}")
    
    # Check if we're in Render
    if os.path.exists('/opt/render'):
        print(f"\n✅ Running in Render environment")
        print(f"Render project path: /opt/render/project")
        if os.path.exists('/opt/render/project'):
            print(f"Project directory contents:")
            try:
                for item in os.listdir('/opt/render/project'):
                    print(f"  {item}")
            except Exception as e:
                print(f"  Error listing project directory: {e}")
    else:
        print(f"\nℹ️ Not running in Render environment")

def check_chromadb_path():
    """Check ChromaDB path and permissions"""
    print("\n🗂️ ChromaDB Path Check")
    print("=" * 40)
    
    chroma_path = os.environ.get('CHROMA_DB_PATH', './chroma_db')
    print(f"ChromaDB path: {chroma_path}")
    print(f"Path exists: {os.path.exists(chroma_path)}")
    
    if os.path.exists(chroma_path):
        print(f"Path is directory: {os.path.isdir(chroma_path)}")
        print(f"Path is writable: {os.access(chroma_path, os.W_OK)}")
        print(f"Path is readable: {os.access(chroma_path, os.R_OK)}")
        
        try:
            contents = os.listdir(chroma_path)
            print(f"Directory contents: {contents}")
        except Exception as e:
            print(f"Error listing directory contents: {e}")
    else:
        print("Directory does not exist - will be created")

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n📦 Dependencies Check")
    print("=" * 40)
    
    required_packages = [
        'flask',
        'flask_cors',
        'chromadb',
        'numpy',
        'sqlalchemy',
        'pydantic',
        'psutil',
        'hnswlib',
        'httpx',
        'duckdb'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
        except Exception as e:
            print(f"⚠️ {package} - ERROR: {e}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {missing_packages}")
        return False
    else:
        print(f"\n✅ All required packages available")
        return True

def test_chromadb_import():
    """Test ChromaDB import and basic functionality"""
    print("\n🧪 ChromaDB Import Test")
    print("=" * 40)
    
    try:
        import chromadb
        print(f"✅ ChromaDB imported successfully")
        print(f"ChromaDB version: {chromadb.__version__}")
        return True
    except ImportError as e:
        print(f"❌ ChromaDB import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_chromadb_initialization():
    """Test ChromaDB initialization"""
    print("\n🔧 ChromaDB Initialization Test")
    print("=" * 40)
    
    try:
        import chromadb
        
        # Test path
        test_path = '/tmp/test_chromadb_debug'
        os.makedirs(test_path, exist_ok=True)
        
        print(f"Creating test client at: {test_path}")
        client = chromadb.PersistentClient(path=test_path)
        print("✅ ChromaDB client created")
        
        # Test embedding function
        embedding_function = chromadb.utils.embedding_functions.DefaultEmbeddingFunction()
        print("✅ Embedding function created")
        
        # Test collection
        collection = client.get_or_create_collection(
            name="test_collection",
            embedding_function=embedding_function
        )
        print("✅ Collection created")
        
        # Test basic operation
        collection.add(
            ids=["test1"],
            documents=["Test document"],
            metadatas=[{"test": True}]
        )
        print("✅ Basic operation successful")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_path, ignore_errors=True)
        print("✅ Test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB initialization failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run all debug checks"""
    print("🐛 Render Deployment Debug Script")
    print("=" * 50)
    
    # Run all checks
    check_environment()
    check_chromadb_path()
    deps_ok = check_dependencies()
    import_ok = test_chromadb_import()
    
    if import_ok:
        init_ok = test_chromadb_initialization()
    else:
        init_ok = False
    
    print("\n" + "=" * 50)
    print("📊 Summary")
    print("=" * 50)
    print(f"Dependencies: {'✅ OK' if deps_ok else '❌ FAILED'}")
    print(f"ChromaDB Import: {'✅ OK' if import_ok else '❌ FAILED'}")
    print(f"ChromaDB Init: {'✅ OK' if init_ok else '❌ FAILED'}")
    
    if deps_ok and import_ok and init_ok:
        print("\n🎉 All checks passed! ChromaDB should work on Render")
        return True
    else:
        print("\n❌ Some checks failed - see details above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
