import requests
import json
import time
import random
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

class RecipeDatabaseService:
    """
    Enhanced recipe service that connects to multiple free recipe APIs
    to provide massive recipe variety (50,000+ recipes)
    """
    
    def __init__(self):
        # Multiple free recipe APIs for maximum variety
        self.apis = {
            'spoonacular': {
                'base_url': 'https://api.spoonacular.com/recipes',
                'api_key': '01f12ed117584307b5cba262f43a8d49',
                'daily_limit': 150,
                'used_today': 0
            },
            'edamam': {
                'base_url': 'https://api.edamam.com/search',
                'app_id': 'your_edamam_app_id',  # Free tier: 5 calls/min, 10,000/month
                'app_key': 'your_edamam_app_key',
                'daily_limit': 300,
                'used_today': 0
            },
            'themealdb': {
                'base_url': 'https://www.themealdb.com/api/json/v1/1',
                'api_key': None,  # Completely free
                'daily_limit': 1000,
                'used_today': 0
            },
            'recipepuppy': {
                'base_url': 'http://www.recipepuppy.com/api',
                'api_key': None,  # Completely free
                'daily_limit': 1000,
                'used_today': 0
            }
        }
        
        # Initialize AI recipe generator for dynamic recipe creation
        try:
            from .ai_recipe_generator import AIRecipeGenerator
            self.ai_generator = AIRecipeGenerator()
            logger.info("AI Recipe Generator initialized successfully")
        except ImportError:
            logger.warning("AI Recipe Generator not available")
            self.ai_generator = None
        
    def search_massive_recipe_database(self, query: str = "", cuisine: str = "", diet: str = "", 
                                     max_time: int = 60, difficulty: str = "", 
                                     limit: int = 20, user_preferences: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search across multiple APIs for high-quality recipes only
        """
        all_results = []
        
        # Prioritize API results - these are real recipes with complete data
        per_source_limit = max(limit // 2, 10)  # Split between 2 main APIs
        
        # Search reliable APIs in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:  # Reduced workers
            futures = []
            
            # Spoonacular (premium API with detailed recipes) - PRIORITIZE
            if self.apis['spoonacular']['used_today'] < self.apis['spoonacular']['daily_limit']:
                futures.append(executor.submit(self._search_spoonacular, query, cuisine, diet, per_source_limit))
            
            # TheMealDB (completely free, reliable, detailed recipes)
            if self.apis['themealdb']['used_today'] < self.apis['themealdb']['daily_limit']:
                futures.append(executor.submit(self._search_themealdb, query, cuisine, per_source_limit))
            
            # Recipe Puppy - DISABLED for now due to reliability issues
            # if len(futures) < 2 and self.apis['recipepuppy']['used_today'] < self.apis['recipepuppy']['daily_limit']:
            #     futures.append(executor.submit(self._search_recipepuppy, query, per_source_limit // 2))
            
            # Collect results
            for future in futures:
                try:
                    results = future.result(timeout=10)
                    if results:
                        # Filter out low-quality results
                        quality_results = [r for r in results if self._is_high_quality_recipe(r)]
                        all_results.extend(quality_results)
                        logger.info(f"Got {len(quality_results)} high-quality recipes from API source")
                except Exception as e:
                    logger.warning(f"API search failed: {e}")
                    continue
        
        logger.info(f"Total high-quality recipes from external APIs: {len(all_results)}")
        
        # Only use AI/fallback generation if we have very few results AND user explicitly requested it
        if len(all_results) < (limit // 3) and self.ai_generator and query:
            try:
                ai_recipes_needed = min(5, limit - len(all_results))  # Maximum 5 AI recipes
                ai_recipes = self._generate_high_quality_ai_recipes(
                    query, cuisine, diet, user_preferences, ai_recipes_needed
                )
                if ai_recipes:
                    all_results.extend(ai_recipes)
                    logger.info(f"Added {len(ai_recipes)} high-quality AI recipes")
            except Exception as e:
                logger.warning(f"AI recipe generation failed: {e}")
        
        # Remove duplicates and filter
        unique_results = self._deduplicate_recipes(all_results)
        filtered_results = self._filter_recipes(unique_results, max_time, difficulty, diet)
        
        # Return results sorted by quality score
        return sorted(filtered_results, key=lambda x: x.get('spoonacularScore', 0), reverse=True)[:limit]
    
    def _is_high_quality_recipe(self, recipe: Dict[str, Any]) -> bool:
        """Check if a recipe meets quality standards"""
        # Must have a proper title (not placeholder)
        title = recipe.get('title', '').lower()
        if not title or 'placeholder' in title or 'untitled' in title or title.startswith('recipe #'):
            return False
        
        # Must have actual ingredients
        ingredients = recipe.get('extendedIngredients', [])
        if not ingredients or len(ingredients) < 3:
            return False
        
        # Must have proper instructions (not placeholder)
        instructions = recipe.get('instructions', '')
        if not instructions or len(instructions) < 50 or 'placeholder' in instructions.lower():
            return False
        
        # Must have a real image URL (not placeholder)
        image = recipe.get('image', '')
        if not image or 'placeholder' in image:
            return False
        
        return True
    
    def _generate_high_quality_ai_recipes(self, query: str, cuisine: str, diet: str, 
                                        user_preferences: Optional[Dict], count: int) -> List[Dict[str, Any]]:
        """Generate only high-quality AI recipes with complete details"""
        if not self.ai_generator:
            return []
        
        ai_recipes = []
        
        # Generate seasonal recipes with complete data
        if len(ai_recipes) < count:
            seasonal = self.ai_generator.generate_seasonal_recipes(count=count)
            # Only keep high-quality AI recipes
            quality_seasonal = [r for r in seasonal if self._is_high_quality_recipe(r)]
            ai_recipes.extend(quality_seasonal)
        
        # Filter AI recipes based on search criteria
        filtered_ai = []
        for recipe in ai_recipes:
            if self._matches_search_criteria(recipe, query, cuisine, diet):
                filtered_ai.append(recipe)
        
        return filtered_ai[:count]
    
    def _generate_fallback_recipes(self, query: str, cuisine: str, diet: str, count: int) -> List[Dict[str, Any]]:
        """Generate rule-based fallback recipes when AI services are unavailable - DISABLED"""
        # Disabled to maintain recipe quality - only return real API recipes
        logger.info("Fallback recipe generation disabled to maintain quality standards")
        return []
    
    def _generate_recipe_title_from_template(self, template: Dict, query: str) -> str:
        """Generate a recipe title from template"""
        try:
            title = template["base_title"]
            
            # Replace placeholders with appropriate values
            if "{cuisine}" in title:
                title = title.replace("{cuisine}", query.title() if query else "International")
            if "{dish_type}" in title:
                dish_types = template.get("dish_types", ["dish"])
                title = title.replace("{dish_type}", random.choice(dish_types).title())
            if "{ingredient}" in title:
                ingredients = template.get("ingredients", ["protein"])
                title = title.replace("{ingredient}", random.choice(ingredients).title())
            if "{cooking_method}" in title:
                methods = ["Grilled", "Roasted", "Sautéed", "Braised", "Steamed"]
                title = title.replace("{cooking_method}", random.choice(methods))
            if "{time}" in title:
                times = template.get("times", ["30"])
                title = title.replace("{time}", random.choice(times))
            if "{meal_type}" in title:
                meal_types = template.get("meal_types", ["meal"])
                title = title.replace("{meal_type}", random.choice(meal_types).title())
                
            return title
        except Exception:
            return f"Delicious {query.title() if query else 'Recipe'}"
    
    def _generate_basic_ingredients(self) -> List[Dict[str, Any]]:
        """Generate basic ingredient list"""
        basic_ingredients = [
            {"id": 1, "name": "olive oil", "amount": 2, "unit": "tablespoons"},
            {"id": 2, "name": "salt", "amount": 1, "unit": "teaspoon"},
            {"id": 3, "name": "black pepper", "amount": 0.5, "unit": "teaspoon"},
            {"id": 4, "name": "garlic", "amount": 2, "unit": "cloves"},
            {"id": 5, "name": "onion", "amount": 1, "unit": "medium"}
        ]
        return basic_ingredients
    
    def _matches_search_criteria(self, recipe: Dict[str, Any], query: str, cuisine: str, diet: str) -> bool:
        """Check if recipe matches search criteria"""
        # Query match
        if query:
            query_lower = query.lower()
            title = recipe.get('title', '').lower()
            summary = recipe.get('summary', '').lower()
            tags = [tag.lower() for tag in recipe.get('tags', [])]
            
            if not (query_lower in title or query_lower in summary or any(query_lower in tag for tag in tags)):
                return False
        
        # Cuisine match
        if cuisine:
            recipe_cuisines = [c.lower() for c in recipe.get('cuisine', [])]
            if not any(cuisine.lower() in rc for rc in recipe_cuisines):
                return False
        
        # Diet match
        if diet:
            recipe_diets = [d.lower() for d in recipe.get('diets', [])]
            if not any(diet.lower() in rd for rd in recipe_diets):
                return False
        
        return True
    
    def get_trending_recipes(self, count: int = 20, user_preferences: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get trending recipes using AI generation and external APIs"""
        recipes = []
        
        # Generate AI trending recipes
        if self.ai_generator:
            try:
                ai_trending = self.ai_generator.generate_trending_recipes(count//2, user_preferences)
                recipes.extend(ai_trending)
            except Exception as e:
                logger.warning(f"Failed to generate AI trending recipes: {e}")
        
        # Get popular recipes from external APIs
        try:
            # TheMealDB popular recipes
            themealdb_popular = self._get_themealdb_popular(count//4)
            recipes.extend(themealdb_popular)
            
            # Spoonacular popular recipes
            if self.apis['spoonacular']['used_today'] < self.apis['spoonacular']['daily_limit']:
                spoon_popular = self._get_spoonacular_popular(count//4)
                recipes.extend(spoon_popular)
                
        except Exception as e:
            logger.warning(f"Failed to get popular recipes from APIs: {e}")
        
        return self._deduplicate_recipes(recipes)[:count]
    
    def get_seasonal_recipes(self, season: str = None, count: int = 15) -> List[Dict[str, Any]]:
        """Get seasonal recipes using AI generation"""
        if not self.ai_generator:
            return []
        
        try:
            return self.ai_generator.generate_seasonal_recipes(season, count)
        except Exception as e:
            logger.warning(f"Failed to generate seasonal recipes: {e}")
            return []
    
    def get_personalized_recommendations(self, user_preferences: Dict[str, Any], count: int = 10) -> List[Dict[str, Any]]:
        """Get highly personalized recipe recommendations"""
        recipes = []
        
        # AI-generated personalized recipes
        if self.ai_generator:
            try:
                ai_personalized = self.ai_generator.generate_personalized_recipes(user_preferences, count//2)
                recipes.extend(ai_personalized)
            except Exception as e:
                logger.warning(f"Failed to generate personalized AI recipes: {e}")
        
        # Search external APIs with user preferences
        try:
            favorite_cuisines = user_preferences.get('favoriteCuisines', [])
            dietary_restrictions = user_preferences.get('dietaryRestrictions', [])
            
            for cuisine in favorite_cuisines[:3]:  # Limit to top 3 cuisines
                external_recipes = self.search_massive_recipe_database(
                    cuisine=cuisine, 
                    diet=dietary_restrictions[0] if dietary_restrictions else "",
                    limit=5,
                    user_preferences=user_preferences
                )
                recipes.extend(external_recipes)
                
        except Exception as e:
            logger.warning(f"Failed to get personalized external recipes: {e}")
        
        return self._deduplicate_recipes(recipes)[:count]
    
    def _search_themealdb(self, query: str, cuisine: str, limit: int) -> List[Dict[str, Any]]:
        """Search TheMealDB (completely free)"""
        try:
            results = []
            base_url = self.apis['themealdb']['base_url']
            
            # Search by name
            if query:
                response = requests.get(f"{base_url}/search.php?s={query}", timeout=5)
                if response.ok:
                    data = response.json()
                    if data and data.get('meals') and data['meals']:
                        for meal in data['meals'][:limit//2]:
                            if meal:  # Check meal is not None
                                normalized = self._normalize_themealdb_recipe(meal)
                                if normalized:  # Only add if normalization succeeded
                                    results.append(normalized)
            
            # Search by cuisine
            if cuisine and len(results) < limit:
                response = requests.get(f"{base_url}/filter.php?a={cuisine}", timeout=5)
                if response.ok:
                    data = response.json()
                    if data and data.get('meals') and data['meals']:
                        for meal in data['meals'][:limit//2]:
                            if meal and meal.get('idMeal'):  # Check meal has ID
                                # Get full recipe details
                                detail_response = requests.get(f"{base_url}/lookup.php?i={meal['idMeal']}", timeout=5)
                                if detail_response.ok:
                                    detail_data = detail_response.json()
                                    if detail_data and detail_data.get('meals') and detail_data['meals'] and detail_data['meals'][0]:
                                        normalized = self._normalize_themealdb_recipe(detail_data['meals'][0])
                                        if normalized:
                                            results.append(normalized)
            
            # If no specific search, get random meals
            if not query and not cuisine:
                for _ in range(limit):
                    response = requests.get(f"{base_url}/random.php", timeout=5)
                    if response.ok:
                        data = response.json()
                        if data and data.get('meals') and data['meals'] and data['meals'][0]:
                            normalized = self._normalize_themealdb_recipe(data['meals'][0])
                            if normalized:
                                results.append(normalized)
            
            # Filter out None results
            results = [r for r in results if r is not None]
            self.apis['themealdb']['used_today'] += len(results)
            return results
            
        except Exception as e:
            logger.warning(f"TheMealDB search failed: {e}")
            return []
    
    def _search_spoonacular(self, query: str, cuisine: str, diet: str, limit: int) -> List[Dict[str, Any]]:
        """Search Spoonacular API with complete recipe information"""
        try:
            base_url = self.apis['spoonacular']['base_url']
            api_key = self.apis['spoonacular']['api_key']
            
            # Use complexSearch with addRecipeInformation for complete data
            params = {
                'apiKey': api_key,
                'number': min(limit, 12),  # Limit to prevent quota exhaustion
                'addRecipeInformation': True,  # This should include instructions
                'fillIngredients': True,
                'instructionsRequired': True,  # Only return recipes with instructions
                'sort': 'popularity',  # Get popular recipes first
                'type': 'main course'  # Focus on main dishes
            }
            
            if query and len(query.strip()) > 0:
                params['query'] = query.strip()
            if cuisine and len(cuisine.strip()) > 0:
                params['cuisine'] = cuisine.strip()
            if diet and len(diet.strip()) > 0:
                params['diet'] = diet.strip()
                
            logger.info(f"Spoonacular search params: {params}")
            response = requests.get(f"{base_url}/complexSearch", params=params, timeout=10)
            
            if response.ok:
                data = response.json()
                results = data.get('results', [])
                logger.info(f"Spoonacular returned {len(results)} raw results")
                
                # Process and validate results
                quality_results = []
                for recipe in results:
                    # Ensure we have required fields
                    if not recipe.get('title') or not recipe.get('id'):
                        continue
                        
                    # Get better instructions if analyzedInstructions is available
                    instructions = recipe.get('instructions', '').strip()
                    if not instructions:
                        analyzed = recipe.get('analyzedInstructions', [])
                        if analyzed and len(analyzed) > 0 and isinstance(analyzed[0], dict):
                            # Convert analyzed instructions to text
                            instruction_text = ""
                            for instruction_set in analyzed:
                                steps = instruction_set.get('steps', [])
                                for i, step in enumerate(steps, 1):
                                    step_text = step.get('step', '').strip()
                                    if step_text:
                                        instruction_text += f"{i}. {step_text}\n"
                            if instruction_text.strip():
                                recipe['instructions'] = instruction_text.strip()
                                instructions = instruction_text.strip()
                    
                    # Only include recipes with meaningful instructions
                    if instructions and len(instructions) > 30:
                        # Ensure we have proper image URLs
                        if not recipe.get('image') or recipe.get('image') == '/placeholder.svg':
                            # Try to use Spoonacular's image service with the recipe ID
                            recipe['image'] = f"https://img.spoonacular.com/recipes/{recipe['id']}-636x393.jpg"
                        elif 'spoonacular.com' in recipe.get('image', '') and '556x370' in recipe.get('image', ''):
                            # Upgrade existing Spoonacular images to higher resolution
                            recipe['image'] = recipe['image'].replace('556x370', '636x393')
                        
                        # Ensure we have extended ingredients
                        if not recipe.get('extendedIngredients'):
                            recipe['extendedIngredients'] = []
                        
                        # Ensure cuisines is a list
                        if isinstance(recipe.get('cuisines'), str):
                            recipe['cuisines'] = [recipe['cuisines']]
                        elif not recipe.get('cuisines'):
                            recipe['cuisines'] = ['American']  # Default cuisine
                        
                        # Ensure diets is a list
                        if not recipe.get('diets'):
                            recipe['diets'] = []
                        
                        quality_results.append(recipe)
                
                logger.info(f"Spoonacular processed {len(quality_results)} quality results")
                self.apis['spoonacular']['used_today'] += len(quality_results)
                return quality_results
            else:
                logger.warning(f"Spoonacular API error: {response.status_code} - {response.text}")
            
        except Exception as e:
            logger.warning(f"Spoonacular search failed: {e}")
        
        return []
    
    def _search_recipepuppy(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search Recipe Puppy (completely free)"""
        try:
            base_url = self.apis['recipepuppy']['base_url']
            params = {}
            
            if query:
                params['q'] = query
                
            response = requests.get(base_url, params=params, timeout=5)
            if response.ok:
                data = response.json()
                results = []
                for recipe in data.get('results', [])[:limit]:
                    results.append(self._normalize_recipepuppy_recipe(recipe))
                    
                self.apis['recipepuppy']['used_today'] += len(results)
                return results
                
        except Exception as e:
            logger.warning(f"Recipe Puppy search failed: {e}")
        
        return []
    
    def _get_themealdb_popular(self, limit: int) -> List[Dict[str, Any]]:
        """Get popular recipes from TheMealDB"""
        try:
            results = []
            base_url = self.apis['themealdb']['base_url']
            
            # Get random meals as "popular"
            for _ in range(limit):
                response = requests.get(f"{base_url}/random.php", timeout=5)
                if response.ok:
                    data = response.json()
                    if data.get('meals'):
                        results.append(self._normalize_themealdb_recipe(data['meals'][0]))
            
            return results
        except Exception as e:
            logger.warning(f"Failed to get TheMealDB popular recipes: {e}")
            return []
    
    def _get_spoonacular_popular(self, limit: int) -> List[Dict[str, Any]]:
        """Get popular recipes from Spoonacular"""
        try:
            base_url = self.apis['spoonacular']['base_url']
            api_key = self.apis['spoonacular']['api_key']
            
            params = {
                'apiKey': api_key,
                'number': limit,
                'addRecipeInformation': True,
                'sort': 'popularity'
            }
            
            response = requests.get(f"{base_url}/complexSearch", params=params, timeout=5)
            if response.ok:
                data = response.json()
                results = data.get('results', [])
                self.apis['spoonacular']['used_today'] += len(results)
                return results
        except Exception as e:
            logger.warning(f"Failed to get Spoonacular popular recipes: {e}")
        
        return []
    
    # Standard cuisine list - these should match across all frontend preferences
    STANDARD_CUISINES = [
        'American', 'British', 'Chinese', 'French', 'German', 'Greek', 
        'Indian', 'Italian', 'Japanese', 'Korean', 'Mexican', 'Spanish', 
        'Thai', 'Vietnamese', 'Mediterranean', 'Middle Eastern', 'Caribbean',
        'African', 'European', 'Asian'
    ]
    
    def _normalize_themealdb_recipe(self, meal: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize TheMealDB recipe to standard format with complete data"""
        try:
            # Check if meal is None or empty
            if not meal or not isinstance(meal, dict):
                return None
                
            # Extract ingredients from TheMealDB format
            ingredients = []
            for i in range(1, 21):  # TheMealDB has up to 20 ingredients
                ingredient = meal.get(f'strIngredient{i}', '') or ''
                measure = meal.get(f'strMeasure{i}', '') or ''
                
                # Handle None values
                if ingredient is None:
                    ingredient = ''
                if measure is None:
                    measure = ''
                    
                ingredient = str(ingredient).strip()
                measure = str(measure).strip()
                
                if ingredient and ingredient.lower() not in ['null', 'none', '']:
                    ingredients.append({
                        "id": i,
                        "name": ingredient,
                        "amount": measure.split()[0] if measure else "1",
                        "unit": " ".join(measure.split()[1:]) if len(measure.split()) > 1 else "piece"
                    })
            
            # Skip recipes with insufficient ingredients
            if len(ingredients) < 3:
                return None
            
            # Determine cuisine from area and category - handle None values
            area = meal.get('strArea', '') or ''
            category = meal.get('strCategory', '') or ''
            
            # Handle None values
            if area is None:
                area = ''
            if category is None:
                category = ''
                
            area = str(area).lower().strip()
            category = str(category).lower().strip()
            
            cuisines = []
            
            # Map TheMealDB areas to standard cuisine names
            cuisine_mapping = {
                'american': 'American',
                'british': 'British', 
                'canadian': 'American',
                'chinese': 'Chinese',
                'croatian': 'European',
                'dutch': 'European',
                'egyptian': 'Middle Eastern',
                'french': 'French',
                'greek': 'Greek',
                'indian': 'Indian',
                'irish': 'British',
                'italian': 'Italian',
                'jamaican': 'Caribbean',
                'japanese': 'Japanese',
                'kenyan': 'African',
                'malaysian': 'Asian',
                'mexican': 'Mexican',
                'moroccan': 'Middle Eastern',
                'polish': 'European',
                'portuguese': 'European',
                'russian': 'European',
                'spanish': 'Spanish',
                'thai': 'Thai',
                'tunisian': 'Middle Eastern',
                'turkish': 'Middle Eastern',
                'vietnamese': 'Vietnamese'
            }
            
            if area and area in cuisine_mapping:
                cuisines.append(cuisine_mapping[area])
            elif area:
                # Try to map to one of our standard cuisines
                area_title = area.title()
                if area_title in self.STANDARD_CUISINES:
                    cuisines.append(area_title)
                else:
                    # Find closest match
                    for standard in self.STANDARD_CUISINES:
                        if area.lower() in standard.lower() or standard.lower() in area.lower():
                            cuisines.append(standard)
                            break
            
            # Must have at least one cuisine, use category-based fallback
            if not cuisines:
                if 'seafood' in category or 'fish' in category:
                    cuisines.append('Mediterranean')
                elif 'chicken' in category or 'beef' in category:
                    cuisines.append('American')
                else:
                    cuisines.append('European')  # Generic fallback
            
            # Determine diets from category and ingredients
            diets = []
            meal_tags = meal.get('strTags', '') or ''
            if meal_tags is None:
                meal_tags = ''
            meal_tags = str(meal_tags).lower()
            
            if category == 'vegetarian' or 'vegetarian' in meal_tags:
                diets.append('Vegetarian')
            if 'vegan' in meal_tags:
                diets.append('Vegan')
            if 'seafood' in category:
                diets.append('Pescetarian')
            
            # Check ingredients for dietary restrictions
            ingredient_text = ' '.join([ing['name'].lower() for ing in ingredients])
            if not any(meat in ingredient_text for meat in ['chicken', 'beef', 'pork', 'lamb', 'turkey']):
                if 'fish' not in ingredient_text and 'seafood' not in ingredient_text:
                    diets.append('Vegetarian')
            
            # Get high-quality image
            image_url = meal.get('strMealThumb', '') or ''
            if not image_url or image_url == 'null':
                # Use a food-related placeholder if no image available
                image_url = 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=400'
            
            # Get complete instructions
            instructions = meal.get('strInstructions', '') or ''
            if instructions is None:
                instructions = ''
            instructions = str(instructions).strip()
            
            if not instructions or len(instructions) < 50:
                return None  # Skip recipes without proper instructions
            
            # Format instructions properly
            formatted_instructions = instructions.replace('\r\n', '\n').replace('\r', '\n')
            
            # Create comprehensive summary
            recipe_name = meal.get('strMeal', '') or 'Unknown Recipe'
            if recipe_name is None:
                recipe_name = 'Unknown Recipe'
            recipe_name = str(recipe_name).strip()
            
            if not recipe_name or recipe_name.lower() in ['null', 'none', '']:
                recipe_name = 'Unknown Recipe'
            
            cuisine_text = cuisines[0] if cuisines else 'regional'
            summary = f"A traditional {cuisine_text.lower()} dish featuring {recipe_name.lower()}. "
            
            # Add cooking method if available in instructions
            if 'bake' in instructions.lower():
                summary += "This baked recipe "
            elif 'fry' in instructions.lower():
                summary += "This fried recipe "
            elif 'grill' in instructions.lower():
                summary += "This grilled recipe "
            else:
                summary += "This recipe "
            
            summary += f"combines authentic flavors and traditional cooking techniques to create a delicious {category or 'meal'}."
            
            # Get meal ID safely
            meal_id = meal.get('idMeal', '0') or '0'
            if meal_id is None:
                meal_id = '0'
            
            try:
                meal_id_int = int(meal_id)
            except (ValueError, TypeError):
                meal_id_int = 0
            
            return {
                "id": meal_id_int,
                "title": recipe_name,
                "cuisines": cuisines,
                "diets": diets,
                "readyInMinutes": 30,  # Default for TheMealDB
                "servings": 4,  # Default
                "image": image_url,
                "summary": summary,
                "extendedIngredients": ingredients,
                "instructions": formatted_instructions,
                "source": "TheMealDB",
                "sourceUrl": meal.get('strSource') or f"https://www.themealdb.com/meal/{meal_id}",
                "spoonacularScore": 85,  # Default good score
                "healthScore": 75,
                "tags": cuisines + diets,  # Only cuisine and diet tags
                "category": category.title() if category else 'Main Course',
                "area": area.title() if area else cuisines[0] if cuisines else 'Unknown'
            }
        except Exception as e:
            logger.error(f"Error normalizing TheMealDB recipe: {e}")
            return None
    
    def _normalize_recipepuppy_recipe(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Recipe Puppy recipe to standard format - with quality filtering"""
        try:
            # Parse ingredients from comma-separated string
            ingredients_str = recipe.get('ingredients', '').strip()
            if not ingredients_str or len(ingredients_str) < 10:
                return None  # Skip recipes with insufficient ingredients
                
            ingredients = []
            if ingredients_str:
                ingredient_list = [ing.strip() for ing in ingredients_str.split(',') if ing.strip()]
                if len(ingredient_list) < 3:
                    return None  # Need at least 3 ingredients
                    
                for i, ingredient in enumerate(ingredient_list):
                    ingredients.append({
                        "id": i + 1,
                        "name": ingredient,
                        "amount": "as needed",
                        "unit": ""
                    })
            
            # Get recipe title and validate
            title = recipe.get('title', '').strip()
            if not title or len(title) < 5:
                return None  # Skip recipes with poor titles
            
            # Try to determine cuisine from title using standard cuisines
            title_lower = title.lower()
            cuisines = []
            diets = []
            
            # Enhanced cuisine detection using our standard list
            cuisine_keywords = {
                'Italian': ['pasta', 'pizza', 'risotto', 'parmesan', 'italian', 'lasagna', 'spaghetti', 'marinara', 'pesto', 'gnocchi'],
                'Mexican': ['taco', 'burrito', 'salsa', 'mexican', 'enchilada', 'quesadilla', 'nachos', 'jalapeño', 'cilantro', 'chipotle'],
                'Chinese': ['stir fry', 'chinese', 'soy sauce', 'ginger', 'fried rice', 'wonton', 'szechuan', 'kung pao', 'chow mein'],
                'Indian': ['curry', 'indian', 'turmeric', 'garam masala', 'tikka', 'tandoori', 'biryani', 'dal', 'naan', 'masala'],
                'Thai': ['thai', 'coconut milk', 'lemongrass', 'pad thai', 'tom yum', 'green curry', 'basil', 'fish sauce'],
                'French': ['french', 'baguette', 'croissant', 'coq au vin', 'ratatouille', 'bouillabaisse', 'cassoulet', 'quiche'],
                'American': ['burger', 'bbq', 'american', 'sandwich', 'fries', 'pancake', 'meatloaf', 'cornbread', 'chili'],
                'Mediterranean': ['mediterranean', 'greek', 'hummus', 'falafel', 'olive', 'tzatziki', 'dolma', 'moussaka'],
                'Japanese': ['japanese', 'sushi', 'teriyaki', 'miso', 'ramen', 'tempura', 'katsu', 'yakitori', 'udon'],
                'Korean': ['korean', 'kimchi', 'bulgogi', 'bibimbap', 'gochujang', 'galbi', 'banchan'],
                'Spanish': ['spanish', 'paella', 'tapas', 'gazpacho', 'churros', 'sangria', 'tortilla española'],
                'German': ['german', 'sauerkraut', 'bratwurst', 'schnitzel', 'pretzel', 'strudel'],
                'Vietnamese': ['vietnamese', 'pho', 'banh mi', 'spring roll', 'nuoc mam', 'vermicelli'],
                'Middle Eastern': ['middle eastern', 'lebanese', 'persian', 'moroccan', 'shawarma', 'kebab', 'tahini', 'harissa'],
                'British': ['british', 'english', 'fish and chips', 'shepherd\'s pie', 'bangers', 'mash'],
                'Caribbean': ['caribbean', 'jerk', 'plantain', 'mango', 'coconut rice', 'callaloo']
            }
            
            # Find matching cuisine
            for cuisine_name, keywords in cuisine_keywords.items():
                if any(keyword in title_lower for keyword in keywords):
                    cuisines.append(cuisine_name)
                    break
            
            # If no specific cuisine found, try ingredient-based detection
            if not cuisines:
                ingredient_text = ingredients_str.lower()
                for cuisine_name, keywords in cuisine_keywords.items():
                    if any(keyword in ingredient_text for keyword in keywords):
                        cuisines.append(cuisine_name)
                        break
            
            # Still no cuisine found, assign based on cooking style or fallback
            if not cuisines:
                if any(word in title_lower for word in ['soup', 'stew', 'roast']):
                    cuisines.append('European')
                elif any(word in title_lower for word in ['grilled', 'bbq', 'fried']):
                    cuisines.append('American')
                else:
                    cuisines.append('European')  # Conservative fallback
            
            # Diet detection from ingredients and title
            ingredient_text = ingredients_str.lower()
            if not any(meat in ingredient_text for meat in ['chicken', 'beef', 'pork', 'lamb', 'turkey', 'meat', 'bacon']):
                if not any(fish in ingredient_text for fish in ['fish', 'salmon', 'tuna', 'shrimp', 'crab']):
                    diets.append('Vegetarian')
            
            # Check for vegan indicators
            if 'vegan' in title_lower or not any(dairy in ingredient_text for dairy in ['milk', 'cheese', 'butter', 'cream', 'egg']):
                if 'Vegetarian' in diets:
                    diets.append('Vegan')
            
            # Create better summary
            cuisine_name = cuisines[0] if cuisines else 'traditional'
            summary = f"A delicious {cuisine_name.lower()} recipe featuring {ingredients_str[:80]}{'...' if len(ingredients_str) > 80 else ''}. "
            summary += f"This {title.lower()} combines traditional flavors and cooking techniques."
            
            # Get recipe URL for instructions
            source_url = recipe.get('href', '').strip()
            if not source_url or 'http' not in source_url:
                return None  # Skip recipes without proper source URLs
            
            # Create better instructions
            instructions = f"This recipe requires the following ingredients: {ingredients_str}.\n\n"
            instructions += f"For detailed cooking instructions, please visit the original recipe at: {source_url}\n\n"
            instructions += "General preparation steps:\n"
            instructions += "1. Gather and prepare all ingredients\n"
            instructions += "2. Follow traditional cooking methods for this style of dish\n"
            instructions += "3. Cook until ingredients are properly combined and heated through\n"
            instructions += "4. Season to taste and serve as desired"
            
            # Use a food image from Unsplash instead of thumbnail
            image_url = 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400'
            
            return {
                "id": abs(hash(title + source_url)) % 100000,
                "title": title,
                "cuisines": cuisines,
                "diets": diets,
                "readyInMinutes": 25,  # Default
                "servings": 4,
                "image": image_url,
                "summary": summary,
                "extendedIngredients": ingredients,
                "instructions": instructions,
                "source": "Recipe Puppy",
                "sourceUrl": source_url,
                "spoonacularScore": 75,
                "healthScore": 70,
                "tags": cuisines + diets  # Only cuisine and diet tags
            }
        except Exception as e:
            logger.error(f"Error normalizing Recipe Puppy recipe: {e}")
            return None
    
    def _deduplicate_recipes(self, recipes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate recipes based on title similarity"""
        unique_recipes = []
        seen_titles = set()
        
        for recipe in recipes:
            title_key = recipe['title'].lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_recipes.append(recipe)
        
        return unique_recipes
    
    def _filter_recipes(self, recipes: List[Dict[str, Any]], max_time: int, 
                       difficulty: str, diet: str) -> List[Dict[str, Any]]:
        """Filter recipes based on criteria"""
        filtered = []
        
        for recipe in recipes:
            # Time filter
            if max_time and recipe.get('readyInMinutes', 30) > max_time:
                continue
            
            # Diet filter
            if diet:
                recipe_diets = [d.lower() for d in recipe.get('diets', [])]
                if diet.lower() not in recipe_diets:
                    continue
            
            filtered.append(recipe)
        
        return filtered
    
    def get_recipe_stats(self) -> Dict[str, Any]:
        """Get statistics about available recipes"""
        ai_available = self.ai_generator is not None
        
        return {
            'ai_generation_available': ai_available,
            'api_quotas': {
                api: {
                    'daily_limit': config['daily_limit'],
                    'used_today': config['used_today'],
                    'remaining': config['daily_limit'] - config['used_today']
                }
                for api, config in self.apis.items()
            },
            'estimated_total_available': 50000 if ai_available else 10000,
            'apis_active': len([api for api, config in self.apis.items() 
                              if config['used_today'] < config['daily_limit']]),
            'generation_capabilities': {
                'trending_recipes': ai_available,
                'seasonal_recipes': ai_available,
                'personalized_recipes': ai_available,
                'ai_variations': ai_available
            }
        } 

    def load_1200_recipes_distributed(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        DISABLED - Load recipes on-demand through search instead
        """
        return {
            "recipes": [],
            "total_loaded": 0,
            "target": 0,
            "message": "Bulk loading disabled - recipes are loaded on-demand through search for better quality",
            "cuisine_distribution": {},
            "cuisines": []
        }
    
    def _load_cuisine_from_apis(self, cuisine: str, limit: int) -> List[Dict[str, Any]]:
        """Load recipes for a specific cuisine from all available APIs"""
        api_recipes = []
        per_api_limit = limit // 3  # Split across 3 APIs
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            
            # TheMealDB
            if self.apis['themealdb']['used_today'] < self.apis['themealdb']['daily_limit']:
                futures.append(executor.submit(self._search_themealdb, "", cuisine, per_api_limit))
            
            # Spoonacular
            if self.apis['spoonacular']['used_today'] < self.apis['spoonacular']['daily_limit']:
                futures.append(executor.submit(self._search_spoonacular, "", cuisine, "", per_api_limit))
            
            # Recipe Puppy (with cuisine keywords)
            if self.apis['recipepuppy']['used_today'] < self.apis['recipepuppy']['daily_limit']:
                futures.append(executor.submit(self._search_recipepuppy, cuisine, per_api_limit))
            
            for future in futures:
                try:
                    results = future.result(timeout=10)
                    if results:
                        api_recipes.extend(results)
                except Exception as e:
                    logger.warning(f"API search failed for {cuisine}: {e}")
        
        return api_recipes
    
    def _generate_ai_recipes_for_cuisine(self, cuisine: str, count: int) -> List[Dict[str, Any]]:
        """Generate AI recipes specifically for a cuisine"""
        if not self.ai_generator:
            return []
        
        try:
            # Use the AI generator to create cuisine-specific recipes
            ai_recipes = []
            
            # Generate trending recipes for this cuisine
            trending = self.ai_generator.generate_trending_recipes(count//2, {"favoriteCuisines": [cuisine]})
            ai_recipes.extend(trending)
            
            # Generate seasonal recipes for this cuisine
            if len(ai_recipes) < count:
                seasonal = self.ai_generator.generate_seasonal_recipes(count=count//2)
                # Filter for cuisine
                cuisine_seasonal = [r for r in seasonal if cuisine.lower() in [c.lower() for c in r.get('cuisines', [])]]
                ai_recipes.extend(cuisine_seasonal)
            
            return ai_recipes[:count]
        except Exception as e:
            logger.warning(f"AI generation failed for {cuisine}: {e}")
            return []
    
    def _generate_template_recipes_for_cuisine(self, cuisine: str, count: int) -> List[Dict[str, Any]]:
        """Generate template-based recipes for a specific cuisine - DISABLED"""
        # Disabled to maintain recipe quality - only return real API recipes  
        logger.info("Template recipe generation disabled to maintain quality standards")
        return []
    
    def _generate_cuisine_specific_ingredients(self, cuisine: str, dish: str) -> List[Dict[str, Any]]:
        """Generate cuisine-specific ingredients"""
        base_ingredients = [
            {"id": 1, "name": "olive oil", "amount": 2, "unit": "tablespoons"},
            {"id": 2, "name": "salt", "amount": 1, "unit": "teaspoon"},
            {"id": 3, "name": "pepper", "amount": 0.5, "unit": "teaspoon"}
        ]
        
        cuisine_ingredients = {
            "italian": [
                {"id": 4, "name": "garlic", "amount": 3, "unit": "cloves"},
                {"id": 5, "name": "tomatoes", "amount": 400, "unit": "g"},
                {"id": 6, "name": "parmesan cheese", "amount": 100, "unit": "g"},
                {"id": 7, "name": "fresh basil", "amount": 20, "unit": "g"}
            ],
            "mexican": [
                {"id": 4, "name": "onion", "amount": 1, "unit": "medium"},
                {"id": 5, "name": "bell peppers", "amount": 2, "unit": "pieces"},
                {"id": 6, "name": "cumin", "amount": 1, "unit": "teaspoon"},
                {"id": 7, "name": "chili powder", "amount": 1, "unit": "teaspoon"}
            ],
            "indian": [
                {"id": 4, "name": "ginger", "amount": 15, "unit": "g"},
                {"id": 5, "name": "turmeric", "amount": 1, "unit": "teaspoon"},
                {"id": 6, "name": "garam masala", "amount": 1, "unit": "teaspoon"},
                {"id": 7, "name": "coconut milk", "amount": 400, "unit": "ml"}
            ],
            "chinese": [
                {"id": 4, "name": "soy sauce", "amount": 3, "unit": "tablespoons"},
                {"id": 5, "name": "ginger", "amount": 15, "unit": "g"},
                {"id": 6, "name": "garlic", "amount": 3, "unit": "cloves"},
                {"id": 7, "name": "sesame oil", "amount": 1, "unit": "tablespoon"}
            ]
        }
        
        specific_ingredients = cuisine_ingredients.get(cuisine.lower(), [
            {"id": 4, "name": "onion", "amount": 1, "unit": "medium"},
            {"id": 5, "name": "garlic", "amount": 2, "unit": "cloves"}
        ])
        
        return base_ingredients + specific_ingredients 