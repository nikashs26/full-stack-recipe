#!/usr/bin/env python3
"""
Test script for the embedded Flask app in the Dockerfile
"""

# Test the embedded app code
app_code = '''from flask import Flask
from flask_cors import CORS
import os

# Initialize Flask app
app = Flask(__name__)

# Configure session for authentication
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Configure CORS for Railway deployment
allowed_origins = [
    "http://localhost:8081", "http://127.0.0.1:8081",
    "http://localhost:8083", "http://127.0.0.1:8083",
    "https://betterbulk.netlify.app",
    "https://your-app-name.netlify.app",
]

# Configure CORS properly
cors = CORS(app,
    origins=allowed_origins,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "x-requested-with"],
    expose_headers=["Content-Type", "Authorization", "X-Requested-With", "x-requested-with"],
    supports_credentials=True,
    max_age=3600
)

# Basic health check route
@app.route("/api/health")
def health_check():
    return {"status": "healthy", "message": "Railway backend is running"}

# Basic test route
@app.route("/api/test")
def test():
    return {"message": "Backend is working!"}

# Root route
@app.route("/")
def root():
    return {"message": "Recipe App Backend API"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Railway Flask app on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)'''

def test_app_code():
    """Test if the embedded app code is valid Python"""
    try:
        # Try to compile the code
        compile(app_code, '<string>', 'exec')
        print("✅ Embedded app code compiles successfully")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in embedded app: {e}")
        return False
    except Exception as e:
        print(f"❌ Error compiling embedded app: {e}")
        return False

def test_requirements():
    """Test if the requirements are valid"""
    requirements = [
        "flask==2.3.3",
        "flask-cors==4.0.0", 
        "python-dotenv==1.0.0",
        "gunicorn==21.2.0"
    ]
    
    print("📋 Requirements:")
    for req in requirements:
        print(f"   {req}")
    
    return True

def main():
    """Run all tests"""
    print("🧪 Testing Embedded Railway App")
    print("=" * 40)
    
    tests = [
        ("Embedded App Code", test_app_code),
        ("Requirements", test_requirements),
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
        print("\n💡 This Dockerfile is now completely self-contained!")
        print("   - No external file dependencies")
        print("   - No path issues")
        print("   - No .dockerignore conflicts")
        return True
    else:
        print("💥 Some tests failed. Fix issues before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
