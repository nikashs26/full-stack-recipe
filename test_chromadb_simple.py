#!/usr/bin/env python3
"""
Simple ChromaDB test for Render deployment
"""

import os
import sys

# Set up environment for Render
os.environ['RENDER_ENVIRONMENT'] = 'true'
os.environ['CHROMA_DB_PATH'] = '/opt/render/project/src/chroma_db'

print("🔧 Testing ChromaDB for Render...")

try:
    # Test basic import
    import chromadb
    print("✅ ChromaDB imported successfully")
    
    # Test client creation
    chroma_path = os.environ.get('CHROMA_DB_PATH', '/opt/render/project/src/chroma_db')
    print(f"   Using path: {chroma_path}")
    
    # Create directory
    os.makedirs(chroma_path, exist_ok=True)
    print(f"   Directory created: {chroma_path}")
    
    # Test persistent client
    client = chromadb.PersistentClient(path=chroma_path)
    print("✅ Persistent client created")
    
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
    
    print("\n🎉 ChromaDB test completed successfully!")
    
except ImportError as e:
    print(f"❌ ChromaDB import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ ChromaDB test failed: {e}")
    import traceback
    print(f"   Traceback: {traceback.format_exc()}")
    sys.exit(1)