#!/usr/bin/env python3
"""
Minimal Recipe Upload - Upload recipes with minimal metadata to avoid ChromaDB issues
"""

import json
import requests
import os

def create_minimal_recipes():
    """Create minimal recipe data that avoids all ChromaDB metadata issues"""
    print("🔍 Creating minimal recipe data...")
    
    # Use the backup we know has good data
    if os.path.exists("complete_recipes_backup.json"):
        with open("complete_recipes_backup.json", 'r') as f:
            recipes = json.load(f)
    elif os.path.exists("recipes_data.json"):
        with open("recipes_data.json", 'r') as f:
            data = json.load(f)
            recipes = data.get('recipes', data) if isinstance(data, dict) else data
    else:
        print("❌ No recipe data found")
        return []
    
    minimal_recipes = []
    for i, recipe in enumerate(recipes[:50]):  # Start with just 50 recipes
        # Ultra-minimal recipe - only essential fields, no nested objects
        minimal = {
            "id": str(recipe.get('id', f'recipe_{i}')),
            "title": str(recipe.get('title', f'Recipe {i}')),
            "ingredients": [],
            "instructions": [],
            "image": "",
            "source": "imported"
        }
        
        # Handle ingredients
        ing = recipe.get('ingredients', [])
        if isinstance(ing, list):
            for ingredient in ing[:10]:  # Limit to 10 ingredients
                if isinstance(ingredient, dict):
                    name = ingredient.get('name', 'Unknown')
                    amount = ingredient.get('amount', '')
                    minimal['ingredients'].append(f"{amount} {name}".strip())
                elif isinstance(ingredient, str):
                    minimal['ingredients'].append(ingredient)
        
        # Handle instructions  
        inst = recipe.get('instructions', [])
        if isinstance(inst, list):
            minimal['instructions'] = [str(step) for step in inst[:10] if step]  # Limit to 10 steps
        elif isinstance(inst, str):
            minimal['instructions'] = [inst]
        
        # Simple image
        if recipe.get('image') and isinstance(recipe['image'], str):
            minimal['image'] = recipe['image']
        
        # Only add if we have basic data
        if minimal['ingredients'] and minimal['instructions']:
            minimal_recipes.append(minimal)
    
    print(f"✅ Created {len(minimal_recipes)} minimal recipes")
    return minimal_recipes

def upload_minimal_recipes(recipes):
    """Upload using the simplest possible approach"""
    # Save to file and try file-based upload
    filename = "minimal_recipes.json"
    with open(filename, 'w') as f:
        json.dump({"recipes": recipes}, f, indent=2)
    
    print(f"📁 Saved {len(recipes)} recipes to {filename}")
    
    # Try direct upload with minimal payload
    try:
        payload = {"limit": len(recipes), "truncate": True}
        
        response = requests.post(
            "https://dietary-delight.onrender.com/api/admin/seed",
            headers={
                "Content-Type": "application/json", 
                "X-Admin-Token": "390a77929dbe4a50705a8d8cd2888678"
            },
            json=payload,
            timeout=60
        )
        
        print(f"📡 Response: {response.status_code}")
        print(f"📄 Response text: {response.text[:300]}")
        
        if response.status_code == 200:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def check_results():
    """Check if recipes are now available"""
    try:
        response = requests.get(
            "https://dietary-delight.onrender.com/api/admin/stats?token=390a77929dbe4a50705a8d8cd2888678",
            timeout=10
        )
        
        if response.status_code == 200:
            stats = response.json()
            count = stats.get('stats', {}).get('recipes', {}).get('total', {}).get('total', 0)
            print(f"📊 Recipe count: {count}")
            return count
        else:
            print(f"⚠️ Stats check failed: {response.status_code}")
            return 0
    except Exception as e:
        print(f"⚠️ Stats error: {e}")
        return 0

def main():
    print("🚀 Minimal Recipe Upload")
    print("=" * 30)
    
    # Create minimal recipes
    recipes = create_minimal_recipes()
    if not recipes:
        print("❌ No recipes to upload")
        return
    
    # Upload them
    success = upload_minimal_recipes(recipes)
    if success:
        print("✅ Upload appears successful")
    else:
        print("❌ Upload failed")
    
    # Check results
    count = check_results()
    if count > 0:
        print(f"🎉 Success! {count} recipes available")
    else:
        print("⚠️ No recipes showing - check Render logs")

if __name__ == "__main__":
    main()
