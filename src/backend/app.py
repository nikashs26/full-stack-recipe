from dotenv import load_dotenv
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os
import json
import time
import sys
import socket
from bson import ObjectId
import dns.resolver
from datetime import datetime

# Print Python version and path for debugging
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Load environment variables from .env file
load_dotenv('../info.env')

# Get MongoDB URI from environment variables
MONGO_URI = os.getenv("MONGO_URI")
MONGO_CONNECT_TIMEOUT_MS = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "5000"))
MONGO_RETRY_COUNT = int(os.getenv("MONGO_RETRY_COUNT", "3"))

if not MONGO_URI:
    print("No MongoDB URI found in environment variables")
    print("Please update the info.env file with your MongoDB URI")
else:
    print(f"Using MongoDB URI from environment variables: {MONGO_URI[:20]}...")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Spoonacular API Key
SPOONACULAR_API_KEY = "01f12ed117584307b5cba262f43a8d49"
SPOONACULAR_URL = "https://api.spoonacular.com/recipes/complexSearch"

# MongoDB Atlas setup
in_memory_recipes = []
mongo_available = False
mongo_client = None
recipes_collection = None
folders_collection = None

# Function to perform DNS lookup for MongoDB hostname
def check_mongodb_dns(uri):
    if not uri or not isinstance(uri, str):
        return {"success": False, "message": "Invalid URI"}
    
    try:
        # Extract hostname from MongoDB URI
        if uri.startswith("mongodb://"):
            # Format: mongodb://hostname:port/dbname
            parts = uri.replace("mongodb://", "").split("/")[0].split(":")
            hostname = parts[0]
        elif uri.startswith("mongodb+srv://"):
            # Format: mongodb+srv://username:password@hostname/dbname
            parts = uri.replace("mongodb+srv://", "").split("@")
            if len(parts) > 1:
                hostname = parts[1].split("/")[0]
            else:
                hostname = parts[0].split("/")[0]
        else:
            return {"success": False, "message": f"Unrecognized MongoDB URI format: {uri[:10]}..."}
        
        print(f"Checking DNS for MongoDB hostname: {hostname}")
        
        # Try basic hostname resolution
        ip_address = socket.gethostbyname(hostname)
        print(f"Resolved {hostname} to IP: {ip_address}")
        
        # Try SRV record for mongodb+srv URIs
        if uri.startswith("mongodb+srv://"):
            try:
                srv_records = dns.resolver.resolve(f"_mongodb._tcp.{hostname}", "SRV")
                print(f"Found {len(srv_records)} SRV records for {hostname}")
                for record in srv_records:
                    print(f"  SRV record: {record.target} (port: {record.port}, priority: {record.priority})")
                return {"success": True, "message": f"DNS resolution successful for {hostname}", "ip": ip_address, "srv_count": len(srv_records)}
            except Exception as dns_err:
                print(f"SRV record lookup failed: {dns_err}")
                return {"success": False, "message": f"SRV record lookup failed: {dns_err}", "ip": ip_address}
        
        return {"success": True, "message": f"DNS resolution successful for {hostname}", "ip": ip_address}
    except socket.gaierror as e:
        return {"success": False, "message": f"DNS resolution failed: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Error checking DNS: {e}"}

