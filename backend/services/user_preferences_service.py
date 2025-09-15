import json

# Import ChromaDB singleton to prevent multiple instances
from utils.chromadb_singleton import get_chromadb_client

class UserPreferencesService:
    _instance = None
    _collection = None
    _embedding_function = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserPreferencesService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        # Use the singleton ChromaDB client and lightweight embeddings
        from utils.lightweight_embeddings import get_lightweight_embedding_function
        self.client = get_chromadb_client()
        
        if self.client is None:
            print("⚠️ ChromaDB client is None, using in-memory fallback")
            self.collection = None
            self.preferences = {}  # In-memory fallback
            return
            
        try:
            # Cache the embedding function to avoid recreating it
            if UserPreferencesService._embedding_function is None:
                UserPreferencesService._embedding_function = get_lightweight_embedding_function(use_token_based=True)
            
            self.embedding_function = UserPreferencesService._embedding_function
            
            # Cache the collection to avoid recreating it
            if UserPreferencesService._collection is None:
                UserPreferencesService._collection = self.client.get_or_create_collection(
                    "user_preferences",
                    embedding_function=self.embedding_function
                )
            
            self.collection = UserPreferencesService._collection
        except Exception as e:
            print(f"⚠️ Failed to create user preferences collection: {e}")
            self.collection = None
            self.preferences = {}  # In-memory fallback

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
            
        try:
            results = self.collection.get(
                ids=[user_id],
                include=['documents']
            )
            
            if results and results["documents"]:
                # Parse the JSON string back to dict
                preferences = json.loads(results["documents"][0])
                return preferences
            else:
                return None
        except Exception as e:
            print(f'⚠️ Error getting preferences for user {user_id}: {e}')
            return None 