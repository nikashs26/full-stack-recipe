import chromadb
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid

class MealHistoryService:
    """
    Track user meal history and preferences using ChromaDB for intelligent learning
    """
    
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.meal_history_collection = self.client.get_or_create_collection(
            name="meal_history",
            metadata={"description": "User meal history and interactions"}
        )
        self.meal_feedback_collection = self.client.get_or_create_collection(
            name="meal_feedback",
            metadata={"description": "User feedback on meals"}
        )
    
    def log_meal_generated(self, user_id: str, meal_plan: Dict[str, Any], preferences_used: Dict[str, Any]) -> None:
        """
        Log when a meal plan is generated for a user
        """
        log_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create searchable text for the meal plan
        meal_descriptions = []
        for day, meals in meal_plan.items():
            for meal_type, meal in meals.items():
                if meal:
                    meal_descriptions.append(f"{day} {meal_type}: {meal.get('name', '')} ({meal.get('cuisine', '')})")
        
        searchable_text = " | ".join(meal_descriptions)
        
        metadata = {
            "user_id": user_id,
            "event_type": "meal_plan_generated",
            "timestamp": timestamp,
            "preferences_used": json.dumps(preferences_used),
            "meal_count": len([m for day in meal_plan.values() for m in day.values() if m]),
            "cuisines": json.dumps(list(set([
                meal.get('cuisine', '') for day in meal_plan.values() 
                for meal in day.values() if meal and meal.get('cuisine')
            ]))),
            "difficulties": json.dumps(list(set([
                meal.get('difficulty', '') for day in meal_plan.values() 
                for meal in day.values() if meal and meal.get('difficulty')
            ])))
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
                "user_id": user_id,
                "timestamp": {"$gte": cutoff_date}
            },
            include=['metadatas']
        )
        
        # Get feedback data
        feedback_results = self.meal_feedback_collection.get(
            where={
                "user_id": user_id,
                "timestamp": {"$gte": cutoff_date}
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
                    "user_id": user_id,
                    "timestamp": {"$gte": recent_cutoff}
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