from flask import Blueprint, jsonify
import os
# Try to import dotenv, fallback if not available
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Warning: python-dotenv not available, using environment variables only")
    def load_dotenv():
        pass  # No-op fallback

# Load environment variables
load_dotenv()

# Create blueprint
health_bp = Blueprint('health', __name__)

@health_bp.route('/api/health/chromadb', methods=['GET'])
def check_chromadb():
    """Check ChromaDB connection status"""
    try:
        # Try to import and initialize ChromaDB
        import chromadb
        import os
        
        # Use the singleton ChromaDB client for health check
        from utils.chromadb_singleton import get_chromadb_client, get_chromadb_path
        
        client = get_chromadb_client()
        chroma_path = get_chromadb_path()
        
        # Check if client is None
        if client is None:
            return jsonify({
                'status': 'error',
                'message': 'ChromaDB client is None - initialization failed',
                'chromadb': {
                    'connected': False,
                    'path': chroma_path,
                    'error': 'Client initialization failed'
                }
            }), 500
        
        # List collections to verify connection
        collections = client.list_collections()
        
        return jsonify({
                'status': 'success',
                'message': 'ChromaDB connection successful',
                'chromadb': {
                    'connected': True,
                    'path': chroma_path,
                    'collections_count': len(collections),
                    'collections': [col.name for col in collections]
                }
            }), 200
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'ChromaDB connection failed',
            'error': str(e),
            'chromadb': {
                'connected': False,
                'path': './chroma_db',
                'error': str(e)
            }
        }), 500

@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """General health check endpoint"""
    return jsonify({
        'status': 'up',
        'services': {
            'chromadb': '/api/health/chromadb'
        }
    }), 200
