#!/usr/bin/env python3
"""
Test ChromaDB with Settings configuration (recommended approach)
"""

import os
import sys
import traceback

# Set up environment for local testing
os.environ['RENDER_ENVIRONMENT'] = 'true'
os.environ['CHROMA_DB_PATH'] = './test_chroma_local'

print("🔧 Testing ChromaDB with Settings configuration...")
print(f"Python version: {sys.version}")

try:
    import chromadb
    from chromadb.config import Settings
    print("✅ ChromaDB and Settings imported successfully")
    
    # Test with Settings configuration
    chroma_path = os.environ.get('CHROMA_DB_PATH', './test_chroma_local')
    print(f"   Using path: {chroma_path}")
    
    # Create directory
    os.makedirs(chroma_path, exist_ok=True)
    print(f"   Directory created: {chroma_path}")
    
    # Test with Settings (recommended approach)
    settings = Settings(
        is_persistent=True,
        persist_directory=chroma_path
    )
    
    client = chromadb.PersistentClient(settings=settings)
    print("✅ Persistent client created with Settings")
    
    # Test collection creation
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
    
    print("\n🎉 ChromaDB with Settings is working correctly!")
    
except ImportError as e:
    print(f"❌ ChromaDB import failed: {e}")
    print(f"   This suggests missing dependencies")
    sys.exit(1)
except Exception as e:
    print(f"❌ ChromaDB test failed: {e}")
    print(f"   Traceback: {traceback.format_exc()}")
    sys.exit(1)
