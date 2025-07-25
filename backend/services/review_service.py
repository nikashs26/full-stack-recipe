import chromadb
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

class ReviewService:
    """
    Review service using ChromaDB for storing and retrieving recipe reviews
    with user authentication integration
    """
    
    def __init__(self):
        # Use the new ChromaDB client configuration with absolute path
        import os
        chroma_path = os.path.abspath("./chroma_db")
        os.makedirs(chroma_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_or_create_collection(
            name="recipe_reviews",
            metadata={"description": "Recipe reviews with user authentication"}
        )
    
    def add_review(self, user_id: str, recipe_id: str, recipe_type: str, 
                   author: str, text: str, rating: int) -> Dict[str, Any]:
        """
        Add a new review to ChromaDB
        
        Args:
            user_id: Authenticated user ID from JWT
            recipe_id: ID of the recipe being reviewed
            recipe_type: Type of recipe ('local', 'external', 'manual')
            author: Display name for the review
            text: Review text content
            rating: Rating from 1-5
            
        Returns:
            Dictionary with review data including generated ID
        """
        try:
            review_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            # Create searchable text for the review
            searchable_text = f"{author} rated {rating}/5: {text}"
            
            # Create comprehensive metadata
            metadata = {
                "review_id": review_id,
                "user_id": user_id,
                "recipe_id": recipe_id,
                "recipe_type": recipe_type,
                "author": author,
                "rating": rating,
                "timestamp": timestamp,
                "has_text": bool(text.strip()),
                "text_length": len(text.strip()),
                "is_positive": rating >= 4,
                "is_negative": rating <= 2
            }
            
            # Store the review data as JSON document
            review_data = {
                "id": review_id,
                "user_id": user_id,
                "recipe_id": recipe_id,
                "recipe_type": recipe_type,
                "author": author,
                "text": text,
                "rating": rating,
                "date": timestamp
            }
            
            # Store in ChromaDB
            self.collection.add(
                documents=[searchable_text],
                metadatas=[metadata],
                ids=[review_id]
            )
            
            print(f"✅ Review added successfully: {review_id}")
            return review_data
            
        except Exception as e:
            print(f"❌ Error adding review: {str(e)}")
            raise Exception(f"Failed to add review: {str(e)}")
    
    def get_reviews_by_recipe(self, recipe_id: str, recipe_type: str) -> List[Dict[str, Any]]:
        """
        Get all reviews for a specific recipe
        
        Args:
            recipe_id: ID of the recipe
            recipe_type: Type of recipe ('local', 'external', 'manual')
            
        Returns:
            List of review dictionaries
        """
        try:
            # Query ChromaDB for reviews matching recipe_id and recipe_type
            results = self.collection.get(
                where={
                    "$and": [
                        {"recipe_id": recipe_id},
                        {"recipe_type": recipe_type}
                    ]
                },
                include=['documents', 'metadatas']
            )
            
            reviews = []
            if results and results['metadatas']:
                for i, metadata in enumerate(results['metadatas']):
                    review = {
                        "id": metadata['review_id'],
                        "author": metadata['author'],
                        "text": self._extract_text_from_document(results['documents'][i]),
                        "rating": metadata['rating'],
                        "date": metadata['timestamp']
                    }
                    reviews.append(review)
                
                # Sort by date (newest first)
                reviews.sort(key=lambda x: x['date'], reverse=True)
            
            print(f"📋 Found {len(reviews)} reviews for recipe {recipe_id} ({recipe_type})")
            return reviews
            
        except Exception as e:
            print(f"❌ Error getting reviews: {str(e)}")
            return []
    
    def get_reviews_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all reviews by a specific user
        
        Args:
            user_id: Authenticated user ID
            
        Returns:
            List of review dictionaries
        """
        try:
            results = self.collection.get(
                where={"user_id": user_id},
                include=['documents', 'metadatas']
            )
            
            reviews = []
            if results and results['metadatas']:
                for i, metadata in enumerate(results['metadatas']):
                    review = {
                        "id": metadata['review_id'],
                        "recipe_id": metadata['recipe_id'],
                        "recipe_type": metadata['recipe_type'],
                        "author": metadata['author'],
                        "text": self._extract_text_from_document(results['documents'][i]),
                        "rating": metadata['rating'],
                        "date": metadata['timestamp']
                    }
                    reviews.append(review)
                
                # Sort by date (newest first)
                reviews.sort(key=lambda x: x['date'], reverse=True)
            
            print(f"📋 Found {len(reviews)} reviews by user {user_id}")
            return reviews
            
        except Exception as e:
            print(f"❌ Error getting user reviews: {str(e)}")
            return []
    
    def delete_review(self, review_id: str, user_id: str) -> bool:
        """
        Delete a review (only by the user who created it)
        
        Args:
            review_id: ID of the review to delete
            user_id: Authenticated user ID (must match review author)
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # First check if the review exists and belongs to the user
            results = self.collection.get(
                ids=[review_id],
                include=['metadatas']
            )
            
            if not results or not results['metadatas']:
                print(f"❌ Review {review_id} not found")
                return False
            
            review_metadata = results['metadatas'][0]
            if review_metadata['user_id'] != user_id:
                print(f"❌ User {user_id} not authorized to delete review {review_id}")
                return False
            
            # Delete the review
            self.collection.delete(ids=[review_id])
            print(f"✅ Review {review_id} deleted successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting review: {str(e)}")
            return False
    
    def get_recipe_stats(self, recipe_id: str, recipe_type: str) -> Dict[str, Any]:
        """
        Get statistics for a recipe's reviews
        
        Args:
            recipe_id: ID of the recipe
            recipe_type: Type of recipe ('local', 'external', 'manual')
            
        Returns:
            Dictionary with review statistics
        """
        try:
            results = self.collection.get(
                where={
                    "$and": [
                        {"recipe_id": recipe_id},
                        {"recipe_type": recipe_type}
                    ]
                },
                include=['metadatas']
            )
            
            if not results or not results['metadatas']:
                return {
                    "total_reviews": 0,
                    "average_rating": 0,
                    "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                }
            
            ratings = [metadata['rating'] for metadata in results['metadatas']]
            rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            
            for rating in ratings:
                rating_distribution[rating] += 1
            
            average_rating = sum(ratings) / len(ratings) if ratings else 0
            
            return {
                "total_reviews": len(ratings),
                "average_rating": round(average_rating, 1),
                "rating_distribution": rating_distribution
            }
            
        except Exception as e:
            print(f"❌ Error getting recipe stats: {str(e)}")
            return {
                "total_reviews": 0,
                "average_rating": 0,
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }
    
    def _extract_text_from_document(self, document: str) -> str:
        """
        Extract the review text from the searchable document
        
        Args:
            document: The searchable text stored in ChromaDB
            
        Returns:
            The original review text
        """
        try:
            # The document format is: "{author} rated {rating}/5: {text}"
            # Extract the text after the last ": "
            if ": " in document:
                return document.split(": ", 1)[1]
            return document
        except:
            return document 