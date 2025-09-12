"""
Image proxy route to serve external images through the backend
This avoids CORS issues when loading images from external sources
"""

from flask import Blueprint, request, Response, jsonify
from flask_cors import cross_origin
import requests
import logging
from functools import wraps
import time

logger = logging.getLogger(__name__)

# Create blueprint
image_proxy_bp = Blueprint('image_proxy', __name__)

# Simple cache for images to avoid repeated requests
image_cache = {}
CACHE_TTL = 3600  # 1 hour

def cache_image(url, data, content_type):
    """Cache image data"""
    image_cache[url] = {
        'data': data,
        'content_type': content_type,
        'timestamp': time.time()
    }

def get_cached_image(url):
    """Get cached image if available and not expired"""
    if url in image_cache:
        cached = image_cache[url]
        if time.time() - cached['timestamp'] < CACHE_TTL:
            return cached['data'], cached['content_type']
    return None, None

@image_proxy_bp.route('/proxy-image')
@cross_origin(origins=['http://localhost:8081', 'http://localhost:5173', 'https://betterbulk.netlify.app'], 
             methods=['GET', 'OPTIONS'],
             allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
             supports_credentials=True)
def proxy_image():
    """
    Proxy external images to avoid CORS issues
    Usage: /proxy-image?url=<encoded_image_url>
    """
    try:
        image_url = request.args.get('url')
        
        if not image_url:
            return jsonify({'error': 'Missing image URL'}), 400
        
        # Check cache first
        cached_data, cached_type = get_cached_image(image_url)
        if cached_data:
            # Create response with proper CORS headers for cached data
            response = Response(cached_data, mimetype=cached_type)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            response.headers['Cache-Control'] = 'public, max-age=3600'
            return response
        
        # Fetch image from external source

        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(image_url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()
        
        # Get content type
        content_type = response.headers.get('content-type', 'image/jpeg')
        
        # Read image data
        image_data = response.content
        
        # Cache the image
        cache_image(image_url, image_data, content_type)
        
        # Create response with proper CORS headers
        response = Response(image_data, mimetype=content_type)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Cache-Control'] = 'public, max-age=3600'
        
        return response
        
    except requests.exceptions.RequestException as e:

        return jsonify({'error': 'Failed to fetch image'}), 502
        
    except Exception as e:
        logger.error(f"Unexpected error in image proxy: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@image_proxy_bp.route('/proxy-image', methods=['OPTIONS'])
def proxy_image_options():
    """Handle CORS preflight request"""
    return '', 200
