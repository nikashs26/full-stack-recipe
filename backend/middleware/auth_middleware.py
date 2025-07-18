from functools import wraps
from flask import request, jsonify, g
from services.user_service import UserService
from typing import Optional, Dict, Any


class AuthMiddleware:
    """
    Authentication middleware for protecting routes
    Uses JWT tokens and ChromaDB user service
    """
    
    def __init__(self):
        self.user_service = UserService()
    
    def require_auth(self, f):
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
                if not auth_header.startswith('Bearer '):
                    return jsonify({'error': 'Invalid authorization header format'}), 401
                
                token = auth_header.split(' ')[1]
                
                if not token or token in ['null', 'undefined']:
                    return jsonify({'error': 'Invalid token'}), 401
                
                # Decode and verify JWT token
                payload = self.user_service.decode_jwt_token(token)
                if not payload:
                    return jsonify({'error': 'Invalid or expired token'}), 401
                
                # Get user from database
                user = self.user_service.get_user_by_id(payload['user_id'])
                if not user:
                    return jsonify({'error': 'User not found'}), 401
                
                # Check if user is verified
                if not user.get('is_verified', False):
                    return jsonify({'error': 'Email not verified'}), 401
                
                # Store user info in Flask's g object for use in the route
                g.current_user = user
                g.user_id = user['user_id']
                g.user_email = user['email']
                
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