# Check MongoDB connection
try:
    if not MONGO_URI:
        raise Exception("No MongoDB URI provided")
    
    # First check DNS resolution
    dns_check = check_mongodb_dns(MONGO_URI)
    if not dns_check["success"]:
        print(f"Warning: DNS check failed: {dns_check['message']}")
        print("This may cause MongoDB connection issues")
    else:
        print(f"DNS check successful: {dns_check['message']}")
    
    # Try to import pymongo or handle the import error gracefully
    try:
        import pymongo
        print("Successfully imported pymongo")
    except ImportError:
        print("Error importing pymongo. This likely means pymongo is not installed.")
        print("Trying to install pymongo now...")
        import subprocess
        try:
            # Try to install pymongo using pip
            result = subprocess.run([sys.executable, "-m", "pip", "install", "pymongo[srv]", "dnspython"], 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"pip install pymongo output: {result.stdout.decode()}")
            if result.stderr:
                print(f"pip install pymongo errors: {result.stderr.decode()}")
            
            # Try importing again after installation
            import pymongo
            print("Successfully imported pymongo after installation")
        except Exception as e:
            print(f"Failed to install pymongo: {e}")
            raise Exception(f"Could not import or install pymongo: {e}")

    # Connect to MongoDB with retry logic
    connect_attempts = 0
    while connect_attempts < MONGO_RETRY_COUNT:
        try:
            print(f"Attempting to connect to MongoDB (attempt {connect_attempts + 1})...")
            # Set shorter serverSelectionTimeoutMS to fail faster if MongoDB is unavailable
            mongo_client = pymongo.MongoClient(
                MONGO_URI, 
                serverSelectionTimeoutMS=MONGO_CONNECT_TIMEOUT_MS,
                connectTimeoutMS=MONGO_CONNECT_TIMEOUT_MS,
                socketTimeoutMS=MONGO_CONNECT_TIMEOUT_MS * 2
            )
            
            # Test connection with server_info
            print("Testing MongoDB connection...")
            mongo_client.server_info()
            
            # If we get here, connection is successful
            print("MongoDB connection successful!")
            
            # Determine database name from URI or use default
            db_name = "nikash"  # Default
            if "/" in MONGO_URI:
                uri_parts = MONGO_URI.split("/")
                if len(uri_parts) > 3:  # mongodb://host:port/dbname
                    potential_db = uri_parts[3].split("?")[0]
                    if potential_db:
                        db_name = potential_db
                        print(f"Using database name from URI: {db_name}")
                elif len(uri_parts) > 1 and uri_parts[-1]:  # mongodb+srv://...@host/dbname
                    potential_db = uri_parts[-1].split("?")[0]
                    if potential_db:
                        db_name = potential_db
                        print(f"Using database name from URI: {db_name}")
                        
            # Use detected database name
            print(f"Using '{db_name}' database")
            db = mongo_client[db_name]
            recipes_collection = db["Recipes"]
            folders_collection = db["Folders"]
            
            # Create indexes for better search performance
            recipes_collection.create_index([("title", pymongo.TEXT)])
            recipes_collection.create_index([("id", pymongo.ASCENDING)])
            
            # Count documents to verify connection
            recipe_count = recipes_collection.count_documents({})
            print(f"MongoDB connection successful. Found {recipe_count} recipes in database")
            mongo_available = True
            break
            
        except Exception as e:
            connect_attempts += 1
            print(f"MongoDB connection attempt {connect_attempts} failed: {e}")
            
            if connect_attempts < MONGO_RETRY_COUNT:
                wait_time = 2 * connect_attempts  # Progressive backoff
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"All {MONGO_RETRY_COUNT} connection attempts failed")
    
    # If connection successful, add seed data if needed
    if mongo_available and recipes_collection:
        # Count documents to verify connection
        recipe_count = recipes_collection.count_documents({})
        
        # Add some test recipes if the collection is empty
        if recipe_count == 0:
            print("Adding test recipes to MongoDB...")
            # Import initialRecipes directly from a Python dictionary
            initialRecipes = [
                {
                    "id": "1",
                    "name": "Vegetable Stir Fry",
                    "title": "Vegetable Stir Fry",
                    "cuisine": "Asian",
                    "cuisines": ["Asian"],
                    "dietaryRestrictions": ["vegetarian", "vegan"],
                    "diets": ["vegetarian", "vegan"],
                    "ingredients": ["broccoli", "carrots", "bell peppers", "soy sauce", "ginger", "garlic"],
                    "instructions": ["Chop all vegetables", "Heat oil in a wok", "Add vegetables and stir fry for 5 minutes", "Add sauce and cook for 2 more minutes"],
                    "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
                    "ratings": [4, 5, 5]
                },
                {
                    "id": "2",
                    "name": "Chicken Parmesan",
                    "title": "Chicken Parmesan",
                    "cuisine": "Italian",
                    "cuisines": ["Italian"],
                    "dietaryRestrictions": ["carnivore"],
                    "diets": ["carnivore"],
                    "ingredients": ["chicken breast", "breadcrumbs", "parmesan cheese", "mozzarella cheese", "tomato sauce", "pasta"],
                    "instructions": ["Bread the chicken", "Fry until golden", "Top with sauce and cheese", "Bake until cheese melts", "Serve with pasta"],
                    "image": "https://images.unsplash.com/photo-1515516089376-88db1e26e9c0?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
                    "ratings": [5, 4, 4, 5]
                },
                {
                    "id": "3",
                    "name": "Beef Tacos",
                    "title": "Beef Tacos",
                    "cuisine": "Mexican",
                    "cuisines": ["Mexican"],
                    "dietaryRestrictions": ["carnivore"],
                    "diets": ["carnivore"],
                    "ingredients": ["ground beef", "taco shells", "lettuce", "tomato", "cheese", "sour cream", "taco seasoning"],
                    "instructions": ["Brown the beef", "Add taco seasoning", "Warm the taco shells", "Assemble with toppings"],
                    "image": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
                    "ratings": [4, 5, 3]
                },
                {
                    "id": "4",
                    "name": "Quinoa Stuffed Bell Peppers",
                    "title": "Quinoa Stuffed Bell Peppers",
                    "cuisine": "Mediterranean",
                    "cuisines": ["Mediterranean"],
                    "dietaryRestrictions": ["vegetarian", "gluten-free"],
                    "diets": ["vegetarian", "gluten-free"],
                    "ingredients": ["bell peppers", "quinoa", "black beans", "corn", "tomatoes", "cumin", "chili powder"],
                    "instructions": ["Cook quinoa", "Mix with beans, corn, and spices", "Stuff bell peppers", "Bake for 25 minutes"],
                    "image": "https://via.placeholder.com/400x300",
                    "ratings": [4, 4, 4, 5]
                },
                {
                    "id": "5",
                    "name": "Lentil Shepherd's Pie",
                    "title": "Lentil Shepherd's Pie",
                    "cuisine": "British",
                    "cuisines": ["British"],
                    "dietaryRestrictions": ["vegetarian", "vegan"],
                    "diets": ["vegetarian", "vegan"],
                    "ingredients": ["lentils", "carrots", "peas", "potatoes", "plant milk", "vegetable broth"],
                    "instructions": ["Cook lentils with vegetables", "Make mashed potatoes with plant milk", "Layer lentil mixture on the bottom of a dish", "Top with mashed potatoes", "Bake until golden"],
                    "image": "https://via.placeholder.com/400x300",
                    "ratings": [5, 4, 5]
                },
                {
                    "id": "6",
                    "name": "Tiramisu",
                    "title": "Tiramisu",
                    "cuisine": "Italian",
                    "cuisines": ["Italian"],
                    "dietaryRestrictions": ["vegetarian"],
                    "diets": ["vegetarian"],
                    "ingredients": ["ladyfingers", "espresso", "mascarpone cheese", "eggs", "sugar", "cocoa powder"],
                    "instructions": ["Mix mascarpone, egg yolks, and sugar", "Whip egg whites and fold into mixture", "Dip ladyfingers in espresso", "Layer ladyfingers and cream", "Dust with cocoa powder"],
                    "image": "https://via.placeholder.com/400x300",
                    "ratings": [5, 5, 5, 4]
                },
                {
                    "id": "7",
                    "name": "Vegan Apple Crisp",
                    "title": "Vegan Apple Crisp",
                    "cuisine": "American",
                    "cuisines": ["American"],
                    "dietaryRestrictions": ["vegetarian", "vegan"],
                    "diets": ["vegetarian", "vegan"],
                    "ingredients": ["apples", "oats", "brown sugar", "cinnamon", "plant butter", "lemon juice"],
                    "instructions": ["Slice apples and toss with lemon juice", "Mix oats, sugar, cinnamon, and butter", "Place apples in dish and top with oat mixture", "Bake until golden and bubbly"],
                    "image": "https://via.placeholder.com/400x300",
                    "ratings": [4, 4, 3, 5]
                }
            ]
            
            for recipe in initialRecipes:
                try:
                    # Add both name and title to ensure consistent access
                    if "name" in recipe and "title" not in recipe:
                        recipe["title"] = recipe["name"]
                    if "title" in recipe and "name" not in recipe:
                        recipe["name"] = recipe["title"]
                    
                    # Ensure cuisines array exists
                    if "cuisine" in recipe and ("cuisines" not in recipe or not recipe["cuisines"]):
                        recipe["cuisines"] = [recipe["cuisine"]]
                    
                    # Ensure diets array exists
                    if "dietaryRestrictions" in recipe and ("diets" not in recipe or not recipe["diets"]):
                        recipe["diets"] = recipe["dietaryRestrictions"]
                    
                    recipes_collection.insert_one(recipe)
                    print(f"Added test recipe: {recipe.get('title') or recipe.get('name')}")
                except Exception as e:
                    print(f"Error adding test recipe {recipe.get('title') or recipe.get('name')}: {e}")
            print(f"Added {len(initialRecipes)} test recipes to MongoDB")
