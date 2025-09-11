#!/usr/bin/env python3
"""
Test script to verify ChromaDB import and basic functionality
"""

import sys
import os

print("Python version:", sys.version)
print("Python path:", sys.path)

# Test basic imports
try:
    import numpy as np
    print("✅ numpy imported successfully")
    print(f"   numpy version: {np.__version__}")
except ImportError as e:
    print(f"❌ numpy import failed: {e}")

try:
    import sqlalchemy
    print("✅ sqlalchemy imported successfully")
    print(f"   sqlalchemy version: {sqlalchemy.__version__}")
except ImportError as e:
    print(f"❌ sqlalchemy import failed: {e}")

try:
    import pydantic
    print("✅ pydantic imported successfully")
    print(f"   pydantic version: {pydantic.__version__}")
except ImportError as e:
    print(f"❌ pydantic import failed: {e}")

try:
    import chromadb
    print("✅ chromadb imported successfully")
    print(f"   chromadb version: {chromadb.__version__}")
except ImportError as e:
    print(f"❌ chromadb import failed: {e}")
    sys.exit(1)

# Test ChromaDB client creation
try:
    print("\nTesting ChromaDB client creation...")
    
    # Test in-memory client
    client = chromadb.Client()
    print("✅ In-memory ChromaDB client created successfully")
    
    # Test persistent client
    test_path = "./test_chroma_db"
    os.makedirs(test_path, exist_ok=True)
    
    persistent_client = chromadb.PersistentClient(path=test_path)
    print("✅ Persistent ChromaDB client created successfully")
    
    # Test collection creation
    collection = persistent_client.get_or_create_collection("test_collection")
    print("✅ Collection created successfully")
    
    # Test adding a document
    collection.add(
        ids=["test1"],
        documents=["This is a test document"],
        metadatas=[{"source": "test"}]
    )
    print("✅ Document added successfully")
    
    # Test querying
    results = collection.query(query_texts=["test document"], n_results=1)
    print("✅ Query executed successfully")
    print(f"   Query results: {results}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_path, ignore_errors=True)
    print("✅ Cleanup completed")
    
except Exception as e:
    print(f"❌ ChromaDB functionality test failed: {e}")
    import traceback
    print(f"   Full traceback: {traceback.format_exc()}")
    sys.exit(1)

print("\n🎉 All ChromaDB tests passed!")
