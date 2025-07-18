import json
import hashlib
import chromadb

USERS_JSON = "users.json"
CHROMA_DB_PATH = "./chroma_db"

# Load users from users.json
with open(USERS_JSON, "r") as f:
    users = json.load(f)

# Connect to ChromaDB
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_or_create_collection("users")

for email, data in users.items():
    password = data["password"]
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    user_doc = json.dumps({"email": email, "password": hashed_password})
    collection.upsert(ids=[email], documents=[user_doc])
    print(f"✅ Migrated user: {email}")

print("All users from users.json migrated to ChromaDB!")
