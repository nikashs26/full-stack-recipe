#!/usr/bin/env python3
"""
Test script for the minimal Railway deployment app
Run this to verify everything works before deploying
"""

import os
import sys

def test_imports():
    """Test if all required packages can be imported"""
    try:
        import flask
        print("✅ Flask imported successfully")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        import flask_cors
        print("✅ Flask-CORS imported successfully")
    except ImportError as e:
        print(f"❌ Flask-CORS import failed: {e}")
        return False
    
    try:
        import dotenv
        print("✅ python-dotenv imported successfully")
    except ImportError as e:
        print(f"❌ python-dotenv import failed: {e}")
        return False
    
    try:
        import gunicorn
        print("✅ Gunicorn imported successfully")
    except ImportError as e:
        print(f"❌ Gunicorn import failed: {e}")
        return False
    
    return True

def test_app_creation():
    """Test if the minimal app can be created"""
    try:
        # Add backend to path
        sys.path.insert(0, 'backend')
        
        # Try to import the minimal app
        from app_super_minimal import app
        
        print("✅ Minimal app imported successfully")
        
        # Test if it's a Flask app
        if hasattr(app, 'route'):
            print("✅ App has route decorator")
        else:
            print("❌ App missing route decorator")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False

def test_requirements():
    """Test if requirements file exists and is readable"""
    req_file = "backend/requirements-minimal.txt"
    
    if not os.path.exists(req_file):
        print(f"❌ Requirements file not found: {req_file}")
        return False
    
    try:
        with open(req_file, 'r') as f:
            requirements = f.read()
            print(f"✅ Requirements file loaded ({len(requirements)} characters)")
            print("📋 Contents:")
            for line in requirements.strip().split('\n'):
                if line.strip() and not line.startswith('#'):
                    print(f"   {line.strip()}")
        return True
    except Exception as e:
        print(f"❌ Failed to read requirements: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Railway Deployment Setup")
    print("=" * 40)
    
    tests = [
        ("Package Imports", test_imports),
        ("App Creation", test_app_creation),
        ("Requirements File", test_requirements),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        print("-" * 20)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready to deploy to Railway.")
        return True
    else:
        print("💥 Some tests failed. Fix issues before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
