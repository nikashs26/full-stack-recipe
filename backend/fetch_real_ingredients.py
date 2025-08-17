#!/usr/bin/env python3
"""
Fetch Real Recipe Ingredients from Original Sources

This script identifies recipes with missing ingredients and attempts to fetch
the real ingredient data from their original sources (TheMealDB, Spoonacular, etc.)
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
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealIngredientFetcher:
    def __init__(self):
        """Initialize the real ingredient fetcher"""
        self.themealdb_url = "https://www.themealdb.com/api/json/v1/1"
        self.spoonacular_api_key = os.environ.get("SPOONACULAR_API_KEY")
        self.spoonacular_url = "https://api.spoonacular.com/recipes"
        
        # Create SSL context
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Initialize ChromaDB
        try:
            self.client = chromadb.PersistentClient(path='./chroma_db')
            self.recipe_collection = self.client.get_collection('recipe_details_cache')
            logger.info("Connected to ChromaDB")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise
    
    def analyze_recipe_sources(self) -> Dict[str, Any]:
        """Analyze recipe sources to understand where to fetch ingredients from"""
        logger.info("🔍 Analyzing recipe sources...")
        
        total_recipes = self.recipe_collection.count()
        results = self.recipe_collection.get(limit=total_recipes)
        
        source_analysis = {
            'total_recipes': total_recipes,
            'mealdb_recipes': [],
            'spoonacular_recipes': [],
            'unknown_source_recipes': [],
            'recipes_with_ingredients': 0,
            'recipes_missing_ingredients': 0
        }
        
        for i, (recipe_id, doc) in enumerate(zip(results['ids'], results['documents'])):
            try:
                recipe = json.loads(doc)
                title = recipe.get('title', 'Unknown')
                ingredients = recipe.get('ingredients', [])
                source = recipe.get('source', 'unknown')
                
                # Check if ingredients exist
                if ingredients and len(ingredients) > 0:
                    source_analysis['recipes_with_ingredients'] += 1
                else:
                    source_analysis['recipes_missing_ingredients'] += 1
                
                # Categorize by source
                if 'mealdb' in recipe_id.lower() or source == 'TheMealDB':
                    source_analysis['mealdb_recipes'].append({
                        'id': recipe_id,
                        'title': title,
                        'has_ingredients': bool(ingredients and len(ingredients) > 0)
                    })
                elif recipe_id.isdigit() and len(recipe_id) > 6:
                    source_analysis['spoonacular_recipes'].append({
                        'id': recipe_id,
                        'title': title,
                        'has_ingredients': bool(ingredients and len(ingredients) > 0)
                    })
                else:
                    source_analysis['unknown_source_recipes'].append({
                        'id': recipe_id,
                        'title': title,
                        'has_ingredients': bool(ingredients and len(ingredients) > 0)
                    })
                
                if (i + 1) % 100 == 0:
                    logger.info(f"   Analyzed {i + 1}/{total_recipes} recipes...")
                    
            except Exception as e:
                logger.error(f"Error analyzing recipe {recipe_id}: {e}")
        
        return source_analysis
    
    async def fetch_mealdb_ingredients(self, meal_id: str) -> Optional[List[Dict[str, str]]]:
        """Fetch real ingredients from TheMealDB"""
        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = f"{self.themealdb_url}/lookup.php?i={meal_id}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('meals') and len(data['meals']) > 0:
                            recipe_data = data['meals'][0]
                            
                            # Extract real ingredients
                            ingredients = []
                            for i in range(1, 21):  # TheMealDB has up to 20 ingredients
                                ingredient = str(recipe_data.get(f'strIngredient{i}', '') or '').strip()
                                measure = str(recipe_data.get(f'strMeasure{i}', '') or '').strip()
                                
                                # Skip empty ingredients
                                if not ingredient or ingredient.lower() in ('', 'null', 'none'):
                                    continue
                                    
                                ingredients.append({
                                    'name': ingredient,
                                    'measure': measure if measure and measure.lower() not in ('', 'null', 'none') else 'to taste',
                                    'original': f"{measure} {ingredient}".strip()
                                })
                            
                            logger.info(f"✅ Fetched {len(ingredients)} real ingredients from TheMealDB for recipe {meal_id}")
                            return ingredients
                        else:
                            logger.warning(f"No meal data found for TheMealDB ID: {meal_id}")
                    else:
                        logger.warning(f"TheMealDB API returned status {response.status} for recipe {meal_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching from TheMealDB for recipe {meal_id}: {e}")
            return None
    
    async def fetch_spoonacular_ingredients(self, recipe_id: str) -> Optional[List[Dict[str, str]]]:
        """Fetch real ingredients from Spoonacular"""
        if not self.spoonacular_api_key:
            logger.warning("No Spoonacular API key found. Cannot fetch ingredients from Spoonacular.")
            return None
        
        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = f"{self.spoonacular_url}/{recipe_id}/ingredientWidget.json"
                params = {'apiKey': self.spoonacular_api_key}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'ingredients' in data:
                            ingredients = []
                            for ing in data['ingredients']:
                                ingredients.append({
                                    'name': ing.get('name', ''),
                                    'measure': ing.get('amount', {}).get('metric', {}).get('unit', ''),
                                    'original': f"{ing.get('amount', {}).get('metric', {}).get('value', '')} {ing.get('amount', {}).get('metric', {}).get('unit', '')} {ing.get('name', '')}".strip()
                                })
                            
                            logger.info(f"✅ Fetched {len(ingredients)} real ingredients from Spoonacular for recipe {recipe_id}")
                            return ingredients
                        else:
                            logger.warning(f"No ingredients found in Spoonacular response for recipe {recipe_id}")
                    else:
                        logger.warning(f"Spoonacular API returned status {response.status} for recipe {recipe_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching from Spoonacular for recipe {recipe_id}: {e}")
            return None
    
    async def fetch_real_ingredients_for_recipe(self, recipe_id: str) -> Optional[List[Dict[str, str]]]:
        """Fetch real ingredients for a specific recipe from its original source"""
        try:
            # Get the recipe from ChromaDB
            results = self.recipe_collection.get(ids=[recipe_id])
            if not results['documents']:
                logger.warning(f"Recipe {recipe_id} not found in ChromaDB")
                return None
            
            recipe_doc = results['documents'][0]
            recipe = json.loads(recipe_doc)
            
            # Check if ingredients are already present
            if recipe.get('ingredients') and len(recipe['ingredients']) > 0:
                logger.info(f"Recipe {recipe_id} already has ingredients, skipping")
                return None
            
            title = recipe.get('title', 'Unknown Recipe')
            logger.info(f"🔍 Fetching real ingredients for: {title}")
            
            # Try TheMealDB first
            if 'mealdb' in recipe_id.lower():
                mealdb_id = recipe_id.replace('mealdb_', '')
                logger.info(f"Attempting to fetch from TheMealDB: {mealdb_id}")
                
                ingredients = await self.fetch_mealdb_ingredients(mealdb_id)
                if ingredients:
                    return ingredients
            
            # Try Spoonacular
            elif recipe_id.isdigit() and len(recipe_id) > 6:
                logger.info(f"Attempting to fetch from Spoonacular: {recipe_id}")
                
                ingredients = await self.fetch_spoonacular_ingredients(recipe_id)
                if ingredients:
                    return ingredients
            
            # If we can't determine the source, log it
            else:
                logger.warning(f"Could not determine source for recipe {recipe_id}: {title}")
                logger.warning(f"Recipe ID format: {recipe_id}")
                logger.warning(f"Recipe source field: {recipe.get('source', 'not set')}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching ingredients for recipe {recipe_id}: {e}")
            return None
    
    async def fetch_all_missing_ingredients(self) -> Dict[str, Any]:
        """Fetch real ingredients for all recipes that are missing them"""
        logger.info("🚀 Starting to fetch real ingredients for all missing recipes...")
        
        # First analyze the current state
        source_analysis = self.analyze_recipe_sources()
        
        logger.info(f"📊 Analysis Results:")
        logger.info(f"   Total recipes: {source_analysis['total_recipes']}")
        logger.info(f"   Recipes with ingredients: {source_analysis['recipes_with_ingredients']}")
        logger.info(f"   Recipes missing ingredients: {source_analysis['recipes_missing_ingredients']}")
        logger.info(f"   TheMealDB recipes: {len(source_analysis['mealdb_recipes'])}")
        logger.info(f"   Spoonacular recipes: {len(source_analysis['spoonacular_recipes'])}")
        logger.info(f"   Unknown source recipes: {len(source_analysis['unknown_source_recipes'])}")
        
        # Focus on recipes missing ingredients
        missing_ingredient_recipes = []
        
        # Check TheMealDB recipes
        for recipe in source_analysis['mealdb_recipes']:
            if not recipe['has_ingredients']:
                missing_ingredient_recipes.append(('mealdb', recipe['id']))
        
        # Check Spoonacular recipes
        for recipe in source_analysis['spoonacular_recipes']:
            if not recipe['has_ingredients']:
                missing_ingredient_recipes.append(('spoonacular', recipe['id']))
        
        # Check unknown source recipes
        for recipe in source_analysis['unknown_source_recipes']:
            if not recipe['has_ingredients']:
                missing_ingredient_recipes.append(('unknown', recipe['id']))
        
        logger.info(f"\n🎯 Found {len(missing_ingredient_recipes)} recipes missing ingredients")
        
        # Track progress
        success_count = 0
        failed_count = 0
        
        for i, (source_type, recipe_id) in enumerate(missing_ingredient_recipes):
            try:
                logger.info(f"\n📝 Processing recipe {i+1}/{len(missing_ingredient_recipes)}: {recipe_id} (Source: {source_type})")
                
                ingredients = await self.fetch_real_ingredients_for_recipe(recipe_id)
                
                if ingredients:
                    # Update the recipe in ChromaDB with real ingredients
                    results = self.recipe_collection.get(ids=[recipe_id])
                    recipe_doc = results['documents'][0]
                    recipe = json.loads(recipe_doc)
                    
                    recipe['ingredients'] = ingredients
                    recipe['updated_at'] = datetime.utcnow().isoformat()
                    recipe['metadata'] = recipe.get('metadata', {})
                    recipe['metadata']['ingredients_fetched'] = True
                    recipe['metadata']['ingredients_source'] = source_type
                    
                    updated_doc = json.dumps(recipe)
                    self.recipe_collection.update(
                        ids=[recipe_id],
                        documents=[updated_doc],
                        metadatas=[self._extract_metadata(recipe)]
                    )
                    
                    logger.info(f"✅ Successfully updated {recipe.get('title', 'Unknown')} with {len(ingredients)} real ingredients")
                    success_count += 1
                else:
                    logger.warning(f"❌ Failed to fetch ingredients for recipe {recipe_id}")
                    failed_count += 1
                
                # Add delay to avoid overwhelming APIs
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing recipe {recipe_id}: {e}")
                failed_count += 1
        
        logger.info(f"\n🎉 Ingredient fetching completed!")
        logger.info(f"   Successfully fetched: {success_count}")
        logger.info(f"   Failed to fetch: {failed_count}")
        
        return {
            'total_missing': len(missing_ingredient_recipes),
            'success_count': success_count,
            'failed_count': failed_count
        }
    
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
                "source": recipe.get('source', 'unknown'),
            }
            
            # Add optional fields
            if recipe.get('tags'):
                metadata["tags"] = ','.join(recipe['tags'])
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}

async def main():
    """Main function"""
    try:
        fetcher = RealIngredientFetcher()
        
        logger.info("🚀 Starting real ingredient fetching process...")
        
        # Fetch all missing ingredients
        results = await fetcher.fetch_all_missing_ingredients()
        
        logger.info("🎉 Real ingredient fetching process completed!")
        logger.info(f"Results: {json.dumps(results, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())
