#!/usr/bin/env python3
"""
Debug script to examine JWT tokens and test refresh logic
"""

import jwt
import os
from dotenv import load_dotenv

def debug_jwt_token():
    """Debug JWT token handling"""
    load_dotenv()
    
    # Get the JWT secret
    jwt_secret = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')
    print(f"🔑 JWT Secret: {jwt_secret[:20]}...")
    
    # Test token from the debug output
    test_token = "eyJhbGciOiJIUzI1NiIs..."  # This is just a placeholder
    
    print("\n🔍 Testing JWT decode with verify_exp=False...")
    
    try:
        # Try to decode without expiration verification
        payload = jwt.decode(
            test_token, 
            jwt_secret, 
            algorithms=['HS256'], 
            options={'verify_exp': False}
        )
        print(f"✅ Token decoded successfully: {payload}")
    except Exception as e:
        print(f"❌ Token decode failed: {e}")
    
    print("\n🔍 Testing JWT decode with verify_exp=True...")
    
    try:
        # Try to decode with expiration verification
        payload = jwt.decode(
            test_token, 
            jwt_secret, 
            algorithms=['HS256']
        )
        print(f"✅ Token decoded successfully: {payload}")
    except Exception as e:
        print(f"❌ Token decode failed: {e}")

if __name__ == "__main__":
    print("🔍 Debugging JWT token handling...")
    debug_jwt_token()
