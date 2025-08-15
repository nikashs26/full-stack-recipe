from flask import Blueprint, request, jsonify, current_app
from services.user_service import UserService
from services.email_service import EmailService
from middleware.auth_middleware import require_auth, get_current_user_id
import re
from typing import Dict, Any
import os
from datetime import datetime
import json

auth_bp = Blueprint('auth', __name__)
user_service = UserService()

# Get the email service from the current app context
def get_email_service():
    """Get the email service from the current app context"""
    if hasattr(current_app, 'extensions') and 'mail' in current_app.extensions:
        # Create email service with the current app
        email_service = EmailService()
        email_service.init_app(current_app)
        return email_service
    else:
        # Fallback to uninitialized service (development mode)
        return EmailService()


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> Dict[str, Any]:
    """Validate password strength"""
    if len(password) < 8:
        return {"valid": False, "error": "Password must be at least 8 characters long"}
    
    if not re.search(r'[A-Z]', password):
        return {"valid": False, "error": "Password must contain at least one uppercase letter"}
    
    if not re.search(r'[a-z]', password):
        return {"valid": False, "error": "Password must contain at least one lowercase letter"}
    
    if not re.search(r'\d', password):
        return {"valid": False, "error": "Password must contain at least one number"}
    
    return {"valid": True}


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        
        # Validation
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        if not password:
            return jsonify({"error": "Password is required"}), 400
        
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        
        password_validation = validate_password(password)
        if not password_validation["valid"]:
            return jsonify({"error": password_validation["error"]}), 400
        
        # Register user
        result = user_service.register_user(email, password, full_name)
        
        if not result["success"]:
            return jsonify({"error": result["error"]}), 400
        
        # Send verification email
        email_service = get_email_service() # Get the service here
        email_result = email_service.send_verification_email(
            email, 
            result["verification_token"], 
            full_name
        )
        
        response_data = {
            "success": True,
            "message": result["message"],
            "user_id": result["user_id"],
            "email": email
        }
        
        # In development mode, include verification URL
        if email_result.get("verification_url"):
            response_data["verification_url"] = email_result["verification_url"]
            response_data["dev_message"] = email_result.get("message", "")
        
        return jsonify(response_data), 201
        
    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user login"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        # Authenticate user
        result = user_service.authenticate_user(email, password)
        
        if not result["success"]:
            return jsonify({"error": result["error"]}), 401
        
        return jsonify({
            "success": True,
            "message": result["message"],
            "user": result["user"],
            "token": result["token"]
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify user's email using verification token"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        verification_token = data.get('token', '').strip()
        
        if not verification_token:
            return jsonify({"error": "Verification token is required"}), 400
        
        # Verify email
        result = user_service.verify_email(verification_token)
        
        if not result["success"]:
            return jsonify({"error": result["error"]}), 400
        
        # Send welcome email
        user = user_service.get_user_by_id(result["user_id"])
        if user:
            email_service = get_email_service() # Get the service here
            email_service.send_welcome_email(user["email"], user.get("full_name", ""))
        
        return jsonify({
            "success": True,
            "message": result["message"]
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Email verification failed: {str(e)}"}), 500


@auth_bp.route('/verify-email/<token>', methods=['GET'])
def verify_email_get(token):
    """Verify email via GET request (for email links)"""
    try:
        if not token:
            return jsonify({"error": "Verification token is required"}), 400
        
        # Verify email
        result = user_service.verify_email(token)
        
        if not result["success"]:
            return jsonify({"error": result["error"]}), 400
        
        # Send welcome email
        user = user_service.get_user_by_id(result["user_id"])
        if user:
            email_service = get_email_service() # Get the service here
            email_service.send_welcome_email(user["email"], user.get("full_name", ""))
        
        return jsonify({
            "success": True,
            "message": result["message"]
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Email verification failed: {str(e)}"}), 500


@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification email"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        
        # Resend verification email
        result = user_service.resend_verification_email(email)
        
        if not result["success"]:
            return jsonify({"error": result["error"]}), 400
        
        # Send new verification email
        user = user_service.get_user_by_email(email)
        if user:
            email_service = get_email_service() # Get the service here
            email_result = email_service.send_verification_email(
                email, 
                result["verification_token"], 
                user.get("full_name", "")
            )
            
            response_data = {
                "success": True,
                "message": result["message"]
            }
            
            # In development mode, include verification URL
            if email_result.get("verification_url"):
                response_data["verification_url"] = email_result["verification_url"]
                response_data["dev_message"] = email_result.get("message", "")
            
            return jsonify(response_data), 200
        
        return jsonify({"error": "User not found"}), 404
        
    except Exception as e:
        return jsonify({"error": f"Failed to resend verification email: {str(e)}"}), 500


@auth_bp.route('/dev-verify-user', methods=['POST'])
def dev_verify_user():
    """
    Development-only endpoint to manually verify a user by email
    This bypasses email verification for testing purposes
    """
    if os.getenv('FLASK_ENV') == 'production':
        return jsonify({"error": "This endpoint is only available in development"}), 403
    
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        # Use UserService to get and update user
        user = user_service.get_user_by_email(email)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get user from ChromaDB using UserService internal methods
        results = user_service.users_collection.get(
            where={"email": email},
            include=['documents', 'metadatas']
        )
        
        if not results['documents']:
            return jsonify({"error": "User not found in database"}), 404
        
        user_id = results['ids'][0]
        user_data = results['documents'][0]
        user_metadata = results['metadatas'][0]
        
        # Parse the user data JSON
        user_data_dict = json.loads(user_data)
        
        # Update user to verified
        user_data_dict['is_verified'] = True
        user_data_dict['updated_at'] = datetime.utcnow().isoformat()
        user_metadata['is_verified'] = True
        
        # Update user in ChromaDB
        user_service.users_collection.upsert(
            documents=[json.dumps(user_data_dict)],
            metadatas=[user_metadata],
            ids=[user_id]
        )
        
        return jsonify({
            "success": True,
            "message": f"User {email} has been manually verified for development",
            "user": {
                "email": user_data_dict['email'],
                "full_name": user_data_dict.get('full_name'),
                "is_verified": True
            }
        }), 200
        
    except Exception as e:
        print(f"Development verification error: {e}")
        return jsonify({"error": f"Failed to verify user: {str(e)}"}), 500


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current authenticated user's information"""
    try:
        user_id = get_current_user_id()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "success": True,
            "user": user
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get user information: {str(e)}"}), 500


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout user (client-side token removal)"""
    try:
        # In JWT-based auth, logout is primarily handled client-side
        # Server can maintain a blacklist of tokens if needed
        return jsonify({
            "success": True,
            "message": "Logged out successfully"
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500


@auth_bp.route('/check-auth', methods=['GET'])
@require_auth
def check_auth():
    """Check if user is authenticated"""
    try:
        user_id = get_current_user_id()
        return jsonify({
            "success": True,
            "authenticated": True,
            "user_id": user_id
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "authenticated": False,
            "error": str(e)
        }), 401 


@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Refresh JWT token using existing token (even if expired)"""
    try:
        # Get the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No valid authorization header provided'}), 401
        
        token = auth_header.split(' ')[1]
        if not token or token in ['null', 'undefined']:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Try to decode the token (even if expired)
        try:
            # Decode without verification to get user info
            import jwt
            jwt_secret = user_service._get_jwt_secret()
            payload = jwt.decode(token, jwt_secret, algorithms=['HS256'], options={'verify_exp': False})
            user_id = payload.get('user_id')
            email = payload.get('email')
            
            if not user_id or not email:
                return jsonify({'error': 'Invalid token payload'}), 401
                
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token format'}), 401
        
        # Get user from database
        user = user_service.get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Check if user is verified
        if not user.get('is_verified', False):
            return jsonify({"error": "Email not verified"}), 401
        
        # Generate new token
        new_token = user_service.generate_jwt_token(user['user_id'], user['email'])
        
        return jsonify({
            "success": True,
            "token": new_token,
            "message": "Token refreshed successfully"
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Token refresh failed: {str(e)}"}), 500 