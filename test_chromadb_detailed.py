#!/usr/bin/env python3
"""
Detailed ChromaDB test for Render - will help debug import issues
"""

import os
import sys
import traceback

# Set up environment for local testing
os.environ['RENDER_ENVIRONMENT'] = 'true'
os.environ['CHROMA_DB_PATH'] = './test_chroma_local'

print("🔧 Detailed ChromaDB test for Render...")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Test the exact same import pattern used in the services
print("\n🔍 Testing ChromaDB import (same pattern as services)...")

try:
    import chromadb
    CHROMADB_AVAILABLE = True
    print("✅ ChromaDB imported successfully")
    print(f"   Version: {chromadb.__version__}")
except ImportError as e:
    CHROMADB_AVAILABLE = False
    print(f"❌ ChromaDB import failed: {e}")
    print(f"   This is the error that causes fallback to in-memory storage")
    
    # Try to get more details about what's missing
    print("\n🔍 Analyzing import failure...")
    
    # Test individual components that might be missing
    critical_deps = ['numpy', 'pydantic', 'typing_extensions', 'bcrypt', 'fastapi']
    for dep in critical_deps:
        try:
            __import__(dep)
            print(f"   ✅ {dep} available")
        except ImportError as de:
            print(f"   ❌ {dep} missing: {de}")
    
    sys.exit(1)
except Exception as e:
    CHROMADB_AVAILABLE = False
    print(f"❌ ChromaDB import failed with unexpected error: {e}")
    print(f"   Traceback: {traceback.format_exc()}")
    sys.exit(1)

# If we get here, ChromaDB imported successfully
print("\n🔍 Testing ChromaDB functionality...")

try:
    # Test the exact same initialization pattern as the services
    chroma_path = os.environ.get('CHROMA_DB_PATH', '/opt/render/project/src/chroma_db')
    print(f"   Using path: {chroma_path}")
    
    # Create directory
    os.makedirs(chroma_path, exist_ok=True)
    print(f"   Directory created: {chroma_path}")
    
    # Test persistent client (same as services)
    client = chromadb.PersistentClient(path=chroma_path)
    print("✅ Persistent client created")
    
    # Test collection creation (same as services)
    collection = client.get_or_create_collection("test_collection")
    print("✅ Collection created")
    
    # Test basic operations
    collection.add(
        ids=["test1"],
        documents=["This is a test document"],
        metadatas=[{"test": True}]
    )
    print("✅ Document added")
    
    results = collection.query(query_texts=["test document"], n_results=1)
    print("✅ Query executed")
    print(f"   Found {len(results['documents'][0])} documents")
    
    print("\n🎉 ChromaDB is working correctly on Render!")
    
except Exception as e:
    print(f"❌ ChromaDB functionality failed: {e}")
    print(f"   Traceback: {traceback.format_exc()}")
    sys.exit(1)
