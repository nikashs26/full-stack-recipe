#!/usr/bin/env python3
"""
Script to improve cuisine tags for recipes by detecting proper cuisines
based on recipe content instead of using generic "International" tags.
"""

import chromadb
import json
import logging
from typing import Dict, List, Any, Optional
from collections import Counter
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def detect_cuisine_from_recipe(recipe_data: Dict[str, Any]) -> str:
    """Detect cuisine from recipe ingredients, title, and other content."""
    
    # Enhanced ingredient to cuisine mappings
    INGREDIENT_CUISINE_MAP = {
        # Italian
        'pasta': 'Italian', 'risotto': 'Italian', 'pesto': 'Italian', 'pancetta': 'Italian',
        'prosciutto': 'Italian', 'mozzarella': 'Italian', 'parmesan': 'Italian',
        'bruschetta': 'Italian', 'tiramisu': 'Italian', 'gnocchi': 'Italian',
        'bolognese': 'Italian', 'carbonara': 'Italian', 'marinara': 'Italian',
        'basil': 'Italian', 'oregano': 'Italian', 'thyme': 'Italian',
        'ricotta': 'Italian', 'provolone': 'Italian', 'pecorino': 'Italian',
        'cannellini': 'Italian', 'farfalle': 'Italian', 'linguine': 'Italian',
        'penne': 'Italian', 'spaghetti': 'Italian', 'fettuccine': 'Italian',
        
        # Mexican
        'taco': 'Mexican', 'burrito': 'Mexican', 'quesadilla': 'Mexican',
        'guacamole': 'Mexican', 'salsa': 'Mexican', 'enchilada': 'Mexican',
        'tamale': 'Mexican', 'mole': 'Mexican', 'pico de gallo': 'Mexican',
        'jalapeno': 'Mexican', 'cilantro': 'Mexican', 'lime': 'Mexican',
        'cumin': 'Mexican', 'chili powder': 'Mexican', 'chipotle': 'Mexican',
        'queso': 'Mexican', 'tortilla': 'Mexican', 'refried beans': 'Mexican',
        'avocado': 'Mexican', 'tomatillo': 'Mexican', 'adobo': 'Mexican',
        
        # Indian
        'curry': 'Indian', 'masala': 'Indian', 'tikka': 'Indian', 'biryani': 'Indian',
        'naan': 'Indian', 'samosas': 'Indian', 'dal': 'Indian', 'vindaloo': 'Indian',
        'tandoori': 'Indian', 'paneer': 'Indian', 'chutney': 'Indian', 'roti': 'Indian',
        'garam masala': 'Indian', 'turmeric': 'Indian', 'cardamom': 'Indian',
        'cumin': 'Indian', 'coriander': 'Indian', 'ginger': 'Indian',
        'coconut milk': 'Indian', 'ghee': 'Indian', 'fenugreek': 'Indian',
        'asafoetida': 'Indian', 'mustard seeds': 'Indian', 'curry leaves': 'Indian',
        
        # Chinese
        'dumpling': 'Chinese', 'wonton': 'Chinese', 'kung pao': 'Chinese',
        'sweet and sour': 'Chinese', 'chow mein': 'Chinese', 'lo mein': 'Chinese',
        'peking duck': 'Chinese', 'char siu': 'Chinese', 'bao': 'Chinese',
        'soy sauce': 'Chinese', 'hoisin': 'Chinese', 'oyster sauce': 'Chinese',
        'sesame oil': 'Chinese', 'five spice': 'Chinese', 'bok choy': 'Chinese',
        'szechuan': 'Chinese', 'sichuan': 'Chinese', 'canton': 'Chinese',
        'wok': 'Chinese', 'stir fry': 'Chinese', 'stir-fry': 'Chinese',
        
        # Japanese
        'sushi': 'Japanese', 'sashimi': 'Japanese', 'ramen': 'Japanese',
        'tempura': 'Japanese', 'teriyaki': 'Japanese', 'udon': 'Japanese',
        'miso': 'Japanese', 'wasabi': 'Japanese', 'bento': 'Japanese',
        'mirin': 'Japanese', 'sake': 'Japanese', 'dashi': 'Japanese',
        'nori': 'Japanese', 'wakame': 'Japanese', 'kombu': 'Japanese',
        'shoyu': 'Japanese', 'tamari': 'Japanese', 'ponzu': 'Japanese',
        'miso soup': 'Japanese', 'tonkatsu': 'Japanese', 'yakitori': 'Japanese',
        
        # Thai
        'pad thai': 'Thai', 'tom yum': 'Thai', 'green curry': 'Thai',
        'massaman': 'Thai', 'satay': 'Thai', 'papaya salad': 'Thai',
        'fish sauce': 'Thai', 'coconut milk': 'Thai', 'lemongrass': 'Thai',
        'galangal': 'Thai', 'kaffir lime': 'Thai', 'bird\'s eye chili': 'Thai',
        'tamarind': 'Thai', 'palm sugar': 'Thai', 'basil': 'Thai',
        'mint': 'Thai', 'cilantro': 'Thai', 'lime leaves': 'Thai',
        
        # French
        'ratatouille': 'French', 'quiche': 'French', 'crepe': 'French',
        'croissant': 'French', 'coq au vin': 'French', 'bouillabaisse': 'French',
        'herbes de provence': 'French', 'brie': 'French', 'camembert': 'French',
        'confit': 'French', 'cassoulet': 'French', 'boeuf bourguignon': 'French',
        'truffle': 'French', 'cognac': 'French', 'wine': 'French',
        'butter': 'French', 'cream': 'French', 'shallot': 'French',
        
        # Mediterranean
        'hummus': 'Mediterranean', 'falafel': 'Mediterranean', 'tzatziki': 'Mediterranean',
        'tabbouleh': 'Mediterranean', 'pita': 'Mediterranean', 'baba ghanoush': 'Mediterranean',
        'feta': 'Mediterranean', 'olives': 'Mediterranean', 'olive oil': 'Mediterranean',
        'sumac': 'Mediterranean', 'za\'atar': 'Mediterranean', 'tahini': 'Mediterranean',
        'pomegranate': 'Mediterranean', 'fig': 'Mediterranean', 'artichoke': 'Mediterranean',
        
        # American
        'burger': 'American', 'hot dog': 'American', 'barbecue': 'American',
        'mac and cheese': 'American', 'apple pie': 'American', 'fried chicken': 'American',
        'biscuits and gravy': 'American', 'cornbread': 'American', 'grits': 'American',
        'bacon': 'American', 'cheddar': 'American', 'ranch': 'American',
        'buffalo': 'American', 'cajun': 'American', 'creole': 'American',
        
        # British
        'fish and chips': 'British', 'bangers and mash': 'British', 'shepherd\'s pie': 'British',
        'yorkshire pudding': 'British', 'black pudding': 'British', 'marmite': 'British',
        'mushy peas': 'British', 'bubble and squeak': 'British', 'toad in the hole': 'British',
        'mint sauce': 'British', 'malt vinegar': 'British', 'brown sauce': 'British',
        
        # German
        'sauerkraut': 'German', 'bratwurst': 'German', 'pretzel': 'German',
        'schnitzel': 'German', 'spaetzle': 'German', 'beer': 'German',
        'mustard': 'German', 'caraway': 'German', 'dill': 'German',
        'potato': 'German', 'cabbage': 'German', 'pork': 'German',
        
        # Korean
        'kimchi': 'Korean', 'bulgogi': 'Korean', 'bibimbap': 'Korean',
        'gochujang': 'Korean', 'soju': 'Korean', 'korean': 'Korean',
        'gochugaru': 'Korean', 'doenjang': 'Korean', 'sesame oil': 'Korean',
        'soy sauce': 'Korean', 'garlic': 'Korean', 'ginger': 'Korean',
        
        # Vietnamese
        'pho': 'Vietnamese', 'banh mi': 'Vietnamese', 'spring roll': 'Vietnamese',
        'nuoc mam': 'Vietnamese', 'fish sauce': 'Vietnamese', 'rice paper': 'Vietnamese',
        'vermicelli': 'Vietnamese', 'lemongrass': 'Vietnamese', 'star anise': 'Vietnamese',
        'cinnamon': 'Vietnamese', 'cloves': 'Vietnamese', 'cardamom': 'Vietnamese',
        
        # Spanish
        'paella': 'Spanish', 'tapas': 'Spanish', 'chorizo': 'Spanish',
        'sangria': 'Spanish', 'gazpacho': 'Spanish', 'sherry': 'Spanish',
        'saffron': 'Spanish', 'paprika': 'Spanish', 'manchego': 'Spanish',
        'jamón': 'Spanish', 'serrano': 'Spanish', 'iberico': 'Spanish',
        
        # Greek
        'moussaka': 'Greek', 'baklava': 'Greek', 'gyro': 'Greek',
        'feta': 'Greek', 'olives': 'Greek', 'oregano': 'Greek',
        'dill': 'Greek', 'mint': 'Greek', 'lemon': 'Greek',
        'phyllo': 'Greek', 'spanakopita': 'Greek', 'dolmades': 'Greek',
        
        # Middle Eastern
        'kebab': 'Middle Eastern', 'pita': 'Middle Eastern', 'tahini': 'Middle Eastern',
        'sumac': 'Middle Eastern', 'za\'atar': 'Middle Eastern', 'pomegranate': 'Middle Eastern',
        'rose water': 'Middle Eastern', 'orange blossom': 'Middle Eastern', 'cardamom': 'Middle Eastern',
        
        # Brazilian
        'feijoada': 'Brazilian', 'caipirinha': 'Brazilian', 'pão de açúcar': 'Brazilian',
        'cassava': 'Brazilian', 'plantain': 'Brazilian', 'coconut': 'Brazilian',
        'palm oil': 'Brazilian', 'dendê': 'Brazilian', 'farofa': 'Brazilian',
        
        # Caribbean
        'jerk': 'Caribbean', 'plantain': 'Caribbean', 'coconut': 'Caribbean',
        'rum': 'Caribbean', 'allspice': 'Caribbean', 'scotch bonnet': 'Caribbean',
        'thyme': 'Caribbean', 'ginger': 'Caribbean', 'lime': 'Caribbean',
        
        # African
        'berbere': 'African', 'harissa': 'African', 'teff': 'African',
        'injera': 'African', 'couscous': 'African', 'tagine': 'African',
        'palm oil': 'African', 'peanut': 'African', 'okra': 'African'
    }
    
    # Get recipe text for analysis
    title = recipe_data.get('title', recipe_data.get('name', '')).lower()
    ingredients = recipe_data.get('ingredients', [])
    instructions = recipe_data.get('instructions', [])
    description = recipe_data.get('description', '').lower()
    summary = recipe_data.get('summary', '').lower()
    
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
    all_text = f"{title} {ingredient_text} {instruction_text} {description} {summary}"
    
    # Check for cuisine indicators
    cuisine_scores = Counter()
    
    # Check ingredient mappings (weight: 3)
    for ingredient, cuisine in INGREDIENT_CUISINE_MAP.items():
        if ingredient in all_text:
            cuisine_scores[cuisine] += 3
    
    # Check title patterns (weight: 5)
    title_patterns = {
        'pasta': 'Italian', 'pizza': 'Italian', 'risotto': 'Italian', 'gnocchi': 'Italian',
        'taco': 'Mexican', 'burrito': 'Mexican', 'enchilada': 'Mexican', 'quesadilla': 'Mexican',
        'curry': 'Indian', 'biryani': 'Indian', 'tikka': 'Indian', 'masala': 'Indian',
        'dumpling': 'Chinese', 'chow mein': 'Chinese', 'lo mein': 'Chinese', 'kung pao': 'Chinese',
        'sushi': 'Japanese', 'ramen': 'Japanese', 'tempura': 'Japanese', 'teriyaki': 'Japanese',
        'pad thai': 'Thai', 'tom yum': 'Thai', 'green curry': 'Thai', 'massaman': 'Thai',
        'ratatouille': 'French', 'quiche': 'French', 'crepe': 'French', 'coq au vin': 'French',
        'hummus': 'Mediterranean', 'falafel': 'Mediterranean', 'tzatziki': 'Mediterranean',
        'burger': 'American', 'barbecue': 'American', 'fried chicken': 'American', 'mac and cheese': 'American',
        'fish and chips': 'British', 'shepherd\'s pie': 'British', 'bangers and mash': 'British',
        'paella': 'Spanish', 'tapas': 'Spanish', 'gazpacho': 'Spanish', 'chorizo': 'Spanish',
        'moussaka': 'Greek', 'baklava': 'Greek', 'gyro': 'Greek', 'spanakopita': 'Greek',
        'pho': 'Vietnamese', 'banh mi': 'Vietnamese', 'spring roll': 'Vietnamese',
        'kimchi': 'Korean', 'bulgogi': 'Korean', 'bibimbap': 'Korean',
        'feijoada': 'Brazilian', 'caipirinha': 'Brazilian', 'jerk': 'Caribbean'
    }
    
    for pattern, cuisine in title_patterns.items():
        if pattern in title:
            cuisine_scores[cuisine] += 5  # Higher weight for title matches
    
    # Check cooking methods (weight: 2)
    cooking_methods = {
        'stir-fry': 'Chinese', 'deep-fry': 'Chinese', 'steam': 'Chinese', 'wok': 'Chinese',
        'grill': 'American', 'barbecue': 'American', 'smoke': 'American', 'fry': 'American',
        'braise': 'French', 'sauté': 'French', 'flambé': 'French', 'confit': 'French',
        'roast': 'British', 'bake': 'British', 'boil': 'British', 'mash': 'British',
        'tempura': 'Japanese', 'teriyaki': 'Japanese', 'miso': 'Japanese',
        'curry': 'Indian', 'tandoori': 'Indian', 'biryani': 'Indian',
        'pad thai': 'Thai', 'tom yum': 'Thai', 'green curry': 'Thai',
        'paella': 'Spanish', 'gazpacho': 'Spanish', 'tapas': 'Spanish',
        'moussaka': 'Greek', 'baklava': 'Greek', 'gyro': 'Greek',
        'pho': 'Vietnamese', 'banh mi': 'Vietnamese', 'spring roll': 'Vietnamese',
        'kimchi': 'Korean', 'bulgogi': 'Korean', 'bibimbap': 'Korean'
    }
    
    for method, cuisine in cooking_methods.items():
        if method in all_text:
            cuisine_scores[cuisine] += 2
    
    # Check for specific spice combinations (weight: 4)
    spice_combinations = {
        'garam masala': 'Indian', 'curry powder': 'Indian', 'tandoori': 'Indian',
        'five spice': 'Chinese', 'szechuan': 'Chinese', 'hoisin': 'Chinese',
        'herbes de provence': 'French', 'bouquet garni': 'French',
        'za\'atar': 'Middle Eastern', 'sumac': 'Middle Eastern',
        'berbere': 'African', 'harissa': 'African',
        'jerk seasoning': 'Caribbean', 'allspice': 'Caribbean'
    }
    
    for spice, cuisine in spice_combinations.items():
        if spice in all_text:
            cuisine_scores[cuisine] += 4
    
    # Return the most likely cuisine
    if cuisine_scores:
        best_cuisine = cuisine_scores.most_common(1)[0][0]
        best_score = cuisine_scores.most_common(1)[0][1]
        
        # Only return if we have a reasonable confidence (score >= 3)
        if best_score >= 3:
            return best_cuisine
    
    # If no specific cuisine detected, return empty string
    return ""

