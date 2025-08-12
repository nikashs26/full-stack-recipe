#!/usr/bin/env python3
"""
Script to analyze all recipes in the cache and add nutritional information.
This script should only be run once to populate nutrition data for all recipes.
"""

import os
import sys
import asyncio
import json
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from services.nutrition_analysis_agent import NutritionAnalysisAgent
from services.recipe_cache_service import RecipeCacheService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nutrition_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def analyze_all_recipes():
    """
    Analyze all recipes in the cache and add nutritional information.
    """
    try:
        logger.info("Starting nutrition analysis for all recipes...")
        
        # Initialize services
        recipe_cache = RecipeCacheService()
        nutrition_agent = NutritionAnalysisAgent()
        
        # Get all recipes from the cache
        logger.info("Fetching all recipes from cache...")
        all_recipes = []
        
        # Get recipes from the recipe collection
        try:
            # Get all documents from the recipe collection
            results = recipe_cache.recipe_collection.get()
            
            for i, (id_, document, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
                if metadata and 'id' in metadata:
                    # Reconstruct recipe from metadata
                    recipe = {
                        'id': metadata['id'],
                        'title': metadata.get('title', 'Unknown Recipe'),
                        'servings': metadata.get('servings', 1),
                        'ingredients': metadata.get('ingredients', []),
                        'instructions': metadata.get('instructions', []),
                        'metadata': metadata
                    }
                    all_recipes.append(recipe)
                    
                    if (i + 1) % 100 == 0:
                        logger.info(f"Loaded {i + 1} recipes...")
            
            logger.info(f"Total recipes loaded: {len(all_recipes)}")
            
        except Exception as e:
            logger.error(f"Failed to load recipes from cache: {e}")
            return
        
        if not all_recipes:
            logger.warning("No recipes found in cache")
            return
        
        # Analyze recipes in batches
        logger.info("Starting nutrition analysis...")
        batch_size = 3  # Conservative batch size to avoid overwhelming LLM services
        
        results = await nutrition_agent.analyze_multiple_recipes(all_recipes, batch_size=batch_size)
        
        # Save results
        output_file = f"nutrition_analysis_results_{len(all_recipes)}_recipes.json"
        saved_file = nutrition_agent.save_nutrition_results(results, output_file)
        
        # Update recipes in cache with nutrition data
        logger.info("Updating recipes in cache with nutrition data...")
        updated_count = 0
        
        for result in results:
            if result.get('status') == 'success' and 'nutrition' in result:
                try:
                    recipe_id = result['recipe_id']
                    nutrition_data = result['nutrition']
                    
                    # Get the recipe from cache
                    recipe = recipe_cache.get_recipe_by_id(recipe_id)
                    if recipe:
                        # Add nutrition data to recipe
                        recipe['nutrition'] = nutrition_data
                        recipe['nutrition_analyzed_at'] = result['analyzed_at']
                        recipe['nutrition_llm_service'] = result['llm_service']
                        
                        # Update recipe in cache
                        success = await recipe_cache.add_recipe(recipe)
                        if success:
                            updated_count += 1
                        else:
                            logger.warning(f"Failed to update recipe {recipe_id} in cache")
                    
                except Exception as e:
                    logger.error(f"Failed to update recipe {result.get('recipe_id')}: {e}")
                    continue
        
        logger.info(f"Successfully updated {updated_count} recipes with nutrition data")
        
        # Generate summary report
        summary = {
            'total_recipes': len(all_recipes),
            'successful_analyses': len([r for r in results if r.get('status') == 'success']),
            'failed_analyses': len([r for r in results if r.get('status') == 'error']),
            'updated_in_cache': updated_count,
            'analysis_date': results[0]['analyzed_at'] if results else None,
            'output_file': saved_file
        }
        
        # Save summary
        summary_file = 'nutrition_analysis_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analysis complete! Summary saved to {summary_file}")
        logger.info(f"Success rate: {summary['successful_analyses']/summary['total_recipes']:.1%}")
        logger.info(f"Updated {summary['updated_in_cache']} recipes in cache")
        
        return summary
        
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        raise

async def analyze_specific_recipes(recipe_ids: list):
    """
    Analyze specific recipes by ID.
    
    Args:
        recipe_ids: List of recipe IDs to analyze
    """
    try:
        logger.info(f"Starting nutrition analysis for {len(recipe_ids)} specific recipes...")
        
        # Initialize services
        recipe_cache = RecipeCacheService()
        nutrition_agent = NutritionAnalysisAgent()
        
        # Get specific recipes
        recipes_to_analyze = []
        for recipe_id in recipe_ids:
            recipe = recipe_cache.get_recipe_by_id(recipe_id)
            if recipe:
                recipes_to_analyze.append(recipe)
            else:
                logger.warning(f"Recipe {recipe_id} not found in cache")
        
        if not recipes_to_analyze:
            logger.warning("No recipes found to analyze")
            return
        
        # Analyze recipes
        results = await nutrition_agent.analyze_multiple_recipes(recipes_to_analyze, batch_size=3)
        
        # Save results
        output_file = f"nutrition_analysis_specific_{len(recipe_ids)}_recipes.json"
        saved_file = nutrition_agent.save_nutrition_results(results, output_file)
        
        logger.info(f"Analysis complete! Results saved to {saved_file}")
        return results
        
    except Exception as e:
        logger.error(f"Error analyzing specific recipes: {e}")
        raise

def main():
    """Main function to run the nutrition analysis"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze recipes for nutritional information')
    parser.add_argument('--specific-ids', nargs='+', help='Specific recipe IDs to analyze')
    parser.add_argument('--all', action='store_true', help='Analyze all recipes in cache')
    
    args = parser.parse_args()
    
    if args.specific_ids:
        # Analyze specific recipes
        asyncio.run(analyze_specific_recipes(args.specific_ids))
    elif args.all:
        # Analyze all recipes
        asyncio.run(analyze_all_recipes())
    else:
        print("Please specify --all to analyze all recipes or --specific-ids with recipe IDs")
        print("Example: python analyze_all_recipes_nutrition.py --all")
        print("Example: python analyze_all_recipes_nutrition.py --specific-ids recipe1 recipe2")

if __name__ == "__main__":
    main() 