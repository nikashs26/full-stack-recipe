#!/usr/bin/env python3

import jwt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get JWT secret
jwt_secret = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')
print(f"JWT Secret: {jwt_secret[:20]}...")

# Test token from the registration
test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl9mOWRmZjFkMy1lODQ5LTRhMGUtYWZlNi1hOTQzOTcwMDU2NzkiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjE3NTU4NDE3NTEsImlhdCI6MTc1NTIzNjk1MX0.ClnxREKZZfwTe-ViPi_4AmMiumyqC96W-2JO2NGy074"

print(f"\nTest Token: {test_token[:50]}...")

try:
    # Decode the token
    print("\nAttempting to decode token...")
    payload = jwt.decode(test_token, jwt_secret, algorithms=['HS256'])
    print(f"✅ Token decoded successfully!")
    print(f"Payload: {payload}")
    
    # Check expiration
    import datetime
    exp_time = datetime.datetime.fromtimestamp(payload['exp'])
    iat_time = datetime.datetime.fromtimestamp(payload['iat'])
    current_time = datetime.datetime.now()
    
    print(f"\nToken expires at: {exp_time}")
    print(f"Token issued at: {iat_time}")
    print(f"Current time: {current_time}")
    
    if current_time < exp_time:
        print("✅ Token is not expired")
    else:
        print("❌ Token is expired")
        
except jwt.ExpiredSignatureError as e:
    print(f"❌ Token expired: {e}")
except jwt.InvalidTokenError as e:
    print(f"❌ Invalid token: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
