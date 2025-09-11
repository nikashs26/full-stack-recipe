
# Minimal UserService fix for Render
import os
import json
import uuid
from datetime import datetime

# Force ChromaDB import
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

class MinimalUserService:
    def __init__(self):
        if not CHROMADB_AVAILABLE:
            print("❌ ChromaDB not available")
            self.users_collection = None
            return
        
        # Try multiple paths
        possible_paths = [
            os.environ.get('CHROMA_DB_PATH', './chroma_db'),
            '/opt/render/project/src/chroma_db',
            './chroma_db',
            '/tmp/chroma_db'
        ]
        
        for path in possible_paths:
            try:
                print(f"Trying ChromaDB path: {path}")
                os.makedirs(path, exist_ok=True)
                client = chromadb.PersistentClient(path=path)
                self.users_collection = client.get_or_create_collection("users")
                print(f"✅ ChromaDB initialized at: {path}")
                return
            except Exception as e:
                print(f"❌ Failed with path {path}: {e}")
                continue
        
        print("❌ All ChromaDB paths failed")
        self.users_collection = None
    
    def register_user(self, email, password, full_name=""):
        if not self.users_collection:
            return {"success": False, "error": "Database not available"}
        
        try:
            # Simple registration logic
            user_id = f"user_{str(uuid.uuid4())}"
            user_data = {
                "user_id": user_id,
                "email": email,
                "password_hash": password,  # In real app, hash this
                "full_name": full_name,
                "is_verified": True,  # Skip verification for testing
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.users_collection.upsert(
                documents=[json.dumps(user_data)],
                metadatas=[{"email": email, "user_id": user_id}],
                ids=[user_id]
            )
            
            return {"success": True, "user_id": user_id, "email": email}
        except Exception as e:
            return {"success": False, "error": str(e)}
