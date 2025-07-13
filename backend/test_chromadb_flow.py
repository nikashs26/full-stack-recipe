#!/usr/bin/env python3
"""
Simple ChromaDB Data Flow Demo

This demonstrates exactly how data flows:
1. Store data in ChromaDB
2. Retrieve data from ChromaDB  
3. Display to user

This is the core concept you asked about!
"""

import chromadb
import json
from datetime import datetime

def demonstrate_chromadb_flow():
    """
    Complete demonstration of ChromaDB data flow:
    Storage → Retrieval → Display
    """
    
    print("🔮 ChromaDB Data Flow Demonstration")
    print("=" * 50)
    
    # 1. INITIALIZE ChromaDB
    print("\n1. 📊 Initializing ChromaDB...")
    client = chromadb.PersistentClient(path="./demo_chroma_db")
    
    # Create a collection for user preferences
    preferences_collection = client.get_or_create_collection(
        name="user_preferences_demo",
        metadata={"description": "Demo user preferences"}
    )
    
    # Create a collection for recipes
    recipes_collection = client.get_or_create_collection(
        name="recipes_demo", 
        metadata={"description": "Demo recipe collection"}
    )
    
    print("✅ ChromaDB initialized successfully!")
    
    # 2. STORE DATA in ChromaDB
    print("\n2. 💾 Storing data in ChromaDB...")
    
    # Store user preferences
    user_preferences = {
        "dietaryRestrictions": ["vegetarian"],
        "favoriteCuisines": ["Mediterranean", "Asian"],
        "cookingSkillLevel": "intermediate",
        "healthGoals": ["weight loss"]
    }
    
    # Convert lists to JSON strings for metadata
    metadata = {
        "user_id": "demo_user",
        "dietaryRestrictions": json.dumps(user_preferences["dietaryRestrictions"]),
        "favoriteCuisines": json.dumps(user_preferences["favoriteCuisines"]),
        "cookingSkillLevel": user_preferences["cookingSkillLevel"],
        "healthGoals": json.dumps(user_preferences["healthGoals"])
    }
    
    preferences_collection.upsert(
        documents=[json.dumps(user_preferences)],
        metadatas=[metadata],
        ids=["demo_user"]
    )
    
    # Store some recipes
    recipes = [
        {
            "id": "recipe_1",
            "name": "Mediterranean Quinoa Bowl",
            "cuisine": "Mediterranean",
            "ingredients": ["quinoa", "chickpeas", "cucumber", "feta"],
            "description": "Healthy Mediterranean bowl with quinoa, fresh vegetables, and feta cheese"
        },
        {
            "id": "recipe_2", 
            "name": "Asian Stir Fry",
            "cuisine": "Asian",
            "ingredients": ["tofu", "broccoli", "soy sauce", "ginger"],
            "description": "Quick and healthy Asian stir fry with tofu and fresh vegetables"
        },
        {
            "id": "recipe_3",
            "name": "Italian Pasta Salad",
            "cuisine": "Italian", 
            "ingredients": ["pasta", "tomatoes", "mozzarella", "basil"],
            "description": "Fresh Italian pasta salad with tomatoes, mozzarella, and basil"
        }
    ]
    
    for recipe in recipes:
        # Convert lists to JSON strings for metadata
        recipe_metadata = {
            "id": recipe["id"],
            "name": recipe["name"],
            "cuisine": recipe["cuisine"],
            "ingredients": json.dumps(recipe["ingredients"])
        }
        
        recipes_collection.upsert(
            documents=[recipe["description"]],
            metadatas=[recipe_metadata],
            ids=[recipe["id"]]
        )
    
    print("✅ Data stored successfully!")
    print(f"   • User preferences for 'demo_user'")
    print(f"   • {len(recipes)} recipes with descriptions")
    
    # 3. RETRIEVE DATA from ChromaDB
    print("\n3. 🔍 Retrieving data from ChromaDB...")
    
    # Get user preferences
    user_prefs_result = preferences_collection.get(
        ids=["demo_user"],
        include=['metadatas']
    )
    
    if user_prefs_result['metadatas']:
        retrieved_preferences = user_prefs_result['metadatas'][0]
        print("✅ Retrieved user preferences:")
        # Parse JSON strings back to lists
        dietary = json.loads(retrieved_preferences.get('dietaryRestrictions', '[]'))
        cuisines = json.loads(retrieved_preferences.get('favoriteCuisines', '[]'))
        print(f"   • Dietary: {dietary}")
        print(f"   • Cuisines: {cuisines}")
        print(f"   • Skill Level: {retrieved_preferences.get('cookingSkillLevel', 'N/A')}")
    
    # Semantic search for recipes based on preferences
    favorite_cuisines = json.loads(retrieved_preferences.get('favoriteCuisines', '[]'))
    search_query = f"healthy {' '.join(favorite_cuisines)} vegetarian recipe"
    
    recipe_results = recipes_collection.query(
        query_texts=[search_query],
        n_results=3,
        include=['documents', 'metadatas', 'distances']
    )
    
    print(f"\n🔍 Semantic search for: '{search_query}'")
    print("✅ Found matching recipes:")
    
    # 4. DISPLAY DATA to user (this is what your frontend would see)
    print("\n4. 📱 Displaying results to user...")
    print("=" * 30)
    
    if recipe_results['metadatas']:
        for i, metadata in enumerate(recipe_results['metadatas'][0]):
            similarity = 1 - recipe_results['distances'][0][i]  # Convert distance to similarity
            ingredients = json.loads(metadata['ingredients'])
            print(f"\n🍽️  Recipe {i+1}: {metadata['name']}")
            print(f"   Cuisine: {metadata['cuisine']}")
            print(f"   Ingredients: {', '.join(ingredients)}")
            print(f"   Match Score: {similarity:.2f}")
            print(f"   Description: {recipe_results['documents'][0][i]}")
    
    # 5. DEMONSTRATE LEARNING (storing user interaction)
    print("\n5. 🧠 Storing user interaction (learning)...")
    
    # User liked recipe_1
    interaction_collection = client.get_or_create_collection(
        name="user_interactions_demo",
        metadata={"description": "User interactions for learning"}
    )
    
    interaction_collection.add(
        documents=[f"User demo_user liked recipe {recipes[0]['name']}"],
        metadatas=[{
            "user_id": "demo_user",
            "recipe_id": "recipe_1",
            "action": "liked",
            "timestamp": datetime.now().isoformat(),
            "cuisine": recipes[0]["cuisine"]
        }],
        ids=[f"interaction_{datetime.now().timestamp()}"]
    )
    
    print("✅ User interaction stored!")
    print("   • This data can be used to improve future recommendations")
    
    # 6. SHOW THE COMPLETE FLOW
    print("\n6. 🎯 Complete Data Flow Summary:")
    print("=" * 40)
    print("1. 💾 STORE: User preferences → ChromaDB")
    print("2. 💾 STORE: Recipe data → ChromaDB") 
    print("3. 🔍 RETRIEVE: Search based on preferences → ChromaDB")
    print("4. 📱 DISPLAY: Show results to user")
    print("5. 🧠 LEARN: Store user interactions → ChromaDB")
    print("6. 🔄 REPEAT: Use learned data for better recommendations")
    
    print("\n✨ This is exactly how your recipe app uses ChromaDB!")
    print("   The data flows from storage → retrieval → user display")
    
    return True

if __name__ == "__main__":
    try:
        demonstrate_chromadb_flow()
        print("\n🎉 ChromaDB data flow demonstration completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc() 