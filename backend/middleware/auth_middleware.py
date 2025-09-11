from functools import wraps
from flask import request, jsonify, g
from services.user_database_service import UserDatabaseService
from typing import Optional, Dict, Any


class AuthMiddleware:
    """
    Authentication middleware for protecting routes
    Uses JWT tokens and ChromaDB user database service
    """
    
    def __init__(self):
        self.user_db = UserDatabaseService()
    
    def require_auth(self, f):
        """
        Decorator that requires authentication for a route.
        Expects a Bearer token in the Authorization header.
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Allow OPTIONS requests to pass through for CORS preflight
            if request.method == 'OPTIONS':
                return f(*args, **kwargs)
            
            # Debug logging
            print(f"🔍 Auth middleware - Request headers: {dict(request.headers)}")
            print(f"🔍 Auth middleware - Authorization header: {request.headers.get('Authorization')}")
            
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                print("❌ Auth middleware - No authorization header provided")
                return jsonify({'error': 'No authorization header provided'}), 401
            
            try:
                # Extract token from "Bearer <token>"
                if not auth_header.startswith('Bearer '):
                    print("❌ Auth middleware - Invalid authorization header format")
                    return jsonify({'error': 'Invalid authorization header format'}), 401
                
                token = auth_header.split(' ')[1]
                print(f"🔍 Auth middleware - Extracted token: {token[:20]}...")
                
                if not token or token in ['null', 'undefined']:
                    print("❌ Auth middleware - Token is null, undefined, or empty")
                    return jsonify({'error': 'Invalid token'}), 401
                
                # Verify token and get user info
                print("🔍 Auth middleware - Attempting to verify token...")
                user_info = self.user_db.verify_token(token)
                if not user_info:
                    print("❌ Auth middleware - Token verification failed or token expired")
                    return jsonify({'error': 'Invalid or expired token'}), 401
                
                # Store user info in Flask's g object for use in the route
                g.current_user = user_info
                g.user_id = user_info['user_id']
                g.user_email = user_info['email']
                
            except Exception as e:
                return jsonify({'error': 'Authentication failed'}), 401
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get the current authenticated user from Flask's g object"""
        return getattr(g, 'current_user', None)
    
    def get_current_user_id(self) -> Optional[str]:
        """Get the current authenticated user's ID from Flask's g object"""
        return getattr(g, 'user_id', None)
    
    def get_current_user_email(self) -> Optional[str]:
        """Get the current authenticated user's email from Flask's g object"""
        return getattr(g, 'user_email', None)


# Create global instance
auth_middleware = AuthMiddleware()

# Export functions for backward compatibility
require_auth = auth_middleware.require_auth
get_current_user = auth_middleware.get_current_user
get_current_user_id = auth_middleware.get_current_user_id
get_current_user_email = auth_middleware.get_current_user_email 