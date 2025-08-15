#!/usr/bin/env python3
"""
Debug script to test authentication and token refresh
"""

import requests
import json
import jwt
import os
from dotenv import load_dotenv

# Test configuration
BASE_URL = "http://localhost:5003"
TEST_EMAIL = "test2@example.com"
TEST_PASSWORD = "TestPass123"

def debug_token(token):
    """Debug JWT token"""
    print(f"\n🔍 Debugging JWT token: {token[:50]}...")
    
    try:
        # Load JWT secret
        load_dotenv()
        jwt_secret = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')
        print(f"   JWT Secret: {jwt_secret[:20]}...")
        
        # Decode without expiration verification
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'], options={'verify_exp': False})
        print(f"   ✅ Token decoded (no exp check): {payload}")
        
        # Check if token is expired
        if 'exp' in payload:
            import time
            current_time = int(time.time())
            exp_time = payload['exp']
            is_expired = current_time > exp_time
            print(f"   ⏰ Token expiration: {exp_time} (current: {current_time}, expired: {is_expired})")
        
        return payload
        
    except Exception as e:
        print(f"   ❌ Token decode failed: {e}")
        return None

def test_cors_preflight():
    """Test CORS preflight request"""
    print("🔍 Testing CORS preflight request...")
    
    try:
        response = requests.options(
            f"{BASE_URL}/api/auth/refresh",
            headers={
                'Origin': 'http://localhost:8081',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
        )
        print(f"✅ CORS preflight response: {response.status_code}")
        print(f"   CORS headers: {dict(response.headers)}")
        return True
    except Exception as e:
        print(f"❌ CORS preflight failed: {e}")
        return False

def test_auth_endpoints():
    """Test basic auth endpoints"""
    print("\n🔍 Testing auth endpoints...")
    
    # Test registration
    try:
        reg_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Test User"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=reg_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print("✅ Registration successful")
            user_data = response.json()
            print(f"   User ID: {user_data.get('user_id')}")
        elif response.status_code == 400 and "already registered" in response.text:
            print("ℹ️  User already registered")
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
    
    # Test login
    try:
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print("✅ Login successful")
            login_result = response.json()
            token = login_result.get('token')
            print(f"   Token: {token[:20] if token else 'None'}...")
            
            # Debug the token
            if token:
                debug_token(token)
                # Test token refresh
                test_token_refresh(token)
                test_protected_endpoint(token)
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Login test failed: {e}")

def test_token_refresh(token):
    """Test token refresh endpoint"""
    print("\n🔍 Testing token refresh...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/refresh",
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code == 200:
            print("✅ Token refresh successful")
            refresh_data = response.json()
            new_token = refresh_data.get('token')
            print(f"   New token: {new_token[:20] if new_token else 'None'}...")
        else:
            print(f"❌ Token refresh failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Token refresh test failed: {e}")

def test_protected_endpoint(token):
    """Test a protected endpoint"""
    print("\n🔍 Testing protected endpoint...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/auth/check-auth",
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code == 200:
            print("✅ Protected endpoint access successful")
            auth_data = response.json()
            print(f"   Auth data: {auth_data}")
        else:
            print(f"❌ Protected endpoint access failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Protected endpoint test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting auth debug tests...")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Test email: {TEST_EMAIL}")
    
    # Test CORS
    test_cors_preflight()
    
    # Test auth flow
    test_auth_endpoints()
    
    print("\n✅ Debug tests completed!")
