#!/usr/bin/env python3
"""
Debug script to identify exactly what's failing in ChromaDB import
"""

import sys
import os

print("🔧 Debugging ChromaDB import...")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")

# Test each dependency individually
dependencies_to_test = [
    'numpy',
    'pydantic', 
    'typing_extensions',
    'bcrypt',
    'fastapi',
    'grpcio',
    'importlib_resources',
    'mmh3',
    'onnxruntime',
    'overrides',
    'pypika',
    'yaml',
    'requests',
    'tenacity',
    'tokenizers',
    'tqdm',
    'typer',
    'uvicorn',
    'psutil',
    'httpx',
    'jwt',
    'cffi'
]

print("\n🔍 Testing individual dependencies...")
failed_deps = []

for dep in dependencies_to_test:
    try:
        __import__(dep)
        print(f"✅ {dep}")
    except ImportError as e:
        print(f"❌ {dep}: {e}")
        failed_deps.append(dep)
    except Exception as e:
        print(f"⚠️ {dep}: {e}")

print(f"\n📊 Failed dependencies: {len(failed_deps)}")
if failed_deps:
    print(f"   {', '.join(failed_deps)}")

# Now test ChromaDB import step by step
print("\n🔍 Testing ChromaDB import step by step...")

try:
    print("   Step 1: Basic import...")
    import chromadb
    print("   ✅ chromadb imported")
    
    print("   Step 2: Check version...")
    print(f"   ✅ chromadb version: {chromadb.__version__}")
    
    print("   Step 3: Test client creation...")
    client = chromadb.Client()
    print("   ✅ Client created")
    
    print("   Step 4: Test persistent client...")
    persistent_client = chromadb.PersistentClient(path="./test_chroma")
    print("   ✅ Persistent client created")
    
    print("   Step 5: Test collection...")
    collection = persistent_client.get_or_create_collection("test")
    print("   ✅ Collection created")
    
    print("\n🎉 ChromaDB is working correctly!")
    
except ImportError as e:
    print(f"❌ ChromaDB import failed: {e}")
    print(f"   This suggests missing dependencies")
    
    # Check if it's a specific dependency issue
    if "grpcio" in str(e):
        print("   → Missing grpcio dependency")
    elif "onnxruntime" in str(e):
        print("   → Missing onnxruntime dependency")
    elif "bcrypt" in str(e):
        print("   → Missing bcrypt dependency")
    else:
        print(f"   → Unknown dependency issue: {e}")
        
except Exception as e:
    print(f"❌ ChromaDB functionality failed: {e}")
    import traceback
    print(f"   Traceback: {traceback.format_exc()}")

# Cleanup
try:
    import shutil
    shutil.rmtree("./test_chroma", ignore_errors=True)
except:
    pass