except Exception as e:
    print(f"MongoDB connection error: {e}")
    print("Using in-memory storage as fallback")

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

@app.route("/get_recipes", methods=["GET"])
def get_recipes():
    start_time = time.time()
    query = request.args.get("query", "").strip()
    ingredient = request.args.get("ingredient", "").strip()
    
    if not query and not ingredient:
        return jsonify({"error": "At least one search parameter is required"}), 400

    # First check if we have recipes in MongoDB that match the query
    db_results = []
    if mongo_available:
        try:
            search_query = {}
            if query:
                search_query["title"] = {"$regex": query, "$options": "i"}
            if ingredient:
                search_query["$or"] = [
                    {"extendedIngredients.name": {"$regex": ingredient, "$options": "i"}},
                    {"ingredients": {"$regex": ingredient, "$options": "i"}}
                ]
            
            print(f"Searching MongoDB with query: {search_query}")
            db_results = list(recipes_collection.find(search_query).limit(10))
            print(f"MongoDB search returned {len(db_results)} results")
            
            if db_results:
                print(f"Found {len(db_results)} recipes in database in {time.time() - start_time:.2f}s")
                return JSONEncoder().encode({"results": db_results})
            else:
                print("No results found in MongoDB, falling back to Spoonacular API")
        except Exception as e:
            print(f"Error querying MongoDB: {e}")
            # Continue to in-memory or API if MongoDB query fails
    else:
        print("MongoDB not available, checking in-memory storage")
    
    # If MongoDB is not available or no results, check in-memory storage
    if not mongo_available:
        results = []
        for recipe in in_memory_recipes:
            if (query and query.lower() in recipe.get("title", "").lower()) or \
               (ingredient and ingredient.lower() in json.dumps(recipe).lower()):
                results.append(recipe)
        if results:
            print(f"Found {len(results)} recipes in in-memory storage")
            return jsonify({"results": results})

    # If no results in DB or in-memory, call the Spoonacular API
    print("No results found locally, calling Spoonacular API")
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "number": 10,  # Limit to 10 results
        "addRecipeInformation": "true",
    }
    
    if query:
        params["query"] = query
    if ingredient:
        params["includeIngredients"] = ingredient

    try:
        # Use a short timeout to avoid hanging
        print(f"Calling Spoonacular API with params: {params}")
        response = requests.get(SPOONACULAR_URL, params=params, timeout=5)
        
        # Check if content type is JSON
        if 'application/json' not in response.headers.get('Content-Type', ''):
            return jsonify({
                "error": f"API returned non-JSON response. Status: {response.status_code}",
                "message": response.text[:100] + "..." # Show part of the response for debugging
            }), 500
            
        response.raise_for_status()  # Raise an error for HTTP failures
        data = response.json()

        if "results" not in data:
            return jsonify({"error": "Invalid response from Spoonacular"}), 500

        # Process the diets for filtering consistency
        for recipe in data["results"]:
            # Normalize diet names for consistent filtering
            if "diets" in recipe:
                normalized_diets = []
                for diet in recipe["diets"]:
                    diet_lower = diet.lower()
                    if "vegetarian" in diet_lower:
                        normalized_diets.append("vegetarian")
                    if "vegan" in diet_lower:
                        normalized_diets.append("vegan")
                    if "gluten" in diet_lower and "free" in diet_lower:
                        normalized_diets.append("gluten-free")
                    if "carnivore" in diet_lower or "meat" in diet_lower:
                        normalized_diets.append("carnivore")
                    # Keep the original diet as well
                    normalized_diets.append(diet)
                recipe["diets"] = normalized_diets

        # Store results in MongoDB for future queries
        api_store_count = 0
        try:
            if mongo_available:
                for recipe in data["results"]:
                    # Ensure recipe has all necessary fields
                    if "title" not in recipe:
                        recipe["title"] = "Untitled Recipe"
                    if "cuisines" not in recipe or not recipe["cuisines"]:
                        recipe["cuisines"] = ["Misc"]
                        
                    # Check if recipe already exists in the database
                    try:
                        # Try with recipe ID as integer
                        existing = recipes_collection.find_one({"id": recipe["id"]})
                    except:
                        # If not an integer, try as string
                        existing = recipes_collection.find_one({"id": str(recipe["id"])})
                        
                    if not existing:
                        # Insert to MongoDB and ensure proper indexing
                        recipes_collection.insert_one(recipe)
                        api_store_count += 1
                print(f"Stored {api_store_count} new recipes in MongoDB Atlas")
            else:
                # Store in in-memory cache if MongoDB not available
                for recipe in data["results"]:
                    if not any(r.get("id") == recipe["id"] for r in in_memory_recipes):
                        in_memory_recipes.append(recipe)
                print(f"Stored {len(data['results'])} recipes in in-memory storage")
        except Exception as e:
            print(f"Error storing recipes: {e}")

        print(f"API request completed in {time.time() - start_time:.2f}s")
        return jsonify(data)  # Send results to frontend

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to Spoonacular API timed out", "results": []}), 504
    except ValueError as e:  # JSON parsing error
        return jsonify({
            "error": "Failed to parse API response as JSON",
            "message": str(e),
            "results": []
        }), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e), "results": []}), 500

