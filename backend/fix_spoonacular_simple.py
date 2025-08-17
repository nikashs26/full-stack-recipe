#!/usr/bin/env python3
"""
Fix Spoonacular Recipes with Missing Ingredients (Simple Version)

This script uses the requests library to avoid SSL issues and fetches
real ingredients from Spoonacular for recipes that are missing them.
"""

import requests
import json
import logging
import time
from typing import List, Dict, Any, Optional
import chromadb
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleSpoonacularFixer:
    def __init__(self):
        """Initialize the simple Spoonacular fixer"""
        self.spoonacular_api_key = os.getenv('SPOONACULAR_API_KEY')
        if not self.spoonacular_api_key:
            raise ValueError("SPOONACULAR_API_KEY environment variable not set")
        
        self.spoonacular_base_url = "https://api.spoonacular.com"
        self.chroma_client = None
        self.collection = None
        
    def connect_to_chromadb(self):
        """Connect to ChromaDB"""
        try:
            self.chroma_client = chromadb.PersistentClient(path='./chroma_db')
            self.collection = self.chroma_client.get_collection('recipe_details_cache')
            logger.info("✅ Connected to ChromaDB")
        except Exception as e:
            logger.error(f"❌ Failed to connect to ChromaDB: {e}")
            raise
    
    def is_likely_spoonacular_id(self, recipe_id: str) -> bool:
        """Check if a recipe ID is likely a Spoonacular ID"""
        # Spoonacular IDs are typically 6-7 digit numbers
        if recipe_id.isdigit():
            id_num = int(recipe_id)
            # Most Spoonacular IDs are in the 100k-2M range
            return 100000 <= id_num <= 2000000
        return False
    
    def fetch_spoonacular_ingredients(self, recipe_id: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch ingredients from Spoonacular API"""
        try:
            url = f"{self.spoonacular_base_url}/recipes/{recipe_id}/ingredientWidget.json"
            params = {"apiKey": self.spoonacular_api_key}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                ingredients = data.get('ingredients', [])
                
                # Convert to our format
                formatted_ingredients = []
                for ing in ingredients:
                    formatted_ingredients.append({
                        "name": ing.get('name', ''),
                        "amount": ing.get('amount', {}),
                        "unit": ing.get('amount', {}).get('us', {}).get('unit', ''),
                        "image": ing.get('image', '')
                    })
                
                logger.info(f"✅ Fetched {len(formatted_ingredients)} ingredients from Spoonacular")
                return formatted_ingredients
            else:
                logger.warning(f"⚠️ Spoonacular API returned status {response.status_code} for recipe {recipe_id}")
                return None
                        
        except Exception as e:
            logger.error(f"❌ Error fetching from Spoonacular for recipe {recipe_id}: {e}")
            return None
    
    def update_recipe_ingredients(self, recipe_id: str, ingredients: List[Dict[str, Any]]) -> bool:
        """Update recipe in ChromaDB with new ingredients"""
        try:
            # Get the current recipe
            results = self.collection.get(ids=[recipe_id])
            if not results['documents']:
                logger.warning(f"⚠️ Recipe {recipe_id} not found in ChromaDB")
                return False
            
            recipe_doc = json.loads(results['documents'][0])
            recipe_metadata = results['metadatas'][0]
            
            # Update ingredients
            recipe_doc['ingredients'] = ingredients
            recipe_doc['updated_at'] = datetime.now().isoformat()
            recipe_doc['ingredients_source'] = 'spoonacular_api'
            
            # Update in ChromaDB
            self.collection.update(
                ids=[recipe_id],
                documents=[json.dumps(recipe_doc)],
                metadatas=[recipe_metadata]
            )
            
            logger.info(f"✅ Successfully updated recipe {recipe_id} with {len(ingredients)} ingredients")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating recipe {recipe_id}: {e}")
            return False
    
    def fix_spoonacular_recipes(self):
        """Fix all Spoonacular recipes with missing ingredients"""
        try:
            self.connect_to_chromadb()
            
            total_recipes = self.collection.count()
            logger.info(f"📊 Total recipes in ChromaDB: {total_recipes}")
            
            # Get all recipes
            results = self.collection.get(limit=total_recipes)
            
            # Find recipes that likely need fixing
            recipes_to_fix = []
            
            for i, (recipe_id, metadata, document) in enumerate(zip(
                results['ids'], results['metadatas'], results['documents']
            )):
                if i % 100 == 0:
                    logger.info(f"   Analyzed {i}/{total_recipes} recipes...")
                
                recipe = json.loads(document)
                ingredients = recipe.get('ingredients', [])
                
                # Check if this recipe needs fixing
                if (not ingredients or 
                    (isinstance(ingredients, list) and len(ingredients) == 0) or
                    (isinstance(ingredients, str) and ingredients.strip() == "")):
                    
                    if self.is_likely_spoonacular_id(recipe_id):
                        recipes_to_fix.append({
                            'id': recipe_id,
                            'title': metadata.get('title', 'Unknown'),
                            'source': metadata.get('source', 'unknown')
                        })
            
            logger.info(f"🎯 Found {len(recipes_to_fix)} Spoonacular recipes with missing ingredients")
            
            if not recipes_to_fix:
                logger.info("🎉 No recipes need fixing!")
                return
            
            # Process each recipe
            success_count = 0
            failed_count = 0
            
            for i, recipe_info in enumerate(recipes_to_fix):
                recipe_id = recipe_info['id']
                title = recipe_info['title']
                
                logger.info(f"\n📝 Processing recipe {i+1}/{len(recipes_to_fix)}: {recipe_id} - {title}")
                
                # Fetch ingredients from Spoonacular
                ingredients = self.fetch_spoonacular_ingredients(recipe_id)
                
                if ingredients:
                    # Update the recipe
                    if self.update_recipe_ingredients(recipe_id, ingredients):
                        success_count += 1
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
                
                # Rate limiting
                time.sleep(0.5)
            
            # Summary
            logger.info(f"\n🎉 Spoonacular ingredient fixing completed!")
            logger.info(f"   Successfully fixed: {success_count}")
            logger.info(f"   Failed to fix: {failed_count}")
            logger.info(f"   Total processed: {len(recipes_to_fix)}")
            
        except Exception as e:
            logger.error(f"❌ Error in fix_spoonacular_recipes: {e}")
            raise

def main():
    """Main function"""
    try:
        fixer = SimpleSpoonacularFixer()
        fixer.fix_spoonacular_recipes()
    except Exception as e:
        logger.error(f"❌ Main error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
