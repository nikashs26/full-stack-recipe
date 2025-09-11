import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid

# Import ChromaDB - required for the application to work
import chromadb

class MealHistoryService:
    """
    Track user meal history and preferences using ChromaDB for intelligent learning
    """
    
    def __init__(self):
        
        # Use absolute path to ensure ChromaDB is created in the right location
        import os
        chroma_path = os.environ.get('CHROMA_DB_PATH', './chroma_db')
        
        # For Railway/Render deployment, use persistent volume
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            chroma_path = os.environ.get('CHROMA_DB_PATH', '/app/data/chroma_db')
        elif os.environ.get('RENDER_ENVIRONMENT'):
            chroma_path = os.environ.get('CHROMA_DB_PATH', '/opt/render/project/src/chroma_db')
        
        chroma_path = os.path.abspath(chroma_path)
        
        # Import ChromaDB singleton to prevent multiple instances
        from utils.chromadb_singleton import get_chromadb_client
        
        # Use the singleton ChromaDB client and lightweight embeddings
        from utils.lightweight_embeddings import get_lightweight_embedding_function
        self.client = get_chromadb_client()
        self.embedding_function = get_lightweight_embedding_function(use_token_based=True)
        
        self.meal_history_collection = self.client.get_or_create_collection(
            name="meal_history",
            metadata={"description": "User meal history and interactions"},
            embedding_function=self.embedding_function
        )
        
        self.meal_feedback_collection = self.client.get_or_create_collection(
            name="meal_feedback",
            metadata={"description": "User feedback on meals"},
            embedding_function=self.embedding_function
        )
    
    def log_meal_generated(self, user_id: str, meal_plan: Dict[str, Any], preferences_used: Dict[str, Any]) -> None:
        """
        Log when a meal plan is generated for a user
        """
        if not self.meal_history_collection:
            return
        log_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        

        
        # Handle both legacy format (day keys) and new format (days array)
        meal_descriptions = []
        cuisines = set()
        difficulties = set()
        meal_count = 0
        
        # Check if it's the new format with 'days' array
        if 'days' in meal_plan and isinstance(meal_plan['days'], list):
            # New format: days array
            for day_data in meal_plan['days']:
                day_name = day_data.get('day', 'Unknown')
                meals = day_data.get('meals', [])
                for meal in meals:
                    if meal:
                        meal_count += 1
                        meal_name = meal.get('name', 'Unknown')
                        meal_cuisine = meal.get('cuisine', 'Unknown')
                        meal_difficulty = meal.get('difficulty', 'Unknown')
                        
                        meal_descriptions.append(f"{day_name} {meal.get('meal_type', 'meal')}: {meal_name} ({meal_cuisine})")
                        if meal_cuisine:
                            cuisines.add(meal_cuisine)
                        if meal_difficulty:
                            difficulties.add(meal_difficulty)
        else:
            # Legacy format: day keys
            for day, meals in meal_plan.items():
                for meal_type, meal in meals.items():
                    if meal:
                        meal_count += 1
                        meal_name = meal.get('name', 'Unknown')
                        meal_cuisine = meal.get('cuisine', 'Unknown')
                        meal_difficulty = meal.get('difficulty', 'Unknown')
                        
                        meal_descriptions.append(f"{day} {meal_type}: {meal_name} ({meal_cuisine})")
                        if meal_cuisine:
                            cuisines.add(meal_cuisine)
                        if meal_difficulty:
                            difficulties.add(meal_difficulty)
        
        searchable_text = " | ".join(meal_descriptions) if meal_descriptions else "Meal plan generated"
        
        metadata = {
            "user_id": user_id,
            "event_type": "meal_plan_generated",
            "timestamp": timestamp,
            "preferences_used": json.dumps(preferences_used),
            "meal_count": meal_count,
            "cuisines": json.dumps(list(cuisines)),
            "difficulties": json.dumps(list(difficulties))
        }
        
        self.meal_history_collection.add(
            documents=[searchable_text],
            metadatas=[metadata],
            ids=[log_id]
        )
    
    def log_meal_feedback(self, user_id: str, meal_id: str, feedback_type: str, rating: Optional[int] = None, notes: Optional[str] = None) -> None:
        """
        Log user feedback on specific meals
        
        feedback_type: 'liked', 'disliked', 'cooked', 'skipped', 'rated'
        """
        if not self.meal_feedback_collection:
            return
        feedback_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create searchable text
        searchable_text = f"Feedback: {feedback_type} for meal {meal_id}"
        if notes:
            searchable_text += f" - {notes}"
        
        metadata = {
            "user_id": user_id,
            "meal_id": meal_id,
            "feedback_type": feedback_type,
            "rating": rating or 0,
            "timestamp": timestamp,
            "has_notes": bool(notes)
        }
        
        self.meal_feedback_collection.add(
            documents=[searchable_text],
            metadatas=[metadata],
            ids=[feedback_id]
        )
    
    def get_user_meal_patterns(self, user_id: str, days_back: int = 30) -> Dict[str, Any]:
        """
        Analyze user's meal patterns and preferences from history
        """
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        # Get recent meal history
        history_results = self.meal_history_collection.get(
            where={
                "$and": [
                    {"user_id": user_id},
                    {"timestamp": {"$gte": cutoff_date}}
                ]
            },
            include=['metadatas']
        )
        
        # Get feedback data
        feedback_results = self.meal_feedback_collection.get(
            where={
                "$and": [
                    {"user_id": user_id},
                    {"timestamp": {"$gte": cutoff_date}}
                ]
            },
            include=['metadatas']
        )
        
        # Analyze patterns
        patterns = {
            "preferred_cuisines": {},
            "preferred_difficulties": {},
            "feedback_summary": {
                "liked_count": 0,
                "disliked_count": 0,
                "cooked_count": 0,
                "skipped_count": 0,
                "avg_rating": 0
            },
            "meal_generation_frequency": len(history_results['metadatas']) if history_results['metadatas'] else 0,
            "most_recent_preferences": None
        }
        
        # Process meal history
        if history_results and history_results['metadatas']:
            for metadata in history_results['metadatas']:
                # Count cuisines
                cuisines = json.loads(metadata.get('cuisines', '[]'))
                for cuisine in cuisines:
                    patterns['preferred_cuisines'][cuisine] = patterns['preferred_cuisines'].get(cuisine, 0) + 1
                
                # Count difficulties
                difficulties = json.loads(metadata.get('difficulties', '[]'))
                for difficulty in difficulties:
                    patterns['preferred_difficulties'][difficulty] = patterns['preferred_difficulties'].get(difficulty, 0) + 1
                
                # Get most recent preferences
                if not patterns['most_recent_preferences']:
                    patterns['most_recent_preferences'] = json.loads(metadata.get('preferences_used', '{}'))
        
        # Process feedback
        if feedback_results and feedback_results['metadatas']:
            ratings = []
            for metadata in feedback_results['metadatas']:
                feedback_type = metadata.get('feedback_type', '')
                patterns['feedback_summary'][f"{feedback_type}_count"] = patterns['feedback_summary'].get(f"{feedback_type}_count", 0) + 1
                
                rating = metadata.get('rating', 0)
                if rating > 0:
                    ratings.append(rating)
            
            if ratings:
                patterns['feedback_summary']['avg_rating'] = sum(ratings) / len(ratings)
        
        return patterns
    
    def get_personalized_meal_suggestions(self, user_id: str, meal_type: str, exclude_recent: bool = True) -> List[str]:
        """
        Get meal suggestions based on user's history and preferences
        """
        patterns = self.get_user_meal_patterns(user_id)
        
        # Build query based on patterns
        query_parts = []
        
        # Favorite cuisines
        if patterns['preferred_cuisines']:
            top_cuisines = sorted(patterns['preferred_cuisines'].items(), key=lambda x: x[1], reverse=True)[:3]
            query_parts.append(f"cuisine: {', '.join([c[0] for c in top_cuisines])}")
        
        # Preferred difficulty
        if patterns['preferred_difficulties']:
            top_difficulty = max(patterns['preferred_difficulties'].items(), key=lambda x: x[1])
            query_parts.append(f"difficulty: {top_difficulty[0]}")
        
        # Meal type
        query_parts.append(f"meal type: {meal_type}")
        
        # Recent preferences
        if patterns['most_recent_preferences']:
            if patterns['most_recent_preferences'].get('dietaryRestrictions'):
                query_parts.append(f"dietary: {', '.join(patterns['most_recent_preferences']['dietaryRestrictions'])}")
        
        query = " ".join(query_parts) if query_parts else f"{meal_type} recipes"
        
        # Get recently generated meals to avoid repetition
        recent_meals = set()
        if exclude_recent:
            recent_cutoff = (datetime.now() - timedelta(days=7)).isoformat()
            recent_history = self.meal_history_collection.get(
                where={
                    "$and": [
                        {"user_id": user_id},
                        {"timestamp": {"$gte": recent_cutoff}}
                    ]
                },
                include=['documents']
            )
            
            if recent_history and recent_history['documents']:
                for doc in recent_history['documents']:
                    # Extract meal names from document
                    meal_names = [part.split(': ')[1].split(' (')[0] for part in doc.split(' | ') if ': ' in part]
                    recent_meals.update(meal_names)
        
        # This would integrate with the RecipeSearchService for actual suggestions
        # For now, return the query that would be used
        return [query]
    
    def get_meal_success_rate(self, user_id: str, meal_id: str) -> Dict[str, Any]:
        """
        Get success metrics for a specific meal across all users
        """
        feedback_results = self.meal_feedback_collection.get(
            where={"meal_id": meal_id},
            include=['metadatas']
        )
        
        if not feedback_results or not feedback_results['metadatas']:
            return {"success_rate": 0, "total_feedback": 0}
        
        total_feedback = len(feedback_results['metadatas'])
        positive_feedback = sum(1 for meta in feedback_results['metadatas'] 
                              if meta.get('feedback_type') in ['liked', 'cooked'])
        
        return {
            "success_rate": positive_feedback / total_feedback if total_feedback > 0 else 0,
            "total_feedback": total_feedback,
            "positive_feedback": positive_feedback
        }
    
    def get_trending_meals(self, days_back: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get trending meals based on recent positive feedback
        """
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        feedback_results = self.meal_feedback_collection.get(
            where={
                "timestamp": {"$gte": cutoff_date},
                "feedback_type": {"$in": ["liked", "cooked"]}
            },
            include=['metadatas']
        )
        
        if not feedback_results or not feedback_results['metadatas']:
            return []
        
        # Count positive feedback per meal
        meal_scores = {}
        for metadata in feedback_results['metadatas']:
            meal_id = metadata.get('meal_id')
            if meal_id:
                meal_scores[meal_id] = meal_scores.get(meal_id, 0) + 1
        
        # Sort by score and return top meals
        trending = sorted(meal_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [{"meal_id": meal_id, "score": score} for meal_id, score in trending]
    
    def get_user_meal_plan_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get user's meal plan generation history with full meal plan details
        """
        try:
            # Get meal history for the user, ordered by timestamp (most recent first)
            results = self.meal_history_collection.get(
                where={
                    "$and": [
                        {"user_id": user_id},
                        {"event_type": "meal_plan_generated"}
                    ]
                },
                include=['metadatas', 'documents']
            )
            
            if not results or not results['metadatas']:
                return []
            
            # Convert to list of dicts with full meal plan info
            history = []
            for i, metadata in enumerate(results['metadatas']):
                try:
                    preferences_used = json.loads(metadata.get('preferences_used', '{}'))
                    cuisines = json.loads(metadata.get('cuisines', '[]'))
                    difficulties = json.loads(metadata.get('difficulties', '[]'))
                    
                    # Parse the meal plan from the searchable text
                    meal_descriptions = results['documents'][i] if i < len(results['documents']) else ""
                    
                    history_item = {
                        "id": metadata.get('timestamp', ''),  # Use timestamp as ID
                        "generated_at": metadata.get('timestamp', ''),
                        "preferences_used": preferences_used,
                        "meal_count": metadata.get('meal_count', 0),
                        "cuisines": cuisines,
                        "difficulties": difficulties,
                        "meal_descriptions": meal_descriptions,
                        "preview": meal_descriptions[:200] + "..." if len(meal_descriptions) > 200 else meal_descriptions
                    }
                    
                    history.append(history_item)
                    
                except (json.JSONDecodeError, KeyError) as e:
                    # Skip malformed entries
                    continue
            
            # Sort by timestamp (most recent first) and limit
            history.sort(key=lambda x: x['generated_at'], reverse=True)
            return history[:limit]
            
        except Exception as e:
            print(f"Error retrieving meal plan history: {e}")
            return []
    
    def get_meal_plan_details(self, user_id: str, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific meal plan
        """
        try:
            results = self.meal_history_collection.get(
                where={
                    "$and": [
                        {"user_id": user_id},
                        {"timestamp": plan_id}  # Using timestamp as plan ID
                    ]
                },
                include=['metadatas', 'documents']
            )
            
            if not results or not results['metadatas']:
                return None
            
            metadata = results['metadatas'][0]
            meal_descriptions = results['documents'][0] if results['documents'] else ""
            
            # Parse meal plan from descriptions
            meal_plan = self._parse_meal_descriptions(meal_descriptions)
            
            return {
                "id": plan_id,
                "generated_at": metadata.get('timestamp', ''),
                "preferences_used": json.loads(metadata.get('preferences_used', '{}')),
                "meal_count": metadata.get('meal_count', 0),
                "cuisines": json.loads(metadata.get('cuisines', '[]')),
                "difficulties": json.loads(metadata.get('difficulties', '[]')),
                "meal_plan": meal_plan,
                "raw_descriptions": meal_descriptions
            }
            
        except Exception as e:
            print(f"Error retrieving meal plan details: {e}")
            return None
    
    def _parse_meal_descriptions(self, descriptions: str) -> Dict[str, Dict[str, str]]:
        """
        Parse meal descriptions back into structured meal plan format
        """
        meal_plan = {}
        
        # Split by " | " to get individual meal entries
        meals = descriptions.split(" | ")
        
        for meal_entry in meals:
            try:
                # Parse format: "day meal_type: meal_name (cuisine)"
                if ": " in meal_entry:
                    day_meal, meal_info = meal_entry.split(": ", 1)
                    
                    # Extract day and meal type
                    day_meal_parts = day_meal.strip().split(" ")
                    if len(day_meal_parts) >= 2:
                        day = day_meal_parts[0].lower()
                        meal_type = day_meal_parts[1].lower()
                        
                        # Extract meal name (everything before the last parenthesis)
                        meal_name = meal_info
                        if " (" in meal_info and meal_info.endswith(")"):
                            meal_name = meal_info.rsplit(" (", 1)[0]
                        
                        # Initialize day if not exists
                        if day not in meal_plan:
                            meal_plan[day] = {}
                        
                        meal_plan[day][meal_type] = meal_name
                        
            except Exception:
                # Skip malformed entries
                continue
        
        return meal_plan

    def cleanup_old_data(self, days_to_keep: int = 90) -> None:
        """
        Clean up old meal history data to keep the database manageable
        """
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        # Get old records
        old_history = self.meal_history_collection.get(
            where={"timestamp": {"$lt": cutoff_date}},
            include=['metadatas']
        )
        
        old_feedback = self.meal_feedback_collection.get(
            where={"timestamp": {"$lt": cutoff_date}},
            include=['metadatas']
        )
        
        # Delete old records (ChromaDB doesn't have direct delete by where, so we need IDs)
        # This would require getting the IDs first, which is a limitation of current ChromaDB
        # For now, we'll just log what would be deleted
        history_count = len(old_history['metadatas']) if old_history['metadatas'] else 0
        feedback_count = len(old_feedback['metadatas']) if old_feedback['metadatas'] else 0
        
        print(f"Would delete {history_count} old history records and {feedback_count} old feedback records") 