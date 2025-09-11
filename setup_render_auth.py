#!/usr/bin/env python3
"""
Setup script for Render authentication system
This script helps you test and configure the user authentication system on Render
"""

import requests
import json
import os
import sys
from datetime import datetime

def test_render_connection(base_url: str) -> bool:
    """Test connection to Render backend"""
    try:
        print(f"🔍 Testing connection to {base_url}...")
        response = requests.get(f"{base_url}/api/health", timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Connection successful: {data.get('message', 'OK')}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_auth_endpoints(base_url: str) -> bool:
    """Test authentication endpoints"""
    print("\n🔐 Testing authentication endpoints...")
    
    # Test registration
    test_email = f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"
    test_password = "TestPassword123!"
    test_name = "Test User"
    
    print(f"📝 Testing registration with email: {test_email}")
    
    try:
        # Register user
        register_data = {
            "email": test_email,
            "password": test_password,
            "full_name": test_name
        }
        
        response = requests.post(
            f"{base_url}/api/auth/register",
            json=register_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 201:
            print("✅ User registration successful")
            register_result = response.json()
            print(f"   User ID: {register_result.get('user_id', 'Unknown')}")
            
            # Test login
            print("🔑 Testing login...")
            login_data = {
                "email": test_email,
                "password": test_password
            }
            
            login_response = requests.post(
                f"{base_url}/api/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if login_response.status_code == 200:
                print("✅ User login successful")
                login_result = login_response.json()
                token = login_result.get('token')
                if token:
                    print(f"   Token received: {token[:20]}...")
                    
                    # Test protected endpoint
                    print("🛡️  Testing protected endpoint...")
                    headers = {"Authorization": f"Bearer {token}"}
                    me_response = requests.get(
                        f"{base_url}/api/auth/me",
                        headers=headers,
                        timeout=10
                    )
                    
                    if me_response.status_code == 200:
                        print("✅ Protected endpoint access successful")
                        me_data = me_response.json()
                        print(f"   User info: {me_data.get('user', {}).get('email', 'Unknown')}")
                        return True
                    else:
                        print(f"❌ Protected endpoint failed: {me_response.status_code}")
                        print(f"   Response: {me_response.text}")
                else:
                    print("❌ No token received from login")
            else:
                print(f"❌ Login failed: {login_response.status_code}")
                print(f"   Response: {login_response.text}")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    return False

def test_admin_endpoints(base_url: str, admin_token: str) -> bool:
    """Test admin endpoints"""
    print("\n👑 Testing admin endpoints...")
    
    headers = {
        "X-Admin-Token": admin_token,
        "Content-Type": "application/json"
    }
    
    try:
        # Test stats endpoint
        print("📊 Testing admin stats...")
        response = requests.get(f"{base_url}/api/admin/stats", headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Admin stats endpoint working")
            stats = response.json()
            print(f"   Users: {stats.get('stats', {}).get('users', {}).get('total', 0)}")
            print(f"   Recipes: {stats.get('stats', {}).get('recipes', {}).get('total', 0)}")
            
            # Test users endpoint
            print("👥 Testing admin users list...")
            users_response = requests.get(f"{base_url}/api/admin/users", headers=headers, timeout=10)
            
            if users_response.status_code == 200:
                print("✅ Admin users endpoint working")
                users_data = users_response.json()
                user_count = len(users_data.get('users', []))
                print(f"   Found {user_count} users")
                return True
            else:
                print(f"❌ Admin users endpoint failed: {users_response.status_code}")
                print(f"   Response: {users_response.text}")
        else:
            print(f"❌ Admin stats endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Admin request failed: {e}")
    
    return False

def get_admin_token_instructions():
    """Print instructions for getting admin token"""
    print("\n🔑 Getting Admin Token")
    print("=" * 40)
    print("To get your admin token:")
    print("1. Go to your Render dashboard")
    print("2. Select your 'dietary-delight-backend' service")
    print("3. Go to the 'Environment' tab")
    print("4. Find the 'ADMIN_SEED_TOKEN' variable")
    print("5. Copy the value")
    print("\nThen set it as an environment variable:")
    print("   export ADMIN_TOKEN='your-admin-token-here'")
    print("\nOr run this script with:")
    print("   ADMIN_TOKEN='your-token' python setup_render_auth.py")

def main():
    """Main setup function"""
    print("🚀 Render Authentication Setup")
    print("=" * 40)
    
    # Configuration
    base_url = os.getenv('RENDER_URL', 'https://dietary-delight.onrender.com')
    admin_token = os.getenv('ADMIN_TOKEN')
    
    print(f"🌐 Render URL: {base_url}")
    print(f"🔑 Admin Token: {'✅ Set' if admin_token else '❌ Not set'}")
    
    # Test connection
    if not test_render_connection(base_url):
        print("\n❌ Cannot connect to Render backend. Please check:")
        print("   - Your Render service is deployed and running")
        print("   - The URL is correct")
        print("   - Your service is not sleeping (free tier limitation)")
        sys.exit(1)
    
    # Test auth endpoints
    if not test_auth_endpoints(base_url):
        print("\n❌ Authentication system not working properly")
        print("   Please check your Render deployment logs")
        sys.exit(1)
    
    print("\n✅ Authentication system is working!")
    
    # Test admin endpoints if token is available
    if admin_token:
        if test_admin_endpoints(base_url, admin_token):
            print("\n✅ Admin system is working!")
            print("\n🎉 Setup complete! You can now use the admin interface:")
            print("   python admin_interface.py stats")
            print("   python admin_interface.py users")
        else:
            print("\n❌ Admin system not working. Please check your admin token")
    else:
        get_admin_token_instructions()
    
    print(f"\n📝 Test user created: test-{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com")
    print("   You can view this user in your admin interface once you have the admin token")

if __name__ == "__main__":
    main()
