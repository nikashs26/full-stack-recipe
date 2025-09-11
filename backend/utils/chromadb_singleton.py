"""
ChromaDB Singleton Factory - Simplified for Render deployment
Uses in-memory storage to avoid configuration issues
"""

import os
from typing import Optional

class ChromaDBSingleton:
    """Singleton factory for ChromaDB client."""
    
    _instance = None
    _path: Optional[str] = None
    
    @classmethod
    def get_client(cls):
        """Get the singleton ChromaDB client instance."""
        if cls._instance is None:
            cls._initialize_client()
        return cls._instance
    
    @classmethod
    def get_settings(cls):
        """Settings not used."""
        return None
    
    @classmethod
    def get_path(cls) -> str:
        """Get the ChromaDB path."""
        if cls._path is None:
            cls._initialize_client()
        return cls._path or './chroma_db'
    
    @classmethod
    def _initialize_client(cls):
        """Initialize with in-memory client for simplicity"""
        # Disable telemetry
        os.environ['ANONYMIZED_TELEMETRY'] = 'FALSE'
        
        # For now, use None (in-memory fallback in services)
        cls._instance = None
        cls._path = './chroma_db'
        print("⚠️ Using in-memory ChromaDB fallback for simplicity")
    
    @classmethod
    def reset(cls):
        """Reset the singleton."""
        cls._instance = None
        cls._path = None

# Convenience functions
def get_chromadb_client():
    """Get the singleton ChromaDB client."""
    return ChromaDBSingleton.get_client()

def get_chromadb_settings():
    """Get the ChromaDB settings."""
    return None

def get_chromadb_path() -> str:
    """Get the ChromaDB path."""
    return ChromaDBSingleton.get_path()