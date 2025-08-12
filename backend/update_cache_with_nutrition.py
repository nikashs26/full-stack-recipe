#!/usr/bin/env python3
"""
Script to update the recipe cache with nutrition data that was already analyzed.
This script reads the nutrition analysis results and updates recipes in the cache.
"""

import json
import logging
import sys
from pathlib import Path

# Add the services directory to the Python path
sys.path.append(str(Path(__file__).parent / 'services'))

from recipe_cache_service import RecipeCacheService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_cache_with_nutrition():
    """Update recipe cache with nutrition data"""
    try:
        logger.info("Starting nutrition data update for recipe cache...")
        
        # Initialize the cache service
        cache_service = RecipeCacheService()
        
        # Load the nutrition analysis results
        nutrition_file = "nutrition_analysis_results_1333_recipes.json"
        logger.info(f"Loading nutrition data from {nutrition_file}...")
        
        with open(nutrition_file, 'r', encoding='utf-8') as f:
            nutrition_data = json.load(f)
        
        results = nutrition_data.get('results', [])
        logger.info(f"Found {len(results)} nutrition analysis results")
        
        # Track statistics
        updated_count = 0
        not_found_count = 0
        error_count = 0
        
        # Process each nutrition result
        for i, result in enumerate(results):
            if result.get('status') != 'success':
                continue
                
            recipe_id = result.get('recipe_id')
            nutrition = result.get('nutrition', {})
            
            if not recipe_id or not nutrition:
                continue
            
            try:
                # Get the recipe from cache
                recipe = cache_service.get_recipe_by_id(recipe_id)
                
                if recipe:
                    # Add nutrition data to recipe
                    recipe['nutrition'] = nutrition
                    recipe['nutrition_analyzed_at'] = result.get('analyzed_at')
                    recipe['nutrition_llm_service'] = result.get('llm_service')
                    
                    # Update recipe in cache
                    success = cache_service.add_recipe(recipe)
                    if success:
                        updated_count += 1
                        if updated_count % 100 == 0:
                            logger.info(f"Updated {updated_count} recipes...")
                    else:
                        logger.warning(f"Failed to update recipe {recipe_id} in cache")
                        error_count += 1
                else:
                    logger.warning(f"Recipe {recipe_id} not found in cache")
                    not_found_count += 1
                    
            except Exception as e:
                logger.error(f"Error updating recipe {recipe_id}: {e}")
                error_count += 1
                continue
        
        # Print summary
        logger.info("=" * 50)
        logger.info("NUTRITION UPDATE SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total nutrition results: {len(results)}")
        logger.info(f"Successfully updated: {updated_count}")
        logger.info(f"Not found in cache: {not_found_count}")
        logger.info(f"Errors: {error_count}")
        logger.info(f"Success rate: {updated_count/len(results)*100:.1f}%")
        
        return {
            'total_results': len(results),
            'updated': updated_count,
            'not_found': not_found_count,
            'errors': error_count
        }
        
    except Exception as e:
        logger.error(f"Unexpected error during nutrition update: {e}")
        raise

def main():
    """Main function"""
    try:
        result = update_cache_with_nutrition()
        print(f"\n✅ Nutrition update completed successfully!")
        print(f"📊 Updated {result['updated']} recipes with nutrition data")
        print(f"🔍 Your recipes now include calories, carbs, fat, and protein!")
        
    except Exception as e:
        logger.error(f"Failed to update nutrition data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 