#!/usr/bin/env python3
"""
Script to manually verify a test user for development testing
"""

import chromadb
import json
import os

def verify_test_user(email="test2@example.com"):
    """Manually verify a test user"""
    try:
        # Initialize ChromaDB
        chroma_path = os.path.abspath("./chroma_db")
        client = chromadb.PersistentClient(path=chroma_path)
        users_collection = client.get_or_create_collection("users")
        
        # Find user by email
        results = users_collection.get(
            where={"email": email},
            include=['documents', 'metadatas']
        )
        
        if not results['documents']:
            print(f"❌ User with email {email} not found")
            return False
        
        user_data = json.loads(results['documents'][0])
        user_metadata = results['metadatas'][0]
        
        print(f"🔍 Found user: {user_data.get('full_name', 'Unknown')} ({email})")
        print(f"   Current verification status: {user_data.get('is_verified', False)}")
        
        # Update user verification status
        user_data['is_verified'] = True
        user_metadata['is_verified'] = True
        
        # Update user in ChromaDB
        users_collection.upsert(
            documents=[json.dumps(user_data)],
            metadatas=[user_metadata],
            ids=[user_data['user_id']]
        )
        
        print(f"✅ User {email} has been manually verified!")
        print(f"   User ID: {user_data['user_id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to verify user: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Manually verifying test user...")
    verify_test_user()
