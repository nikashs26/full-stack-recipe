#!/usr/bin/env python3
"""
Script to analyze recipes and identify which ones are missing cuisine tags,
then add appropriate cuisine tags based on recipe content.
"""

import chromadb
import json
import logging
from typing import Dict, List, Any, Optional
from collections import Counter

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_recipe_cuisines():
    """Analyze all recipes to identify missing or invalid cuisine tags."""
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path="./backend/chroma_db")
        collection = client.get_collection('recipe_details_cache')
        
        # Get all recipes
        all_recipes = collection.get(include=['metadatas', 'documents'])
        
        logger.info(f"Analyzing {len(all_recipes['ids'])} recipes...")
        
        # Statistics
        stats = {
            'total_recipes': len(all_recipes['ids']),
            'missing_cuisine': 0,
            'empty_cuisine': 0,
            'invalid_cuisine': 0,
            'valid_cuisine': 0,
            'cuisine_distribution': Counter(),
            'recipes_missing_cuisine': []
        }
        
        # Common invalid cuisine values
        invalid_cuisines = {'', 'none', 'null', 'other', 'unknown', 'n/a', 'na', 'undefined'}
        
        for i, (recipe_id, metadata, document) in enumerate(zip(
            all_recipes['ids'], 
            all_recipes['metadatas'], 
            all_recipes['documents']
        )):
            try:
                # Parse recipe data
                recipe_data = json.loads(document) if isinstance(document, str) else document
                
                # Get cuisine from metadata
                cuisine_meta = metadata.get('cuisine', '').lower().strip() if metadata.get('cuisine') else ''
                
                # Get cuisine from recipe data
                cuisine_recipe = recipe_data.get('cuisine', '').lower().strip() if recipe_data.get('cuisine') else ''
                cuisines_recipe = recipe_data.get('cuisines', [])
                
                # Determine the actual cuisine
                actual_cuisine = None
                if cuisine_meta and cuisine_meta not in invalid_cuisines:
                    actual_cuisine = cuisine_meta
                elif cuisine_recipe and cuisine_recipe not in invalid_cuisines:
                    actual_cuisine = cuisine_recipe
                elif cuisines_recipe and isinstance(cuisines_recipe, list) and cuisines_recipe:
                    # Use first cuisine from array
                    first_cuisine = cuisines_recipe[0]
                    if isinstance(first_cuisine, str) and first_cuisine.lower().strip() not in invalid_cuisines:
                        actual_cuisine = first_cuisine.lower().strip()
                
                # Categorize the recipe
                if not actual_cuisine:
                    stats['missing_cuisine'] += 1
                    stats['recipes_missing_cuisine'].append({
                        'id': recipe_id,
                        'title': recipe_data.get('title', recipe_data.get('name', 'Unknown')),
                        'metadata_cuisine': metadata.get('cuisine', ''),
                        'recipe_cuisine': recipe_data.get('cuisine', ''),
                        'recipe_cuisines': cuisines_recipe,
                        'ingredients': recipe_data.get('ingredients', [])[:5]  # First 5 ingredients
                    })
                elif actual_cuisine in invalid_cuisines:
                    stats['invalid_cuisine'] += 1
                    stats['recipes_missing_cuisine'].append({
                        'id': recipe_id,
                        'title': recipe_data.get('title', recipe_data.get('name', 'Unknown')),
                        'metadata_cuisine': metadata.get('cuisine', ''),
                        'recipe_cuisine': recipe_data.get('cuisine', ''),
                        'recipe_cuisines': cuisines_recipe,
                        'ingredients': recipe_data.get('ingredients', [])[:5]
                    })
                else:
                    stats['valid_cuisine'] += 1
                    stats['cuisine_distribution'][actual_cuisine] += 1
                
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1}/{len(all_recipes['ids'])} recipes...")
                    
            except Exception as e:
                logger.error(f"Error processing recipe {recipe_id}: {e}")
                continue
        
        # Print statistics
        logger.info("\n" + "="*60)
        logger.info("CUISINE ANALYSIS RESULTS")
        logger.info("="*60)
        logger.info(f"Total recipes: {stats['total_recipes']}")
        logger.info(f"Valid cuisine: {stats['valid_cuisine']}")
        logger.info(f"Missing cuisine: {stats['missing_cuisine']}")
        logger.info(f"Invalid cuisine: {stats['invalid_cuisine']}")
        logger.info(f"Total needing fix: {stats['missing_cuisine'] + stats['invalid_cuisine']}")
        
        logger.info("\nTop 20 cuisines found:")
        for cuisine, count in stats['cuisine_distribution'].most_common(20):
            logger.info(f"  {cuisine}: {count}")
        
        # Save detailed results
        with open('cuisine_analysis_results.json', 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"\nDetailed results saved to 'cuisine_analysis_results.json'")
        logger.info(f"Recipes needing cuisine fixes: {len(stats['recipes_missing_cuisine'])}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error analyzing recipe cuisines: {e}")
        raise

