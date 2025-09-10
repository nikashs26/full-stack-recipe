import os
from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional

# Try to import jwt, fallback if not available
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("Warning: JWT not available, authentication will be disabled")

# This should match your Supabase JWT secret
SUPABASE_JWT_SECRET = os.environ.get('SUPABASE_JWT_SECRET', 'your-supabase-jwt-secret')

def require_auth(f):
    """
    Decorator that requires authentication for a route.
    Expects a Bearer token in the Authorization header.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'No authorization header provided'}), 401
        
        try:
            # Extract token from "Bearer <token>"
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
            
            # For now, we'll do a simple validation
            # In a production app, you'd verify the JWT signature with Supabase
            if not token or token == 'null' or token == 'undefined':
                return jsonify({'error': 'Invalid token'}), 401
                
            # Store token in request context for use in the route
            request.auth_token = token
            
        except (IndexError, AttributeError):
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_user_id_from_request() -> Optional[str]:
    """
    Extract user ID from the request.
    This is a simplified version - in production you'd decode the JWT.
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return None
    
    try:
        token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
        
        # For now, return a placeholder user ID
        # In production, you'd decode the JWT and extract the user ID
        if token and token != 'null' and token != 'undefined':
            return "user_placeholder_id"  # This should be extracted from the JWT
        
    except (IndexError, AttributeError):
        pass
    
    return None

def decode_jwt_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token.
    This is a placeholder implementation.
    """
    try:
        # In production, you'd use the actual Supabase JWT secret
        # and properly verify the token
        # For now, we'll just return a mock payload
        return {
            'sub': 'user_placeholder_id',
            'email': 'user@example.com'
        }
    except Exception as e:
        print(f"Error decoding JWT: {e}")
        return None 