def improve_cuisine_tags():
    """Improve cuisine tags for all recipes."""
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path="./backend/chroma_db")
        collection = client.get_collection('recipe_details_cache')
        
        # Get all recipes
        all_recipes = collection.get(include=['metadatas', 'documents'])
        
        logger.info(f"Improving cuisine tags for {len(all_recipes['ids'])} recipes...")
        
        stats = {
            'total_processed': 0,
            'improved': 0,
            'kept_international': 0,
            'cuisine_distribution': Counter(),
            'improvements': []
        }
        
        for i, (recipe_id, metadata, document) in enumerate(zip(
            all_recipes['ids'], 
            all_recipes['metadatas'], 
            all_recipes['documents']
        )):
            try:
                # Parse recipe data
                recipe_data = json.loads(document) if isinstance(document, str) else document
                
                current_cuisine = metadata.get('cuisine', '').lower().strip()
                
                # Skip if already has a specific cuisine (not International)
                if current_cuisine and current_cuisine not in ['', 'international', 'none', 'null', 'other']:
                    stats['cuisine_distribution'][current_cuisine] += 1
                    stats['total_processed'] += 1
                    continue
                
                # Detect cuisine
                detected_cuisine = detect_cuisine_from_recipe(recipe_data)
                
                if detected_cuisine:
                    # Update metadata
                    old_cuisine = metadata.get('cuisine', 'International')
                    metadata['cuisine'] = detected_cuisine
                    
                    # Update recipe data
                    recipe_data['cuisine'] = detected_cuisine
                    
                    # Update in database
                    collection.update(
                        ids=[recipe_id],
                        metadatas=[metadata],
                        documents=[json.dumps(recipe_data)]
                    )
                    
                    stats['improved'] += 1
                    stats['cuisine_distribution'][detected_cuisine] += 1
                    stats['improvements'].append({
                        'id': recipe_id,
                        'title': recipe_data.get('title', recipe_data.get('name', 'Unknown')),
                        'old_cuisine': old_cuisine,
                        'new_cuisine': detected_cuisine
                    })
                    
                    logger.info(f"Improved recipe {recipe_id}: '{recipe_data.get('title', 'Unknown')}' -> {detected_cuisine}")
                else:
                    # Keep as International if we can't detect
                    stats['kept_international'] += 1
                    stats['cuisine_distribution']['International'] += 1
                
                stats['total_processed'] += 1
                
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1}/{len(all_recipes['ids'])} recipes...")
                    
            except Exception as e:
                logger.error(f"Error processing recipe {recipe_id}: {e}")
                continue
        
        # Print final statistics
        logger.info("\n" + "="*60)
        logger.info("CUISINE IMPROVEMENT RESULTS")
        logger.info("="*60)
        logger.info(f"Total recipes processed: {stats['total_processed']}")
        logger.info(f"Recipes improved: {stats['improved']}")
        logger.info(f"Recipes kept as International: {stats['kept_international']}")
        
        logger.info("\nFinal cuisine distribution:")
        for cuisine, count in stats['cuisine_distribution'].most_common(20):
            logger.info(f"  {cuisine}: {count}")
        
        # Save detailed results
        with open('cuisine_improvement_results.json', 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"\nDetailed results saved to 'cuisine_improvement_results.json'")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error improving cuisine tags: {e}")
        raise

if __name__ == "__main__":
    print("Recipe Cuisine Improvement Tool")
    print("="*50)
    print("This tool will analyze all recipes and improve their cuisine tags")
    print("based on ingredients, cooking methods, and recipe names.")
    print()
    
    # Run the improvement
    stats = improve_cuisine_tags()
    
    print(f"\nImprovement completed!")
    print(f"  Recipes improved: {stats['improved']}")
    print(f"  Recipes kept as International: {stats['kept_international']}")
    print(f"  Total processed: {stats['total_processed']}")
