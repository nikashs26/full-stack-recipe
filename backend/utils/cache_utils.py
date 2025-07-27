import json
import hashlib
import os
import sys
from functools import wraps
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Ensure the backend directory is in the Python path
backend_dir = str(Path(__file__).parent.parent)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMResponseCache:
    def __init__(self, cache_dir='.llm_cache', ttl_hours=24):
        """
        Initialize the LLM response cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = os.path.abspath(cache_dir)
        self.ttl = timedelta(hours=ttl_hours)
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_key(self, *args, **kwargs):
        """Generate a unique cache key from function arguments."""
        key_parts = [
            str(arg) for arg in args
        ] + [
            f"{k}={v}" for k, v in sorted(kwargs.items())
        ]
        key_string = ":".join(key_parts).encode('utf-8')
        return hashlib.md5(key_string).hexdigest()
    
    def _get_cache_path(self, key):
        """Get the filesystem path for a cache key."""
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def get(self, key):
        """Get a cached response if it exists and isn't expired."""
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
            
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
                
            # Check if cache entry is expired
            cache_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - cache_time > self.ttl:
                return None
                
            return data['response']
            
        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(f"Error reading cache entry {key}: {e}")
            return None
    
    def set(self, key, response):
        """Cache a response."""
        cache_path = self._get_cache_path(key)
        
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'response': response
            }
            
            with open(cache_path, 'w') as f:
                json.dump(data, f)
                
        except (TypeError, OSError) as e:
            logger.warning(f"Error writing to cache {key}: {e}")

def cached_llm_response(cache: LLMResponseCache):
    """
    Decorator to cache LLM responses.
    
    Args:
        cache: An instance of LLMResponseCache
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip caching if cache is None
            if cache is None:
                return func(*args, **kwargs)
                
            # Generate cache key
            cache_key = cache._get_cache_key(*args, **kwargs)
            
            # Try to get cached response
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                logger.info(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_response
                
            # Call the function if no cache hit
            logger.info(f"Cache miss for {func.__name__}: {cache_key}")
            response = func(*args, **kwargs)
            
            # Cache the response if successful
            if response is not None:
                cache.set(cache_key, response)
                
            return response
            
        return wrapper
    return decorator

# Global cache instance
llm_cache = LLMResponseCache()

def get_llm_cache():
    """
    Get the global LLM cache instance.
    
    Returns:
        LLMResponseCache: The global cache instance
    """
    return llm_cache

# Export only the necessary functions and classes
__all__ = ['LLMResponseCache', 'cached_llm_response', 'get_llm_cache']
