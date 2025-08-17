#!/usr/bin/env python3
"""
Enhanced Script to Fix Missing Ingredients in Recipes

This script handles missing ingredients for both TheMealDB and Spoonacular recipes.
It attempts to fetch missing data from APIs and generates fallback ingredients when needed.
"""

import asyncio
import aiohttp
import json
import logging
import ssl
import certifi
import re
from typing import List, Dict, Any, Optional
import chromadb
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedIngredientFixer:
    def __init__(self):
        """Initialize the enhanced ingredient fixer"""
        self.themealdb_url = "https://www.themealdb.com/api/json/v1/1"
        self.spoonacular_url = "https://api.spoonacular.com/recipes"
        
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
    
    def is_mealdb_id(self, recipe_id: str) -> bool:
        """Check if recipe ID is from TheMealDB"""
        return recipe_id.startswith('mealdb_') or recipe_id.isdigit()
    
    def is_spoonacular_id(self, recipe_id: str) -> bool:
        """Check if recipe ID is from Spoonacular"""
        return recipe_id.isdigit() and len(recipe_id) > 6
    
    async def fetch_mealdb_recipe(self, meal_id: str) -> Optional[Dict[str, Any]]:
        """Fetch recipe from TheMealDB"""
        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = f"{self.themealdb_url}/lookup.php?i={meal_id}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('meals') and len(data['meals']) > 0:
                            return data['meals'][0]
            return None
        except Exception as e:
            logger.error(f"Error fetching TheMealDB recipe {meal_id}: {e}")
            return None
    
    def extract_mealdb_ingredients(self, recipe_data: Dict[str, Any]) -> List[Dict[str, str]]:
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
    
    def generate_fallback_ingredients(self, recipe_title: str, source: str = "unknown") -> List[Dict[str, str]]:
        """Generate fallback ingredients based on recipe title and common patterns"""
        title_lower = recipe_title.lower()
        
        # Common ingredient patterns based on recipe types
        fallback_ingredients = []
        
        # Basic ingredients that most recipes need
        basic_ingredients = [
            {'name': 'salt', 'measure': 'to taste', 'original': 'salt to taste'},
            {'name': 'black pepper', 'measure': 'to taste', 'original': 'black pepper to taste'},
            {'name': 'olive oil', 'measure': '2 tablespoons', 'original': '2 tablespoons olive oil'}
        ]
        
        # Add basic ingredients
        fallback_ingredients.extend(basic_ingredients)
        
        # Add ingredients based on recipe type
        if 'pasta' in title_lower or 'noodle' in title_lower:
            fallback_ingredients.extend([
                {'name': 'pasta', 'measure': '8 ounces', 'original': '8 ounces pasta'},
                {'name': 'garlic', 'measure': '3 cloves', 'original': '3 cloves garlic, minced'},
                {'name': 'onion', 'measure': '1 medium', 'original': '1 medium onion, diced'}
            ])
        
        if 'soup' in title_lower or 'stew' in title_lower:
            fallback_ingredients.extend([
                {'name': 'vegetables', 'measure': '2 cups', 'original': '2 cups mixed vegetables'},
                {'name': 'broth', 'measure': '4 cups', 'original': '4 cups vegetable or chicken broth'},
                {'name': 'herbs', 'measure': '1 tablespoon', 'original': '1 tablespoon fresh herbs'}
            ])
        
        if 'salad' in title_lower:
            fallback_ingredients.extend([
                {'name': 'lettuce', 'measure': '1 head', 'original': '1 head lettuce'},
                {'name': 'tomatoes', 'measure': '2 medium', 'original': '2 medium tomatoes'},
                {'name': 'cucumber', 'measure': '1 medium', 'original': '1 medium cucumber'}
            ])
        
        if 'chicken' in title_lower:
            fallback_ingredients.extend([
                {'name': 'chicken breast', 'measure': '4 pieces', 'original': '4 chicken breasts'},
                {'name': 'seasoning', 'measure': '2 tablespoons', 'original': '2 tablespoons seasoning blend'}
            ])
        
        if 'fish' in title_lower or 'salmon' in title_lower:
            fallback_ingredients.extend([
                {'name': 'fish fillets', 'measure': '4 pieces', 'original': '4 fish fillets'},
                {'name': 'lemon', 'measure': '1 medium', 'original': '1 medium lemon'},
                {'name': 'herbs', 'measure': '2 tablespoons', 'original': '2 tablespoons fresh herbs'}
            ])
        
        if 'vegetable' in title_lower or 'veggie' in title_lower:
            fallback_ingredients.extend([
                {'name': 'mixed vegetables', 'measure': '3 cups', 'original': '3 cups mixed vegetables'},
                {'name': 'olive oil', 'measure': '3 tablespoons', 'original': '3 tablespoons olive oil'},
                {'name': 'garlic', 'measure': '2 cloves', 'original': '2 cloves garlic, minced'}
            ])
        
        # Add source-specific note
        if source == "TheMealDB":
            fallback_ingredients.append({
                'name': 'Note', 
                'measure': '', 
                'original': 'Ingredients generated from recipe title - please verify quantities'
            })
        elif source == "Spoonacular":
            fallback_ingredients.append({
                'name': 'Note', 
                'measure': '', 
                'original': 'Ingredients generated from recipe title - please verify quantities'
            })
        
        return fallback_ingredients
    
    def normalize_recipe_with_ingredients(self, recipe_data: Dict[str, Any], source: str = "unknown") -> Dict[str, Any]:
        """Normalize recipe data and ensure it has ingredients"""
        try:
            # Extract ingredients based on source
            if source == "TheMealDB":
                ingredients = self.extract_mealdb_ingredients(recipe_data)
            else:
                ingredients = []
            
            # If no ingredients found, generate fallback
            if not ingredients:
                title = recipe_data.get('strMeal', recipe_data.get('title', 'Untitled Recipe'))
                ingredients = self.generate_fallback_ingredients(title, source)
                logger.info(f"Generated {len(ingredients)} fallback ingredients for: {title}")
            
            # Handle instructions
            instructions = recipe_data.get('strInstructions', recipe_data.get('instructions', ''))
            if instructions:
                # Split instructions into steps
                steps = re.split(r'[.!?]+', instructions)
                steps = [s.strip() for s in steps if s.strip() and len(s.strip()) > 10]
                
                if not steps:
                    steps = [instructions.strip()]
            else:
                steps = ['No instructions provided.']
            
            # Build normalized recipe
            normalized = {
                'id': recipe_data.get('id', f"{source.lower()}_{recipe_data.get('idMeal', 'unknown')}"),
                'title': str(recipe_data.get('strMeal', recipe_data.get('title', 'Untitled Recipe')) or 'Untitled Recipe').strip(),
                'image': str(recipe_data.get('strMealThumb', recipe_data.get('image', '')) or ''),
                'source': source,
                'source_url': str(recipe_data.get('strSource', recipe_data.get('sourceUrl', '')) or ''),
                'ingredients': ingredients,
                'instructions': steps,
                'prep_time': recipe_data.get('prep_time', None),
                'cook_time': recipe_data.get('cook_time', None),
                'cuisines': [],
                'tags': [],
                'nutrition': recipe_data.get('nutrition', {}),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'metadata': {
                    'source_id': recipe_data.get('idMeal', recipe_data.get('id', '')),
                    'source': source,
                    'ingredients_generated': len(ingredients) > 0 and source != "TheMealDB",
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
            
            title = recipe.get('title', 'Unknown Recipe')
            logger.info(f"Fixing missing ingredients for: {title}")
            
            # Try to fetch from TheMealDB first
            if self.is_mealdb_id(recipe_id):
                mealdb_id = recipe_id.replace('mealdb_', '') if 'mealdb_' in recipe_id else recipe_id
                logger.info(f"Attempting to fetch from TheMealDB: {mealdb_id}")
                
                fresh_data = await self.fetch_mealdb_recipe(mealdb_id)
                if fresh_data:
                    normalized_recipe = self.normalize_recipe_with_ingredients(fresh_data, "TheMealDB")
                    if normalized_recipe:
                        # Update the recipe in ChromaDB
                        updated_doc = json.dumps(normalized_recipe)
                        self.recipe_collection.update(
                            ids=[recipe_id],
                            documents=[updated_doc],
                            metadatas=[self._extract_metadata(normalized_recipe)]
                        )
                        logger.info(f"✅ Updated {title} with {len(normalized_recipe['ingredients'])} ingredients from TheMealDB")
                        return True
            
            # If TheMealDB failed or not applicable, generate fallback ingredients
            logger.info(f"Generating fallback ingredients for: {title}")
            fallback_ingredients = self.generate_fallback_ingredients(title, "unknown")
            
            # Update recipe with fallback ingredients
            recipe['ingredients'] = fallback_ingredients
            recipe['updated_at'] = datetime.utcnow().isoformat()
            recipe['metadata'] = recipe.get('metadata', {})
            recipe['metadata']['ingredients_generated'] = True
            recipe['metadata']['ingredients_source'] = 'fallback'
            
            updated_doc = json.dumps(recipe)
            self.recipe_collection.update(
                ids=[recipe_id],
                documents=[updated_doc],
                metadatas=[self._extract_metadata(recipe)]
            )
            
            logger.info(f"✅ Updated {title} with {len(fallback_ingredients)} fallback ingredients")
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
                "source": recipe.get('source', 'unknown'),
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
        fixer = EnhancedIngredientFixer()
        
        logger.info("Starting enhanced ingredient fix process...")
        
        # Fix all missing ingredients
        results = await fixer.fix_all_missing_ingredients()
        
        logger.info("Enhanced ingredient fix process completed!")
        logger.info(f"Results: {json.dumps(results, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())
