
import os
import time
import sys
import socket
import dns.resolver
from bson import ObjectId

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

# Initialize MongoDB connection
def initialize_mongodb(mongo_uri, connect_timeout_ms=5000, retry_count=3):
    try:
        if not mongo_uri:
            raise Exception("No MongoDB URI provided")
        
        # First check DNS resolution
        dns_check = check_mongodb_dns(mongo_uri)
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
        mongo_client = None
        recipes_collection = None
        folders_collection = None
        mongo_available = False
        
        while connect_attempts < retry_count:
            try:
                print(f"Attempting to connect to MongoDB (attempt {connect_attempts + 1})...")
                # Set shorter serverSelectionTimeoutMS to fail faster if MongoDB is unavailable
                mongo_client = pymongo.MongoClient(
                    mongo_uri, 
                    serverSelectionTimeoutMS=connect_timeout_ms,
                    connectTimeoutMS=connect_timeout_ms,
                    socketTimeoutMS=connect_timeout_ms * 2
                )
                
                # Test connection with server_info
                print("Testing MongoDB connection...")
                mongo_client.server_info()
                
                # If we get here, connection is successful
                print("MongoDB connection successful!")
                
                # Determine database name from URI or use default
                db_name = "nikash"  # Default
                if "/" in mongo_uri:
                    uri_parts = mongo_uri.split("/")
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
                
                if connect_attempts < retry_count:
                    wait_time = 2 * connect_attempts  # Progressive backoff
                    print(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"All {retry_count} connection attempts failed")
        
        return mongo_client, recipes_collection, folders_collection, mongo_available
    except Exception as e:
        print(f"MongoDB initialization error: {e}")
        return None, None, None, False

# Add seed data to MongoDB if needed
def add_seed_data(recipes_collection):
    if not recipes_collection:
        print("Cannot add seed data: recipes_collection is None")
        return
    
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
               {
    "id": "5",
    "name": "Shepherd's Pie",
    "title": "Shepherd's Pie",
    "cuisine": "British",
    "cuisines": ["British"],
    "dietaryRestrictions": ["Non-Vegetarian"],
    "diets": ["Non-Vegetarian"],
    "ingredients": ["ground round beef", "beef broth", "Worcestershire sauce", "salt", "potatoes", "butter", "onions", "chopped carrots", "corn", "peas"],
    "instructions": [

        "Bake potatoes until golden",
        "Boil the potatoes: Place the peeled and quartered potatoes in medium sized pot. Cover with at least an inch of cold water. Add a teaspoon of salt. Bring to a boil, reduce to a simmer, and cook until tender (about 20 minutes).",
        "Sauté the vegetables: While the potatoes are cooking, melt 4 tablespoons of the butter in a large sauté pan on medium heat. Add the chopped onions and cook until tender, about 6 to 10 minutes.",
        "If you are including vegetables, add them according to their cooking time. Carrots should be cooked with the onions, because they take as long to cook as the onions do.",
        "If you are including peas or corn, add them toward the end of the cooking of the onions, or after the meat starts to cook, as they take very little cooking time.",
        "Add ground beef to the pan with the onions and vegetables. Cook until no longer pink. Drain the pan of excess fat, if necessary (anything more than 1 tablespoon). Season with salt and pepper.",
        "Add the Worcestershire sauce and beef broth. Bring the broth to a simmer and reduce heat to low. Cook uncovered for 10 minutes, adding more beef broth if necessary to keep the meat from drying out.",
        "Mash the cooked potatoes: When the potatoes are done cooking (a fork can easily pierce), remove them from the pot and place them in a bowl with the remaining 4 tablespoons of butter. Mash with a fork or potato masher, taste, and adjust seasonings with salt and pepper.",
        "Layer the meat mixture and mashed potatoes in a casserole dish: Spread the cooked filling in an even layer in a large baking dish (such as a 9 x 13-inch casserole).",
        "Spread the mashed potatoes over the top of the ground beef. Rough up the surface of the mashed potatoes with a fork so there are peaks that will get well browned. You can even use a fork to make creative designs in the mashed potatoes.",
        "Bake: Place in a 400°F oven and cook until browned and bubbling, about 30 minutes. If necessary, broil for the last few minutes to help the surface of the mashed potatoes brown."
    ],
    "image": "https://www.simplyrecipes.com/thmb/fviw6rJNW_LXdVykXA-tk6hr2II=/750x0/filters:no_upscale():max_bytes(150000):strip_icc():format(webp)/Simply-Recipes-Easy-Shepherds-Pie-Lead-2_SERP-fdf8883477354e85bd05f9243f71657f.jpg",
    "ratings": [5, 4, 5]
}

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
