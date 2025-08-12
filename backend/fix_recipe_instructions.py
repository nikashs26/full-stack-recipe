#!/usr/bin/env python3
"""
Script to fix recipe instructions in the cache by properly parsing them into individual steps.
This script updates all existing cached recipes to have properly formatted instructions.
"""

import json
import logging
import sys
import re
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

def parse_instructions(instructions_text):
    """Parse recipe instructions into individual steps"""
    if not instructions_text:
        return ['No instructions provided.']
    
    # Clean up the instructions - preserve original structure but normalize whitespace
    instructions_text = instructions_text.replace('\r\n', '\n').replace('\r', '\n')
    
    # First, try to split by actual numbered steps (e.g., "1.", "1)", "Step 1:")
    import re
    
    # Look for actual step numbers at the beginning of lines or after periods
    # This pattern is more conservative and won't split on measurements
    step_pattern = r'(?:\n\s*\d+[.)]|\A\s*\d+[.)])'
    
    # Split by the step pattern
    raw_steps = re.split(f'({step_pattern})', instructions_text, flags=re.MULTILINE)
    
    # Clean up the split results
    steps = []
    current_step = ''
    
    for i, part in enumerate(raw_steps):
        part = part.strip()
        if not part:
            continue
            
        # If this part is a step number/indicator
        if re.match(f'^{step_pattern}$', part, flags=re.MULTILINE):
            if current_step:  # Save the previous step if exists
                steps.append(current_step.strip())
            current_step = part + ' '  # Start new step with the number
        else:
            current_step += part + ' '
    
    # Add the last step if it exists
    if current_step.strip():
        steps.append(current_step.strip())
    
    # If we couldn't split by numbers, try other methods
    if len(steps) <= 1:
        # Try splitting by double newlines first (preserve natural paragraph breaks)
        steps = [s.strip() for s in instructions_text.split('\n\n') if s.strip()]
        
        # If that doesn't work, try splitting by single newlines that look like step separators
        if len(steps) <= 1:
            # Look for newlines that are followed by capital letters (likely new steps)
            steps = [s.strip() for s in re.split(r'\n(?=\s*[A-Z])', instructions_text) if s.strip()]
    
    # Clean up each step - remove leading numbers and normalize
    cleaned_steps = []
    for step in steps:
        if step:
            # Remove leading step numbers
            cleaned_step = re.sub(r'^\s*\d+[.)]?\s*', '', step).strip()
            if cleaned_step:
                # Normalize whitespace within the step
                cleaned_step = ' '.join(cleaned_step.split())
                cleaned_steps.append(cleaned_step)
    
    # If we still don't have multiple steps, try to split by cooking action keywords
    if len(cleaned_steps) <= 1 and instructions_text:
        # Look for common cooking instruction patterns that indicate new steps
        cooking_keywords = [
            'preheat', 'heat', 'add', 'stir', 'mix', 'combine', 'pour', 'bake', 'cook', 'fry',
            'grill', 'roast', 'boil', 'simmer', 'season', 'salt', 'pepper', 'drain', 'remove',
            'serve', 'garnish', 'decorate', 'cool', 'chill', 'refrigerate', 'freeze', 'place',
            'transfer', 'return', 'bring', 'lower', 'cover', 'uncover', 'flip', 'turn'
        ]
        
        # Split by sentences that contain cooking keywords
        sentences = re.split(r'[.!?]+', instructions_text)
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 15:  # Only meaningful sentences
                # Check if sentence contains cooking keywords
                if any(keyword in sentence.lower() for keyword in cooking_keywords):
                    cleaned_steps.append(sentence)
    
    # If all else fails, try to split by periods that end sentences
    if len(cleaned_steps) <= 1:
        # More intelligent sentence splitting that doesn't break on measurements
        # Look for periods followed by space and capital letter, but avoid breaking on measurements
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z][a-z])', instructions_text)
        cleaned_steps = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
    
    # Ensure we have at least one step
    if not cleaned_steps:
        cleaned_steps = [instructions_text.strip()]
    
    return cleaned_steps

