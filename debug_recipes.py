from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "recipes_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "recipes")

client = MongoClient(MONGO_URI)
collection = client[DB_NAME][COLLECTION_NAME]

count = collection.count_documents({})
print(f"Total recipes in collection: {count}")

for recipe in collection.find({}, {"title": 1, "cuisine": 1}).limit(10):
    print(recipe)