#!/usr/bin/env python3
"""
Simple ChromaDB Preferences Demo App

This demonstrates the complete flow you asked about:
1. Store user preferences in ChromaDB
2. Retrieve preferences from ChromaDB
3. Use preferences for meal planning
4. Display results to user

No authentication required - works immediately!
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
import chromadb
import json
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configure session
app.config['SECRET_KEY'] = 'demo-secret-key'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

# Initialize ChromaDB
client = chromadb.PersistentClient(path="./simple_demo_chroma_db")
preferences_collection = client.get_or_create_collection(
    name="user_preferences_simple",
    metadata={"description": "Simple user preferences demo"}
)

@app.route('/api/preferences', methods=['POST'])
def save_preferences():
    """
    Save user preferences to ChromaDB
    This is STEP 1: Data Storage
    """
    try:
        preferences_data = request.get_json()
        if not preferences_data:
            return jsonify({"error": "No preferences provided"}), 400
        
        # Get or create session user ID
        if 'user_id' not in session:
            session['user_id'] = f"user_{str(uuid.uuid4())[:8]}"
        
        user_id = session['user_id']
        
        # Convert lists to JSON strings for ChromaDB metadata
        metadata = {
            "user_id": user_id,
            "dietaryRestrictions": json.dumps(preferences_data.get("dietaryRestrictions", [])),
            "favoriteCuisines": json.dumps(preferences_data.get("favoriteCuisines", [])),
            "cookingSkillLevel": preferences_data.get("cookingSkillLevel", "beginner"),
            "healthGoals": json.dumps(preferences_data.get("healthGoals", [])),
            "stored_at": datetime.now().isoformat()
        }
        
        # STORE in ChromaDB
        preferences_collection.upsert(
            documents=[json.dumps(preferences_data)],
            metadatas=[metadata],
            ids=[user_id]
        )
        
        return jsonify({
            "success": True,
            "message": "Preferences saved to ChromaDB successfully!",
            "user_id": user_id,
            "preferences": preferences_data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/preferences', methods=['GET'])
def get_preferences():
    """
    Get user preferences from ChromaDB
    This is STEP 2: Data Retrieval
    """
    try:
        if 'user_id' not in session:
            return jsonify({
                "success": False,
                "message": "No preferences found. Please set preferences first."
            }), 200
        
        user_id = session['user_id']
        
        # RETRIEVE from ChromaDB
        results = preferences_collection.get(
            ids=[user_id],
            include=['metadatas', 'documents']
        )
        
        if not results['metadatas']:
            return jsonify({
                "success": False,
                "message": "No preferences found for this user."
            }), 200
        
        # Parse the stored preferences
        metadata = results['metadatas'][0]
        preferences = {
            "dietaryRestrictions": json.loads(metadata.get('dietaryRestrictions', '[]')),
            "favoriteCuisines": json.loads(metadata.get('favoriteCuisines', '[]')),
            "cookingSkillLevel": metadata.get('cookingSkillLevel', 'beginner'),
            "healthGoals": json.loads(metadata.get('healthGoals', '[]')),
            "stored_at": metadata.get('stored_at')
        }
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "preferences": preferences
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/meal-plan', methods=['POST'])
def generate_meal_plan():
    """
    Generate meal plan using ChromaDB-stored preferences
    This is STEP 3: Using Retrieved Data
    """
    try:
        if 'user_id' not in session:
            return jsonify({
                "error": "No user session found. Please set preferences first."
            }), 400
        
        user_id = session['user_id']
        
        # RETRIEVE preferences from ChromaDB
        results = preferences_collection.get(
            ids=[user_id],
            include=['metadatas']
        )
        
        if not results['metadatas']:
            return jsonify({
                "error": "No preferences found. Please set preferences first."
            }), 400
        
        # Parse preferences
        metadata = results['metadatas'][0]
        preferences = {
            "dietaryRestrictions": json.loads(metadata.get('dietaryRestrictions', '[]')),
            "favoriteCuisines": json.loads(metadata.get('favoriteCuisines', '[]')),
            "cookingSkillLevel": metadata.get('cookingSkillLevel', 'beginner'),
            "healthGoals": json.loads(metadata.get('healthGoals', '[]'))
        }
        
        # Generate meal plan based on preferences
        meal_plan = generate_personalized_meal_plan(preferences)
        
        return jsonify({
            "success": True,
            "meal_plan": meal_plan,
            "preferences_used": preferences,
            "user_id": user_id,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_personalized_meal_plan(preferences):
    """
    Generate a personalized meal plan based on ChromaDB-retrieved preferences
    This shows how the retrieved data is USED
    """
    
    # Base meal templates
    meal_templates = {
        "Mediterranean": {
            "breakfast": "Greek Yogurt with Honey and Nuts",
            "lunch": "Mediterranean Quinoa Bowl",
            "dinner": "Grilled Fish with Vegetables"
        },
        "Asian": {
            "breakfast": "Miso Soup with Tofu",
            "lunch": "Asian Stir Fry Bowl",
            "dinner": "Teriyaki Salmon with Rice"
        },
        "Italian": {
            "breakfast": "Avocado Toast with Tomatoes",
            "lunch": "Caprese Salad with Pasta",
            "dinner": "Pasta Primavera"
        }
    }
    
    # Apply dietary restrictions
    dietary_restrictions = preferences.get("dietaryRestrictions", [])
    favorite_cuisines = preferences.get("favoriteCuisines", ["Mediterranean"])
    skill_level = preferences.get("cookingSkillLevel", "beginner")
    
    # Select cuisine based on preferences
    selected_cuisine = favorite_cuisines[0] if favorite_cuisines else "Mediterranean"
    if selected_cuisine not in meal_templates:
        selected_cuisine = "Mediterranean"
    
    meals = meal_templates[selected_cuisine]
    
    # Modify meals based on dietary restrictions
    if "vegetarian" in dietary_restrictions:
        meals = {
            "breakfast": "Vegetarian " + meals["breakfast"],
            "lunch": "Vegetarian " + meals["lunch"],
            "dinner": "Vegetarian " + meals["dinner"].replace("Fish", "Eggplant").replace("Salmon", "Tofu")
        }
    
    if "vegan" in dietary_restrictions:
        meals = {
            "breakfast": "Vegan " + meals["breakfast"].replace("Yogurt", "Coconut Yogurt"),
            "lunch": "Vegan " + meals["lunch"],
            "dinner": "Vegan " + meals["dinner"]
        }
    
    # Create weekly plan
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekly_plan = {}
    
    for day in days:
        weekly_plan[day.lower()] = {
            "breakfast": {
                "name": meals["breakfast"],
                "cuisine": selected_cuisine,
                "difficulty": skill_level,
                "dietary_notes": f"Matches your {', '.join(dietary_restrictions)} preferences" if dietary_restrictions else "Standard recipe"
            },
            "lunch": {
                "name": meals["lunch"],
                "cuisine": selected_cuisine,
                "difficulty": skill_level,
                "dietary_notes": f"Matches your {', '.join(dietary_restrictions)} preferences" if dietary_restrictions else "Standard recipe"
            },
            "dinner": {
                "name": meals["dinner"],
                "cuisine": selected_cuisine,
                "difficulty": skill_level,
                "dietary_notes": f"Matches your {', '.join(dietary_restrictions)} preferences" if dietary_restrictions else "Standard recipe"
            }
        }
    
    return weekly_plan

@app.route('/api/demo-setup', methods=['POST'])
def setup_demo():
    """
    Quick setup for demo purposes
    """
    try:
        # Create demo preferences
        demo_preferences = {
            "dietaryRestrictions": ["vegetarian"],
            "favoriteCuisines": ["Mediterranean", "Asian"],
            "cookingSkillLevel": "intermediate",
            "healthGoals": ["weight loss", "general wellness"]
        }
        
        # Create session
        session['user_id'] = "demo_user"
        
        # Store in ChromaDB
        metadata = {
            "user_id": "demo_user",
            "dietaryRestrictions": json.dumps(demo_preferences["dietaryRestrictions"]),
            "favoriteCuisines": json.dumps(demo_preferences["favoriteCuisines"]),
            "cookingSkillLevel": demo_preferences["cookingSkillLevel"],
            "healthGoals": json.dumps(demo_preferences["healthGoals"]),
            "stored_at": datetime.now().isoformat()
        }
        
        preferences_collection.upsert(
            documents=[json.dumps(demo_preferences)],
            metadatas=[metadata],
            ids=["demo_user"]
        )
        
        return jsonify({
            "success": True,
            "message": "Demo setup complete! Preferences stored in ChromaDB.",
            "user_id": "demo_user",
            "preferences": demo_preferences
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def status():
    """
    Check app status and ChromaDB connection
    """
    try:
        # Test ChromaDB connection
        collections = client.list_collections()
        
        return jsonify({
            "status": "running",
            "chromadb_connected": True,
            "collections": [col.name for col in collections],
            "session_user": session.get('user_id', 'None')
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "chromadb_connected": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Simple ChromaDB Preferences Demo App")
    print("=" * 50)
    print("This app demonstrates the complete ChromaDB data flow:")
    print("1. 💾 Store preferences in ChromaDB")
    print("2. 🔍 Retrieve preferences from ChromaDB")
    print("3. 🍽️ Generate meal plan using retrieved data")
    print("4. 📱 Display results to user")
    print("")
    print("🌐 Available endpoints:")
    print("  • POST /api/demo-setup - Quick demo setup")
    print("  • POST /api/preferences - Save preferences")
    print("  • GET /api/preferences - Get preferences")
    print("  • POST /api/meal-plan - Generate meal plan")
    print("  • GET /api/status - Check status")
    print("")
    print("🧪 Test commands:")
    print("  curl -X POST http://localhost:5002/api/demo-setup")
    print("  curl http://localhost:5002/api/preferences")
    print("  curl -X POST http://localhost:5002/api/meal-plan")
    print("")
    
    app.run(debug=True, port=5002) 