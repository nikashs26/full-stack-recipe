#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from services.user_service import UserService

# Load environment variables
load_dotenv()

print("Environment variables loaded:")
print(f"JWT_SECRET_KEY: {os.getenv('JWT_SECRET_KEY', 'NOT_SET')[:20]}...")

# Create UserService instance
print("\nCreating UserService instance...")
user_service = UserService()

# Test JWT secret access
print(f"UserService JWT secret: {user_service._get_jwt_secret()[:20]}...")

# Test token generation
print("\nTesting token generation...")
test_token = user_service.generate_jwt_token("test_user", "test@example.com")
print(f"Generated token: {test_token[:50]}...")

# Test token decoding
print("\nTesting token decoding...")
try:
    payload = user_service.decode_jwt_token(test_token)
    if payload:
        print("✅ Token decoded successfully!")
        print(f"Payload: {payload}")
    else:
        print("❌ Token decode failed")
except Exception as e:
    print(f"❌ Error: {e}")
