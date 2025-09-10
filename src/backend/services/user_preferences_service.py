import chromadb
import json

class UserPreferencesService:
    def __init__(self):
        # Use the new ChromaDB client configuration with absolute path
        import os
        chroma_path = os.environ.get('CHROMA_DB_PATH', './chroma_db')
        
        # For Railway/Render deployment, use persistent volume
        if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RENDER_ENVIRONMENT'):
            chroma_path = os.environ.get('CHROMA_DB_PATH', '/app/data/chroma_db')
        
        chroma_path = os.path.abspath(chroma_path)
        try:
            os.makedirs(chroma_path, exist_ok=True)
        except PermissionError:
            # Directory might already exist with correct permissions
            if not os.path.exists(chroma_path):
                raise PermissionError(f"Cannot create ChromaDB directory at {chroma_path}. Please ensure the directory exists and has correct permissions.")
        self.client = chromadb.PersistentClient(path=chroma_path)
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