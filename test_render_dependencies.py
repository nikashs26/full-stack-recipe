#!/usr/bin/env python3
"""
Test script to verify all dependencies work on Render
"""

import sys
import os

print("🔧 Testing Render Dependencies...")
print(f"Python version: {sys.version}")

# Test core dependencies
dependencies = [
    'numpy',
    'pydantic', 
    'typing_extensions',
    'bcrypt',
    'fastapi',
    'grpcio',
    'importlib_resources',
    'kubernetes',
    'mmh3',
    'onnxruntime',
    'opentelemetry_api',
    'opentelemetry_exporter_otlp_proto_grpc',
    'opentelemetry_instrumentation_fastapi',
    'opentelemetry_sdk',
    'overrides',
    'posthog',
    'pulsar_client',
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
    'cffi',
    'flask_mail',
    'itsdangerous',
    'werkzeug'
]

failed_imports = []

for dep in dependencies:
    try:
        __import__(dep)
        print(f"✅ {dep}")
    except ImportError as e:
        print(f"❌ {dep}: {e}")
        failed_imports.append(dep)

# Test ChromaDB specifically
print("\n🔧 Testing ChromaDB...")
try:
    import chromadb
    print(f"✅ chromadb {chromadb.__version__}")
    
    # Test basic functionality
    client = chromadb.Client()
    print("✅ ChromaDB client created")
    
    collection = client.get_or_create_collection("test")
    print("✅ Collection created")
    
    collection.add(
        ids=["test1"],
        documents=["test document"],
        metadatas=[{"test": True}]
    )
    print("✅ Document added")
    
    results = collection.query(query_texts=["test"], n_results=1)
    print("✅ Query executed")
    
except ImportError as e:
    print(f"❌ chromadb: {e}")
    failed_imports.append('chromadb')
except Exception as e:
    print(f"❌ chromadb functionality: {e}")

# Test user service
print("\n🔧 Testing UserService...")
try:
    from backend.services.user_service import UserService
    user_service = UserService()
    
    if user_service.client is not None:
        print("✅ UserService ChromaDB client initialized")
    else:
        print("⚠️ UserService using fallback (ChromaDB not available)")
        
except Exception as e:
    print(f"❌ UserService: {e}")

# Summary
print(f"\n📊 Summary:")
print(f"   Total dependencies tested: {len(dependencies) + 1}")
print(f"   Failed imports: {len(failed_imports)}")

if failed_imports:
    print(f"   Failed: {', '.join(failed_imports)}")
    sys.exit(1)
else:
    print("🎉 All dependencies working correctly!")
