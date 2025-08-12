import chromadb
import json

def check_nutrition_data():
    """Check what nutrition data is currently stored in recipes"""
    
    print("🔍 Checking current nutrition data in recipes...")
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    recipe_collection = client.get_collection("recipe_details_cache")
    
    # Get a few recipes
    results = recipe_collection.get(limit=5, include=['documents', 'metadatas'])
    
    for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
        print(f"\n🍽️  Recipe {i+1}: {meta.get('title', 'Unknown')}")
        print(f"   Metadata calories: {meta.get('calories', 'NO DATA')}")
        print(f"   Metadata protein: {meta.get('protein', 'NO DATA')}")
        
        # Check document content
        if doc and doc.strip():
            try:
                recipe_doc = json.loads(doc)
                print(f"   Document calories: {recipe_doc.get('calories', 'NO DATA')}")
                print(f"   Document protein: {recipe_doc.get('protein', 'NO DATA')}")
                print(f"   Has nutrition field: {'nutrition' in recipe_doc}")
                if 'nutrition' in recipe_doc:
                    print(f"   Nutrition field: {recipe_doc['nutrition']}")
            except:
                print(f"   Document: {doc[:100]}...")
        else:
            print("   No document content")

if __name__ == "__main__":
    check_nutrition_data() 