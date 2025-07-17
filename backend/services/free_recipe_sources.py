import json
import csv
import requests
import os
import time
from typing import List, Dict, Any, Optional
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class FreeRecipeSourcesImporter:
    """
    Import thousands of recipes from free sources:
    1. Recipe JSON datasets from GitHub
    2. Open recipe databases
    3. Recipe scrapers for public sites
    4. CSV/JSON file imports
    """
    
    def __init__(self, recipes_collection=None):
        self.recipes_collection = recipes_collection
        
    def import_from_recipe1m_dataset(self) -> Dict[str, Any]:
        """
        Import from Recipe1M+ dataset (subset available freely)
        This contains 1M+ recipes with ingredients and instructions
        """
        results = {
            "total_imported": 0,
            "errors": [],
            "success": False
        }
        
        try:
            # Recipe1M+ sample dataset URL (you can expand this)
            dataset_urls = [
                "https://raw.githubusercontent.com/Glovedsasquatch/recipe-dataset/main/recipes.json",
                "https://raw.githubusercontent.com/cookpad/recipe-dataset/main/sample_recipes.json"
            ]
            
            all_recipes = []
            
            for url in dataset_urls:
                try:
                    logger.info(f"Downloading recipes from {url}")
                    response = requests.get(url, timeout=30)
                    
                    if response.ok:
                        recipes_data = response.json()
                        
                        # Handle different data structures
                        if isinstance(recipes_data, list):
                            all_recipes.extend(recipes_data)
                        elif isinstance(recipes_data, dict):
                            if "recipes" in recipes_data:
                                all_recipes.extend(recipes_data["recipes"])
                            else:
                                # Assume each key is a recipe
                                all_recipes.extend(recipes_data.values())
                        
                        logger.info(f"Downloaded {len(recipes_data)} recipes from {url}")
                    
                except Exception as e:
                    error_msg = f"Failed to download from {url}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # Process and normalize recipes
            processed_recipes = []
            for recipe in all_recipes:
                processed = self._normalize_dataset_recipe(recipe)
                if processed:
                    processed_recipes.append(processed)
            
            # Store in database
            stored_count = self._store_recipes(processed_recipes)
            
            results["total_imported"] = stored_count
            results["success"] = stored_count > 0
            
        except Exception as e:
            error_msg = f"Failed to import recipe dataset: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
        
        return results
    
    def import_from_json_file(self, file_path: str) -> Dict[str, Any]:
        """
        Import recipes from a local JSON file
        """
        results = {
            "total_imported": 0,
            "errors": [],
            "success": False
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            recipes = []
            if isinstance(data, list):
                recipes = data
            elif isinstance(data, dict):
                if "recipes" in data:
                    recipes = data["recipes"]
                else:
                    recipes = list(data.values())
            
            processed_recipes = []
            for recipe in recipes:
                processed = self._normalize_dataset_recipe(recipe)
                if processed:
                    processed_recipes.append(processed)
            
            stored_count = self._store_recipes(processed_recipes)
            
            results["total_imported"] = stored_count
            results["success"] = stored_count > 0
            
        except Exception as e:
            error_msg = f"Failed to import from JSON file {file_path}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
        
        return results
    
    def import_from_csv_file(self, file_path: str) -> Dict[str, Any]:
        """
        Import recipes from a CSV file
        Expected columns: title, ingredients, instructions, cuisine, diet, image_url, prep_time
        """
        results = {
            "total_imported": 0,
            "errors": [],
            "success": False
        }
        
        try:
            recipes = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    recipe = {
                        "title": row.get("title", "").strip(),
                        "ingredients": self._parse_csv_ingredients(row.get("ingredients", "")),
                        "instructions": self._parse_csv_instructions(row.get("instructions", "")),
                        "cuisine": row.get("cuisine", "International"),
                        "diets": self._parse_csv_diets(row.get("diet", "")),
                        "image": row.get("image_url", ""),
                        "readyInMinutes": self._parse_time(row.get("prep_time", "30")),
                        "servings": int(row.get("servings", 4)) if row.get("servings", "").isdigit() else 4,
                        "difficulty": row.get("difficulty", "medium"),
                        "description": row.get("description", ""),
                        "source": "CSV Import"
                    }
                    recipes.append(recipe)
            
            processed_recipes = []
            for recipe in recipes:
                processed = self._normalize_dataset_recipe(recipe)
                if processed:
                    processed_recipes.append(processed)
            
            stored_count = self._store_recipes(processed_recipes)
            
            results["total_imported"] = stored_count
            results["success"] = stored_count > 0
            
        except Exception as e:
            error_msg = f"Failed to import from CSV file {file_path}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
        
        return results
    
    def import_curated_recipe_collection(self) -> Dict[str, Any]:
        """
        Import a curated collection of thousands of recipes from multiple free sources
        """
        results = {
            "total_imported": 0,
            "errors": [],
            "sources_imported": [],
            "success": False
        }
        
        # Collection of free recipe sources
        sources = [
            {
                "name": "AllRecipes Sample",
                "url": "https://raw.githubusercontent.com/pbusenius/recipe-dataset/main/allrecipes_sample.json",
                "type": "json"
            },
            {
                "name": "Food.com Recipes",
                "url": "https://raw.githubusercontent.com/FFFFred/food-com-recipes/main/sample_recipes.json",
                "type": "json"
            },
            {
                "name": "Epicurious Recipes",
                "url": "https://raw.githubusercontent.com/kgullikson88/epicurious-recipes/master/sample_data.json",
                "type": "json"
            }
        ]
        
        all_recipes = []
        
        for source in sources:
            try:
                logger.info(f"Importing from {source['name']}")
                
                response = requests.get(source["url"], timeout=30)
                
                if response.ok:
                    if source["type"] == "json":
                        data = response.json()
                        
                        # Handle different JSON structures
                        source_recipes = []
                        if isinstance(data, list):
                            source_recipes = data
                        elif isinstance(data, dict):
                            if "recipes" in data:
                                source_recipes = data["recipes"]
                            elif "data" in data:
                                source_recipes = data["data"]
                            else:
                                source_recipes = list(data.values())
                        
                        # Add source information
                        for recipe in source_recipes:
                            recipe["import_source"] = source["name"]
                        
                        all_recipes.extend(source_recipes)
                        results["sources_imported"].append(source["name"])
                        
                        logger.info(f"Imported {len(source_recipes)} recipes from {source['name']}")
                
            except Exception as e:
                error_msg = f"Failed to import from {source['name']}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        # Process all recipes
        processed_recipes = []
        for recipe in all_recipes:
            processed = self._normalize_dataset_recipe(recipe)
            if processed:
                processed_recipes.append(processed)
        
        # Store in database
        stored_count = self._store_recipes(processed_recipes)
        
        results["total_imported"] = stored_count
        results["success"] = stored_count > 0
        
        return results
    
    def generate_synthetic_recipes(self, count: int = 500) -> Dict[str, Any]:
        """
        Generate synthetic but realistic recipes using templates and variations
        This is useful when other sources are limited
        """
        results = {
            "total_generated": 0,
            "success": False
        }
        
        # Recipe templates with variations
        templates = {
            "pasta": {
                "base": "{pasta_type} with {sauce} and {protein}",
                "pasta_types": ["Spaghetti", "Penne", "Fettuccine", "Linguine", "Rigatoni"],
                "sauces": ["Marinara", "Alfredo", "Pesto", "Carbonara", "Arrabbiata"],
                "proteins": ["Chicken", "Shrimp", "Italian Sausage", "Ground Beef", "Vegetables"],
                "cuisine": "Italian"
            },
            "curry": {
                "base": "{curry_type} {protein} Curry",
                "curry_types": ["Thai Green", "Indian Butter", "Coconut", "Red", "Tikka Masala"],
                "proteins": ["Chicken", "Beef", "Vegetable", "Paneer", "Tofu"],
                "cuisine": "Asian"
            },
            "stir_fry": {
                "base": "{protein} and {vegetable} Stir Fry",
                "proteins": ["Chicken", "Beef", "Pork", "Tofu", "Shrimp"],
                "vegetables": ["Broccoli", "Bell Peppers", "Snow Peas", "Mushrooms", "Bok Choy"],
                "cuisine": "Asian"
            },
            "salad": {
                "base": "{base} Salad with {dressing}",
                "bases": ["Caesar", "Greek", "Quinoa", "Spinach", "Arugula"],
                "dressings": ["Vinaigrette", "Ranch", "Balsamic", "Lemon", "Tahini"],
                "cuisine": "Mediterranean"
            },
            "soup": {
                "base": "{soup_type} Soup",
                "soup_types": ["Tomato Basil", "Chicken Noodle", "Minestrone", "Split Pea", "Butternut Squash"],
                "cuisine": "American"
            }
        }
        
        generated_recipes = []
        
        for i in range(count):
            # Choose random template
            template_name = list(templates.keys())[i % len(templates)]
            template = templates[template_name]
            
            # Generate recipe based on template
            recipe = self._generate_recipe_from_template(template, i)
            if recipe:
                generated_recipes.append(recipe)
        
        # Store generated recipes
        stored_count = self._store_recipes(generated_recipes)
        
        results["total_generated"] = stored_count
        results["success"] = stored_count > 0
        
        return results
    
    def _normalize_dataset_recipe(self, raw_recipe: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize recipe from various dataset formats to our standard format
        """
        try:
            # Handle different possible field names
            title = (raw_recipe.get("title") or 
                    raw_recipe.get("name") or 
                    raw_recipe.get("recipe_name") or "").strip()
            
            if not title or len(title) < 3:
                return None
            
            # Parse ingredients
            ingredients = self._parse_ingredients(raw_recipe)
            if not ingredients or len(ingredients) == 0:
                return None
            
            # Parse instructions
            instructions = self._parse_instructions(raw_recipe)
            if not instructions:
                return None
            
            # Generate unique ID if not present
            recipe_id = raw_recipe.get("id") or f"import_{hash(title)}"
            
            processed = {
                "id": recipe_id,
                "title": title,
                "image": self._get_recipe_image(raw_recipe),
                "readyInMinutes": self._parse_cook_time(raw_recipe),
                "servings": self._parse_servings(raw_recipe),
                "summary": raw_recipe.get("description", "")[:500],  # Limit summary
                "cuisines": self._parse_cuisines(raw_recipe),
                "diets": self._parse_diets(raw_recipe),
                "ingredients": ingredients,
                "instructions": instructions,
                "difficulty": raw_recipe.get("difficulty", "medium"),
                "source": raw_recipe.get("source", "Dataset Import"),
                "import_source": raw_recipe.get("import_source", "Unknown"),
                "added_at": time.time(),
                "quality_score": self._calculate_import_quality_score(raw_recipe, ingredients, instructions)
            }
            
            return processed
            
        except Exception as e:
            logger.warning(f"Failed to normalize recipe: {str(e)}")
            return None
    
    def _parse_ingredients(self, recipe: Dict[str, Any]) -> List[str]:
        """Parse ingredients from various formats"""
        ingredients_raw = (recipe.get("ingredients") or 
                          recipe.get("ingredient_list") or 
                          recipe.get("recipe_ingredients") or [])
        
        if isinstance(ingredients_raw, str):
            # Handle string format (comma or newline separated)
            if '\n' in ingredients_raw:
                ingredients = [ing.strip() for ing in ingredients_raw.split('\n')]
            else:
                ingredients = [ing.strip() for ing in ingredients_raw.split(',')]
        elif isinstance(ingredients_raw, list):
            ingredients = [str(ing).strip() for ing in ingredients_raw]
        else:
            return []
        
        # Filter out empty ingredients
        return [ing for ing in ingredients if ing and len(ing) > 2]
    
    def _parse_instructions(self, recipe: Dict[str, Any]) -> str:
        """Parse instructions from various formats"""
        instructions_raw = (recipe.get("instructions") or 
                           recipe.get("directions") or 
                           recipe.get("method") or 
                           recipe.get("recipe_instructions") or "")
        
        if isinstance(instructions_raw, list):
            # Join list of instruction steps
            instructions = "\n".join([str(step).strip() for step in instructions_raw])
        else:
            instructions = str(instructions_raw).strip()
        
        # Minimum instruction length check
        if len(instructions) < 20:
            return ""
        
        return instructions
    
    def _parse_cuisines(self, recipe: Dict[str, Any]) -> List[str]:
        """Parse cuisine information"""
        cuisine = (recipe.get("cuisine") or 
                  recipe.get("category") or 
                  recipe.get("cuisine_type") or "International")
        
        if isinstance(cuisine, list):
            return [str(c).title() for c in cuisine]
        else:
            return [str(cuisine).title()]
    
    def _parse_diets(self, recipe: Dict[str, Any]) -> List[str]:
        """Parse dietary information"""
        diet_info = recipe.get("diet", [])
        
        if isinstance(diet_info, str):
            diet_info = [diet_info]
        elif not isinstance(diet_info, list):
            diet_info = []
        
        return [str(d).lower() for d in diet_info]
    
    def _parse_cook_time(self, recipe: Dict[str, Any]) -> int:
        """Parse cooking time"""
        time_str = (recipe.get("cook_time") or 
                   recipe.get("prep_time") or 
                   recipe.get("total_time") or 
                   recipe.get("readyInMinutes") or "30")
        
        return self._parse_time(str(time_str))
    
    def _parse_servings(self, recipe: Dict[str, Any]) -> int:
        """Parse serving size"""
        servings = recipe.get("servings", recipe.get("yield", 4))
        
        try:
            return int(servings)
        except:
            return 4
    
    def _get_recipe_image(self, recipe: Dict[str, Any]) -> str:
        """Get recipe image URL"""
        image = (recipe.get("image") or 
                recipe.get("image_url") or 
                recipe.get("photo") or "")
        
        # Validate URL
        if image and urlparse(image).scheme in ['http', 'https']:
            return image
        
        return ""
    
    def _parse_time(self, time_str: str) -> int:
        """Parse time string to minutes"""
        if not time_str:
            return 30
        
        # Extract numbers from string
        import re
        numbers = re.findall(r'\d+', str(time_str))
        
        if not numbers:
            return 30
        
        time_value = int(numbers[0])
        
        # Handle hours
        if 'hour' in time_str.lower() or 'hr' in time_str.lower():
            time_value *= 60
        
        # Reasonable bounds
        return max(5, min(time_value, 480))  # 5 min to 8 hours
    
    def _parse_csv_ingredients(self, ingredients_str: str) -> List[str]:
        """Parse ingredients from CSV format"""
        if not ingredients_str:
            return []
        
        # Handle semicolon, pipe, or newline separated
        separators = [';', '|', '\n', ',']
        
        for sep in separators:
            if sep in ingredients_str:
                return [ing.strip() for ing in ingredients_str.split(sep) if ing.strip()]
        
        return [ingredients_str.strip()]
    
    def _parse_csv_instructions(self, instructions_str: str) -> str:
        """Parse instructions from CSV format"""
        if not instructions_str:
            return ""
        
        # Replace common separators with periods
        instructions = instructions_str.replace('|', '. ').replace(';', '. ')
        return instructions.strip()
    
    def _parse_csv_diets(self, diet_str: str) -> List[str]:
        """Parse diet restrictions from CSV"""
        if not diet_str:
            return []
        
        return [d.strip().lower() for d in diet_str.split(',') if d.strip()]
    
    def _calculate_import_quality_score(self, recipe: Dict[str, Any], ingredients: List[str], instructions: str) -> float:
        """Calculate quality score for imported recipe"""
        score = 0.0
        
        # Title quality
        title = recipe.get("title", "")
        if title and len(title) > 5:
            score += 1.0
        
        # Ingredients quality
        if len(ingredients) >= 3:
            score += 1.0
        if len(ingredients) >= 6:
            score += 0.5
        
        # Instructions quality
        if instructions and len(instructions) > 50:
            score += 1.0
        if len(instructions) > 200:
            score += 0.5
        
        # Image presence
        if recipe.get("image"):
            score += 0.5
        
        # Additional metadata
        if recipe.get("cuisine"):
            score += 0.3
        if recipe.get("cook_time") or recipe.get("prep_time"):
            score += 0.3
        
        return min(score, 5.0)
    
    def _generate_recipe_from_template(self, template: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Generate a recipe from a template"""
        import random
        
        # Generate title
        base_title = template["base"]
        
        # Replace placeholders
        for key, values in template.items():
            if key != "base" and key != "cuisine" and isinstance(values, list):
                placeholder = f"{{{key[:-1]}}}"  # Remove 's' from key
                if placeholder in base_title:
                    base_title = base_title.replace(placeholder, random.choice(values))
        
        # Generate basic recipe data
        recipe = {
            "id": f"generated_{index}",
            "title": base_title,
            "cuisine": template.get("cuisine", "International"),
            "readyInMinutes": random.randint(15, 90),
            "servings": random.randint(2, 8),
            "difficulty": random.choice(["easy", "medium", "hard"]),
            "ingredients": self._generate_ingredients_for_recipe(base_title),
            "instructions": self._generate_instructions_for_recipe(base_title),
            "image": "",
            "source": "Generated",
            "added_at": time.time()
        }
        
        return recipe
    
    def _generate_ingredients_for_recipe(self, title: str) -> List[str]:
        """Generate plausible ingredients based on recipe title"""
        # This is a simplified version - you could make this much more sophisticated
        common_ingredients = [
            "Salt", "Black pepper", "Olive oil", "Garlic", "Onion",
            "Butter", "Flour", "Eggs", "Milk", "Water"
        ]
        
        # Add specific ingredients based on title keywords
        specific_ingredients = []
        title_lower = title.lower()
        
        if "chicken" in title_lower:
            specific_ingredients.extend(["Chicken breast", "Chicken thighs"])
        if "pasta" in title_lower:
            specific_ingredients.extend(["Pasta", "Parmesan cheese"])
        if "curry" in title_lower:
            specific_ingredients.extend(["Curry powder", "Coconut milk", "Ginger"])
        if "soup" in title_lower:
            specific_ingredients.extend(["Vegetable broth", "Celery", "Carrots"])
        
        # Combine and return
        all_ingredients = specific_ingredients + common_ingredients[:5]
        return all_ingredients[:8]  # Limit to 8 ingredients
    
    def _generate_instructions_for_recipe(self, title: str) -> str:
        """Generate basic instructions based on recipe title"""
        # This is very simplified - you could use AI or more complex templates
        base_instructions = [
            "Prepare all ingredients by washing and chopping as needed.",
            "Heat oil in a large pan over medium heat.",
            "Cook the main ingredients according to the recipe requirements.",
            "Season with salt, pepper, and other spices to taste.",
            "Serve hot and enjoy!"
        ]
        
        return ". ".join(base_instructions)
    
    def _store_recipes(self, recipes: List[Dict[str, Any]]) -> int:
        """Store recipes in database, avoiding duplicates"""
        if not self.recipes_collection or not recipes:
            return 0
        
        stored_count = 0
        
        for recipe in recipes:
            try:
                # Check for duplicates by title
                existing = self.recipes_collection.find_one({
                    "$or": [
                        {"id": recipe["id"]},
                        {"title": recipe["title"]}
                    ]
                })
                
                if not existing:
                    self.recipes_collection.insert_one(recipe)
                    stored_count += 1
                
            except Exception as e:
                logger.error(f"Failed to store recipe {recipe.get('title', 'unknown')}: {e}")
        
        return stored_count 