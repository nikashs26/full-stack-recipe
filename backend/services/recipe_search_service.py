import chromadb
import json
from typing import List, Dict, Any, Optional
# from sentence_transformers import SentenceTransformer  # Commented out due to dependency issues
import numpy as np

class RecipeSearchService:
    """
    Advanced recipe search using ChromaDB for semantic similarity
    """
    
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.recipe_collection = self.client.get_or_create_collection(
            name="recipes",
            metadata={"description": "Recipe collection with semantic search capabilities"}
        )
        
        # Initialize sentence transformer for better embeddings
        # For now, use ChromaDB's default embeddings to avoid dependency issues
        self.encoder = None
        print("Using ChromaDB's default embeddings (sentence-transformers not available)")
    
    def index_recipe(self, recipe: Dict[str, Any]) -> None:
        """
        Index a recipe for semantic search
        """
        # Create rich text representation for embedding
        searchable_text = self._create_searchable_text(recipe)
        
        # Create comprehensive metadata for filtering
        metadata = {
            "recipe_id": str(recipe.get("id", "")),
            "name": recipe.get("name", ""),
            "cuisine": recipe.get("cuisine", ""),
            "difficulty": recipe.get("difficulty", ""),
            "meal_type": recipe.get("mealType", ""),
            "cooking_time": recipe.get("cookingTime", ""),
            "dietary_restrictions": json.dumps(recipe.get("dietaryRestrictions", [])),
            "ingredient_count": len(recipe.get("ingredients", [])),
            "avg_rating": self._calculate_avg_rating(recipe.get("ratings", [])),
            "has_reviews": len(recipe.get("comments", [])) > 0,
            "is_vegetarian": "vegetarian" in recipe.get("dietaryRestrictions", []),
            "is_vegan": "vegan" in recipe.get("dietaryRestrictions", []),
            "is_gluten_free": "gluten-free" in recipe.get("dietaryRestrictions", [])
        }
        
        # Generate embedding if we have the encoder
        embedding = None
        if self.encoder:
            embedding = self.encoder.encode([searchable_text])[0].tolist()
        
        # Store in ChromaDB
        self.recipe_collection.upsert(
            documents=[searchable_text],
            metadatas=[metadata],
            ids=[f"recipe_{recipe.get('id')}"],
            embeddings=[embedding] if embedding else None
        )
    
    def semantic_search(self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform semantic search on recipes
        
        Examples:
        - "healthy dinner for weight loss" 
        - "quick breakfast with eggs"
        - "comfort food for cold weather"
        - "spicy Asian noodles"
        """
        
        # Build where clause for filtering
        where_clause = {}
        if filters:
            if filters.get("cuisine"):
                where_clause["cuisine"] = filters["cuisine"]
            if filters.get("difficulty"):
                where_clause["difficulty"] = filters["difficulty"]
            if filters.get("meal_type"):
                where_clause["meal_type"] = filters["meal_type"]
            if filters.get("is_vegetarian"):
                where_clause["is_vegetarian"] = True
            if filters.get("max_cooking_time"):
                # This would need custom logic for time comparison
                pass
        
        # Perform semantic search
        results = self.recipe_collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_clause if where_clause else None,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Process and return results
        processed_results = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                similarity_score = 1 - results['distances'][0][i]  # Convert distance to similarity
                
                processed_results.append({
                    "recipe_id": metadata["recipe_id"],
                    "name": metadata["name"],
                    "cuisine": metadata["cuisine"],
                    "difficulty": metadata["difficulty"],
                    "meal_type": metadata["meal_type"],
                    "similarity_score": similarity_score,
                    "metadata": metadata
                })
        
        return processed_results
    
    def find_similar_recipes(self, recipe_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find recipes similar to a given recipe
        """
        # Get the recipe document
        recipe_doc = self.recipe_collection.get(
            ids=[f"recipe_{recipe_id}"],
            include=['documents']
        )
        
        if not recipe_doc or not recipe_doc['documents']:
            return []
        
        # Use the recipe's document as query
        query_text = recipe_doc['documents'][0]
        
        results = self.recipe_collection.query(
            query_texts=[query_text],
            n_results=limit + 1,  # +1 to exclude the original recipe
            include=['documents', 'metadatas', 'distances']
        )
        
        # Filter out the original recipe and process results
        similar_recipes = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                if metadata["recipe_id"] != recipe_id:  # Exclude original
                    similarity_score = 1 - results['distances'][0][i]
                    similar_recipes.append({
                        "recipe_id": metadata["recipe_id"],
                        "name": metadata["name"],
                        "cuisine": metadata["cuisine"],
                        "similarity_score": similarity_score,
                        "metadata": metadata
                    })
        
        return similar_recipes[:limit]
    
    def get_recipe_recommendations(self, user_preferences: Dict[str, Any], limit: int = 8) -> List[Dict[str, Any]]:
        """
        Get personalized recipe recommendations based on user preferences
        """
        # Create a query based on user preferences
        query_parts = []
        
        if user_preferences.get("favoriteCuisines"):
            query_parts.append(f"cuisine: {', '.join(user_preferences['favoriteCuisines'])}")
        
        if user_preferences.get("cookingSkillLevel"):
            query_parts.append(f"difficulty: {user_preferences['cookingSkillLevel']}")
        
        if user_preferences.get("dietaryRestrictions"):
            query_parts.append(f"dietary: {', '.join(user_preferences['dietaryRestrictions'])}")
        
        if user_preferences.get("healthGoals"):
            query_parts.append(f"healthy: {', '.join(user_preferences['healthGoals'])}")
        
        query = " ".join(query_parts) if query_parts else "popular delicious recipes"
        
        # Build filters
        filters = {}
        if "vegetarian" in user_preferences.get("dietaryRestrictions", []):
            filters["is_vegetarian"] = True
        if "vegan" in user_preferences.get("dietaryRestrictions", []):
            filters["is_vegan"] = True
        if "gluten-free" in user_preferences.get("dietaryRestrictions", []):
            filters["is_gluten_free"] = True
        
        return self.semantic_search(query, filters, limit)
    
    def _create_searchable_text(self, recipe: Dict[str, Any]) -> str:
        """
        Create a rich text representation of the recipe for embedding
        """
        parts = []
        
        # Recipe name and description
        parts.append(f"Recipe: {recipe.get('name', '')}")
        
        # Cuisine and meal type
        parts.append(f"Cuisine: {recipe.get('cuisine', '')}")
        parts.append(f"Meal type: {recipe.get('mealType', '')}")
        
        # Dietary info
        if recipe.get('dietaryRestrictions'):
            parts.append(f"Dietary: {', '.join(recipe['dietaryRestrictions'])}")
        
        # Ingredients
        if recipe.get('ingredients'):
            parts.append(f"Ingredients: {', '.join(recipe['ingredients'])}")
        
        # Instructions (first few steps)
        if recipe.get('instructions'):
            instructions = recipe['instructions'][:3]  # First 3 steps
            parts.append(f"Cooking method: {' '.join(instructions)}")
        
        # Difficulty and time
        parts.append(f"Difficulty: {recipe.get('difficulty', '')}")
        parts.append(f"Cooking time: {recipe.get('cookingTime', '')}")
        
        return " | ".join(parts)
    
    def _calculate_avg_rating(self, ratings: List[float]) -> float:
        """Calculate average rating"""
        if not ratings:
            return 0.0
        return sum(ratings) / len(ratings)
    
    def bulk_index_recipes(self, recipes: List[Dict[str, Any]]) -> None:
        """
        Index multiple recipes at once for better performance
        """
        documents = []
        metadatas = []
        ids = []
        embeddings = []
        
        for recipe in recipes:
            searchable_text = self._create_searchable_text(recipe)
            documents.append(searchable_text)
            
            metadata = {
                "recipe_id": str(recipe.get("id", "")),
                "name": recipe.get("name", ""),
                "cuisine": recipe.get("cuisine", ""),
                "difficulty": recipe.get("difficulty", ""),
                "meal_type": recipe.get("mealType", ""),
                "cooking_time": recipe.get("cookingTime", ""),
                "dietary_restrictions": json.dumps(recipe.get("dietaryRestrictions", [])),
                "ingredient_count": len(recipe.get("ingredients", [])),
                "avg_rating": self._calculate_avg_rating(recipe.get("ratings", [])),
                "has_reviews": len(recipe.get("comments", [])) > 0,
                "is_vegetarian": "vegetarian" in recipe.get("dietaryRestrictions", []),
                "is_vegan": "vegan" in recipe.get("dietaryRestrictions", []),
                "is_gluten_free": "gluten-free" in recipe.get("dietaryRestrictions", [])
            }
            metadatas.append(metadata)
            ids.append(f"recipe_{recipe.get('id')}")
            
            # Generate embedding if we have the encoder
            if self.encoder:
                embedding = self.encoder.encode([searchable_text])[0].tolist()
                embeddings.append(embedding)
        
        # Bulk upsert
        self.recipe_collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings if embeddings else None
        ) 