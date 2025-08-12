#!/usr/bin/env python3
"""
Script to analyze duplicate recipes in ChromaDB without removing them
Shows you what duplicates exist and their quality differences
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

def find_duplicate_recipes(collection) -> Dict[str, List[Tuple[str, int, Dict[str, Any], Dict[str, Any]]]]:
    """
    Find duplicate recipes based on name similarity
    Returns: {recipe_name: [(recipe_id, score, metadata, recipe_data), ...]}
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

def analyze_duplicates(duplicates: Dict[str, List[Tuple[str, int, Dict[str, Any], Dict[str, Any]]]]):
    """
    Analyze and display information about duplicates
    """
    if not duplicates:
        print("🎉 No duplicate recipes found!")
        return
    
    print(f"\n📊 Duplicate Analysis Summary:")
    print(f"- Groups with duplicates: {len(duplicates)}")
    
    total_duplicates = sum(len(recipes) for recipes in duplicates.values())
    unique_recipes = len(duplicates)
    print(f"- Total duplicate recipes: {total_duplicates}")
    print(f"- Unique recipe names: {unique_recipes}")
    print(f"- Potential recipes to remove: {total_duplicates - unique_recipes}")
    
    # Show some examples
    print(f"\n🔍 Sample Duplicate Groups:")
    
    # Sort by number of duplicates (most duplicates first)
    sorted_duplicates = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
    
    for i, (recipe_name, recipe_list) in enumerate(sorted_duplicates[:10]):  # Show top 10
        print(f"\n{i+1}. {recipe_name}")
        print(f"   Found {len(recipe_list)} duplicates:")
        
        # Sort by score (highest first)
        sorted_recipes = sorted(recipe_list, key=lambda x: x[1], reverse=True)
        
        for j, (recipe_id, score, metadata, recipe_data) in enumerate(sorted_recipes):
            status = "⭐ BEST" if j == 0 else "🗑️  DUPLICATE"
            print(f"   {j+1}. {status} - ID: {recipe_id} (Score: {score})")
            print(f"       Quality: {metadata}")
            
            # Show some recipe details
            if j == 0:  # Show details for the best recipe
                print(f"       Name: {recipe_data.get('name', 'N/A')}")
                print(f"       Cuisine: {recipe_data.get('cuisine', 'N/A')}")
                print(f"       Ingredients: {len(recipe_data.get('ingredients', []))}")
                print(f"       Instructions: {len(recipe_data.get('instructions', []))}")
                print(f"       Step formatted: {metadata.get('step_formatted', False)}")
                print(f"       Has tags: {metadata.get('has_tags', False)}")
    
    # Show quality distribution
    print(f"\n📈 Quality Distribution:")
    all_scores = []
    for recipe_list in duplicates.values():
        for _, score, _, _ in recipe_list:
            all_scores.append(score)
    
    if all_scores:
        print(f"- Average score: {sum(all_scores) / len(all_scores):.1f}")
        print(f"- Highest score: {max(all_scores)}")
        print(f"- Lowest score: {min(all_scores)}")
        
        # Score ranges
        score_ranges = {
            "Excellent (80+)": len([s for s in all_scores if s >= 80]),
            "Good (60-79)": len([s for s in all_scores if 60 <= s < 80]),
            "Fair (40-59)": len([s for s in all_scores if 40 <= s < 60]),
            "Poor (<40)": len([s for s in all_scores if s < 40])
        }
        
        for range_name, count in score_ranges.items():
            print(f"- {range_name}: {count} recipes")

def main():
    """Main function to analyze duplicates"""
    print("🔍 Recipe Duplicate Analysis Tool")
    print("=" * 50)
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_collection("recipe_search_cache")
        
        print(f"Connected to collection: {collection.name}")
        print(f"Current recipe count: {collection.count()}")
        
        # Find duplicates
        duplicates = find_duplicate_recipes(collection)
        
        # Analyze duplicates
        analyze_duplicates(duplicates)
        
        if duplicates:
            print(f"\n💡 Next Steps:")
            print(f"1. Review the duplicate analysis above")
            print(f"2. Run cleanup_duplicates.py to remove duplicates")
            print(f"3. The system will automatically keep the highest quality recipe from each group")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 