# Try to import ChromaDB, fallback to in-memory storage if not available
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("Warning: ChromaDB not available, using fallback in-memory storage for user service")
    from .fallback_user_service import FallbackUserService
import json
import uuid
from datetime import datetime, timedelta

# Try to import jwt, fallback if not available
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("Warning: JWT not available, authentication will be disabled")

# Try to import bcrypt, fallback if not available
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    print("Warning: bcrypt not available, using fallback password hashing")
from typing import Dict, Optional, Any
import os


class UserService:
    """
    User authentication service using ChromaDB for storage
    Handles registration, login, email verification, and user management
    """
    
    # Class-level JWT secret to ensure consistency across instances
    _jwt_secret = None
    
    @classmethod
    def _get_jwt_secret(cls):
        """Get the JWT secret, loading it from environment if not already loaded"""
        if cls._jwt_secret is None:
            import os
            from dotenv import load_dotenv
            load_dotenv()  # Ensure environment variables are loaded
            cls._jwt_secret = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')
        return cls._jwt_secret
    
    def __init__(self):
        # Initialize ChromaDB
        import os
        chroma_path = os.environ.get('CHROMA_DB_PATH', './chroma_db')
        
        # For Railway/Render deployment, use persistent volume
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            chroma_path = os.environ.get('CHROMA_DB_PATH', '/app/data/chroma_db')
        elif os.environ.get('RENDER_ENVIRONMENT'):
            chroma_path = os.environ.get('CHROMA_DB_PATH', '/opt/render/project/src/chroma_db')
        
        chroma_path = os.path.abspath(chroma_path)
        
        # Check if ChromaDB is available
        if not CHROMADB_AVAILABLE:
            print("❌ Warning: ChromaDB not available, using fallback in-memory storage for user service")
            # Use fallback service
            from .fallback_user_service import FallbackUserService
            fallback = FallbackUserService()
            # Copy all methods from fallback to this instance
            for attr_name in dir(fallback):
                if not attr_name.startswith('_') and callable(getattr(fallback, attr_name)):
                    setattr(self, attr_name, getattr(fallback, attr_name))
            return
        
        print(f"🔧 Initializing ChromaDB at path: {chroma_path}")
        
        # Try to create directory, but don't fail if it already exists or permission denied
        try:
            os.makedirs(chroma_path, exist_ok=True)
            print(f"✅ ChromaDB directory created/verified: {chroma_path}")
        except PermissionError as e:
            print(f"⚠️ Permission error creating directory: {e}")
            # Directory might already exist with correct permissions
            if not os.path.exists(chroma_path):
                print(f"❌ Directory does not exist and cannot be created: {chroma_path}")
                self.client = None
                self.users_collection = None
                self.verification_tokens_collection = None
                return
            else:
                print(f"✅ Directory exists: {chroma_path}")
        except Exception as e:
            print(f"❌ Error creating ChromaDB directory: {e}")
            self.client = None
            self.users_collection = None
            self.verification_tokens_collection = None
            return
        
        try:
            # Use Settings configuration (recommended approach)
            from chromadb.config import Settings
            settings = Settings(
                is_persistent=True,
                persist_directory=chroma_path
            )
            self.client = chromadb.PersistentClient(settings=settings)
            print("✅ ChromaDB client initialized")
            
            # User collections
            self.users_collection = self.client.get_or_create_collection("users")
            self.verification_tokens_collection = self.client.get_or_create_collection("verification_tokens")
            print("✅ User collections created/verified")
            
        except Exception as e:
            print(f"❌ Error initializing ChromaDB client: {e}")
            print(f"   ChromaDB path: {chroma_path}")
            print(f"   Path exists: {os.path.exists(chroma_path) if 'chroma_path' in locals() else 'N/A'}")
            print(f"   Path is writable: {os.access(chroma_path, os.W_OK) if 'chroma_path' in locals() and os.path.exists(chroma_path) else 'N/A'}")
            import traceback
            print(f"   Full traceback: {traceback.format_exc()}")
            self.client = None
            self.users_collection = None
            self.verification_tokens_collection = None
        
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt or fallback"""
        if BCRYPT_AVAILABLE:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        else:
            # Fallback to simple hash (not secure, but functional)
            import hashlib
            return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        if BCRYPT_AVAILABLE:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        else:
            # Fallback to simple hash verification
            import hashlib
            return hashlib.sha256(password.encode('utf-8')).hexdigest() == hashed_password
    
    def generate_jwt_token(self, user_id: str, email: str) -> str:
        """Generate a JWT token for authenticated user"""
        if not JWT_AVAILABLE:
            raise RuntimeError("JWT not available, cannot generate token")
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(days=7),  # Token expires in 7 days
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self._get_jwt_secret(), algorithm='HS256')
    
    def decode_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and verify a JWT token"""
        if not JWT_AVAILABLE:
            print("❌ UserService - JWT not available, cannot decode token")
            return None
        try:
            jwt_secret = self._get_jwt_secret()
            print(f"🔍 UserService - Attempting to decode token with secret: {jwt_secret[:20]}...")
            payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
            print(f"✅ UserService - Token decoded successfully, payload: {payload}")
            return payload
        except jwt.ExpiredSignatureError as e:
            print(f"❌ UserService - Token expired: {e}")
            return None
        except jwt.InvalidTokenError as e:
            print(f"❌ UserService - Invalid token: {e}")
            return None
        except Exception as e:
            print(f"❌ UserService - Unexpected error decoding token: {e}")
            return None
    
    def generate_verification_token(self) -> str:
        """Generate a unique verification token"""
        return str(uuid.uuid4())
    
    def email_exists(self, email: str) -> bool:
        """Check if an email is already registered"""
        if not CHROMADB_AVAILABLE or not self.users_collection:
            return False
        try:
            results = self.users_collection.get(
                where={"email": email},
                include=['metadatas']
            )
            return len(results['metadatas']) > 0
        except Exception:
            return False
    
    def register_user(self, email: str, password: str, full_name: str = "") -> Dict[str, Any]:
        """Register a new user"""
        if not CHROMADB_AVAILABLE or not self.users_collection:
            return {"success": False, "error": "Database not available"}
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
                "is_verified": False,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            user_metadata = {
                "user_id": user_id,
                "email": email,
                "is_verified": False,
                "type": "user",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Store user in ChromaDB
            self.users_collection.upsert(
                documents=[json.dumps(user_data)],
                metadatas=[user_metadata],
                ids=[user_id]
            )
            
            # Store verification token
            verification_data = {
                "token": verification_token,
                "user_id": user_id,
                "email": email,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
            
            self.verification_tokens_collection.upsert(
                documents=[json.dumps(verification_data)],
                metadatas={"user_id": user_id, "email": email, "type": "verification"},
                ids=[verification_token]
            )
            
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
            # Get verification token data
            results = self.verification_tokens_collection.get(
                ids=[verification_token],
                include=['documents', 'metadatas']
            )
            
            if not results['documents']:
                return {"success": False, "error": "Invalid verification token"}
            
            token_data = json.loads(results['documents'][0])
            
            # Check if token is expired
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            if datetime.utcnow() > expires_at:
                return {"success": False, "error": "Verification token has expired"}
            
            user_id = token_data['user_id']
            
            # Get user data
            user_results = self.users_collection.get(
                ids=[user_id],
                include=['documents', 'metadatas']
            )
            
            if not user_results['documents']:
                return {"success": False, "error": "User not found"}
            
            user_data = json.loads(user_results['documents'][0])
            user_metadata = user_results['metadatas'][0]
            
            # Update user verification status
            user_data['is_verified'] = True
            user_data['updated_at'] = datetime.utcnow().isoformat()
            user_metadata['is_verified'] = True
            
            # Update user in ChromaDB
            self.users_collection.upsert(
                documents=[json.dumps(user_data)],
                metadatas=[user_metadata],
                ids=[user_id]
            )
            
            # Delete verification token
            self.verification_tokens_collection.delete(ids=[verification_token])
            
            return {
                "success": True,
                "message": "Email verified successfully! You can now sign in.",
                "user_id": user_id,
                "email": user_data['email']
            }
            
        except Exception as e:
            return {"success": False, "error": f"Email verification failed: {str(e)}"}
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user login"""
        if not CHROMADB_AVAILABLE or not self.users_collection:
            return {"success": False, "error": "Database not available"}
        try:
            # Find user by email
            results = self.users_collection.get(
                where={"email": email},
                include=['documents', 'metadatas']
            )
            
            if not results['documents']:
                return {"success": False, "error": "Invalid email or password"}
            
            user_data = json.loads(results['documents'][0])
            
            # Check if email is verified
            if not user_data['is_verified']:
                return {"success": False, "error": "Please verify your email before signing in"}
            
            # Verify password
            if not self.verify_password(password, user_data['password_hash']):
                return {"success": False, "error": "Invalid email or password"}
            
            # Generate JWT token
            jwt_token = self.generate_jwt_token(user_data['user_id'], user_data['email'])
            
            return {
                "success": True,
                "user": {
                    "user_id": user_data['user_id'],
                    "email": user_data['email'],
                    "full_name": user_data.get('full_name', ''),
                    "created_at": user_data['created_at']
                },
                "token": jwt_token,
                "message": "Login successful"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Authentication failed: {str(e)}"}
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user ID"""
        if not CHROMADB_AVAILABLE or not self.users_collection:
            return None
        try:
            results = self.users_collection.get(
                ids=[user_id],
                include=['documents']
            )
            
            if results['documents']:
                user_data = json.loads(results['documents'][0])
                # Remove password hash from response
                user_data.pop('password_hash', None)
                return user_data
            
            return None
            
        except Exception:
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        if not CHROMADB_AVAILABLE or not self.users_collection:
            return None
        try:
            results = self.users_collection.get(
                where={"email": email},
                include=['documents']
            )
            
            if results['documents']:
                user_data = json.loads(results['documents'][0])
                # Remove password hash from response
                user_data.pop('password_hash', None)
                return user_data
            
            return None
            
        except Exception:
            return None
    
    def resend_verification_email(self, email: str) -> Dict[str, Any]:
        """Resend verification email"""
        try:
            # Check if user exists and is not verified
            user = self.get_user_by_email(email)
            if not user:
                return {"success": False, "error": "User not found"}
            
            if user['is_verified']:
                return {"success": False, "error": "Email is already verified"}
            
            # Generate new verification token
            verification_token = self.generate_verification_token()
            
            # Store new verification token
            verification_data = {
                "token": verification_token,
                "user_id": user['user_id'],
                "email": email,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
            
            self.verification_tokens_collection.upsert(
                documents=[json.dumps(verification_data)],
                metadatas={"user_id": user['user_id'], "email": email, "type": "verification"},
                ids=[verification_token]
            )
            
            return {
                "success": True,
                "verification_token": verification_token,
                "message": "Verification email sent successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to resend verification email: {str(e)}"} 