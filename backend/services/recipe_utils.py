"""Utility functions for recipe processing and normalization."""
import json
import hashlib
import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

def normalize_recipe(recipe: Union[Dict[str, Any], str]) -> Optional[Dict[str, Any]]:
    """
    Normalize recipe data to ensure it has all required fields and proper formatting.
    
    Args:
        recipe: The recipe data to normalize (can be a dict or JSON string)
        
    Returns:
        Normalized recipe dictionary or None if invalid
    """
    try:
        # Parse JSON string if needed
        if isinstance(recipe, str):
            try:
                recipe = json.loads(recipe)
            except json.JSONDecodeError:
                # If it's not JSON, use it as a title
                recipe = {'title': recipe.strip()}
        
        # Ensure we have a dictionary
        if not isinstance(recipe, dict):
            return None
            
        # Create a copy to avoid modifying the original
        normalized = dict(recipe)
        
        # Ensure required fields exist with defaults
        if 'title' not in normalized or not normalized['title']:
            normalized['title'] = 'Untitled Recipe'
            
        # Handle ingredients - ensure it's a list of strings
        if 'ingredients' not in normalized:
            normalized['ingredients'] = []
        elif isinstance(normalized['ingredients'], str):
            normalized['ingredients'] = [ing.strip() for ing in normalized['ingredients'].split('\n') if ing.strip()]
        elif not isinstance(normalized['ingredients'], list):
            normalized['ingredients'] = [str(normalized['ingredients'])]
        else:
            # Ensure each ingredient is a string
            normalized['ingredients'] = [str(ing) for ing in normalized['ingredients']]
            
        # Handle instructions - ensure it's a list of strings
        if 'instructions' not in normalized:
            normalized['instructions'] = ['No instructions available']
        elif isinstance(normalized['instructions'], str):
            normalized['instructions'] = [instr.strip() for instr in normalized['instructions'].split('\n') if instr.strip()]
            if not normalized['instructions']:
                normalized['instructions'] = ['No instructions available']
        elif not isinstance(normalized['instructions'], list):
            normalized['instructions'] = [str(normalized['instructions'])]
        else:
            # Ensure each instruction is a string
            normalized['instructions'] = [str(instr) for instr in normalized['instructions']]
            
        # Handle tags - ensure it's a list of strings
        if 'tags' not in normalized:
            normalized['tags'] = []
        elif isinstance(normalized['tags'], str):
            normalized['tags'] = [tag.strip() for tag in normalized['tags'].split(',') if tag.strip()]
        elif not isinstance(normalized['tags'], list):
            normalized['tags'] = [str(normalized['tags'])]
        else:
            # Ensure each tag is a string
            normalized['tags'] = [str(tag) for tag in normalized['tags']]
            
        # Ensure there's at least one cuisine tag
        has_cuisine = any(tag.lower() in [
            'american', 'mexican', 'italian', 'chinese', 'japanese', 'indian', 'thai',
            'french', 'mediterranean', 'greek', 'spanish', 'korean', 'vietnamese',
            'german', 'british', 'caribbean', 'brazilian', 'moroccan', 'turkish',
            'ethiopian', 'russian'
        ] for tag in normalized['tags'])
        
        if not has_cuisine:
            # Try to infer cuisine from title or ingredients if possible
            title = normalized.get('title', '').lower()
            ingredients = ' '.join(normalized.get('ingredients', [])).lower()
            
            # Common cuisine indicators
            cuisine_hints = {
                'pasta|risotto|pizza|bruschetta|tiramisu': 'Italian',
                'taco|burrito|enchilada|quesadilla|guacamole': 'Mexican',
                'sushi|ramen|teriyaki|tempura|udon|miso': 'Japanese',
                'curry|tikka|masala|naan|biryani|samosas': 'Indian',
                'pho|banh mi|spring roll|pad thai|tom yum': 'Vietnamese',
                'kebab|hummus|falafel|shakshuka|tzatziki': 'Mediterranean',
                'paella|tapas|gazpacho|chorizo|tortilla': 'Spanish',
                'kimchi|bulgogi|bibimbap|kimbap|tteokbokki': 'Korean',
                'burger|hot dog|mac and cheese|apple pie': 'American',
                'croissant|ratatouille|quiche|crepe|souffle': 'French'
            }
            
            # Check for cuisine hints in title and ingredients
            inferred_cuisine = None
            for pattern, cuisine in cuisine_hints.items():
                if re.search(pattern, title) or re.search(pattern, ingredients):
                    inferred_cuisine = cuisine
                    break
            
            # If no cuisine could be inferred, use a default
            if not inferred_cuisine:
                # Use a random world cuisine as fallback
                world_cuisines = [
                    'American', 'Mexican', 'Italian', 'Chinese', 'Japanese',
                    'Indian', 'Thai', 'French', 'Mediterranean', 'Greek',
                    'Spanish', 'Korean', 'Vietnamese', 'German', 'British',
                    'Caribbean', 'Brazilian', 'Moroccan', 'Turkish', 'Ethiopian'
                ]
                # Use a consistent hash of the title to always return the same cuisine for the same title
                if title:
                    hash_val = int(hashlib.md5(title.encode()).hexdigest(), 16)
                    inferred_cuisine = world_cuisines[hash_val % len(world_cuisines)]
                else:
                    inferred_cuisine = 'International'
            
            normalized['tags'].append(inferred_cuisine)
            
            # Also add to a dedicated cuisine field if it exists
            if 'cuisine' not in normalized or not normalized['cuisine']:
                normalized['cuisine'] = inferred_cuisine
            
        # Ensure ID exists and is a string
        if 'id' not in normalized or not normalized['id']:
            # Create a stable hash of the recipe content for ID generation
            recipe_str = json.dumps(normalized, sort_keys=True)
            recipe_hash = hashlib.md5(recipe_str.encode()).hexdigest()
            normalized['id'] = f"recipe_{recipe_hash}"
        else:
            normalized['id'] = str(normalized['id'])
            
        # Ensure summary exists
        if 'summary' not in normalized or not normalized['summary']:
            normalized['summary'] = f"A delicious {normalized['title']} recipe."
            
        # Ensure image URL is a string
        if 'image' not in normalized:
            normalized['image'] = ''
        else:
            normalized['image'] = str(normalized['image'])
            
        return normalized
        
    except Exception as e:
        logger.error(f"Error normalizing recipe: {e}")
        return None

def extract_search_terms(recipe: Dict[str, Any]) -> str:
    """
    Extract searchable terms from a recipe.
    
    Args:
        recipe: The recipe dictionary
        
    Returns:
        String of searchable terms
    """
    if not recipe or not isinstance(recipe, dict):
        return ""
        
    # Extract basic fields
    title = recipe.get('title', '')
    ingredients = ' '.join(recipe.get('ingredients', []))
    instructions = ' '.join(recipe.get('instructions', []))
    tags = ' '.join(recipe.get('tags', []))
    
    # Include additional fields if available
    cuisine = ' '.join(recipe.get('cuisine', [])) if isinstance(recipe.get('cuisine'), list) else recipe.get('cuisine', '')
    diets = ' '.join(recipe.get('diets', [])) if isinstance(recipe.get('diets'), list) else recipe.get('diets', '')
    
    # Combine all searchable text
    search_terms = f"{title} {ingredients} {instructions} {tags} {cuisine} {diets}"
    
    # Clean up and return
    return ' '.join(term for term in search_terms.split() if term)
