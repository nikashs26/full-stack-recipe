from flask import Blueprint, jsonify
import os
from dotenv import load_dotenv

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
        
        # Check if ChromaDB directory exists and is accessible
        chroma_path = os.path.abspath("./chroma_db")
        if os.path.exists(chroma_path):
            # Try to create a test client
            client = chromadb.PersistentClient(path=chroma_path)
            
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
        else:
            return jsonify({
                'status': 'error',
                'message': 'ChromaDB directory not found',
                'chromadb': {
                    'connected': False,
                    'path': chroma_path,
                    'error': 'Directory does not exist'
                }
            }), 500
            
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
