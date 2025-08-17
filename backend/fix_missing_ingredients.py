#!/usr/bin/env python3
"""
Script to fix missing ingredients in recipes by re-fetching from TheMealDB
and updating the ChromaDB with the complete ingredient data.
"""

import asyncio
import aiohttp
import json
import logging
import ssl
import certifi
from typing import List, Dict, Any, Optional
import chromadb
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IngredientFixer:
    def __init__(self):
        """Initialize the ingredient fixer"""
        self.base_url = "https://www.themealdb.com/api/json/v1/1"
        
        # Create SSL context
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Initialize ChromaDB
        try:
            self.client = chromadb.PersistentClient(path="./chroma_db")
            self.recipe_collection = self.client.get_collection('recipe_details_cache')
            logger.info("Connected to ChromaDB")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise
    
    async def fetch_recipe_details(self, meal_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed recipe information from TheMealDB"""
        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = f"{self.base_url}/lookup.php?i={meal_id}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('meals') and len(data['meals']) > 0:
                            return data['meals'][0]
                    else:
                        logger.warning(f"Failed to fetch recipe {meal_id}: {response.status}")
            return None
        except Exception as e:
            logger.error(f"Error fetching recipe {meal_id}: {e}")
            return None
    
    def extract_ingredients(self, recipe_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract ingredients from TheMealDB recipe data"""
        ingredients = []
        
        for i in range(1, 21):  # TheMealDB has up to 20 ingredients
            ingredient = str(recipe_data.get(f'strIngredient{i}', '') or '').strip()
            measure = str(recipe_data.get(f'strMeasure{i}', '') or '').strip()
            
            # Skip empty ingredients or placeholders
            if not ingredient or ingredient.lower() in ('', 'null', 'none'):
                continue
                
            ingredients.append({
                'name': ingredient,
                'measure': measure if measure and measure.lower() not in ('', 'null', 'none') else 'to taste',
                'original': f"{measure} {ingredient}".strip()
            })
        
        return ingredients
    
    def normalize_recipe(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize recipe data to our standard format"""
        try:
            # Extract ingredients
            ingredients = self.extract_ingredients(recipe_data)
            
            # Handle instructions
            instructions = recipe_data.get('strInstructions', '')
            if instructions:
                # Split instructions into steps
                import re
                steps = re.split(r'[.!?]+', instructions)
                steps = [s.strip() for s in steps if s.strip() and len(s.strip()) > 10]
                
                if not steps:
                    steps = [instructions.strip()]
            else:
                steps = ['No instructions provided.']
            
            # Build normalized recipe
            normalized = {
                'id': f"mealdb_{recipe_data.get('idMeal', '')}",
                'title': str(recipe_data.get('strMeal', 'Untitled Recipe') or 'Untitled Recipe').strip(),
                'image': str(recipe_data.get('strMealThumb', '') or ''),
                'source': 'TheMealDB',
                'source_url': str(recipe_data.get('strSource', '') or ''),
                'ingredients': ingredients,
                'instructions': steps,
                'prep_time': None,
                'cook_time': None,
                'cuisines': [],
                'tags': [],
                'nutrition': {},
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'metadata': {
                    'source_id': recipe_data.get('idMeal', ''),
                    'source': 'TheMealDB',
                    'original_data': recipe_data
                }
            }
            
            # Add category as a tag
            if recipe_data.get('strCategory'):
                category = str(recipe_data['strCategory'] or '').strip().lower()
                if category:
                    normalized['tags'].append(category)
            
            # Handle cuisine/area
            if recipe_data.get('strArea'):
                area = str(recipe_data['strArea'] or '').strip().lower()
                if area:
                    normalized['cuisines'].append(area)
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing recipe: {e}")
            return None
    
    async def fix_recipe_ingredients(self, recipe_id: str) -> bool:
        """Fix ingredients for a single recipe"""
        try:
            # Get the recipe from ChromaDB
            results = self.recipe_collection.get(ids=[recipe_id])
            if not results['documents']:
                logger.warning(f"Recipe {recipe_id} not found in ChromaDB")
                return False
            
            recipe_doc = results['documents'][0]
            recipe = json.loads(recipe_doc)
            
            # Check if ingredients are missing
            if recipe.get('ingredients') and len(recipe['ingredients']) > 0:
                logger.info(f"Recipe {recipe_id} already has ingredients, skipping")
                return True
            
            # Extract the original TheMealDB ID
            if 'mealdb_' in recipe_id:
                mealdb_id = recipe_id.replace('mealdb_', '')
            else:
                # Try to find it in metadata or other fields
                mealdb_id = recipe.get('metadata', {}).get('source_id') or recipe.get('id')
            
            if not mealdb_id:
                logger.warning(f"Could not determine TheMealDB ID for recipe {recipe_id}")
                return False
            
            # Fetch fresh data from TheMealDB
            logger.info(f"Fetching fresh data for recipe {mealdb_id} from TheMealDB")
            fresh_data = await self.fetch_recipe_details(mealdb_id)
            
            if not fresh_data:
                logger.warning(f"Failed to fetch fresh data for recipe {mealdb_id}")
                return False
            
            # Normalize the fresh data
            normalized_recipe = self.normalize_recipe(fresh_data)
            
            if not normalized_recipe:
                logger.warning(f"Failed to normalize recipe {mealdb_id}")
                return False
            
            # Update the recipe in ChromaDB
            updated_doc = json.dumps(normalized_recipe)
            
            # Update the document
            self.recipe_collection.update(
                ids=[recipe_id],
                documents=[updated_doc],
                metadatas=[self._extract_metadata(normalized_recipe)]
            )
            
            logger.info(f"Successfully updated recipe {recipe_id} with {len(normalized_recipe['ingredients'])} ingredients")
            return True
            
        except Exception as e:
            logger.error(f"Error fixing recipe {recipe_id}: {e}")
            return False
    
    def _extract_metadata(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata for ChromaDB"""
        try:
            # Extract cuisines
            cuisines = recipe.get('cuisines', [])
            if isinstance(cuisines, str):
                cuisines = [c.strip() for c in cuisines.split(',') if c.strip()]
            
            # Extract ingredients for metadata
            ingredients = []
            if recipe.get('ingredients'):
                for ing in recipe['ingredients']:
                    if isinstance(ing, dict) and 'name' in ing:
                        ingredients.append(ing['name'])
                    elif isinstance(ing, str):
                        ingredients.append(ing)
            
            metadata = {
                "id": recipe.get('id', ''),
                "title": recipe.get('title', ''),
                "cuisine": cuisines[0] if cuisines else 'Other',
                "cuisines": ','.join(cuisines) if cuisines else '',
                "ingredients": ','.join(ingredients) if ingredients else '',
                "cached_at": datetime.now().isoformat(),
                "source": recipe.get('source', 'TheMealDB'),
            }
            
            # Add optional fields
            if recipe.get('tags'):
                metadata["tags"] = ','.join(recipe['tags'])
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}
    
    async def fix_all_missing_ingredients(self) -> Dict[str, Any]:
        """Fix ingredients for all recipes with missing ingredients"""
        try:
            # Get all recipes from ChromaDB
            total_recipes = self.recipe_collection.count()
            logger.info(f"Total recipes in ChromaDB: {total_recipes}")
            
            # Get all recipe IDs
            results = self.recipe_collection.get(limit=total_recipes)
            recipe_ids = results['ids']
            
            logger.info(f"Processing {len(recipe_ids)} recipes...")
            
            # Track progress
            fixed_count = 0
            skipped_count = 0
            error_count = 0
            
            for i, recipe_id in enumerate(recipe_ids):
                try:
                    logger.info(f"Processing recipe {i+1}/{len(recipe_ids)}: {recipe_id}")
                    
                    if await self.fix_recipe_ingredients(recipe_id):
                        fixed_count += 1
                    else:
                        skipped_count += 1
                    
                    # Add a small delay to avoid overwhelming the API
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error processing recipe {recipe_id}: {e}")
                    error_count += 1
            
            return {
                'total_recipes': total_recipes,
                'fixed_count': fixed_count,
                'skipped_count': skipped_count,
                'error_count': error_count
            }
            
        except Exception as e:
            logger.error(f"Error in fix_all_missing_ingredients: {e}")
            return {}

async def main():
    """Main function"""
    try:
        fixer = IngredientFixer()
        
        logger.info("Starting ingredient fix process...")
        
        # Fix all missing ingredients
        results = await fixer.fix_all_missing_ingredients()
        
        logger.info("Ingredient fix process completed!")
        logger.info(f"Results: {json.dumps(results, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())
