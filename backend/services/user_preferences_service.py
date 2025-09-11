import json

# Try to import ChromaDB, fallback to in-memory storage if not available
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("Warning: ChromaDB not available, using fallback in-memory storage for user preferences")

class UserPreferencesService:
    def __init__(self):
        if not CHROMADB_AVAILABLE:
            # Use fallback in-memory storage
            self.preferences = {}  # In-memory storage
            self.collection = self  # Mock collection interface
            print("Using fallback in-memory user preferences storage")
            return
            
        # Use the new ChromaDB client configuration with absolute path
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
                # Try to use a fallback local directory
                chroma_path = './chroma_db'
                os.makedirs(chroma_path, exist_ok=True)
                print(f"⚠️ Using fallback ChromaDB directory: {chroma_path}")
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_or_create_collection("user_preferences")

    def save_preferences(self, user_id: str, preferences: dict):
        if not CHROMADB_AVAILABLE:
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
        if not CHROMADB_AVAILABLE:
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