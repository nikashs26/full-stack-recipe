"""
Persistent fallback user service that uses JSON files when ChromaDB is not available
This ensures user data persists across app restarts even without ChromaDB
"""

import json
import uuid
import hashlib
import os
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

class PersistentFallbackUserService:
    """
    Persistent fallback user service using JSON files
    This is used when ChromaDB is not available but we still want persistence
    """
    
    def __init__(self):
        print("⚠️ Using persistent fallback user service (JSON files)")
        
        # Create data directory
        self.data_dir = os.environ.get('FALLBACK_DATA_DIR', './fallback_data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # File paths
        self.users_file = os.path.join(self.data_dir, 'users.json')
        self.tokens_file = os.path.join(self.data_dir, 'verification_tokens.json')
        
        # Load existing data
        self.users = self._load_json_file(self.users_file, {})
        self.verification_tokens = self._load_json_file(self.tokens_file, {})
        
        self._jwt_secret = os.getenv('JWT_SECRET_KEY', 'fallback-jwt-secret-change-in-production')
        
        print(f"📁 Loaded {len(self.users)} users from {self.users_file}")
        print(f"📁 Loaded {len(self.verification_tokens)} tokens from {self.tokens_file}")
    
    def _load_json_file(self, filepath: str, default: Any = None) -> Any:
        """Load data from JSON file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading {filepath}: {e}")
        return default if default is not None else {}
    
    def _save_json_file(self, filepath: str, data: Any) -> bool:
        """Save data to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error saving {filepath}: {e}")
            return False
    
    def _save_users(self):
        """Save users to file"""
        self._save_json_file(self.users_file, self.users)
    
    def _save_tokens(self):
        """Save tokens to file"""
        self._save_json_file(self.tokens_file, self.verification_tokens)
    
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
            # Fallback verification
            return hashlib.sha256(password.encode('utf-8')).hexdigest() == hashed_password
    
    def generate_jwt_token(self, user_id: str, email: str) -> str:
        """Generate JWT token"""
        if not JWT_AVAILABLE:
            return "jwt-not-available"
        
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(days=7)  # 7 days expiry
        }
        
        return jwt.encode(payload, self._jwt_secret, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        if not JWT_AVAILABLE:
            return None
        
        try:
            payload = jwt.decode(token, self._jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def register_user(self, email: str, password: str, full_name: str = "") -> Dict[str, Any]:
        """Register a new user"""
        # Check if user already exists
        for user_id, user_data in self.users.items():
            if user_data.get('email') == email:
                return {"success": False, "error": "User already exists"}
        
        # Create new user
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        password_hash = self.hash_password(password)
        
        user_data = {
            'user_id': user_id,
            'email': email,
            'password_hash': password_hash,
            'full_name': full_name,
            'is_verified': False,
            'created_at': datetime.now().isoformat()
        }
        
        self.users[user_id] = user_data
        self._save_users()
        
        return {
            "success": True,
            "user_id": user_id,
            "email": email,
            "full_name": full_name
        }
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user login"""
        for user_id, user_data in self.users.items():
            if user_data.get('email') == email:
                if self.verify_password(password, user_data.get('password_hash', '')):
                    return user_data
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        for user_id, user_data in self.users.items():
            if user_data.get('email') == email:
                return user_data
        return None
    
    def verify_email(self, token: str) -> bool:
        """Verify email with token"""
        if token not in self.verification_tokens:
            return False
        
        token_data = self.verification_tokens[token]
        user_id = token_data.get('user_id')
        
        if user_id in self.users:
            self.users[user_id]['is_verified'] = True
            self._save_users()
            
            # Remove used token
            del self.verification_tokens[token]
            self._save_tokens()
            
            return True
        
        return False
    
    def create_verification_token(self, user_id: str, email: str) -> str:
        """Create email verification token"""
        token = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(hours=24)
        
        self.verification_tokens[token] = {
            'user_id': user_id,
            'email': email,
            'expires_at': expires_at.isoformat()
        }
        
        self._save_tokens()
        return token
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user data"""
        if user_id in self.users:
            self.users[user_id].update(updates)
            self._save_users()
            return True
        return False
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        if user_id in self.users:
            del self.users[user_id]
            self._save_users()
            return True
        return False