def detect_cuisine_from_recipe(recipe_data: Dict[str, Any]) -> str:
    """Detect cuisine from recipe ingredients, title, and other content."""
    
    # Common ingredient to cuisine mappings
    INGREDIENT_CUISINE_MAP = {
        # Italian
        'pasta': 'Italian', 'risotto': 'Italian', 'pesto': 'Italian', 'pancetta': 'Italian',
        'prosciutto': 'Italian', 'mozzarella': 'Italian', 'parmesan': 'Italian',
        'bruschetta': 'Italian', 'tiramisu': 'Italian', 'gnocchi': 'Italian',
        'bolognese': 'Italian', 'carbonara': 'Italian', 'marinara': 'Italian',
        
        # Mexican
        'taco': 'Mexican', 'burrito': 'Mexican', 'quesadilla': 'Mexican',
        'guacamole': 'Mexican', 'salsa': 'Mexican', 'enchilada': 'Mexican',
        'tamale': 'Mexican', 'mole': 'Mexican', 'pico de gallo': 'Mexican',
        'jalapeno': 'Mexican', 'cilantro': 'Mexican', 'lime': 'Mexican',
        
        # Indian
        'curry': 'Indian', 'masala': 'Indian', 'tikka': 'Indian', 'biryani': 'Indian',
        'naan': 'Indian', 'samosas': 'Indian', 'dal': 'Indian', 'vindaloo': 'Indian',
        'tandoori': 'Indian', 'paneer': 'Indian', 'chutney': 'Indian', 'roti': 'Indian',
        'garam masala': 'Indian', 'turmeric': 'Indian', 'cardamom': 'Indian',
        
        # Chinese
        'dumpling': 'Chinese', 'wonton': 'Chinese', 'kung pao': 'Chinese',
        'sweet and sour': 'Chinese', 'chow mein': 'Chinese', 'lo mein': 'Chinese',
        'peking duck': 'Chinese', 'char siu': 'Chinese', 'bao': 'Chinese',
        'soy sauce': 'Chinese', 'hoisin': 'Chinese', 'oyster sauce': 'Chinese',
        
        # Japanese
        'sushi': 'Japanese', 'sashimi': 'Japanese', 'ramen': 'Japanese',
        'tempura': 'Japanese', 'teriyaki': 'Japanese', 'udon': 'Japanese',
        'miso': 'Japanese', 'wasabi': 'Japanese', 'bento': 'Japanese',
        'mirin': 'Japanese', 'sake': 'Japanese', 'dashi': 'Japanese',
        
        # Thai
        'pad thai': 'Thai', 'tom yum': 'Thai', 'green curry': 'Thai',
        'massaman': 'Thai', 'satay': 'Thai', 'papaya salad': 'Thai',
        'fish sauce': 'Thai', 'coconut milk': 'Thai', 'lemongrass': 'Thai',
        
        # French
        'ratatouille': 'French', 'quiche': 'French', 'crepe': 'French',
        'croissant': 'French', 'coq au vin': 'French', 'bouillabaisse': 'French',
        'herbes de provence': 'French', 'brie': 'French', 'camembert': 'French',
        
        # Mediterranean
        'hummus': 'Mediterranean', 'falafel': 'Mediterranean', 'tzatziki': 'Mediterranean',
        'tabbouleh': 'Mediterranean', 'pita': 'Mediterranean', 'baba ghanoush': 'Mediterranean',
        'feta': 'Mediterranean', 'olives': 'Mediterranean', 'olive oil': 'Mediterranean',
        
        # American
        'burger': 'American', 'hot dog': 'American', 'barbecue': 'American',
        'mac and cheese': 'American', 'apple pie': 'American', 'fried chicken': 'American',
        'biscuits and gravy': 'American', 'cornbread': 'American', 'grits': 'American',
        
        # British
        'fish and chips': 'British', 'bangers and mash': 'British', 'shepherd\'s pie': 'British',
        'yorkshire pudding': 'British', 'black pudding': 'British', 'marmite': 'British',
        
        # German
        'sauerkraut': 'German', 'bratwurst': 'German', 'pretzel': 'German',
        'schnitzel': 'German', 'spaetzle': 'German', 'beer': 'German',
        
        # Korean
        'kimchi': 'Korean', 'bulgogi': 'Korean', 'bibimbap': 'Korean',
        'gochujang': 'Korean', 'soju': 'Korean', 'korean': 'Korean',
        
        # Vietnamese
        'pho': 'Vietnamese', 'banh mi': 'Vietnamese', 'spring roll': 'Vietnamese',
        'nuoc mam': 'Vietnamese', 'fish sauce': 'Vietnamese',
        
        # Spanish
        'paella': 'Spanish', 'tapas': 'Spanish', 'chorizo': 'Spanish',
        'sangria': 'Spanish', 'gazpacho': 'Spanish', 'sherry': 'Spanish',
        
        # Greek
        'moussaka': 'Greek', 'baklava': 'Greek', 'gyro': 'Greek',
        'feta': 'Greek', 'olives': 'Greek', 'oregano': 'Greek',
        
        # Middle Eastern
        'kebab': 'Middle Eastern', 'pita': 'Middle Eastern', 'tahini': 'Middle Eastern',
        'sumac': 'Middle Eastern', 'za\'atar': 'Middle Eastern'
    }
    
    # Get recipe text for analysis
    title = recipe_data.get('title', recipe_data.get('name', '')).lower()
    ingredients = recipe_data.get('ingredients', [])
    instructions = recipe_data.get('instructions', [])
    
    # Convert ingredients to text
    ingredient_text = ' '.join([
        str(ingredient).lower() 
        for ingredient in ingredients 
        if isinstance(ingredient, (str, dict))
    ])
    
    # Convert instructions to text
    instruction_text = ' '.join([
        str(instruction).lower() 
        for instruction in instructions 
        if isinstance(instruction, str)
    ])
    
    # Combine all text for analysis
    all_text = f"{title} {ingredient_text} {instruction_text}"
    
    # Check for cuisine indicators
    cuisine_scores = Counter()
    
    # Check ingredient mappings
    for ingredient, cuisine in INGREDIENT_CUISINE_MAP.items():
        if ingredient in all_text:
            cuisine_scores[cuisine] += 1
    
    # Check title patterns
    title_patterns = {
        'pasta': 'Italian', 'pizza': 'Italian', 'risotto': 'Italian',
        'taco': 'Mexican', 'burrito': 'Mexican', 'enchilada': 'Mexican',
        'curry': 'Indian', 'biryani': 'Indian', 'tikka': 'Indian',
        'dumpling': 'Chinese', 'chow mein': 'Chinese', 'lo mein': 'Chinese',
        'sushi': 'Japanese', 'ramen': 'Japanese', 'tempura': 'Japanese',
        'pad thai': 'Thai', 'tom yum': 'Thai', 'green curry': 'Thai',
        'ratatouille': 'French', 'quiche': 'French', 'crepe': 'French',
        'hummus': 'Mediterranean', 'falafel': 'Mediterranean', 'tzatziki': 'Mediterranean',
        'burger': 'American', 'barbecue': 'American', 'fried chicken': 'American',
        'fish and chips': 'British', 'shepherd\'s pie': 'British', 'bangers and mash': 'British',
        'paella': 'Spanish', 'tapas': 'Spanish', 'gazpacho': 'Spanish',
        'moussaka': 'Greek', 'baklava': 'Greek', 'gyro': 'Greek',
        'pho': 'Vietnamese', 'banh mi': 'Vietnamese', 'spring roll': 'Vietnamese',
        'kimchi': 'Korean', 'bulgogi': 'Korean', 'bibimbap': 'Korean'
    }
    
    for pattern, cuisine in title_patterns.items():
        if pattern in title:
            cuisine_scores[cuisine] += 2  # Higher weight for title matches
    
    # Return the most likely cuisine
    if cuisine_scores:
        return cuisine_scores.most_common(1)[0][0]
    
    # Fallback: check for common cooking methods
    cooking_methods = {
        'stir-fry': 'Chinese', 'deep-fry': 'Chinese', 'steam': 'Chinese',
        'grill': 'American', 'barbecue': 'American', 'smoke': 'American',
        'braise': 'French', 'sauté': 'French', 'flambé': 'French',
        'roast': 'British', 'bake': 'British', 'boil': 'British'
    }
    
    for method, cuisine in cooking_methods.items():
        if method in all_text:
            return cuisine
    
    # If no specific cuisine detected, return empty string
    return ""

