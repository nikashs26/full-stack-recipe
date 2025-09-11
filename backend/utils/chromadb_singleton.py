"""
ChromaDB Singleton Factory - Updated for ChromaDB v0.5+
Ensures only one ChromaDB client instance across all services.
"""

import os
import chromadb
from typing import Optional

class ChromaDBSingleton:
    """Singleton factory for ChromaDB client to prevent multiple instances."""
    
    _instance: Optional[chromadb.Client] = None
    _path: Optional[str] = None
    
    @classmethod
    def get_client(cls) -> chromadb.Client:
        """Get the singleton ChromaDB client instance."""
        if cls._instance is None:
            cls._initialize_client()
        return cls._instance
    
    @classmethod
    def get_settings(cls):
        """Settings not used in ChromaDB v0.5+"""
        return None
    
    @classmethod
    def get_path(cls) -> str:
        """Get the ChromaDB path used for the singleton."""
        if cls._path is None:
            cls._initialize_client()
        return cls._path
    
    @classmethod
    def _initialize_client(cls):
        """Initialize the singleton ChromaDB client for v0.5+"""
        # Disable telemetry via environment variables
        os.environ['ANONYMIZED_TELEMETRY'] = 'FALSE'
        
        # Determine the correct ChromaDB path based on environment
        chroma_path = os.environ.get('CHROMA_DB_PATH', './chroma_db')
        
        # For Railway/Render deployment, use persistent volume
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            chroma_path = '/app/data/chroma_db'
        elif os.environ.get('RENDER_ENVIRONMENT'):
            chroma_path = '/opt/render/project/src/chroma_db'
        
        # Ensure we use absolute path for consistency
        chroma_path = os.path.abspath(chroma_path)
        
        # Create directory if it doesn't exist
        try:
            os.makedirs(chroma_path, exist_ok=True)
            print(f"🔧 ChromaDB singleton using path: {chroma_path}")
        except PermissionError:
            if not os.path.exists(chroma_path):
                chroma_path = os.path.abspath('./chroma_db')
                os.makedirs(chroma_path, exist_ok=True)
                print(f"⚠️ Using fallback ChromaDB directory: {chroma_path}")
        
        # Create the singleton client with ChromaDB v0.5+ format
        try:
            cls._instance = chromadb.PersistentClient(path=chroma_path)
            print(f"✅ ChromaDB v0.5+ client created successfully")
        except Exception as e:
            print(f"⚠️ Error creating ChromaDB v0.5+ client: {e}")
            # Fallback: try in-memory client
            try:
                cls._instance = chromadb.Client()
                print(f"⚠️ Using in-memory ChromaDB fallback")
            except Exception as e2:
                print(f"⚠️ ChromaDB initialization completely failed: {e2}")
                cls._instance = None
        
        cls._path = chroma_path
        print(f"✅ ChromaDB singleton initialized")
    
    @classmethod
    def reset(cls):
        """Reset the singleton (for testing purposes)."""
        cls._instance = None
        cls._path = None

# Convenience functions for easy imports
def get_chromadb_client() -> chromadb.Client:
    """Get the singleton ChromaDB client."""
    return ChromaDBSingleton.get_client()

def get_chromadb_settings():
    """Get the ChromaDB settings (not used in v0.5+)."""
    return None

def get_chromadb_path() -> str:
    """Get the ChromaDB path."""
    return ChromaDBSingleton.get_path()
