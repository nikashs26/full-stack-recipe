"""
Lightweight embedding functions for ChromaDB to avoid model downloads
"""

import hashlib
from typing import List


class LightweightEmbeddingFunction:
    """
    Simple hash-based embedding function that doesn't require model downloads.
    Creates deterministic embeddings from text using SHA-256 hash.
    """
    
    def __init__(self, dimensions: int = 384):
        """
        Initialize the embedding function.
        
        Args:
            dimensions: Number of dimensions for the embedding (default: 384, same as all-MiniLM-L6-v2)
        """
        self.dimensions = dimensions
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        Generate embeddings for input texts.
        
        Args:
            input: List of text strings to embed
            
        Returns:
            List of embedding vectors (one per input text)
        """
        embeddings = []
        
        for text in input:
            # Create a simple embedding from text hash
            hash_obj = hashlib.sha256(text.encode('utf-8'))
            hash_bytes = hash_obj.digest()
            
            # Convert to specified number of float dimensions
            embedding = []
            for i in range(self.dimensions):
                # Use hash bytes cyclically and normalize to [-1, 1] range
                byte_val = hash_bytes[i % len(hash_bytes)]
                # Normalize to [-1, 1] range
                normalized_val = (byte_val / 128.0) - 1.0
                embedding.append(normalized_val)
            
            embeddings.append(embedding)
        
        return embeddings


class TokenBasedEmbeddingFunction:
    """
    Simple token-based embedding function for better semantic similarity.
    Still lightweight but more meaningful than pure hash-based.
    """
    
    def __init__(self, dimensions: int = 384):
        """
        Initialize the embedding function.
        
        Args:
            dimensions: Number of dimensions for the embedding
        """
        self.dimensions = dimensions
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        Generate embeddings for input texts using simple token analysis.
        
        Args:
            input: List of text strings to embed
            
        Returns:
            List of embedding vectors (one per input text)
        """
        embeddings = []
        
        for text in input:
            # Simple tokenization and feature extraction
            text_lower = text.lower()
            words = text_lower.split()
            
            # Create embedding based on word characteristics
            embedding = [0.0] * self.dimensions
            
            # Use various text features to populate embedding
            for i, word in enumerate(words[:self.dimensions]):
                # Position-based features
                pos_weight = 1.0 - (i / max(len(words), 1))
                
                # Word length feature
                length_feature = min(len(word) / 10.0, 1.0)
                
                # Character-based features
                char_sum = sum(ord(c) for c in word) % 1000
                char_feature = (char_sum / 1000.0) * 2.0 - 1.0
                
                # Combine features
                idx = i % self.dimensions
                embedding[idx] = pos_weight * length_feature * char_feature
            
            # Normalize to reasonable range
            max_val = max(abs(v) for v in embedding) or 1.0
            embedding = [v / max_val for v in embedding]
            
            embeddings.append(embedding)
        
        return embeddings


def get_lightweight_embedding_function(use_token_based: bool = False, dimensions: int = 384):
    """
    Get a lightweight embedding function for ChromaDB.
    
    Args:
        use_token_based: If True, use token-based embeddings; if False, use hash-based
        dimensions: Number of dimensions for embeddings
        
    Returns:
        Embedding function instance
    """
    if use_token_based:
        return TokenBasedEmbeddingFunction(dimensions)
    else:
        return LightweightEmbeddingFunction(dimensions)
