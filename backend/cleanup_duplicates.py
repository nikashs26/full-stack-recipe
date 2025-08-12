#!/usr/bin/env python3
"""
Script to identify and clean up duplicate recipes in ChromaDB
Keeps the recipe with better formatting and removes duplicates
"""

import chromadb
import json
from collections import defaultdict
import re
from typing import Dict, List, Tuple, Any

def analyze_recipe_quality(recipe: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """
    Analyze recipe quality and return a score and metadata
    Higher score = better quality recipe
    """
    score = 0
    metadata = {}
    
    # Check if recipe has basic required fields
    if recipe.get('name') or recipe.get('title'):
        score += 10
        metadata['has_name'] = True
    else:
        metadata['has_name'] = False
    
    if recipe.get('description'):
        score += 5
        metadata['has_description'] = True
    else:
        metadata['has_description'] = False
    
    # Check ingredients quality
    ingredients = recipe.get('ingredients', [])
    if ingredients:
        score += 10
        metadata['has_ingredients'] = True
        metadata['ingredient_count'] = len(ingredients)
        
        # Check if ingredients are properly formatted
        well_formatted_ingredients = 0
        for ing in ingredients:
            if isinstance(ing, dict) and ('name' in ing or 'ingredient' in ing):
                well_formatted_ingredients += 1
            elif isinstance(ing, str) and ing.strip():
                well_formatted_ingredients += 1
        
        if well_formatted_ingredients == len(ingredients):
            score += 5
            metadata['well_formatted_ingredients'] = True
        else:
            metadata['well_formatted_ingredients'] = False
    else:
        metadata['has_ingredients'] = False
        metadata['ingredient_count'] = 0
    
    # Check instructions quality
    instructions = recipe.get('instructions', [])
    if instructions:
        score += 10
        metadata['has_instructions'] = True
        metadata['instruction_count'] = len(instructions)
        
        # Check if instructions are properly formatted
        well_formatted_instructions = 0
        for inst in instructions:
            if isinstance(inst, str) and inst.strip() and len(inst.strip()) > 10:
                well_formatted_instructions += 1
        
        if well_formatted_instructions == len(instructions):
            score += 5
            metadata['well_formatted_instructions'] = True
        else:
            metadata['well_formatted_instructions'] = False
    else:
        metadata['has_instructions'] = False
        metadata['instruction_count'] = 0
    
    # Check nutrition info
    nutrition = recipe.get('nutrition', {})
    if nutrition and any(nutrition.values()):
        score += 5
        metadata['has_nutrition'] = True
    else:
        metadata['has_nutrition'] = False
    
    # Check cooking time
    if recipe.get('cookingTime') or recipe.get('totalTime'):
        score += 3
        metadata['has_cooking_time'] = True
    else:
        metadata['has_cooking_time'] = False
    
    # Check difficulty level
    if recipe.get('difficulty'):
        score += 2
        metadata['has_difficulty'] = True
    else:
        metadata['has_difficulty'] = False
    
    # Check servings
    if recipe.get('servings'):
        score += 2
        metadata['has_servings'] = True
    else:
        metadata['has_servings'] = False
    
    # Check cuisine
    if recipe.get('cuisine'):
        score += 3
        metadata['has_cuisine'] = True
    else:
        metadata['has_cuisine'] = False
    
    # Check for proper step formatting (numbered or bulleted instructions)
    if instructions:
        step_formatted = False
        for inst in instructions:
            if isinstance(inst, str):
                # Check for numbered steps (1., 2., etc.) or bullet points
                if re.match(r'^\d+\.', inst.strip()) or inst.strip().startswith('•') or inst.strip().startswith('-'):
                    step_formatted = True
                    break
        
        if step_formatted:
            score += 8
            metadata['step_formatted'] = True
        else:
            metadata['step_formatted'] = False
    
    # Check for proper tagging
    tags = recipe.get('tags', [])
    if tags and isinstance(tags, list) and len(tags) > 0:
        score += 3
        metadata['has_tags'] = True
        metadata['tag_count'] = len(tags)
    else:
        metadata['has_tags'] = False
        metadata['tag_count'] = 0
    
    metadata['total_score'] = score
    return score, metadata

def find_duplicate_recipes(collection) -> Dict[str, List[Tuple[str, int, Dict[str, Any]]]]:
    """
    Find duplicate recipes based on name similarity
    Returns: {recipe_name: [(recipe_id, score, metadata), ...]}
    """
    print("Fetching all recipes from collection...")
    
    # Get all recipes
    results = collection.get(limit=collection.count(), include=['documents', 'metadatas'])
    
    print(f"Analyzing {len(results['documents'])} recipes...")
    
    # Group recipes by name (normalized)
    recipe_groups = defaultdict(list)
    
    for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
        try:
            # Parse the document
            if isinstance(doc, str):
                recipe_data = json.loads(doc)
            else:
                recipe_data = doc
            
            # Get recipe name
            recipe_name = recipe_data.get('name') or recipe_data.get('title') or f"Recipe_{i}"
            
            # Normalize name for grouping (remove extra spaces, lowercase)
            normalized_name = re.sub(r'\s+', ' ', recipe_name.strip().lower())
            
            # Get recipe ID
            recipe_id = metadata.get('recipe_id') or str(i)
            
            # Analyze recipe quality
            score, quality_metadata = analyze_recipe_quality(recipe_data)
            
            # Store recipe info
            recipe_groups[normalized_name].append((recipe_id, score, quality_metadata, recipe_data))
            
        except Exception as e:
            print(f"Error processing recipe {i}: {e}")
            continue
    
    # Filter to only groups with duplicates
    duplicates = {name: recipes for name, recipes in recipe_groups.items() if len(recipes) > 1}
    
    return duplicates

def cleanup_duplicates(collection, duplicates: Dict[str, List[Tuple[str, int, Dict[str, Any], Dict[str, Any]]]]):
    """
    Clean up duplicates by keeping the best recipe and removing others
    """
    print(f"\nFound {len(duplicates)} groups of duplicate recipes")
    
    recipes_to_remove = []
    recipes_to_keep = []
    
    for recipe_name, recipe_list in duplicates.items():
        print(f"\n--- {recipe_name} ---")
        print(f"Found {len(recipe_list)} duplicates:")
        
        # Sort by score (highest first)
        sorted_recipes = sorted(recipe_list, key=lambda x: x[1], reverse=True)
        
        # Keep the best one
        best_recipe = sorted_recipes[0]
        recipes_to_keep.append(best_recipe)
        
        print(f"  KEEPING: ID {best_recipe[0]} (Score: {best_recipe[1]})")
        print(f"    Quality: {best_recipe[2]}")
        
        # Mark others for removal
        for recipe_id, score, metadata, _ in sorted_recipes[1:]:
            recipes_to_remove.append(recipe_id)
            print(f"  REMOVING: ID {recipe_id} (Score: {score})")
            print(f"    Quality: {metadata}")
    
    print(f"\nSummary:")
    print(f"- Recipes to keep: {len(recipes_to_keep)}")
    print(f"- Recipes to remove: {len(recipes_to_remove)}")
    
    # Remove duplicates
    if recipes_to_remove:
        print(f"\nRemoving {len(recipes_to_remove)} duplicate recipes...")
        try:
            collection.delete(ids=recipes_to_remove)
            print("✅ Successfully removed duplicate recipes")
        except Exception as e:
            print(f"❌ Error removing duplicates: {e}")
    else:
        print("No duplicates to remove")
    
    return len(recipes_to_remove)

def main():
    """Main function to run the duplicate cleanup"""
    print("🔍 Recipe Duplicate Cleanup Tool")
    print("=" * 50)
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_collection("recipe_search_cache")
        
        print(f"Connected to collection: {collection.name}")
        print(f"Current recipe count: {collection.count()}")
        
        # Find duplicates
        duplicates = find_duplicate_recipes(collection)
        
        if not duplicates:
            print("🎉 No duplicate recipes found!")
            return
        
        # Show duplicates summary
        total_duplicates = sum(len(recipes) for recipes in duplicates.values())
        print(f"\n📊 Duplicate Analysis:")
        print(f"- Groups with duplicates: {len(duplicates)}")
        print(f"- Total duplicate recipes: {total_duplicates}")
        print(f"- Unique recipe names: {len(duplicates)}")
        
        # Ask for confirmation
        response = input(f"\nDo you want to remove {total_duplicates - len(duplicates)} duplicate recipes? (y/N): ")
        
        if response.lower() in ['y', 'yes']:
            removed_count = cleanup_duplicates(collection, duplicates)
            print(f"\n🎯 Cleanup complete! Removed {removed_count} duplicate recipes")
            print(f"New recipe count: {collection.count()}")
        else:
            print("Cleanup cancelled")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 