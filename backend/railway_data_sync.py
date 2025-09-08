#!/usr/bin/env python3
"""
Railway Data Sync Script

This script creates a comprehensive data file that can be uploaded to Railway
and used to populate the production database with your local data.
"""

import os
import sys
import json
import chromadb
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def extract_all_local_data() -> Dict[str, Any]:
    """Extract all data from local ChromaDB"""
    print("🔄 Extracting all data from local ChromaDB...")
    
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Initialize data structure
    sync_data = {
        "sync_timestamp": datetime.now().isoformat(),
        "recipes": [],
        "user_preferences": [],
        "meal_plans": [],
        "meal_history": [],
        "shopping_lists": [],
        "reviews": [],
        "folders": []
    }
    
    # Extract recipes from all collections
    recipe_collections = [
        "recipe_details_cache",
        "recipe_search_cache", 
        "recipes"
    ]
    
    all_recipes = []
    for collection_name in recipe_collections:
        try:
            collection = client.get_collection(collection_name)
            count = collection.count()
            print(f"📊 Found {count} items in '{collection_name}' collection")
            
            if count > 0:
                results = collection.get(include=['documents', 'metadatas'])
                
                for i, (doc_id, document, metadata) in enumerate(zip(
                    results['ids'], 
                    results['documents'], 
                    results['metadatas']
                )):
                    try:
                        if isinstance(document, str):
                            recipe_data = json.loads(document)
                        else:
                            recipe_data = document
                        
                        if isinstance(recipe_data, dict) and recipe_data.get('id'):
                            recipe_data['_source_collection'] = collection_name
                            all_recipes.append(recipe_data)
                            
                    except Exception as e:
                        print(f"⚠️ Error processing item {i} from {collection_name}: {e}")
                        continue
                        
        except Exception as e:
            print(f"⚠️ Could not access collection '{collection_name}': {e}")
            continue
    
    # Remove duplicates and clean recipes
    unique_recipes = {}
    for recipe in all_recipes:
        recipe_id = recipe.get('id')
        if recipe_id and recipe_id not in unique_recipes:
            # Clean the recipe for Railway
            clean_recipe = clean_recipe_for_railway(recipe)
            unique_recipes[recipe_id] = clean_recipe
    
    sync_data["recipes"] = list(unique_recipes.values())
    print(f"✅ Extracted {len(sync_data['recipes'])} unique recipes")
    
    # Extract user preferences
    try:
        collection = client.get_collection("user_preferences")
        count = collection.count()
        print(f"📊 Found {count} user preferences")
        
        if count > 0:
            results = collection.get(include=['documents', 'metadatas'])
            
            for doc_id, document, metadata in zip(
                results['ids'], 
                results['documents'], 
                results['metadatas']
            ):
                try:
                    if isinstance(document, str):
                        pref_data = json.loads(document)
                    else:
                        pref_data = document
                    
                    if isinstance(pref_data, dict):
                        pref_data['_id'] = doc_id
                        sync_data["user_preferences"].append(pref_data)
                        
                except Exception as e:
                    print(f"⚠️ Error processing preference {doc_id}: {e}")
                    continue
                    
    except Exception as e:
        print(f"⚠️ Could not access user preferences: {e}")
    
    # Extract meal plans
    try:
        collection = client.get_collection("meal_plans")
        count = collection.count()
        print(f"📊 Found {count} meal plans")
        
        if count > 0:
            results = collection.get(include=['documents', 'metadatas'])
            
            for doc_id, document, metadata in zip(
                results['ids'], 
                results['documents'], 
                results['metadatas']
            ):
                try:
                    if isinstance(document, str):
                        plan_data = json.loads(document)
                    else:
                        plan_data = document
                    
                    if isinstance(plan_data, dict):
                        plan_data['_id'] = doc_id
                        sync_data["meal_plans"].append(plan_data)
                        
                except Exception as e:
                    print(f"⚠️ Error processing meal plan {doc_id}: {e}")
                    continue
                    
    except Exception as e:
        print(f"⚠️ Could not access meal plans: {e}")
    
    # Extract meal history
    try:
        collection = client.get_collection("meal_history")
        count = collection.count()
        print(f"📊 Found {count} meal history entries")
        
        if count > 0:
            results = collection.get(include=['documents', 'metadatas'])
            
            for doc_id, document, metadata in zip(
                results['ids'], 
                results['documents'], 
                results['metadatas']
            ):
                try:
                    if isinstance(document, str):
                        history_data = json.loads(document)
                    else:
                        history_data = document
                    
                    if isinstance(history_data, dict):
                        history_data['_id'] = doc_id
                        sync_data["meal_history"].append(history_data)
                        
                except Exception as e:
                    print(f"⚠️ Error processing meal history {doc_id}: {e}")
                    continue
                    
    except Exception as e:
        print(f"⚠️ Could not access meal history: {e}")
    
    print(f"✅ Data extraction complete!")
    print(f"   - Recipes: {len(sync_data['recipes'])}")
    print(f"   - User Preferences: {len(sync_data['user_preferences'])}")
    print(f"   - Meal Plans: {len(sync_data['meal_plans'])}")
    print(f"   - Meal History: {len(sync_data['meal_history'])}")
    
    return sync_data

