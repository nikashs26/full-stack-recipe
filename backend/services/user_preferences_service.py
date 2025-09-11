import json

# Import ChromaDB singleton to prevent multiple instances
from utils.chromadb_singleton import get_chromadb_client

class UserPreferencesService:
    def __init__(self):
        # Use the singleton ChromaDB client
        self.client = get_chromadb_client()
        self.collection = self.client.get_or_create_collection("user_preferences")

    def save_preferences(self, user_id: str, preferences: dict):
        if not self.collection:
            # Store in memory
            self.preferences[user_id] = preferences
            return
            
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
        if not self.collection:
            # Get from memory
            return self.preferences.get(user_id)
            
        print(f'🔥 USER_PREFERENCES_SERVICE: get_preferences called for user_id: {user_id}')
        
        results = self.collection.get(
            ids=[user_id],
            include=['documents']
        )
        
        print(f'🔥 USER_PREFERENCES_SERVICE: ChromaDB results: {results}')
        
        if results and results["documents"]:
            print(f'🔥 USER_PREFERENCES_SERVICE: Found documents: {results["documents"]}')
            # Parse the JSON string back to dict
            try:
                preferences = json.loads(results["documents"][0])
                print(f'🔥 USER_PREFERENCES_SERVICE: Parsed preferences: {preferences}')
                return preferences
            except json.JSONDecodeError as e:
                print(f'🔥 USER_PREFERENCES_SERVICE: JSON decode error: {e}')
                return None
        else:
            print(f'🔥 USER_PREFERENCES_SERVICE: No documents found for user_id: {user_id}')
        
        return None 