def fix_missing_cuisines():
    """Fix recipes that are missing cuisine tags."""
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path="./backend/chroma_db")
        collection = client.get_collection('recipe_details_cache')
        
        # Load analysis results
        try:
            with open('cuisine_analysis_results.json', 'r') as f:
                analysis_results = json.load(f)
        except FileNotFoundError:
            logger.error("Analysis results not found. Please run analyze_recipe_cuisines() first.")
            return
        
        recipes_to_fix = analysis_results['recipes_missing_cuisine']
        logger.info(f"Fixing cuisines for {len(recipes_to_fix)} recipes...")
        
        fixed_count = 0
        failed_count = 0
        
        for i, recipe_info in enumerate(recipes_to_fix):
            try:
                recipe_id = recipe_info['id']
                
                # Get current recipe data
                result = collection.get(ids=[recipe_id], include=['metadatas', 'documents'])
                if not result['documents']:
                    logger.warning(f"Recipe {recipe_id} not found")
                    failed_count += 1
                    continue
                
                document = result['documents'][0]
                metadata = result['metadatas'][0]
                
                # Parse recipe data
                recipe_data = json.loads(document) if isinstance(document, str) else document
                
                # Detect cuisine
                detected_cuisine = detect_cuisine_from_recipe(recipe_data)
                
                if detected_cuisine:
                    # Update metadata
                    metadata['cuisine'] = detected_cuisine
                    
                    # Update recipe data
                    recipe_data['cuisine'] = detected_cuisine
                    
                    # Update in database
                    collection.update(
                        ids=[recipe_id],
                        metadatas=[metadata],
                        documents=[json.dumps(recipe_data)]
                    )
                    
                    fixed_count += 1
                    logger.info(f"Fixed recipe {recipe_id}: '{recipe_info['title']}' -> {detected_cuisine}")
                else:
                    # If we can't detect cuisine, set to "International"
                    metadata['cuisine'] = 'International'
                    recipe_data['cuisine'] = 'International'
                    
                    collection.update(
                        ids=[recipe_id],
                        metadatas=[metadata],
                        documents=[json.dumps(recipe_data)]
                    )
                    
                    fixed_count += 1
                    logger.info(f"Set recipe {recipe_id}: '{recipe_info['title']}' -> International (fallback)")
                
                if (i + 1) % 50 == 0:
                    logger.info(f"Processed {i + 1}/{len(recipes_to_fix)} recipes...")
                    
            except Exception as e:
                logger.error(f"Error fixing recipe {recipe_info.get('id', 'unknown')}: {e}")
                failed_count += 1
                continue
        
        logger.info(f"\nCuisine fix completed:")
        logger.info(f"  Fixed: {fixed_count}")
        logger.info(f"  Failed: {failed_count}")
        logger.info(f"  Total processed: {fixed_count + failed_count}")
        
    except Exception as e:
        logger.error(f"Error fixing missing cuisines: {e}")
        raise

if __name__ == "__main__":
    print("Recipe Cuisine Analysis and Fix Tool")
    print("="*50)
    
    # Step 1: Analyze current state
    print("\n1. Analyzing current cuisine status...")
    stats = analyze_recipe_cuisines()
    
    # Step 2: Fix missing cuisines
    if stats['missing_cuisine'] + stats['invalid_cuisine'] > 0:
        print(f"\n2. Fixing {stats['missing_cuisine'] + stats['invalid_cuisine']} recipes with missing/invalid cuisines...")
        fix_missing_cuisines()
        
        # Step 3: Re-analyze to confirm fixes
        print("\n3. Re-analyzing to confirm fixes...")
        final_stats = analyze_recipe_cuisines()
        
        print(f"\nFinal Results:")
        print(f"  Recipes with valid cuisines: {final_stats['valid_cuisine']}")
        print(f"  Recipes still missing cuisines: {final_stats['missing_cuisine']}")
        print(f"  Improvement: {stats['missing_cuisine'] - final_stats['missing_cuisine']} recipes fixed")
    else:
        print("\nAll recipes already have valid cuisine tags!")
