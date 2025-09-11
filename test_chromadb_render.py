#!/usr/bin/env python3
"""
Test script to verify ChromaDB is working properly on Render
"""

import os
import sys

# Set up environment for Render
os.environ['RENDER_ENVIRONMENT'] = 'true'
os.environ['CHROMA_DB_PATH'] = '/opt/render/project/src/chroma_db'

print("🔧 Testing ChromaDB on Render...")
print(f"   RENDER_ENVIRONMENT: {os.environ.get('RENDER_ENVIRONMENT')}")
print(f"   CHROMA_DB_PATH: {os.environ.get('CHROMA_DB_PATH')}")

# Test ChromaDB import
try:
    import chromadb
    print("✅ ChromaDB imported successfully")
except ImportError as e:
    print(f"❌ ChromaDB import failed: {e}")
    sys.exit(1)

# Test ChromaDB client creation
try:
    chroma_path = os.environ.get('CHROMA_DB_PATH', '/opt/render/project/src/chroma_db')
    print(f"   Using path: {chroma_path}")
    
    # Create directory if it doesn't exist
    os.makedirs(chroma_path, exist_ok=True)
    print(f"   Directory created/verified: {chroma_path}")
    
    # Test persistent client
    client = chromadb.PersistentClient(path=chroma_path)
    print("✅ ChromaDB persistent client created successfully")
    
    # Test collection creation
    collection = client.get_or_create_collection("test_collection")
    print("✅ Collection created successfully")
    
    # Test adding a document
    collection.add(
        ids=["test1"],
        documents=["This is a test document"],
        metadatas=[{"source": "test", "type": "test"}]
    )
    print("✅ Document added successfully")
    
    # Test querying
    results = collection.query(query_texts=["test document"], n_results=1)
    print("✅ Query executed successfully")
    print(f"   Query results: {len(results['documents'])} documents found")
    
    # Test user service
    print("\n🔧 Testing UserService...")
    from backend.services.user_service import UserService
    user_service = UserService()
    
    if user_service.client is not None:
        print("✅ UserService ChromaDB client initialized successfully")
    else:
        print("❌ UserService ChromaDB client is None - falling back to in-memory storage")
    
    print("\n🎉 ChromaDB test completed successfully!")
    
except Exception as e:
    print(f"❌ ChromaDB test failed: {e}")
    import traceback
    print(f"   Full traceback: {traceback.format_exc()}")
    sys.exit(1)