def fix_recipe_instructions():
    """Fix instruction parsing for all cached recipes"""
    try:
        logger.info("Starting recipe instruction fix...")
        
        # Initialize the cache service
        cache_service = RecipeCacheService()
        
        # Get all recipes from cache
        all_recipes = cache_service._get_all_recipes_from_cache()
        logger.info(f"Found {len(all_recipes)} recipes in cache")
        
        # Track statistics
        updated_count = 0
        already_fixed_count = 0
        error_count = 0
        
        # Process each recipe
        for i, recipe in enumerate(all_recipes):
            if not recipe or not isinstance(recipe, dict):
                continue
                
            recipe_id = recipe.get('id', 'unknown')
            recipe_title = recipe.get('title', 'Unknown Recipe')
            
            try:
                # Check if instructions need fixing
                instructions = recipe.get('instructions', [])
                
                # If instructions is already a list with multiple items, skip
                if isinstance(instructions, list) and len(instructions) > 1:
                    already_fixed_count += 1
                    continue
                
                # If instructions is a string, parse it
                if isinstance(instructions, str):
                    parsed_instructions = parse_instructions(instructions)
                    recipe['instructions'] = parsed_instructions
                    
                    # Update recipe in cache - use the sync method instead of async
                    try:
                        # Try to use the sync method if available
                        if hasattr(cache_service, 'cache_recipe'):
                            success = cache_service.cache_recipe(recipe)
                        else:
                            # Fallback to direct upsert
                            success = True
                            cache_service.recipe_collection.upsert(
                                ids=[recipe_id],
                                documents=[json.dumps(recipe)],
                                metadatas=[cache_service._extract_recipe_metadata(recipe)]
                            )
                        
                        if success:
                            updated_count += 1
                            if updated_count % 50 == 0:
                                logger.info(f"Updated {updated_count} recipes...")
                            logger.debug(f"Fixed instructions for: {recipe_title}")
                        else:
                            logger.warning(f"Failed to update recipe {recipe_id} in cache")
                            error_count += 1
                    except Exception as e:
                        logger.error(f"Error updating recipe {recipe_id}: {e}")
                        error_count += 1
                        
                # If instructions is a list with only one item, check if it needs parsing
                elif isinstance(instructions, list) and len(instructions) == 1:
                    single_instruction = instructions[0]
                    if isinstance(single_instruction, str) and len(single_instruction) > 200:
                        # This looks like it might be multiple steps combined
                        parsed_instructions = parse_instructions(single_instruction)
                        if len(parsed_instructions) > 1:
                            recipe['instructions'] = parsed_instructions
                            
                            # Update recipe in cache - use the sync method instead of async
                            try:
                                # Try to use the sync method if available
                                if hasattr(cache_service, 'cache_recipe'):
                                    success = cache_service.cache_recipe(recipe)
                                else:
                                    # Fallback to direct upsert
                                    success = True
                                    cache_service.recipe_collection.upsert(
                                        ids=[recipe_id],
                                        documents=[json.dumps(recipe)],
                                        metadatas=[cache_service._extract_recipe_metadata(recipe)]
                                    )
                                
                                if success:
                                    updated_count += 1
                                    if updated_count % 50 == 0:
                                        logger.info(f"Fixed instructions for: {updated_count} recipes...")
                                    logger.debug(f"Fixed instructions for: {recipe_title}")
                                else:
                                    logger.warning(f"Failed to update recipe {recipe_id} in cache")
                                    error_count += 1
                            except Exception as e:
                                logger.error(f"Error updating recipe {recipe_id}: {e}")
                                error_count += 1
                        else:
                            already_fixed_count += 1
                    else:
                        already_fixed_count += 1
                else:
                    already_fixed_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing recipe {recipe_id}: {e}")
                error_count += 1
                continue
        
        # Print summary
        logger.info("=" * 50)
        logger.info("INSTRUCTION FIX SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total recipes processed: {len(all_recipes)}")
        logger.info(f"Successfully updated: {updated_count}")
        logger.info(f"Already properly formatted: {already_fixed_count}")
        logger.info(f"Errors: {error_count}")
        
        return {
            'total_processed': len(all_recipes),
            'updated': updated_count,
            'already_fixed': already_fixed_count,
            'errors': error_count
        }
        
    except Exception as e:
        logger.error(f"Unexpected error during instruction fix: {e}")
        raise

def main():
    """Main function"""
    try:
        result = fix_recipe_instructions()
        print(f"\n✅ Recipe instruction fix completed successfully!")
        print(f"📝 Updated {result['updated']} recipes with properly parsed instructions")
        print(f"✅ {result['already_fixed']} recipes were already properly formatted")
        print(f"🔧 Your recipes now have properly numbered steps!")
        
    except Exception as e:
        logger.error(f"Failed to fix recipe instructions: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 