def clean_recipe_for_railway(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and format recipe for Railway storage"""
    
    # Extract title and create a stable ID
    title = recipe.get('title', 'Untitled Recipe')
    recipe_id = recipe.get('id') or f"local-{abs(hash(title)) % 10000000}"
    
    clean_recipe = {
        'id': str(recipe_id),
        'title': title,
        'description': recipe.get('description', recipe.get('summary', '')),
        'ingredients': recipe.get('ingredients', []),
        'instructions': recipe.get('instructions', ['No instructions provided']),
        'cuisines': recipe.get('cuisines', []),
        'diets': recipe.get('diets', []),
        'dietary_restrictions': recipe.get('dietary_restrictions', []),
        'readyInMinutes': recipe.get('readyInMinutes', recipe.get('ready_in_minutes', 30)),
        'servings': recipe.get('servings', 4),
        'image': recipe.get('image', ''),
        'sourceName': recipe.get('sourceName', 'Local Recipe'),
        'createdAt': recipe.get('createdAt', '2024-01-01T00:00:00Z'),
        'updatedAt': recipe.get('updatedAt', '2024-01-01T00:00:00Z')
    }
    
    # Add nutrition data if available
    if 'nutrition' in recipe and isinstance(recipe['nutrition'], dict):
        clean_recipe['nutrition'] = recipe['nutrition']
    else:
        # Legacy flat fields
        calories = recipe.get('calories'); protein = recipe.get('protein'); carbs = recipe.get('carbs'); fat = recipe.get('fat')
        if any(v is not None for v in [calories, protein, carbs, fat]):
            clean_recipe['nutrition'] = {
                'calories': calories or 0,
                'protein': protein or 0,
                'carbs': carbs or 0,
                'fat': fat or 0
            }
    
    # Normalizations
    if not isinstance(clean_recipe['ingredients'], list):
        clean_recipe['ingredients'] = []
    if not isinstance(clean_recipe['instructions'], list):
        if isinstance(clean_recipe['instructions'], str):
            clean_recipe['instructions'] = [clean_recipe['instructions']]
        else:
            clean_recipe['instructions'] = ['No instructions provided']
    if not isinstance(clean_recipe['cuisines'], list):
        clean_recipe['cuisines'] = []
    if not isinstance(clean_recipe['diets'], list):
        clean_recipe['diets'] = []
    
    return clean_recipe

def create_railway_population_script(sync_data: Dict[str, Any]) -> str:
    """Create a script that can be run on Railway to populate the data"""
    
    script_content = f'''#!/usr/bin/env python3
"""
Railway Data Population Script
Generated on {datetime.now().isoformat()}

This script populates Railway ChromaDB with data from your local environment.
Run this script on Railway after deployment to sync your data.
"""

import json
import chromadb
from services.recipe_search_service import RecipeSearchService
from services.meal_history_service import MealHistoryService
from services.smart_shopping_service import SmartShoppingService
from services.user_preferences_service import UserPreferencesService

def populate_railway_data():
    """Populate Railway ChromaDB with synced data"""
    print("🚀 Populating Railway ChromaDB...")
    
    # Load synced data
    recipes = {json.dumps(sync_data['recipes'], indent=2)}
    preferences = {json.dumps(sync_data['user_preferences'], indent=2)}
    meal_plans = {json.dumps(sync_data['meal_plans'], indent=2)}
    meal_history = {json.dumps(sync_data['meal_history'], indent=2)}
    
    # Initialize services
    try:
        recipe_search_service = RecipeSearchService()
        meal_history_service = MealHistoryService()
        smart_shopping_service = SmartShoppingService()
        user_preferences_service = UserPreferencesService()
        
        # Index recipes
        print(f"📚 Indexing {{len(recipes)}} recipes...")
        recipe_search_service.bulk_index_recipes(recipes)
        
        # Save user preferences
        print(f"👤 Saving {{len(preferences)}} user preferences...")
        for pref in preferences:
            user_id = pref.get('_id', 'default_user')
            pref_data = {{k: v for k, v in pref.items() if k != '_id'}}
            user_preferences_service.save_preferences(user_id, pref_data)
        
        # Save meal plans
        print(f"🍽️ Saving {{len(meal_plans)}} meal plans...")
        for plan in meal_plans:
            plan_id = plan.get('_id', 'default_plan')
            plan_data = {{k: v for k, v in plan.items() if k != '_id'}}
            # You'll need to implement meal plan saving in your service
            print(f"Meal plan {{plan_id}}: {{plan_data.get('title', 'Untitled')}}")
        
        # Save meal history
        print(f"📅 Saving {{len(meal_history)}} meal history entries...")
        for history in meal_history:
            history_id = history.get('_id', 'default_history')
            history_data = {{k: v for k, v in history.items() if k != '_id'}}
            # You'll need to implement meal history saving in your service
            print(f"Meal history {{history_id}}: {{history_data.get('title', 'Untitled')}}")
        
        print("✅ Railway data population complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error populating Railway data: {{e}}")
        return False

if __name__ == "__main__":
    success = populate_railway_data()
    if success:
        print("🎉 Data population successful!")
    else:
        print("❌ Data population failed!")
'''
    
    script_filename = f"populate_railway_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    with open(script_filename, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"📝 Railway population script created: {script_filename}")
    return script_filename

def main():
    """Main function"""
    print("🚀 Railway Data Sync Tool")
    print("=" * 50)
    
    # Extract all local data
    sync_data = extract_all_local_data()
    
    if not sync_data["recipes"]:
        print("❌ No recipes found to sync")
        return
    
    # Save sync data to JSON file
    data_filename = f"railway_sync_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(data_filename, 'w', encoding='utf-8') as f:
        json.dump(sync_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Sync data saved to: {data_filename}")
    
    # Create population script
    script_filename = create_railway_population_script(sync_data)
    
    print("\n" + "="*60)
    print("🎉 Data sync preparation complete!")
    print("="*60)
    print(f"📊 Data extracted:")
    print(f"   - {len(sync_data['recipes'])} recipes")
    print(f"   - {len(sync_data['user_preferences'])} user preferences") 
    print(f"   - {len(sync_data['meal_plans'])} meal plans")
    print(f"   - {len(sync_data['meal_history'])} meal history entries")
    print(f"\n📁 Files created:")
    print(f"   - Sync data: {data_filename}")
    print(f"   - Population script: {script_filename}")
    print(f"\n🚀 Next steps:")
    print(f"   1. Upload both files to your Railway deployment")
    print(f"   2. Run the population script on Railway to populate the database")
    print(f"   3. Verify your Netlify frontend can access the data")
    print(f"\n💡 Alternative: Use the backup file to restore data directly")

if __name__ == "__main__":
    main()
