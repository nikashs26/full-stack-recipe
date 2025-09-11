#!/usr/bin/env python3
"""
Test script for the authentication system
Tests user registration, login, and admin functionality
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:5003"
# BASE_URL = "https://dietary-delight.onrender.com"  # Uncomment to test production

def test_auth_system():
    print("🧪 Testing Authentication System")
    print("=" * 50)
    
    # Test data
    test_user = {
        "username": f"testuser_{int(time.time())}",
        "email": f"test_{int(time.time())}@example.com",
        "password": "TestPassword123"
    }
    
    print(f"📝 Test User: {test_user['username']}")
    print(f"📧 Email: {test_user['email']}")
    print()
    
    # Test 1: User Registration
    print("1️⃣ Testing User Registration...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=test_user)
        data = response.json()
        
        if response.status_code == 201 and data.get('success'):
            print("✅ Registration successful!")
            print(f"   User ID: {data.get('user_id')}")
        else:
            print(f"❌ Registration failed: {data.get('error', 'Unknown error')}")
            return
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return
    
    print()
    
    # Test 2: User Login
    print("2️⃣ Testing User Login...")
    try:
        login_data = {
            "username_or_email": test_user['username'],
            "password": test_user['password']
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            print("✅ Login successful!")
            token = data.get('token')
            user_info = data.get('user')
            print(f"   Token: {token[:20]}...")
            print(f"   User: {user_info.get('username')} ({user_info.get('email')})")
        else:
            print(f"❌ Login failed: {data.get('error', 'Unknown error')}")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    print()
    
    # Test 3: Check Authentication
    print("3️⃣ Testing Authentication Check...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/check-auth", headers=headers)
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            print("✅ Authentication check successful!")
            print(f"   Authenticated: {data.get('authenticated')}")
            print(f"   User ID: {data.get('user_id')}")
        else:
            print(f"❌ Authentication check failed: {data.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Authentication check error: {e}")
    
    print()
    
    # Test 4: Get All Users (Admin)
    print("4️⃣ Testing Admin User List...")
    try:
        response = requests.get(f"{BASE_URL}/api/auth/admin/users")
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            print("✅ Admin user list successful!")
            users = data.get('users', [])
            total_users = data.get('total_users', 0)
            print(f"   Total users: {total_users}")
            print(f"   Users returned: {len(users)}")
            
            # Show first few users
            for i, user in enumerate(users[:3]):
                print(f"   User {i+1}: {user.get('username')} ({user.get('email')})")
        else:
            print(f"❌ Admin user list failed: {data.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Admin user list error: {e}")
    
    print()
    
    # Test 5: Logout
    print("5️⃣ Testing User Logout...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/api/auth/logout", headers=headers)
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            print("✅ Logout successful!")
        else:
            print(f"❌ Logout failed: {data.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Logout error: {e}")
    
    print()
    print("🎉 Authentication system test completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_auth_system()
