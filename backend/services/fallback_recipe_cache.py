"""
Fallback recipe cache service for when ChromaDB is not available
Uses in-memory storage as a simple alternative
"""

import json
import hashlib
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FallbackRecipeCacheService:
    """
    Fallback recipe cache service that uses in-memory storage
    when ChromaDB is not available (e.g., on Render free tier)
    """
    
    def __init__(self):
        self.recipes = {}  # In-memory storage
        self.recipe_collection = self  # Mock collection interface
        logger.info("Using fallback in-memory recipe cache")
    
    def get_recipe_count(self):
        """Get the total number of recipes in cache"""
        return {
            'total': len(self.recipes),
            'valid': len(self.recipes),
            'expired': 0
        }
    
    def get(self, limit=10, where=None, include=None):
        """Mock ChromaDB get method"""
        recipe_list = list(self.recipes.values())
        if limit:
            recipe_list = recipe_list[:limit]
        
        return {
            'ids': [recipe['id'] for recipe in recipe_list],
            'documents': [recipe.get('document', '') for recipe in recipe_list],
            'metadatas': [recipe.get('metadata', {}) for recipe in recipe_list]
        }
    
    def add(self, ids, documents=None, metadatas=None, embeddings=None):
        """Mock ChromaDB add method"""
        for i, recipe_id in enumerate(ids):
            self.recipes[recipe_id] = {
                'id': recipe_id,
                'document': documents[i] if documents else '',
                'metadata': metadatas[i] if metadatas else {},
                'embedding': embeddings[i] if embeddings else None
            }
        logger.info(f"Added {len(ids)} recipes to fallback cache. Total recipes now: {len(self.recipes)}")
    
    def upsert(self, ids, documents=None, metadatas=None, embeddings=None):
        """Mock ChromaDB upsert method"""
        self.add(ids, documents, metadatas, embeddings)
    
    def query(self, query_texts=None, query_embeddings=None, n_results=10, where=None, include=None):
        """Mock ChromaDB query method - returns empty results for now"""
        return {
            'ids': [[]],
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        }
    
    def delete(self, ids):
        """Mock ChromaDB delete method"""
        for recipe_id in ids:
            if recipe_id in self.recipes:
                del self.recipes[recipe_id]
    
    def search_recipes(self, query, limit=10, filters=None):
        """Search recipes using simple text matching"""
        results = []
        query_lower = query.lower()
        
        for recipe in self.recipes.values():
            if query_lower in recipe.get('document', '').lower():
                results.append(recipe)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_recipe_by_id(self, recipe_id):
        """Get a specific recipe by ID"""
        return self.recipes.get(recipe_id)
    
    def add_recipe(self, recipe_data):
        """Add a recipe to the cache"""
        recipe_id = recipe_data.get('id', str(hash(recipe_data.get('title', ''))))
        self.recipes[recipe_id] = {
            'id': recipe_id,
            'document': recipe_data.get('title', ''),
            'metadata': recipe_data,
            'embedding': None
        }
        return recipe_id
