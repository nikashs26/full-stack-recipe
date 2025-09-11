#!/usr/bin/env python3
"""
Test script to verify Render deployment configuration
This tests the path configuration without requiring ChromaDB to work locally
"""

import os
import sys

print("🔧 Testing Render deployment configuration...")

# Test 1: Environment variables
print("\n1. Environment Variables:")
print(f"   RENDER_ENVIRONMENT: {os.environ.get('RENDER_ENVIRONMENT', 'Not set')}")
print(f"   CHROMA_DB_PATH: {os.environ.get('CHROMA_DB_PATH', 'Not set')}")

# Test 2: Path logic
print("\n2. Path Logic Test:")
chroma_path = os.environ.get('CHROMA_DB_PATH', './chroma_db')

if os.environ.get('RAILWAY_ENVIRONMENT'):
    chroma_path = os.environ.get('CHROMA_DB_PATH', '/app/data/chroma_db')
    print(f"   Railway environment detected: {chroma_path}")
elif os.environ.get('RENDER_ENVIRONMENT'):
    chroma_path = os.environ.get('CHROMA_DB_PATH', '/opt/render/project/src/chroma_db')
    print(f"   Render environment detected: {chroma_path}")
else:
    print(f"   Local environment: {chroma_path}")

# Test 3: Directory creation
print("\n3. Directory Creation Test:")
try:
    os.makedirs(chroma_path, exist_ok=True)
    print(f"   ✅ Directory created/verified: {chroma_path}")
    print(f"   ✅ Directory exists: {os.path.exists(chroma_path)}")
    print(f"   ✅ Directory is writable: {os.access(chroma_path, os.W_OK)}")
except Exception as e:
    print(f"   ❌ Directory creation failed: {e}")

# Test 4: Service initialization logic
print("\n4. Service Initialization Logic:")
print("   Testing UserService path logic...")

# Simulate the UserService path logic
def test_user_service_path():
    chroma_path = os.environ.get('CHROMA_DB_PATH', './chroma_db')
    
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        chroma_path = os.environ.get('CHROMA_DB_PATH', '/app/data/chroma_db')
    elif os.environ.get('RENDER_ENVIRONMENT'):
        chroma_path = os.environ.get('CHROMA_DB_PATH', '/opt/render/project/src/chroma_db')
    
    return chroma_path

user_service_path = test_user_service_path()
print(f"   UserService would use path: {user_service_path}")

# Test 5: Check if paths match
print("\n5. Path Consistency Check:")
expected_render_path = '/opt/render/project/src/chroma_db'
if user_service_path == expected_render_path:
    print(f"   ✅ UserService path matches expected Render path: {expected_render_path}")
else:
    print(f"   ❌ UserService path mismatch!")
    print(f"      Expected: {expected_render_path}")
    print(f"      Actual: {user_service_path}")

print("\n🎉 Configuration test completed!")
print("\nNext steps:")
print("1. Deploy to Render with these configuration changes")
print("2. Check Render logs for ChromaDB initialization")
print("3. Verify that user sessions persist after refresh")
