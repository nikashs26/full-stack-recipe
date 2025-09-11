"""
ChromaDB Singleton Factory
Ensures only one ChromaDB client instance with consistent settings across all services.
This prevents the "An instance of Chroma already exists" error on Render.
"""

import os
import chromadb
from chromadb.config import Settings
from typing import Optional

class ChromaDBSingleton:
    """Singleton factory for ChromaDB client to prevent multiple instances with different settings."""
    
    _instance: Optional[chromadb.Client] = None
    _settings: Optional[Settings] = None
    _path: Optional[str] = None
    
    @classmethod
    def get_client(cls) -> chromadb.Client:
        """Get the singleton ChromaDB client instance."""
        if cls._instance is None:
            cls._initialize_client()
        return cls._instance
    
    @classmethod
    def get_settings(cls) -> Settings:
        """Get the ChromaDB settings used for the singleton."""
        if cls._settings is None:
            cls._initialize_client()
        return cls._settings
    
    @classmethod
    def get_path(cls) -> str:
        """Get the ChromaDB path used for the singleton."""
        if cls._path is None:
            cls._initialize_client()
        return cls._path
    
    @classmethod
    def _initialize_client(cls):
        """Initialize the singleton ChromaDB client with consistent settings."""
        # Aggressively disable telemetry before creating client
        os.environ['ANONYMIZED_TELEMETRY'] = 'FALSE'
        os.environ['CHROMA_CLIENT_AUTHN_PROVIDER'] = ''
        os.environ['CHROMA_CLIENT_AUTHN_CREDENTIALS'] = ''
        os.environ['ALLOW_RESET'] = 'FALSE'
        os.environ['CHROMA_DB_IMPL'] = 'duckdb+parquet'
        os.environ['CHROMA_SERVER_NOFILE'] = '65536'
        # Disable PostHog completely
        os.environ['POSTHOG_DISABLED'] = 'TRUE'
        os.environ['TELEMETRY_DISABLED'] = 'TRUE'
        
        # Determine the correct ChromaDB path based on environment
        chroma_path = os.environ.get('CHROMA_DB_PATH', './chroma_db')
        
        # For Railway/Render deployment, use persistent volume
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            chroma_path = os.environ.get('CHROMA_DB_PATH', '/app/data/chroma_db')
        elif os.environ.get('RENDER_ENVIRONMENT'):
            chroma_path = os.environ.get('CHROMA_DB_PATH', '/opt/render/project/src/chroma_db')
        
        # Ensure we use absolute path for consistency
        chroma_path = os.path.abspath(chroma_path)
        
        # Create directory if it doesn't exist
        try:
            os.makedirs(chroma_path, exist_ok=True)
            print(f"🔧 ChromaDB singleton using path: {chroma_path}")
        except PermissionError:
            # Directory might already exist with correct permissions
            if not os.path.exists(chroma_path):
                # Try to use a fallback local directory
                chroma_path = os.path.abspath('./chroma_db')
                os.makedirs(chroma_path, exist_ok=True)
                print(f"⚠️ Using fallback ChromaDB directory: {chroma_path}")
        
        # Create the singleton client with new ChromaDB v0.5+ configuration
        try:
            # Use the new client configuration format
            cls._instance = chromadb.PersistentClient(path=chroma_path)
            cls._settings = None  # Not needed with new client
        except Exception as e:
            print(f"⚠️ Error creating ChromaDB client: {e}")
            # If that fails, try fallback configuration
            try:
                import tempfile
                fallback_path = tempfile.mkdtemp()
                cls._instance = chromadb.PersistentClient(path=fallback_path)
                print(f"⚠️ Using temporary ChromaDB directory: {fallback_path}")
            except Exception as e2:
                print(f"⚠️ ChromaDB initialization completely failed: {e2}")
                cls._instance = None
        cls._path = chroma_path
        
        print(f"✅ ChromaDB singleton initialized at: {chroma_path}")
    
    @classmethod
    def reset(cls):
        """Reset the singleton (for testing purposes)."""
        cls._instance = None
        cls._settings = None
        cls._path = None

# Convenience functions for easy imports
def get_chromadb_client() -> chromadb.Client:
    """Get the singleton ChromaDB client."""
    return ChromaDBSingleton.get_client()

def get_chromadb_settings() -> Settings:
    """Get the ChromaDB settings."""
    return ChromaDBSingleton.get_settings()

def get_chromadb_path() -> str:
    """Get the ChromaDB path."""
    return ChromaDBSingleton.get_path()
