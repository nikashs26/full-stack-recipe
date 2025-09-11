#!/usr/bin/env python3
"""
Test script to verify the fallback authentication system works
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_fallback_user_service():
    """Test the fallback user service directly"""
    print("🔍 Testing Fallback User Service")
    print("=" * 40)
    
    try:
        from backend.services.fallback_user_service import FallbackUserService
        
        # Create service instance
        user_service = FallbackUserService()
        print("✅ Fallback user service created")
        
        # Test registration
        print("\n📝 Testing user registration...")
        result = user_service.register_user(
            email="test@example.com",
            password="TestPassword123!",
            full_name="Test User"
        )
        
        if result["success"]:
            print("✅ User registration successful")
            print(f"   User ID: {result['user_id']}")
            print(f"   Email: {result['email']}")
            
            # Test login
            print("\n🔑 Testing user login...")
            login_result = user_service.authenticate_user(
                email="test@example.com",
                password="TestPassword123!"
            )
            
            if login_result["success"]:
                print("✅ User login successful")
                print(f"   Token: {login_result['token'][:20]}...")
            else:
                print(f"❌ Login failed: {login_result['error']}")
            
            # Test admin functions
            print("\n👑 Testing admin functions...")
            all_users = user_service.get_all_users()
            print(f"   Total users: {all_users['total_count']}")
            
            return True
        else:
            print(f"❌ Registration failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing fallback service: {e}")
        return False

def test_user_service_with_fallback():
    """Test the main UserService with fallback"""
    print("\n🔍 Testing Main UserService with Fallback")
    print("=" * 40)
    
    try:
        # Mock ChromaDB not available
        import backend.services.user_service as user_service_module
        original_chromadb_available = user_service_module.CHROMADB_AVAILABLE
        user_service_module.CHROMADB_AVAILABLE = False
        
        from backend.services.user_service import UserService
        
        # Create service instance
        user_service = UserService()
        print("✅ UserService created with fallback")
        
        # Test registration
        print("\n📝 Testing user registration...")
        result = user_service.register_user(
            email="test2@example.com",
            password="TestPassword123!",
            full_name="Test User 2"
        )
        
        if result["success"]:
            print("✅ User registration successful")
            print(f"   User ID: {result['user_id']}")
            
            # Test login
            print("\n🔑 Testing user login...")
            login_result = user_service.authenticate_user(
                email="test2@example.com",
                password="TestPassword123!"
            )
            
            if login_result["success"]:
                print("✅ User login successful")
                return True
            else:
                print(f"❌ Login failed: {login_result['error']}")
                return False
        else:
            print(f"❌ Registration failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing main service: {e}")
        return False
    finally:
        # Restore original state
        user_service_module.CHROMADB_AVAILABLE = original_chromadb_available

def main():
    """Main test function"""
    print("🚀 Testing Fallback Authentication System")
    print("=" * 50)
    
    # Test fallback service directly
    fallback_success = test_fallback_user_service()
    
    # Test main service with fallback
    main_success = test_user_service_with_fallback()
    
    print("\n📊 Test Results")
    print("=" * 20)
    print(f"Fallback Service: {'✅ PASS' if fallback_success else '❌ FAIL'}")
    print(f"Main Service: {'✅ PASS' if main_success else '❌ FAIL'}")
    
    if fallback_success and main_success:
        print("\n🎉 All tests passed! The fallback system should work on Render.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