@app.route("/get_recipe_by_id", methods=["GET"])
def get_recipe_by_id():
    recipe_id = request.args.get("id")
    if not recipe_id:
        return jsonify({"error": "Recipe ID is required"}), 400
    
    # First check if we have this recipe in MongoDB
    if mongo_available:
        try:
            # Try to find as integer ID (for external recipes)
            try:
                db_recipe = recipes_collection.find_one({"id": int(recipe_id)})
            except ValueError:
                # If not an integer, look for it as a string (for local recipes)
                db_recipe = recipes_collection.find_one({"id": recipe_id})
                
            if db_recipe:
                print(f"Found recipe {recipe_id} in MongoDB database")
                return JSONEncoder().encode(db_recipe)
        except Exception as e:
            print(f"Error querying MongoDB for recipe {recipe_id}: {e}")
    else:
        # Check in-memory storage
        for recipe in in_memory_recipes:
            if str(recipe.get("id")) == str(recipe_id):
                print(f"Found recipe {recipe_id} in in-memory storage")
                return jsonify(recipe)
    
    # If not in storage, call the Spoonacular API
    api_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": SPOONACULAR_API_KEY}
    
    try:
        print(f"Calling Spoonacular API for recipe {recipe_id}")
        response = requests.get(api_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Ensure recipe has all necessary fields
        if "title" not in data:
            data["title"] = "Untitled Recipe"
        if "cuisines" not in data or not data["cuisines"]:
            data["cuisines"] = ["Misc"]
        
        # Normalize diets for consistent filtering
        if "diets" in data:
            normalized_diets = []
            for diet in data["diets"]:
                diet_lower = diet.lower()
                if "vegetarian" in diet_lower:
                    normalized_diets.append("vegetarian")
                if "vegan" in diet_lower:
                    normalized_diets.append("vegan")
                if "gluten" in diet_lower and "free" in diet_lower:
                    normalized_diets.append("gluten-free")
                if "carnivore" in diet_lower or "meat" in diet_lower:
                    normalized_diets.append("carnivore")
                # Keep the original diet as well
                normalized_diets.append(diet)
            data["diets"] = normalized_diets
            
        # Store in MongoDB for future queries
        try:
            if mongo_available:
                existing = recipes_collection.find_one({"id": data["id"]})
                if not existing:
                    recipes_collection.insert_one(data)
                    print(f"Stored recipe {recipe_id} in MongoDB Atlas")
            else:
                # Store in in-memory cache
                if not any(r.get("id") == data["id"] for r in in_memory_recipes):
                    in_memory_recipes.append(data)
                    print(f"Stored recipe {recipe_id} in in-memory storage")
        except Exception as e:
            print(f"Error storing recipe {recipe_id}: {e}")
        
        return jsonify(data)
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to Spoonacular API timed out"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# Endpoints for direct MongoDB CRUD operations
@app.route("/recipes", methods=["GET"])
def get_all_recipes():
    if not mongo_available:
        return jsonify({"error": "MongoDB not available"}), 503
    
    try:
        recipes = list(recipes_collection.find())
        return JSONEncoder().encode({"results": recipes})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/recipes/<recipe_id>", methods=["GET"])
def get_recipe_from_db(recipe_id):
    if not mongo_available:
        return jsonify({"error": "MongoDB not available"}), 503
    
    try:
        # Try first as ObjectId
        try:
            recipe = recipes_collection.find_one({"_id": ObjectId(recipe_id)})
        except:
            # Then try as regular id
            recipe = recipes_collection.find_one({"id": recipe_id})
            if not recipe:
                try:
                    recipe = recipes_collection.find_one({"id": int(recipe_id)})
                except ValueError:
                    pass
                
        if recipe:
            return JSONEncoder().encode(recipe)
        return jsonify({"error": "Recipe not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/recipes", methods=["POST"])
def add_recipe_to_db():
    if not mongo_available:
        return jsonify({"error": "MongoDB not available"}), 503
    
    try:
        recipe = request.json
        if not recipe:
            return jsonify({"error": "Recipe data is required"}), 400
        
        # Ensure recipe has all necessary fields
        if "title" not in recipe:
            recipe["title"] = "Untitled Recipe"
            
        # If no ID is provided, generate one
        if "id" not in recipe:
            recipe["id"] = str(ObjectId())
            
        # Check if recipe already exists
        existing = None
        if "id" in recipe:
            try:
                existing = recipes_collection.find_one({"id": recipe["id"]})
            except:
                # Try as integer if string fails
                try:
                    existing = recipes_collection.find_one({"id": int(recipe["id"])})
                except ValueError:
                    pass
        
        if existing:
            recipes_collection.update_one({"id": recipe["id"]}, {"$set": recipe})
            return jsonify({"message": "Recipe updated", "id": recipe["id"]})
        else:
            result = recipes_collection.insert_one(recipe)
            return jsonify({"message": "Recipe added", "id": recipe["id"] if "id" in recipe else str(result.inserted_id)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/recipes/<recipe_id>", methods=["PUT"])
def update_recipe_in_db(recipe_id):
    if not mongo_available:
        return jsonify({"error": "MongoDB not available"}), 503
    
    try:
        recipe = request.json
        if not recipe:
            return jsonify({"error": "Recipe data is required"}), 400
        
        # Try to update by ObjectId first
        try:
            result = recipes_collection.update_one({"_id": ObjectId(recipe_id)}, {"$set": recipe})
        except:
            # Then try by regular id
            result = recipes_collection.update_one({"id": recipe_id}, {"$set": recipe})
            
        if result.matched_count == 0:
            return jsonify({"error": "Recipe not found"}), 404
        
        return jsonify({"message": "Recipe updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/recipes/<recipe_id>", methods=["DELETE"])
def delete_recipe_from_db(recipe_id):
    if not mongo_available:
        return jsonify({"error": "MongoDB not available"}), 503
    
    try:
        # Try to delete by ObjectId first
        try:
            result = recipes_collection.delete_one({"_id": ObjectId(recipe_id)})
        except:
            # Then try by regular id
            result = recipes_collection.delete_one({"id": recipe_id})
            if result.deleted_count == 0:
                try:
                    result = recipes_collection.delete_one({"id": int(recipe_id)})
                except ValueError:
                    pass
                
        if result.deleted_count == 0:
            return jsonify({"error": "Recipe not found"}), 404
        
        return jsonify({"message": "Recipe deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add a new route for direct testing of MongoDB connection
@app.route("/test-mongodb", methods=["GET"])
def test_mongodb():
    if not mongo_available:
        # Try to get more specific connection error information
        error_message = "MongoDB is not available. Check your connection string and make sure MongoDB is accessible."
        error_type = "Connection Error"
        
        # Check DNS resolution for more specific errors
        dns_check = check_mongodb_dns(MONGO_URI)
        if not dns_check["success"]:
            error_type = "DNS Resolution Error"
            error_message = f"Could not resolve MongoDB hostname: {dns_check['message']}"
        
        return jsonify({
            "status": "error",
            "connected": False,
            "message": error_message,
            "error_type": error_type,
            "dns_check": dns_check
        }), 503
    
    try:
        # Verify connection by getting server stats
        if mongo_client:
            mongo_client.admin.command('ping')
            recipe_count = recipes_collection.count_documents({}) if recipes_collection else 0
            
            # Check if we can get sample data from the collection
            sample = []
            if recipes_collection and recipe_count > 0:
                sample = list(recipes_collection.find().limit(3))
                # Convert ObjectId to string for JSON serialization
                for doc in sample:
                    if "_id" in doc and isinstance(doc["_id"], ObjectId):
                        doc["_id"] = str(doc["_id"])
            
            return jsonify({
                "status": "success",
                "connected": True,
                "message": f"MongoDB is connected and operational. Found {recipe_count} recipes.",
                "database": recipes_collection.database.name if recipes_collection else "unknown",
                "collection": recipes_collection.name if recipes_collection else "unknown",
                "recipeCount": recipe_count,
                "sample": sample[:3],  # Just send a few samples to avoid large payloads
                "connectionInfo": {
                    "host": mongo_client.address[0] if mongo_client.address else "unknown",
                    "port": mongo_client.address[1] if mongo_client.address else "unknown",
                }
            })
        else:
            return jsonify({
                "status": "error",
                "connected": False,
                "message": "MongoDB client is not initialized."
            }), 500
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "connected": False,
            "message": f"Error testing MongoDB connection: {str(e)}"
        }), 500

# Add a new route for adding a test recipe
@app.route("/add-test-recipe", methods=["POST"])
def add_test_recipe():
    if not mongo_available:
        return jsonify({
            "status": "error",
            "success": False,
            "message": "MongoDB is not available."
        }), 503
    
    try:
        # Create a test recipe with timestamp to ensure uniqueness
        timestamp = int(time.time())
        test_recipe = {
            "id": f"test-{timestamp}",
            "title": f"Test Recipe {timestamp}",
            "name": f"Test Recipe {timestamp}",
            "cuisine": "Test",
            "cuisines": ["Test"],
            "dietaryRestrictions": ["test"],
            "diets": ["test"],
            "ingredients": ["test ingredient 1", "test ingredient 2"],
            "instructions": ["Step 1: Test", "Step 2: Complete"],
            "image": "https://via.placeholder.com/300",
            "ratings": [5],
            "createdAt": timestamp
        }
        
        # Try to insert the recipe
        result = recipes_collection.insert_one(test_recipe)
        
        return jsonify({
            "status": "success",
            "success": True,
            "message": "Test recipe added successfully",
            "recipeId": str(result.inserted_id),
            "recipe": {
                **test_recipe,
                "_id": str(result.inserted_id)
            }
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "success": False,
            "message": f"Error adding test recipe: {str(e)}"
        }), 500

# Add a new route for MongoDB diagnostic information
@app.route("/mongodb-diagnostics", methods=["GET"])
def mongodb_diagnostics():
    uri = MONGO_URI or "No URI specified"
    
    # Mask password in URI for security
    masked_uri = uri
    if "@" in masked_uri and ":" in masked_uri:
        prefix = masked_uri.split("@")[0]
        if ":" in prefix:
            username = prefix.split(":")[-2].split("/")[-1]
            masked_uri = masked_uri.replace(prefix, f"{username}:****")
    
    # Basic diagnostics
    diagnostics = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mongodb_available": mongo_available,
        "connection_string": {
            "provided": bool(MONGO_URI),
            "masked_uri": masked_uri,
            "type": "mongodb+srv" if uri and "mongodb+srv" in uri else "mongodb" if uri and "mongodb://" in uri else "unknown"
        },
        "dns_check": check_mongodb_dns(MONGO_URI),
        "pymongo_version": pymongo.__version__ if 'pymongo' in sys.modules else "Not installed",
        "python_version": sys.version,
        "platform": sys.platform,
        "connection_attempts": MONGO_RETRY_COUNT,
        "connection_timeout_ms": MONGO_CONNECT_TIMEOUT_MS,
    }
    
    # Add collection info if available
    if mongo_available and recipes_collection:
        try:
            diagnostics["database_info"] = {
                "database_name": recipes_collection.database.name,
                "collection_name": recipes_collection.name,
                "document_count": recipes_collection.count_documents({}),
                "indexes": list(recipes_collection.list_indexes())
            }
        except Exception as e:
            diagnostics["database_info"] = {"error": str(e)}
    
    return jsonify(diagnostics)

@app.route("/folders", methods=["GET"])
def get_folders():
    if not mongo_available:
        return jsonify({"error": "MongoDB not available"}), 503
    
    try:
        folders = list(folders_collection.find({}, {'_id': 0}))
        return jsonify({"folders": folders})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/folders", methods=["POST"])
def create_folder():
    if not mongo_available:
        return jsonify({"error": "MongoDB not available"}), 503
    
    try:
        folder_data = request.json
        if not folder_data or "name" not in folder_data:
            return jsonify({"error": "Folder name is required"}), 400
        
        folder = {
            "id": str(ObjectId()),
            "name": folder_data["name"],
            "description": folder_data.get("description", ""),
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat()
        }
        
        folders_collection.insert_one(folder)
        return jsonify({"message": "Folder created", "folder": folder})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/folders/<folder_id>", methods=["PUT"])
def update_folder(folder_id):
    if not mongo_available:
        return jsonify({"error": "MongoDB not available"}), 503
    
    try:
        folder_data = request.json
        if not folder_data:
            return jsonify({"error": "Folder data is required"}), 400
        
        folder_data["updatedAt"] = datetime.utcnow().isoformat()
        
        result = folders_collection.update_one(
            {"id": folder_id},
            {"$set": folder_data}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "Folder not found"}), 404
        
        return jsonify({"message": "Folder updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/folders/<folder_id>", methods=["DELETE"])
def delete_folder(folder_id):
    if not mongo_available:
        return jsonify({"error": "MongoDB not available"}), 503
    
    try:
        # First, remove folder reference from all recipes
        recipes_collection.update_many(
            {"folderId": folder_id},
            {"$unset": {"folderId": ""}}
        )
        
        # Then delete the folder
        result = folders_collection.delete_one({"id": folder_id})
        
        if result.deleted_count == 0:
            return jsonify({"error": "Folder not found"}), 404
        
        return jsonify({"message": "Folder deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/folders/<folder_id>/recipes", methods=["GET"])
def get_folder_recipes(folder_id):
    if not mongo_available:
        return jsonify({"error": "MongoDB not available"}), 503
    
    try:
        recipes = list(recipes_collection.find({"folderId": folder_id}, {'_id': 0}))
        return jsonify({"recipes": recipes})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Starting Flask application...")
    # Run the Flask app on 0.0.0.0 to make it accessible from other devices on the network
    app.run(host='0.0.0.0', debug=True, port=5000)
