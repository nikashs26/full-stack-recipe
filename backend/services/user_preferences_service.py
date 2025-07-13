import chromadb
import json

class UserPreferencesService:
    def __init__(self):
        # Use the new ChromaDB client configuration
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection("user_preferences")

    def save_preferences(self, user_id: str, preferences: dict):
        # Store preferences as a JSON document in ChromaDB
        # Convert preferences to JSON string for storage
        preferences_json = json.dumps(preferences)
        
        # Store with simple metadata
        self.collection.upsert(
            documents=[preferences_json], 
            metadatas=[{"user_id": user_id, "type": "preferences"}], 
            ids=[user_id] 
        )

    def get_preferences(self, user_id: str):
        results = self.collection.get(
            ids=[user_id],
            include=['documents']
        )
        if results and results["documents"]:
            # Parse the JSON string back to dict
            try:
                preferences = json.loads(results["documents"][0])
                return preferences
            except json.JSONDecodeError:
                return None
        return None 