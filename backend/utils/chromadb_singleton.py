"""
ChromaDB Singleton Factory - Working with ChromaDB v0.4.10
Ensures only one ChromaDB client instance across all services.
"""

import os
import chromadb
from chromadb import PersistentClient, EphemeralClient
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
        """Settings not used in this version."""
        return None
    
    @classmethod
    def get_path(cls) -> str:
        """Get the ChromaDB path used for the singleton."""
        if cls._path is None:
            cls._initialize_client()
        return cls._path
    
    @classmethod
    def _initialize_client(cls):
        """Initialize the singleton ChromaDB client with latest v0.4.22+ API"""
        # Set all telemetry environment variables to ensure complete disable
        os.environ['ANONYMIZED_TELEMETRY'] = 'FALSE'
        os.environ['CHROMA_CLIENT_AUTHN_PROVIDER'] = ''
        os.environ['CHROMA_CLIENT_AUTHN_CREDENTIALS'] = ''
        os.environ['POSTHOG_DISABLED'] = 'TRUE'
        os.environ['TELEMETRY_DISABLED'] = 'TRUE'
        os.environ['ALLOW_RESET'] = 'FALSE'
        
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
        
        # Check if forced clean initialization is requested
        force_clean = os.environ.get('CHROMADB_FORCE_CLEAN_INIT', '').lower() == 'true'
        if force_clean and os.path.exists(chroma_path):
            print(f"🔧 CHROMADB_FORCE_CLEAN_INIT set - removing existing ChromaDB data")
            import shutil
            shutil.rmtree(chroma_path, ignore_errors=True)
            os.makedirs(chroma_path, exist_ok=True)
        
        # Create the singleton client with LATEST ChromaDB API (v0.4.22+)
        try:
            # Use ONLY the new PersistentClient API without any settings
            # This avoids all deprecated configuration patterns
            cls._instance = PersistentClient(path=chroma_path)
            print(f"✅ ChromaDB v0.4.22+ PersistentClient created successfully")
        except Exception as e:
            error_str = str(e).lower()
            if "deprecated configuration" in error_str or "deprecated" in error_str:
                print(f"⚠️ ChromaDB deprecated configuration detected. Forcing clean initialization...")
                try:
                    # Force clean initialization by removing old data
                    import shutil
                    from datetime import datetime
                    
                    if os.path.exists(chroma_path):
                        # In deployment, we need to be more aggressive about cleaning up
                        if os.environ.get('RENDER_ENVIRONMENT') or os.environ.get('RAILWAY_ENVIRONMENT'):
                            print(f"🔧 Deployment environment detected - removing deprecated ChromaDB data")
                            shutil.rmtree(chroma_path, ignore_errors=True)
                        else:
                            # In development, backup first
                            backup_path = f"{chroma_path}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            shutil.move(chroma_path, backup_path)
                            print(f"📦 Backed up existing ChromaDB data to: {backup_path}")
                    
                    # Recreate the directory with fresh structure
                    os.makedirs(chroma_path, exist_ok=True)
                    
                    # Try creating client again with clean directory
                    cls._instance = PersistentClient(path=chroma_path)
                    print(f"✅ ChromaDB v0.4.22+ PersistentClient created successfully after clean initialization")
                except Exception as migration_error:
                    print(f"⚠️ Clean initialization failed: {migration_error}")
                    print(f"⚠️ Falling back to EphemeralClient")
                    # Fallback: try in-memory client with new API
                    try:
                        cls._instance = EphemeralClient()
                        print(f"⚠️ Using EphemeralClient ChromaDB fallback")
                    except Exception as e2:
                        print(f"⚠️ ChromaDB initialization completely failed: {e2}")
                        cls._instance = None
            else:
                print(f"⚠️ Error creating persistent ChromaDB client: {e}")
                # For any other error, also try fallback
                try:
                    cls._instance = EphemeralClient()
                    print(f"⚠️ Using EphemeralClient ChromaDB fallback")
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
    """Get the ChromaDB settings (not used in v0.4.10)."""
    return None

def get_chromadb_path() -> str:
    """Get the ChromaDB path."""
    return ChromaDBSingleton.get_path()