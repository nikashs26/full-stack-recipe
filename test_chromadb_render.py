#!/usr/bin/env python3
"""
Test script to verify ChromaDB installation and initialization on Render
"""

import os
import sys
import traceback

def test_chromadb_import():
    """Test if ChromaDB can be imported"""
    print("Testing ChromaDB import...")
    try:
        import chromadb
        print("✅ ChromaDB imported successfully")
        print(f"ChromaDB version: {chromadb.__version__}")
        return True
    except ImportError as e:
        print(f"❌ ChromaDB import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error importing ChromaDB: {e}")
        return False

def test_chromadb_dependencies():
    """Test if ChromaDB dependencies are available"""
    print("\nTesting ChromaDB dependencies...")
    
    dependencies = [
        'numpy',
        'sqlalchemy', 
        'pydantic',
        'psutil',
        'hnswlib',
        'httpx',
        'duckdb',
        'sentence_transformers'
    ]
    
    missing_deps = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} available")
        except ImportError:
            print(f"❌ {dep} missing")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\nMissing dependencies: {missing_deps}")
        return False
    else:
        print("\n✅ All dependencies available")
        return True

def test_chromadb_initialization():
    """Test if ChromaDB can be initialized"""
    print("\nTesting ChromaDB initialization...")
    
    try:
        import chromadb
        
        # Set up test path
        test_path = '/tmp/test_chromadb'
        os.makedirs(test_path, exist_ok=True)
        
        print(f"Creating ChromaDB client at: {test_path}")
        client = chromadb.PersistentClient(path=test_path)
        print("✅ ChromaDB client created successfully")
        
        # Test embedding function
        print("Testing embedding function...")
        embedding_function = chromadb.utils.embedding_functions.DefaultEmbeddingFunction()
        print("✅ Embedding function created successfully")
        
        # Test collection creation
        print("Testing collection creation...")
        collection = client.get_or_create_collection(
            name="test_collection",
            metadata={"description": "Test collection"},
            embedding_function=embedding_function
        )
        print("✅ Collection created successfully")
        
        # Test basic operations
        print("Testing basic operations...")
        collection.add(
            ids=["test1"],
            documents=["This is a test document"],
            metadatas=[{"type": "test"}]
        )
        
        results = collection.get(ids=["test1"])
        if results['ids']:
            print("✅ Basic operations work")
        else:
            print("❌ Basic operations failed")
            return False
        
        # Cleanup
        import shutil
        shutil.rmtree(test_path, ignore_errors=True)
        print("✅ Test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB initialization failed: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        return False

def test_environment():
    """Test environment variables and paths"""
    print("\nTesting environment...")
    
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    
    # Check environment variables
    env_vars = ['CHROMA_DB_PATH', 'RENDER_ENVIRONMENT', 'RAILWAY_ENVIRONMENT']
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        print(f"{var}: {value}")
    
    # Check if we're in Render environment
    if os.path.exists('/opt/render'):
        print("✅ Running in Render environment")
        render_path = '/opt/render/project/src/chroma_db'
        print(f"Render ChromaDB path: {render_path}")
        print(f"Path exists: {os.path.exists(render_path)}")
        if os.path.exists(render_path):
            print(f"Path is writable: {os.access(render_path, os.W_OK)}")
    else:
        print("ℹ️ Not running in Render environment")

def main():
    """Run all tests"""
    print("🧪 ChromaDB Render Test Script")
    print("=" * 50)
    
    # Test environment
    test_environment()
    
    # Test import
    import_success = test_chromadb_import()
    if not import_success:
        print("\n❌ ChromaDB import failed - cannot proceed with other tests")
        return False
    
    # Test dependencies
    deps_success = test_chromadb_dependencies()
    if not deps_success:
        print("\n⚠️ Some dependencies missing - ChromaDB may not work properly")
    
    # Test initialization
    init_success = test_chromadb_initialization()
    
    print("\n" + "=" * 50)
    if import_success and init_success:
        print("🎉 All tests passed! ChromaDB should work on Render")
        return True
    else:
        print("❌ Some tests failed - ChromaDB may not work properly on Render")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)