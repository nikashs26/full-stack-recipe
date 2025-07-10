import chromadb
from chromadb.config import Settings

class UserPreferencesService:
    def __init__(self):
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./chroma_db" # Ensure this matches your existing ChromaDB path
        ))
        self.collection = self.client.get_or_create_collection("user_preferences")

    def save_preferences(self, user_id: str, preferences: dict):
        # Store preferences as a document in ChromaDB
        # Each user has one preferences document, so we can upsert
        self.collection.upsert(
            documents=[str(preferences)], # Storing preferences as string for simplicity, or use a better embedding if needed
            metadatas=[{"user_id": user_id, **preferences}], # Store individual preferences as metadata for querying
            ids=[user_id] # Use user_id as the unique ID for their preferences document
        )

    def get_preferences(self, user_id: str):
        results = self.collection.get(
            ids=[user_id],
            include=['metadatas']
        )
        if results and results["metadatas"]:
            # Return the stored preferences from metadata
            # Exclude user_id from the returned dict if it's already implicitly available
            prefs = results["metadatas"][0]
            prefs.pop("user_id", None)
            return prefs
        return None 