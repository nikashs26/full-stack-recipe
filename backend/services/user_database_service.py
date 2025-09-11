"""
User Database Service using ChromaDB
Manages user registration, authentication, and data storage
"""

import json
import uuid
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging

# Try to import ChromaDB, fallback to in-memory storage if not available
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("ChromaDB not available, using fallback in-memory storage for user database")

logger = logging.getLogger(__name__)

class UserDatabaseService:
    """
    User database service using ChromaDB for persistent storage
    Falls back to in-memory storage if ChromaDB is not available
    """
    
    def __init__(self):
        self.users_collection = None
        self.sessions_collection = None
        self.client = None
        self.jwt_secret = None
        
        if not CHROMADB_AVAILABLE:
            self._init_fallback_storage()
        else:
            self._init_chromadb()
    
    def _init_fallback_storage(self):
        """Initialize fallback in-memory storage"""
        self.users = {}  # {user_id: user_data}
        self.sessions = {}  # {token: session_data}
        logger.info("Using fallback in-memory user database")
    
    def _init_chromadb(self):
        """Initialize ChromaDB for user storage"""
        try:
            import os
            chroma_path = os.environ.get('CHROMA_DB_PATH', './chroma_db')
            
            # For Railway/Render deployment, use persistent volume
            if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RENDER_ENVIRONMENT'):
                chroma_path = os.environ.get('CHROMA_DB_PATH', '/app/data/chroma_db')
            
            # Ensure directory exists
            os.makedirs(chroma_path, exist_ok=True)
            
            self.client = chromadb.PersistentClient(path=chroma_path)
            
            # Create collections for users and sessions
            self.users_collection = self.client.get_or_create_collection(
                name="users",
                metadata={"description": "User accounts and profiles"}
            )
            
            self.sessions_collection = self.client.get_or_create_collection(
                name="user_sessions",
                metadata={"description": "User authentication sessions"}
            )
            
            # Get JWT secret from environment
            self.jwt_secret = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
            
            logger.info("ChromaDB user database initialized")
            logger.info(f"Users collection has {self.users_collection.count()} users")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB user database: {e}")
            self._init_fallback_storage()
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def _generate_jwt_token(self, user_id: str, username: str) -> str:
        """Generate a JWT token for user authentication"""
        payload = {
            'user_id': user_id,
            'username': username,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
        }
        return jwt.encode(payload, self.jwt_secret or 'dev-secret', algorithm='HS256')
    
    def _verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret or 'dev-secret', algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    def create_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Create a new user account"""
        try:
            # Check if user already exists
            if self.get_user_by_username(username):
                return {'success': False, 'error': 'Username already exists'}
            
            if self.get_user_by_email(email):
                return {'success': False, 'error': 'Email already exists'}
            
            # Generate user ID
            user_id = str(uuid.uuid4())
            
            # Hash password
            password_hash = self._hash_password(password)
            
            # Create user data
            user_data = {
                'id': user_id,
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'created_at': datetime.utcnow().isoformat(),
                'last_login': None,
                'is_active': True
            }
            
            if CHROMADB_AVAILABLE and self.users_collection:
                # Store in ChromaDB
                self.users_collection.add(
                    ids=[user_id],
                    documents=[username],  # Use username as document for search
                    metadatas=[user_data]
                )
            else:
                # Store in fallback storage
                self.users[user_id] = user_data
            
            logger.info(f"User created: {username} ({user_id})")
            return {'success': True, 'user_id': user_id, 'username': username}
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return {'success': False, 'error': 'Failed to create user'}
    
    def authenticate_user(self, username_or_email: str, password: str) -> Dict[str, Any]:
        """Authenticate a user and return JWT token"""
        try:
            # Find user by username or email
            user = self.get_user_by_username(username_or_email) or self.get_user_by_email(username_or_email)
            
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Verify password
            if not self._verify_password(password, user['password_hash']):
                return {'success': False, 'error': 'Invalid password'}
            
            # Check if user is active
            if not user.get('is_active', True):
                return {'success': False, 'error': 'Account is deactivated'}
            
            # Update last login
            user['last_login'] = datetime.utcnow().isoformat()
            self._update_user(user['id'], user)
            
            # Generate JWT token
            token = self._generate_jwt_token(user['id'], user['username'])
            
            # Store session
            self._create_session(user['id'], token)
            
            logger.info(f"User authenticated: {user['username']}")
            return {
                'success': True,
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'created_at': user['created_at'],
                    'last_login': user['last_login']
                }
            }
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return {'success': False, 'error': 'Authentication failed'}
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            if CHROMADB_AVAILABLE and self.users_collection:
                results = self.users_collection.get(
                    where={"username": username},
                    include=['metadatas']
                )
                if results['metadatas']:
                    return results['metadatas'][0]
            else:
                # Search in fallback storage
                for user in self.users.values():
                    if user['username'] == username:
                        return user
            return None
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            if CHROMADB_AVAILABLE and self.users_collection:
                results = self.users_collection.get(
                    where={"email": email},
                    include=['metadatas']
                )
                if results['metadatas']:
                    return results['metadatas'][0]
            else:
                # Search in fallback storage
                for user in self.users.values():
                    if user['email'] == email:
                        return user
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            if CHROMADB_AVAILABLE and self.users_collection:
                results = self.users_collection.get(
                    ids=[user_id],
                    include=['metadatas']
                )
                if results['metadatas']:
                    return results['metadatas'][0]
            else:
                return self.users.get(user_id)
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    def _update_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Update user data"""
        try:
            if CHROMADB_AVAILABLE and self.users_collection:
                self.users_collection.update(
                    ids=[user_id],
                    metadatas=[user_data]
                )
            else:
                self.users[user_id] = user_data
            return True
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    def _create_session(self, user_id: str, token: str) -> bool:
        """Create a user session"""
        try:
            session_data = {
                'user_id': user_id,
                'token': token,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
            
            if CHROMADB_AVAILABLE and self.sessions_collection:
                self.sessions_collection.add(
                    ids=[token],
                    documents=[user_id],
                    metadatas=[session_data]
                )
            else:
                self.sessions[token] = session_data
            
            return True
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user info"""
        try:
            # Verify JWT token
            payload = self._verify_jwt_token(token)
            if not payload:
                return None
            
            # Get user data
            user = self.get_user_by_id(payload['user_id'])
            if not user or not user.get('is_active', True):
                return None
            
            return {
                'user_id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'created_at': user['created_at'],
                'last_login': user['last_login']
            }
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    def logout_user(self, token: str) -> bool:
        """Logout user by invalidating session"""
        try:
            if CHROMADB_AVAILABLE and self.sessions_collection:
                self.sessions_collection.delete(ids=[token])
            else:
                self.sessions.pop(token, None)
            return True
        except Exception as e:
            logger.error(f"Error logging out user: {e}")
            return False
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (for admin purposes)"""
        try:
            if CHROMADB_AVAILABLE and self.users_collection:
                results = self.users_collection.get(include=['metadatas'])
                users = []
                for metadata in results['metadatas']:
                    # Remove password hash from admin view
                    user_info = {k: v for k, v in metadata.items() if k != 'password_hash'}
                    users.append(user_info)
                return users
            else:
                # Return users from fallback storage
                users = []
                for user in self.users.values():
                    user_info = {k: v for k, v in user.items() if k != 'password_hash'}
                    users.append(user_info)
                return users
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    def get_user_count(self) -> int:
        """Get total number of users"""
        try:
            if CHROMADB_AVAILABLE and self.users_collection:
                return self.users_collection.count()
            else:
                return len(self.users)
        except Exception as e:
            logger.error(f"Error getting user count: {e}")
            return 0
