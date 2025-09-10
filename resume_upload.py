#!/usr/bin/env python3
"""
Resume uploading remaining recipes to Railway
This script will upload the remaining recipes that weren't uploaded due to interruption
"""

import os
import sys
import json
import requests
import time
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.recipe_cache_service import RecipeCacheService

class ResumeUploader:
    def __init__(self, railway_url: str = "https://full-stack-recipe-production.up.railway.app"):
        self.railway_url = railway_url.rstrip('/')
        self.api_url = f"{self.railway_url}/api"
        
        # Local services
        self.local_recipe_cache = RecipeCacheService()
        
        print(f"🚀 Resume Uploader initialized")
        print(f"   Railway URL: {self.railway_url}")
        print(f"   API URL: {self.api_url}")
    
    def get_remaining_recipes(self):
        """Get recipes that haven't been uploaded yet"""
        try:
            print("📊 Checking current Railway recipes...")
            
            # Get current recipes from Railway
            response = requests.get(f"{self.api_url}/get_recipes?limit=1000", timeout=30)
            if response.status_code == 200:
                railway_data = response.json()
                current_recipe_ids = set()
                for recipe in railway_data.get('results', []):
                    current_recipe_ids.add(str(recipe.get('id', '')))
                print(f"   Found {len(current_recipe_ids)} recipes already on Railway")
            else:
                print("   Could not check Railway recipes, assuming none uploaded")
                current_recipe_ids = set()
            
            # Get all local recipes
            print("📊 Fetching all local recipes...")
            all_recipes = self.local_recipe_cache.recipe_collection.get(
                include=['metadatas', 'documents']
            )
            
            # Process recipes and filter out already uploaded ones
            remaining_recipes = []
            for i, (recipe_id, metadata, document) in enumerate(zip(
                all_recipes['ids'], 
                all_recipes['metadatas'], 
                all_recipes['documents']
            )):
                if str(recipe_id) not in current_recipe_ids:
                    try:
                        # Parse the document
                        recipe_data = json.loads(document)
                        
                        # Create comprehensive recipe with all metadata
                        processed_recipe = {
                            'id': recipe_id,
                            'title': recipe_data.get('title', metadata.get('title', 'Unknown Recipe')),
                            'cuisine': recipe_data.get('cuisine', metadata.get('cuisine', 'unknown')),
                            'cuisines': recipe_data.get('cuisines', [metadata.get('cuisines', 'unknown')]),
                            'diets': recipe_data.get('diets', metadata.get('diets', [])),
                            'ingredients': recipe_data.get('ingredients', []),
                            'instructions': recipe_data.get('instructions', []),
                            'calories': recipe_data.get('calories', metadata.get('calories', 0)),
                            'protein': recipe_data.get('protein', metadata.get('protein', 0)),
                            'carbs': recipe_data.get('carbs', metadata.get('carbs', 0)),
                            'fat': recipe_data.get('fat', metadata.get('fat', 0)),
                            'image': recipe_data.get('image', metadata.get('image', '')),
                            'description': recipe_data.get('description', ''),
                            
                            # Add all the metadata that was missing
                            'tags': metadata.get('tags', ''),
                            'dish_types': metadata.get('dish_types', ''),
                            'cooking_time': metadata.get('cooking_time', 0),
                            'ingredient_count': metadata.get('ingredient_count', 0),
                            'source': metadata.get('source', ''),
                            'nutrition_analyzed': metadata.get('nutrition_analyzed', False),
                            'nutrition_analyzed_at': metadata.get('nutrition_analyzed_at', ''),
                            'cached_at': metadata.get('cached_at', ''),
                            
                            # Preserve original metadata
                            'metadata': metadata
                        }
                        
                        # Parse ingredients and instructions from metadata if they're strings
                        if isinstance(processed_recipe['ingredients'], str):
                            try:
                                processed_recipe['ingredients'] = json.loads(processed_recipe['ingredients'])
                            except:
                                processed_recipe['ingredients'] = []
                        
                        if isinstance(processed_recipe['instructions'], str):
                            try:
                                processed_recipe['instructions'] = json.loads(processed_recipe['instructions'])
                            except:
                                processed_recipe['instructions'] = []
                        
                        # If ingredients/instructions are empty, try to get them from metadata
                        if not processed_recipe['ingredients'] and metadata.get('ingredients'):
                            try:
                                processed_recipe['ingredients'] = json.loads(metadata['ingredients'])
                            except:
                                pass
                        
                        if not processed_recipe['instructions'] and metadata.get('instructions'):
                            try:
                                processed_recipe['instructions'] = json.loads(metadata['instructions'])
                            except:
                                pass
                        
                        # Ensure cuisines and diets are lists
                        if isinstance(processed_recipe['cuisines'], str):
                            processed_recipe['cuisines'] = [processed_recipe['cuisines']]
                        if isinstance(processed_recipe['diets'], str):
                            processed_recipe['diets'] = [processed_recipe['diets']]
                        
                        remaining_recipes.append(processed_recipe)
                        
                    except Exception as e:
                        print(f"   ⚠️  Error processing recipe {recipe_id}: {e}")
                        continue
            
            print(f"   ✅ Found {len(remaining_recipes)} recipes remaining to upload")
            return remaining_recipes
            
        except Exception as e:
            print(f"   ❌ Error getting remaining recipes: {e}")
            return []
    
    def upload_recipes_batch(self, recipes, batch_size=25):
        """Upload recipes in smaller batches to avoid timeouts"""
        total_recipes = len(recipes)
        uploaded_count = 0
        failed_count = 0
        
        print(f"📤 Uploading {total_recipes} remaining recipes in batches of {batch_size}...")
        
        for i in range(0, total_recipes, batch_size):
            batch = recipes[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_recipes + batch_size - 1) // batch_size
            
            print(f"   📦 Uploading batch {batch_num}/{total_batches} ({len(batch)} recipes)...")
            
            try:
                # Create upload data
                upload_data = {
                    'recipes': batch,
                    'batch_info': {
                        'batch_number': batch_num,
                        'total_batches': total_batches,
                        'total_recipes': total_recipes
                    }
                }
                
                # Upload to Railway
                response = requests.post(
                    f"{self.api_url}/upload-recipes",
                    json=upload_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    batch_uploaded = result.get('uploaded_count', len(batch))
                    uploaded_count += batch_uploaded
                    print(f"   ✅ Batch {batch_num} uploaded successfully ({batch_uploaded} recipes)")
                else:
                    print(f"   ❌ Batch {batch_num} failed: {response.status_code} - {response.text}")
                    failed_count += len(batch)
                
                # Longer delay between batches
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Error uploading batch {batch_num}: {e}")
                failed_count += len(batch)
        
        return uploaded_count, failed_count
    
    def run_resume_upload(self):
        """Run the resume upload process"""
        print("🚀 Starting Resume Upload to Railway")
        print("=" * 60)
        
        # Step 1: Get remaining recipes
        print("\n1️⃣ Finding remaining recipes to upload...")
        remaining_recipes = self.get_remaining_recipes()
        
        if not remaining_recipes:
            print("   ✅ No remaining recipes to upload!")
            return True
        
        print(f"   📊 {len(remaining_recipes)} recipes remaining to upload")
        
        # Step 2: Upload remaining recipes
        print("\n2️⃣ Uploading remaining recipes...")
        uploaded_count, failed_count = self.upload_recipes_batch(remaining_recipes)
        
        # Step 3: Verify upload
        print("\n3️⃣ Verifying upload...")
        try:
            verify_response = requests.get(f"{self.api_url}/get_recipes?limit=1", timeout=10)
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                total_on_railway = verify_data.get('total', 0)
                print(f"   📊 Total recipes on Railway: {total_on_railway}")
            else:
                print("   ⚠️  Could not verify upload")
        except Exception as e:
            print(f"   ⚠️  Error verifying upload: {e}")
        
        # Final summary
        print("\n" + "=" * 60)
        print("📊 RESUME UPLOAD SUMMARY")
        print(f"   Recipes to upload: {len(remaining_recipes)}")
        print(f"   Successfully uploaded: {uploaded_count}")
        print(f"   Failed uploads: {failed_count}")
        print(f"   Success rate: {(uploaded_count / len(remaining_recipes) * 100):.1f}%")
        
        if uploaded_count > 0:
            print(f"\n🎉 SUCCESS! {uploaded_count} additional recipes uploaded!")
            print(f"🌐 Your app is live at: {self.railway_url}")
            return True
        else:
            print("\n❌ No additional recipes were uploaded successfully")
            return False

def main():
    """Main function"""
    uploader = ResumeUploader()
    uploader.run_resume_upload()

if __name__ == "__main__":
    main()
