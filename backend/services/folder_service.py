import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import ChromaDB - required for the application to work
import chromadb

class FolderService:
    """
    Service for managing recipe folders using ChromaDB
    """
    
    def __init__(self):
        
        import os
        chroma_path = os.environ.get('CHROMA_DB_PATH', './chroma_db')
        
        # For Railway/Render deployment, use persistent volume
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            chroma_path = os.environ.get('CHROMA_DB_PATH', '/app/data/chroma_db')
        elif os.environ.get('RENDER_ENVIRONMENT'):
            chroma_path = os.environ.get('CHROMA_DB_PATH', '/opt/render/project/src/chroma_db')
        
        chroma_path = os.path.abspath(chroma_path)
        try:
            os.makedirs(chroma_path, exist_ok=True)
        except PermissionError:
            # Directory might already exist with correct permissions
            if not os.path.exists(chroma_path):
                raise PermissionError(f"Cannot create ChromaDB directory at {chroma_path}. Please ensure the directory exists and has correct permissions.")
        # Import ChromaDB singleton to prevent multiple instances
        from utils.chromadb_singleton import get_chromadb_client
        
        # Use the singleton ChromaDB client and lightweight embeddings
        from utils.lightweight_embeddings import get_lightweight_embedding_function
        self.client = get_chromadb_client()
        self.embedding_function = get_lightweight_embedding_function(use_token_based=True)
        self.folders_collection = self.client.get_or_create_collection(
            name="recipe_folders",
            metadata={"description": "Recipe folders for organizing recipes"},
            embedding_function=self.embedding_function
        )
        self.folder_items_collection = self.client.get_or_create_collection(
            name="folder_items",
            metadata={"description": "Items within recipe folders"},
            embedding_function=self.embedding_function
        )
    
    def create_folder(self, user_id: str, name: str, description: str = "") -> Dict[str, Any]:
        """Create a new folder"""
        if not self.folders_collection:
            return {"success": False, "error": "Database not available"}
        folder_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        folder_data = {
            "folder_id": folder_id,
            "user_id": user_id,
            "name": name,
            "description": description,
            "created_at": timestamp,
            "updated_at": timestamp,
            "recipe_count": 0
        }
        
        self.folders_collection.add(
            documents=[json.dumps(folder_data)],
            metadatas=[{
                "type": "folder",
                "user_id": user_id,
                "folder_id": folder_id
            }],
            ids=[folder_id]
        )
        
        return folder_data
    
    def get_user_folders(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all folders for a user"""
        if not self.folders_collection:
            return []
        results = self.folders_collection.get(
            where={"user_id": user_id},
            include=["documents", "metadatas"]
        )
        
        folders = []
        for doc, metadata in zip(results['documents'], results['metadatas']):
            folder_data = json.loads(doc)
            folders.append(folder_data)
            
        return sorted(folders, key=lambda x: x['name'].lower())
    
    def update_folder(self, folder_id: str, user_id: str, **updates) -> Optional[Dict[str, Any]]:
        """Update folder details"""
        folder = self.folders_collection.get(
            ids=[folder_id],
            where={"user_id": user_id}
        )
        
        if not folder['documents']:
            return None
            
        folder_data = json.loads(folder['documents'][0])
        
        # Update fields
        for key, value in updates.items():
            if key in folder_data and key not in ['folder_id', 'user_id', 'created_at']:
                folder_data[key] = value
        
        folder_data['updated_at'] = datetime.now().isoformat()
        
        self.folders_collection.update(
            ids=[folder_id],
            documents=[json.dumps(folder_data)],
            metadatas=[{
                "type": "folder",
                "user_id": user_id,
                "folder_id": folder_id
            }]
        )
        
        return folder_data
    
    def delete_folder(self, folder_id: str, user_id: str) -> bool:
        """Delete a folder and all its items"""
        # Verify folder exists and belongs to user
        folder = self.folders_collection.get(
            ids=[folder_id],
            where={"user_id": user_id}
        )
        
        if not folder['documents']:
            return False
        
        # Delete all items in the folder
        self.folder_items_collection.delete(
            where={"folder_id": folder_id}
        )
        
        # Delete the folder
        self.folders_collection.delete(
            ids=[folder_id]
        )
        
        return True
    
    def add_to_folder(self, folder_id: str, user_id: str, recipe_id: str, 
                     recipe_type: str, recipe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add a recipe to a folder"""
        # Verify folder exists and belongs to user
        folder = self.folders_collection.get(
            ids=[folder_id],
            where={"user_id": user_id}
        )
        
        if not folder['documents']:
            return None
        
        # Check if recipe already in folder
        existing = self.folder_items_collection.get(
            where={"$and": [
                {"folder_id": folder_id},
                {"recipe_id": recipe_id},
                {"recipe_type": recipe_type}
            ]}
        )
        
        if existing['ids']:
            return None  # Already in folder
        
        item_id = f"{folder_id}:{recipe_id}:{recipe_type}"
        timestamp = datetime.now().isoformat()
        
        item_data = {
            "item_id": item_id,
            "folder_id": folder_id,
            "user_id": user_id,
            "recipe_id": recipe_id,
            "recipe_type": recipe_type,
            "recipe_data": recipe_data,
            "added_at": timestamp
        }
        
        self.folder_items_collection.add(
            documents=[json.dumps(item_data)],
            metadatas=[{
                "type": "folder_item",
                "folder_id": folder_id,
                "user_id": user_id,
                "recipe_id": recipe_id,
                "recipe_type": recipe_type
            }],
            ids=[item_id]
        )
        
        # Update folder's recipe count
        folder_data = json.loads(folder['documents'][0])
        folder_data['recipe_count'] = folder_data.get('recipe_count', 0) + 1
        folder_data['updated_at'] = timestamp
        
        self.folders_collection.update(
            ids=[folder_id],
            documents=[json.dumps(folder_data)],
            metadatas=[{
                "type": "folder",
                "user_id": user_id,
                "folder_id": folder_id
            }]
        )
        
        return item_data
    
    def remove_from_folder(self, folder_id: str, user_id: str, item_id: str) -> bool:
        """Remove an item from a folder"""
        # Verify folder exists and belongs to user
        folder = self.folders_collection.get(
            ids=[folder_id],
            where={"user_id": user_id}
        )
        
        if not folder['documents']:
            return False
        
        # Verify item exists in folder
        item = self.folder_items_collection.get(
            ids=[item_id],
            where={"folder_id": folder_id}
        )
        
        if not item['documents']:
            return False
        
        # Delete the item
        self.folder_items_collection.delete(ids=[item_id])
        
        # Update folder's recipe count
        folder_data = json.loads(folder['documents'][0])
        folder_data['recipe_count'] = max(0, folder_data.get('recipe_count', 1) - 1)
        folder_data['updated_at'] = datetime.now().isoformat()
        
        self.folders_collection.update(
            ids=[folder_id],
            documents=[json.dumps(folder_data)],
            metadatas=[{
                "type": "folder",
                "user_id": user_id,
                "folder_id": folder_id
            }]
        )
        
        return True
    
    def get_folder_contents(self, folder_id: str, user_id: str) -> Dict[str, Any]:
        """Get all recipes in a folder"""
        # Verify folder exists and belongs to user
        folder = self.folders_collection.get(
            ids=[folder_id],
            where={"user_id": user_id}
        )
        
        if not folder['documents']:
            return {"folder": None, "items": []}
        
        # Get all items in the folder
        items = self.folder_items_collection.get(
            where={"folder_id": folder_id},
            include=["documents", "metadatas"]
        )
        
        folder_data = json.loads(folder['documents'][0])
        recipe_items = []
        
        for doc in items['documents']:
            item_data = json.loads(doc)
            
            # Get recipe data with reviews and stats
            recipe_data = item_data['recipe_data']
            
            # Try to get review statistics for this recipe
            try:
                from .review_service import ReviewService
                review_service = ReviewService()
                review_stats = review_service.get_recipe_stats(
                    item_data['recipe_id'], 
                    item_data['recipe_type']
                )
                
                # Enhance recipe data with review information
                enhanced_recipe_data = {
                    **recipe_data,
                    "rating": review_stats.get("average_rating", 0),
                    "reviewCount": review_stats.get("total_reviews", 0),
                    "ratingDistribution": review_stats.get("rating_distribution", {})
                }
            except Exception as e:
                # If we can't get review stats, use the original data
                enhanced_recipe_data = recipe_data
                print(f"Warning: Could not get review stats for recipe {item_data['recipe_id']}: {e}")
            
            recipe_items.append({
                "id": item_data['item_id'],
                "recipe_id": item_data['recipe_id'],
                "recipe_type": item_data['recipe_type'],
                "recipe_data": enhanced_recipe_data,
                "added_at": item_data['added_at']
            })
        
        return {
            "folder": folder_data,
            "items": sorted(recipe_items, key=lambda x: x['added_at'], reverse=True)
        }
    
    def search_folders(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Search folders by name or description"""
        results = self.folders_collection.query(
            query_texts=[query],
            where={"user_id": user_id},
            n_results=10,
            include=["documents", "metadatas"]
        )
        
        folders = []
        for doc in results['documents'][0]:
            folder_data = json.loads(doc)
            folders.append(folder_data)
            
        return folders
    
    def get_recipe_folders(self, user_id: str, recipe_id: str, recipe_type: str) -> List[Dict[str, Any]]:
        """Get all folders containing a specific recipe"""
        items = self.folder_items_collection.get(
            where={
                "$and": [
                    {"user_id": user_id},
                    {"recipe_id": recipe_id},
                    {"recipe_type": recipe_type}
                ]
            },
            include=["metadatas"]
        )
        
        if not items['ids']:
            return []
        
        # Get all folder IDs
        folder_ids = [meta['folder_id'] for meta in items['metadatas']]
        
        # Get folder details
        folders = self.folders_collection.get(
            ids=folder_ids,
            include=["documents"]
        )
        
        return [json.loads(doc) for doc in folders['documents']]
