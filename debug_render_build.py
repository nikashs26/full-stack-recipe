#!/usr/bin/env python3
"""
Debug script to test what happens during Render build process
"""

import sys
import os

print("🔧 Debugging Render build process...")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Test each step of the build process
print("\n1. Testing basic imports...")

# Test numpy first (ChromaDB dependency)
try:
    import numpy
    print(f"✅ numpy {numpy.__version__}")
except ImportError as e:
    print(f"❌ numpy: {e}")
    sys.exit(1)

# Test pydantic
try:
    import pydantic
    print(f"✅ pydantic {pydantic.__version__}")
except ImportError as e:
    print(f"❌ pydantic: {e}")
    sys.exit(1)

# Test other critical dependencies
critical_deps = [
    'typing_extensions',
    'bcrypt', 
    'fastapi',
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
    'httpx'
]

print("\n2. Testing critical dependencies...")
failed_deps = []

for dep in critical_deps:
    try:
        module = __import__(dep)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {dep} {version}")
    except ImportError as e:
        print(f"❌ {dep}: {e}")
        failed_deps.append(dep)

print(f"\n3. Failed dependencies: {len(failed_deps)}")
if failed_deps:
    print(f"   {', '.join(failed_deps)}")

# Test ChromaDB import
print("\n4. Testing ChromaDB import...")
try:
    import chromadb
    print(f"✅ chromadb {chromadb.__version__}")
    
    # Test Settings import
    from chromadb.config import Settings
    print("✅ Settings imported")
    
    # Test basic functionality
    client = chromadb.Client()
    print("✅ Basic client created")
    
except ImportError as e:
    print(f"❌ ChromaDB import failed: {e}")
    print("\n🔍 Analyzing ChromaDB import failure...")
    
    # Check if it's a specific missing dependency
    if "grpcio" in str(e):
        print("   → Missing grpcio")
    elif "onnxruntime" in str(e):
        print("   → Missing onnxruntime")
    elif "bcrypt" in str(e):
        print("   → Missing bcrypt")
    else:
        print(f"   → Unknown error: {e}")
    
    sys.exit(1)
except Exception as e:
    print(f"❌ ChromaDB functionality failed: {e}")
    import traceback
    print(f"   Traceback: {traceback.format_exc()}")
    sys.exit(1)

print("\n🎉 All tests passed! ChromaDB should work on Render.")
