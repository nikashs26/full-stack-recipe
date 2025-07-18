import chromadb
import json
import hashlib

class UserService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection("users")

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, email: str, password: str) -> bool:
        # Check if user already exists
        existing = self.collection.get(ids=[email], include=["documents"])
        if existing and existing["documents"] and existing["documents"][0]:
            return False  # User already exists
        user_doc = json.dumps({"email": email, "password": self.hash_password(password)})
        self.collection.upsert(ids=[email], documents=[user_doc])
        return True

    def authenticate(self, email: str, password: str) -> bool:
        user = self.collection.get(ids=[email], include=["documents"])
        if user and user["documents"] and user["documents"][0]:
            user_data = json.loads(user["documents"][0])
            return user_data["password"] == self.hash_password(password)
        return False

    def get_user(self, email: str):
        user = self.collection.get(ids=[email], include=["documents"])
        if user and user["documents"] and user["documents"][0]:
            return json.loads(user["documents"][0])
        return None
