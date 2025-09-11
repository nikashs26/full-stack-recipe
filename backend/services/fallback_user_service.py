"""
Fallback UserService for when ChromaDB is not available
This provides basic user management using in-memory storage
"""

import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

# Try to import jwt, fallback if not available
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

# Try to import bcrypt, fallback if not available
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

class FallbackUserService:
    """
    Fallback user service using in-memory storage
    This is used when ChromaDB is not available
    """
    
    def __init__(self):
        print("⚠️ Using fallback in-memory user service")
        self.users = {}  # user_id -> user_data
        self.verification_tokens = {}  # token -> verification_data
        self._jwt_secret = "fallback-jwt-secret-change-in-production"
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt or fallback"""
        if BCRYPT_AVAILABLE:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        else:
            # Fallback to simple hash (not secure, but functional)
            return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        if BCRYPT_AVAILABLE:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        else:
            # Fallback to simple hash verification
            return hashlib.sha256(password.encode('utf-8')).hexdigest() == hashed_password
    
    def generate_jwt_token(self, user_id: str, email: str) -> str:
        """Generate a JWT token for authenticated user"""
        if not JWT_AVAILABLE:
            # Fallback to simple token
            return f"fallback_token_{user_id}_{email}"
        
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(days=7),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self._jwt_secret, algorithm='HS256')
    
    def decode_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and verify a JWT token"""
        if not JWT_AVAILABLE:
            # Fallback token parsing
            if token.startswith("fallback_token_"):
                parts = token.split("_")
                if len(parts) >= 4:
                    return {
                        'user_id': parts[2],
                        'email': parts[3],
                        'exp': (datetime.utcnow() + timedelta(days=7)).timestamp()
                    }
            return None
        
        try:
            payload = jwt.decode(token, self._jwt_secret, algorithms=['HS256'])
            return payload
        except:
            return None
    
    def generate_verification_token(self) -> str:
        """Generate a unique verification token"""
        return str(uuid.uuid4())
    
    def email_exists(self, email: str) -> bool:
        """Check if an email is already registered"""
        return any(user['email'] == email for user in self.users.values())
    
    def register_user(self, email: str, password: str, full_name: str = "") -> Dict[str, Any]:
        """Register a new user"""
        try:
            # Check if email already exists
            if self.email_exists(email):
                return {"success": False, "error": "Email already registered"}
            
            # Generate user ID and hash password
            user_id = f"user_{str(uuid.uuid4())}"
            hashed_password = self.hash_password(password)
            
            # Generate verification token
            verification_token = self.generate_verification_token()
            
            # Prepare user data
            user_data = {
                "user_id": user_id,
                "email": email,
                "password_hash": hashed_password,
                "full_name": full_name,
                "is_verified": True,  # Auto-verify for fallback service
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Store user
            self.users[user_id] = user_data
            
            # Store verification token
            verification_data = {
                "token": verification_token,
                "user_id": user_id,
                "email": email,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
            
            self.verification_tokens[verification_token] = verification_data
            
            return {
                "success": True,
                "user_id": user_id,
                "email": email,
                "verification_token": verification_token,
                "message": "User registered successfully. Please check your email for verification."
            }
            
        except Exception as e:
            return {"success": False, "error": f"Registration failed: {str(e)}"}
    
    def verify_email(self, verification_token: str) -> Dict[str, Any]:
        """Verify user's email using verification token"""
        try:
            if verification_token not in self.verification_tokens:
                return {"success": False, "error": "Invalid verification token"}
            
            token_data = self.verification_tokens[verification_token]
            
            # Check if token is expired
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            if datetime.utcnow() > expires_at:
                return {"success": False, "error": "Verification token has expired"}
            
            user_id = token_data['user_id']
            
            # Update user to verified
            if user_id in self.users:
                self.users[user_id]['is_verified'] = True
                self.users[user_id]['updated_at'] = datetime.utcnow().isoformat()
                
                # Remove verification token
                del self.verification_tokens[verification_token]
                
                return {
                    "success": True,
                    "message": "Email verified successfully"
                }
            else:
                return {"success": False, "error": "User not found"}
                
        except Exception as e:
            return {"success": False, "error": f"Verification failed: {str(e)}"}
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user login"""
        try:
            # Find user by email
            user = None
            for user_data in self.users.values():
                if user_data['email'] == email:
                    user = user_data
                    break
            
            if not user:
                return {"success": False, "error": "Invalid email or password"}
            
            # Verify password
            if not self.verify_password(password, user['password_hash']):
                return {"success": False, "error": "Invalid email or password"}
            
            # Check if user is verified
            if not user['is_verified']:
                return {"success": False, "error": "Please verify your email before logging in"}
            
            # Update last login
            user['last_login'] = datetime.utcnow().isoformat()
            user['updated_at'] = datetime.utcnow().isoformat()
            
            # Generate JWT token
            token = self.generate_jwt_token(user['user_id'], user['email'])
            
            return {
                "success": True,
                "message": "Login successful",
                "user": {
                    "user_id": user['user_id'],
                    "email": user['email'],
                    "full_name": user['full_name'],
                    "is_verified": user['is_verified']
                },
                "token": token
            }
            
        except Exception as e:
            return {"success": False, "error": f"Authentication failed: {str(e)}"}
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        for user in self.users.values():
            if user['email'] == email:
                return user
        return None
    
    def get_all_users(self) -> Dict[str, Any]:
        """Get all users (for admin purposes)"""
        return {
            "users": list(self.users.values()),
            "total_count": len(self.users)
        }
