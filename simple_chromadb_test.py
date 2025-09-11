#!/usr/bin/env python3
"""
Simple test to verify ChromaDB works locally
Run this with: python3 simple_chromadb_test.py
"""

def test_chromadb_import():
    """Test if ChromaDB can be imported"""
    print("🧪 Testing ChromaDB Import")
    print("=" * 30)
    
    try:
        import chromadb
        print(f"✅ ChromaDB imported successfully")
        print(f"ChromaDB version: {chromadb.__version__}")
        return True
    except ImportError as e:
        print(f"❌ ChromaDB import failed: {e}")
        print("💡 Try installing with: pip install chromadb")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_chromadb_basic_functionality():
    """Test basic ChromaDB functionality"""
    print("\n🧪 Testing ChromaDB Basic Functionality")
    print("=" * 40)
    
    try:
        import chromadb
        import tempfile
        import os
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        print(f"Using temp directory: {temp_dir}")
        
        # Test client creation
        print("Creating ChromaDB client...")
        client = chromadb.PersistentClient(path=temp_dir)
        print("✅ ChromaDB client created")
        
        # Test embedding function
        print("Creating embedding function...")
        embedding_function = chromadb.utils.embedding_functions.DefaultEmbeddingFunction()
        print("✅ Embedding function created")
        
        # Test collection creation
        print("Creating collection...")
        collection = client.get_or_create_collection(
            name="test_collection",
            embedding_function=embedding_function
        )
        print("✅ Collection created")
        
        # Test basic operations
        print("Testing basic operations...")
        collection.add(
            ids=["test1"],
            documents=["This is a test document"],
            metadatas=[{"type": "test"}]
        )
        print("✅ Document added")
        
        # Test retrieval
        results = collection.get(ids=["test1"])
        if results['ids']:
            print("✅ Document retrieved successfully")
            print(f"Retrieved document: {results['documents'][0]}")
        else:
            print("❌ Document retrieval failed")
            return False
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("✅ Cleanup completed")
        
        print("\n🎉 All ChromaDB tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Simple ChromaDB Test")
    print("=" * 50)
    
    # Test import
    import_success = test_chromadb_import()
    
    if not import_success:
        print("\n❌ ChromaDB import failed - cannot proceed with functionality test")
        print("\n💡 To install ChromaDB, run:")
        print("   pip install chromadb")
        print("   or")
        print("   pip install -r backend/requirements-render-comprehensive.txt")
        return False
    
    # Test functionality
    functionality_success = test_chromadb_basic_functionality()
    
    print("\n" + "=" * 50)
    print("📊 Test Results")
    print("=" * 50)
    print(f"ChromaDB Import: {'✅ PASS' if import_success else '❌ FAIL'}")
    print(f"ChromaDB Functionality: {'✅ PASS' if functionality_success else '❌ FAIL'}")
    
    if import_success and functionality_success:
        print("\n🎉 All tests passed! ChromaDB should work on Render")
        return True
    else:
        print("\n❌ Some tests failed - check installation")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
