#!/usr/bin/env python3
"""
Test script for Flask dependencies to ensure they work correctly
"""

def test_flask_dependencies():
    """Test if all Flask dependencies can be imported"""
    dependencies = [
        ("flask", "Flask"),
        ("flask_cors", "CORS"),
        ("werkzeug", "werkzeug"),
        ("click", "click"),
        ("itsdangerous", "itsdangerous"),
        ("jinja2", "Jinja2"),
        ("blinker", "blinker"),
        ("python-dotenv", "dotenv"),
        ("gunicorn", "gunicorn")
    ]
    
    print("🧪 Testing Flask Dependencies")
    print("=" * 40)
    
    passed = 0
    total = len(dependencies)
    
    for package_name, import_name in dependencies:
        try:
            if package_name == "flask":
                import flask
                print(f"✅ {package_name} imported successfully")
            elif package_name == "flask_cors":
                import flask_cors
                print(f"✅ {package_name} imported successfully")
            elif package_name == "werkzeug":
                import werkzeug
                print(f"✅ {package_name} imported successfully")
            elif package_name == "click":
                import click
                print(f"✅ {package_name} imported successfully")
            elif package_name == "itsdangerous":
                import itsdangerous
                print(f"✅ {package_name} imported successfully")
            elif package_name == "jinja2":
                import jinja2
                print(f"✅ {package_name} imported successfully")
            elif package_name == "blinker":
                import blinker
                print(f"✅ {package_name} imported successfully")
            elif package_name == "python-dotenv":
                import dotenv
                print(f"✅ {package_name} imported successfully")
            elif package_name == "gunicorn":
                import gunicorn
                print(f"✅ {package_name} imported successfully")
            
            passed += 1
            
        except ImportError as e:
            print(f"❌ {package_name} import failed: {e}")
        except Exception as e:
            print(f"❌ {package_name} unexpected error: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{total} dependencies imported successfully")
    
    if passed == total:
        print("🎉 All Flask dependencies work correctly!")
        return True
    else:
        print("💥 Some dependencies failed to import.")
        return False

def test_flask_app_creation():
    """Test if we can create a Flask app with all dependencies"""
    try:
        from flask import Flask
        from flask_cors import CORS
        
        app = Flask(__name__)
        CORS(app)
        
        print("✅ Flask app created successfully with CORS")
        return True
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Flask Dependency Test Suite")
    print("=" * 50)
    
    tests = [
        ("Dependencies Import", test_flask_dependencies),
        ("Flask App Creation", test_flask_app_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        print("-" * 30)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Flask dependencies are working correctly.")
        print("\n💡 Your Railway deployment should now work without missing module errors!")
        return True
    else:
        print("💥 Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
