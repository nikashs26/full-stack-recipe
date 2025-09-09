import chromadb
import json
import hashlib
from typing import List, Dict, Any, Optional
import logging
import time
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecipeCacheService:
    def __init__(self, cache_ttl_days: int = None):
        """
        Initialize ChromaDB client and collections for recipe caching
        
        Args:
            cache_ttl_days: Number of days before cache entries expire (default: None - TTL disabled)
        """
        try:
            # Initialize ChromaDB with persistent storage
            # Use Railway persistent volume if available, fallback to local storage
            import os
            chroma_path = os.environ.get('CHROMA_DB_PATH', './chroma_db')
            
            # For Railway deployment, use persistent volume
            if os.environ.get('RAILWAY_ENVIRONMENT'):
                chroma_path = os.environ.get('CHROMA_DB_PATH', '/app/data/chroma_db')
            
            # Ensure directory exists
            os.makedirs(chroma_path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=chroma_path)
            
            # Create embedding function
            self.embedding_function = chromadb.utils.embedding_functions.DefaultEmbeddingFunction()
            
            # Collection for search results
            self.search_collection = self.client.get_or_create_collection(
                name="recipe_search_cache",
                metadata={"description": "Cache for recipe search results"},
                embedding_function=self.embedding_function
            )
            
            # Collection for individual recipes
            self.recipe_collection = self.client.get_or_create_collection(
                name="recipe_details_cache",
                metadata={"description": "Cache for individual recipe details"},
                embedding_function=self.embedding_function
            )
            
            # TTL is disabled - recipes will never expire
            self.cache_ttl = None
            logger.info("ChromaDB recipe cache initialized with TTL disabled - recipes will never expire")
            logger.info(f"Using persistent storage at {chroma_path}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB recipe cache: {e}")
            self.client = None
            self.search_collection = None
            self.recipe_collection = None
            self.cache_ttl = None  # TTL disabled even if initialization fails

    def _generate_cache_key(self, query: str = "", ingredient: str = "", filters: Optional[Dict[str, Any]] = None) -> str:
        """Generate a unique cache key for the search parameters including filters"""
        search_params = {
            "query": query.lower().strip(),
            "ingredient": ingredient.lower().strip(),
            "filters": filters or {}
        }
        return hashlib.md5(json.dumps(search_params, sort_keys=True).encode()).hexdigest()

    def _is_cache_valid(self, cached_at: str) -> bool:
        """Check if a cache entry is still valid based on TTL"""
        # Always return True to disable TTL - recipes will never expire
        return True
        
        # Original TTL logic (commented out):
        # if not cached_at or not isinstance(cached_at, str):
        #     return False
        #     
        # try:
        #     cached_time = datetime.fromisoformat(cached_at)
        #     return datetime.now() - cached_time < self.cache_ttl
        # except (ValueError, TypeError) as e:
        #     logger.warning(f"Invalid cache timestamp '{cached_at}': {str(e)}")
        #     return False
            
    async def add_recipe(self, recipe: Dict[str, Any]) -> bool:
        """
        Add or update a recipe in the cache
        
        Args:
            recipe: The recipe data to cache
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not recipe or not isinstance(recipe, dict):
            logger.error("Invalid recipe: must be a non-empty dictionary")
            return False
            
        try:
            # Extract metadata for search
            metadata = self._extract_recipe_metadata(recipe)
            if not metadata or 'id' not in metadata:
                logger.error("Failed to extract required metadata from recipe")
                return False
                
            # Store the full recipe data as the document, not just text summary
            recipe_document = json.dumps(recipe)
            
            # Add to recipe collection
            self.recipe_collection.upsert(
                ids=[metadata['id']],
                documents=[recipe_document],  # Store full recipe data
                metadatas=[metadata]
            )
            
            logger.debug(f"Successfully cached recipe: {metadata.get('title')} (ID: {metadata['id']})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding recipe to cache: {str(e)}")
            return False

    def _extract_recipe_metadata(self, recipe: Dict[Any, Any]) -> Dict[str, Any]:
        """Extract searchable metadata from a recipe"""
        if not recipe or not isinstance(recipe, dict):
            logger.warning("Invalid recipe format: recipe must be a non-empty dictionary")
            return {}
            
        try:
            # Handle different recipe formats (TheMealDB vs Spoonacular)
            cuisines = []
            if 'cuisine' in recipe:  # TheMealDB format
                cuisines = [recipe['cuisine']] if recipe.get('cuisine') else []
            else:  # Spoonacular format
                cuisines = recipe.get('cuisines', [])
                if isinstance(cuisines, str):
                    cuisines = [c.strip() for c in cuisines.split(',') if c.strip()]
                
            # Handle dietary restrictions
            dietary_restrictions = recipe.get('dietary_restrictions', recipe.get('diets', []))
            if isinstance(dietary_restrictions, str):
                dietary_restrictions = [d.strip() for d in dietary_restrictions.split(',') if d.strip()]
                
            # Handle ingredients
            ingredients = []
            if 'strIngredient1' in recipe:  # TheMealDB format
                ingredients = [
                    recipe[f'strIngredient{i}'] 
                    for i in range(1, 21) 
                    if recipe.get(f'strIngredient{i}') and str(recipe[f'strIngredient{i}']).strip()
                ]
            else:  # Spoonacular format
                ingredients = [
                    str(ing.get('name', '')) 
                    for ing in recipe.get('extendedIngredients', []) 
                    if ing and isinstance(ing, dict)
                ]
            
            # Get recipe ID and title with proper fallbacks
            recipe_id = str(recipe.get('idMeal', recipe.get('id', ''))).strip()
            if not recipe_id:
                logger.warning("Recipe is missing an ID, generating a random one")
                import uuid
                recipe_id = str(uuid.uuid4())
                
            title = str(recipe.get('strMeal', recipe.get('title', 'Untitled Recipe'))).strip()
            
            # Create base metadata dictionary
            metadata = {
                "id": recipe_id,
                "title": title,
                "cuisine": cuisines[0] if cuisines else 'Other',
                "cuisines": ','.join(cuisines) if cuisines else '',
                "diets": ','.join(dietary_restrictions) if dietary_restrictions else '',
                "tags": ','.join(recipe.get('tags', [])) if recipe.get('tags') else '',
                "dish_types": ','.join(recipe.get('dishTypes', [])) if recipe.get('dishTypes') else '',
                "ingredients": ','.join(ingredients) if ingredients else '',
                "cached_at": datetime.now().isoformat(),
                "source": recipe.get('source', 'themealdb' if 'idMeal' in recipe else 'spoonacular'),
            }
            
            # Add optional fields if they exist
            if 'nutrition' in recipe and recipe['nutrition']:
                metadata["calories"] = recipe['nutrition'].get('calories', 0)
                
            if 'readyInMinutes' in recipe:
                metadata["cooking_time"] = recipe['readyInMinutes']
                
            if 'strArea' in recipe:
                metadata["area"] = recipe['strArea']
                
            # Add category if it exists
            if 'strCategory' in recipe:
                metadata["category"] = recipe['strCategory']
                
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting recipe metadata: {str(e)}")
            return {}

    def _extract_search_terms(self, recipe: Dict[Any, Any]) -> str:
        """Extract searchable terms from a recipe"""
        terms = []
        
        # Add title with higher weight
        title = recipe.get('title', '')
        if title:
            terms.extend([title] * 3)  # Repeat title for higher weight
            
        # Add cuisine types
        terms.extend(recipe.get('cuisines', []))
        
        # Add diet types
        terms.extend(recipe.get('diets', []))
        
        # Add dish types
        terms.extend(recipe.get('dishTypes', []))
        
        # Add main ingredients
        ingredients = [ing.get('name', '') for ing in recipe.get('ingredients', [])]
        terms.extend(ingredients)
        
        # Add cooking method keywords from instructions
        instructions = recipe.get('instructions', '')
        # Handle case where instructions is a list
        if isinstance(instructions, list):
            instructions = ' '.join(str(step) for step in instructions)
        # Ensure instructions is a string
        instructions = str(instructions or '').lower()
        
        cooking_methods = ['bake', 'fry', 'grill', 'roast', 'boil', 'steam', 'saute']
        for method in cooking_methods:
            if method in instructions:
                terms.append(method)
        
        # Join all terms and create searchable text
        return ' '.join(filter(None, terms)).lower()

    def get_cached_recipes(self, query: str = "", ingredient: str = "", filters: Optional[Dict[str, Any]] = None) -> List[Dict[Any, Any]]:
        """Retrieve cached recipes for the given search parameters with TTL support"""
       
        
        if not self.recipe_collection:
            logger.warning("ChromaDB recipe collection not initialized")
            return []
        
        try:
            # Get all recipes from cache first
            all_recipes = self._get_all_recipes_from_cache()
            logger.info(f"Retrieved {len(all_recipes)} recipes from cache")
            
            # Debug: Show exactly what parameters we received
            logger.info("🔍 SEARCH PARAMETERS RECEIVED:")
            logger.info(f"  - query parameter: '{query}' (type: {type(query)}, length: {len(query) if query else 0})")
            logger.info(f"  - ingredient parameter: '{ingredient}' (type: {type(ingredient)}, length: {len(ingredient) if ingredient else 0})")
            logger.info(f"  - query.strip(): '{query.strip() if query else ''}'")
            logger.info(f"  - ingredient.strip(): '{ingredient.strip() if ingredient else ''}'")
            
            # Check for chained search: base recipes from previous search
            base_recipes = None
            if filters and 'baseRecipes' in filters and filters['baseRecipes']:
                base_recipes = filters['baseRecipes']
                logger.info(f"🔗 CHAINED SEARCH DETECTED: {len(base_recipes)} base recipes from previous search")
                # Use base recipes instead of all recipes for filtering
                all_recipes = base_recipes
                logger.info(f"  - Will filter ingredient search within {len(all_recipes)} base recipes")
            
            # If no search terms, return all recipes (or base recipes if chained search)
            if not query.strip() and not ingredient.strip():
                logger.info(f"🔍 DEBUG: No search terms detected - query.strip(): '{query.strip()}', ingredient.strip(): '{ingredient.strip()}'")
                if base_recipes:
                    logger.debug("Chained search with no new terms - returning base recipes")
                else:
                    logger.debug("No search terms - applying filters if provided")
                    # Apply filters to all recipes when no search terms
                    if filters:
                        logger.info(f"🔍 DEBUG: About to check filters: {filters}")
                        logger.info(f"🔍 DEBUG: filters type: {type(filters)}")
                        logger.info(f"🔍 DEBUG: filters truthy: {bool(filters)}")
                        logger.info(f"🔍 Applying filters to all recipes: {filters}")
                        logger.info(f"🔍 Total recipes to filter: {len(all_recipes)}")
                        logger.info(f"🔍 Dietary restrictions filter: {filters.get('dietary_restrictions', 'None')}")
                        filtered_recipes = []
                        
                        for recipe in all_recipes:
                            should_include = True
                            
                            # Cuisine filter
                            if filters.get("cuisine"):
                                cuisine_filter = filters["cuisine"]
                                recipe_cuisines = []
                                
                                # Check both cuisine and cuisines fields
                                if recipe.get('cuisine'):
                                    recipe_cuisines.append(recipe['cuisine'].lower())
                                if recipe.get('cuisines') and isinstance(recipe['cuisines'], list):
                                    recipe_cuisines.extend([c.lower() for c in recipe['cuisines'] if c])
                                
                                # CUISINE EXPANSION: Automatically include related/subset cuisines
                                expanded_cuisine_filter = self._expand_cuisine_filter(cuisine_filter)
                                if expanded_cuisine_filter != cuisine_filter:
                                    logger.info(f"🔍 CUISINE EXPANSION: {cuisine_filter} -> {expanded_cuisine_filter}")
                                
                                logger.info(f"🔍 DEBUG: Recipe '{recipe.get('title', 'Unknown')}' has cuisines: {recipe_cuisines}")
                                logger.info(f"🔍 DEBUG: Filtering for cuisine: {cuisine_filter}")
                                logger.info(f"🔍 DEBUG: Expanded cuisine filter: {expanded_cuisine_filter}")
                                logger.info(f"🔍 DEBUG: cuisine_filter type: {type(cuisine_filter)}")
                                
                                # Handle both single string and list of strings for cuisine filter
                                if isinstance(expanded_cuisine_filter, str):
                                    # Single cuisine filter - check for exact match or contains
                                    if not any(expanded_cuisine_filter.lower() == cuisine.lower() or cuisine.lower() in expanded_cuisine_filter.lower() for cuisine in recipe_cuisines):
                                        should_include = False
                                        logger.debug(f"Recipe '{recipe.get('title', 'Unknown')}' excluded by cuisine filter: {expanded_cuisine_filter}")
                                elif isinstance(expanded_cuisine_filter, list):
                                    # Multiple cuisine filters - check if ANY of the requested cuisines match ANY of the recipe's cuisines
                                    # This is the key fix: we want to include recipes that match ANY of the requested cuisines
                                    logger.info(f"🔍 DEBUG: Processing expanded list cuisine filter: {expanded_cuisine_filter}")
                                    cuisine_matched = False
                                    for filter_cuisine in expanded_cuisine_filter:
                                        if not filter_cuisine:
                                            continue
                                        filter_cuisine_lower = filter_cuisine.lower().strip()
                                        logger.info(f"🔍 DEBUG: Checking filter cuisine: '{filter_cuisine}' -> '{filter_cuisine_lower}'")
                                        
                                        for recipe_cuisine in recipe_cuisines:
                                            if not recipe_cuisine:
                                                continue
                                            recipe_cuisine_lower = recipe_cuisine.lower().strip()
                                            logger.info(f"🔍 DEBUG: Against recipe cuisine: '{recipe_cuisine}' -> '{recipe_cuisine_lower}'")
                                            
                                            # Check for exact match or partial match
                                            if (filter_cuisine_lower == recipe_cuisine_lower or 
                                                filter_cuisine_lower in recipe_cuisine_lower or 
                                                recipe_cuisine_lower in filter_cuisine_lower):
                                                cuisine_matched = True
                                                logger.info(f"🔍 DEBUG: ✅ Cuisine match found: '{filter_cuisine_lower}' matches '{recipe_cuisine_lower}'")
                                                break
                                        
                                        if cuisine_matched:
                                            break
                                    
                                    if not cuisine_matched:
                                        should_include = False
                                        logger.info(f"🔍 DEBUG: ❌ Recipe '{recipe.get('title', 'Unknown')}' excluded by cuisine filter: {expanded_cuisine_filter} - no matches found")
                                        logger.info(f"🔍 DEBUG: Recipe cuisines: {recipe_cuisines}")
                                        logger.info(f"🔍 DEBUG: Expanded filter cuisines: {expanded_cuisine_filter}")
                                else:
                                    # Invalid filter type
                                    should_include = False
                                    logger.warning(f"Invalid cuisine filter type: {type(expanded_cuisine_filter)}")
                            
                            # Dietary restrictions filter
                            if should_include and filters.get("dietary_restrictions"):
                                dietary_filter = [d.lower() for d in filters["dietary_restrictions"]]
                                recipe_dietary = []
                                
                                # Check dietaryRestrictions and diets arrays
                                if recipe.get('dietaryRestrictions'):
                                    recipe_dietary.extend([d.lower() for d in recipe['dietaryRestrictions'] if d])
                                if recipe.get('diets'):
                                    recipe_dietary.extend([d.lower() for d in recipe['diets'] if d])
                                
                                # Check vegetarian and vegan boolean fields
                                if recipe.get('vegetarian') is True:
                                    recipe_dietary.append('vegetarian')
                                if recipe.get('vegan') is True:
                                    recipe_dietary.append('vegan')
                                
                                # FIXED: Always validate vegetarian/vegan recipes with ingredient-based detection
                                # This catches both missing tags AND incorrectly tagged recipes
                                if 'vegetarian' in dietary_filter:
                                    # Check if recipe is actually vegetarian by analyzing ingredients
                                    if self._is_recipe_vegetarian_by_ingredients(recipe):
                                        # Add vegetarian tag if not already present
                                        if not any('vegetarian' in diet.lower() for diet in recipe_dietary):
                                            recipe_dietary.append('vegetarian')
                                            logger.debug(f"🔍 Detected vegetarian recipe by ingredients: {recipe.get('title', 'Unknown')}")
                                    else:
                                        # Recipe has meat - remove any incorrect vegetarian tags
                                        recipe_dietary = [d for d in recipe_dietary if 'vegetarian' not in d.lower()]
                                        logger.debug(f"❌ Removed incorrect vegetarian tag from meat recipe: {recipe.get('title', 'Unknown')}")
                                
                                if 'vegan' in dietary_filter:
                                    # Check if recipe is actually vegan by analyzing ingredients
                                    if self._is_recipe_vegan_by_ingredients(recipe):
                                        # Add vegan tag if not already present
                                        if not any('vegan' in diet.lower() for diet in recipe_dietary):
                                            recipe_dietary.append('vegan')
                                            logger.debug(f"🔍 Detected vegan recipe by ingredients: {recipe.get('title', 'Unknown')}")
                                    else:
                                        # Recipe has animal products - remove any incorrect vegan tags
                                        recipe_dietary = [d for d in recipe_dietary if 'vegan' not in d.lower()]
                                        logger.debug(f"❌ Removed incorrect vegan tag from non-vegan recipe: {recipe.get('title', 'Unknown')}")
                                
                                # IMPROVED: Check if any recipe dietary info matches the filter
                                # Use more flexible matching to catch variations
                                dietary_matched = False
                                for diet_filter in dietary_filter:
                                    for recipe_diet in recipe_dietary:
                                        # Check for exact match or partial match
                                        if (diet_filter == recipe_diet or 
                                            diet_filter in recipe_diet or 
                                            recipe_diet in diet_filter):
                                            dietary_matched = True
                                            logger.debug(f"✅ Dietary match found: '{diet_filter}' matches '{recipe_diet}'")
                                            break
                                    if dietary_matched:
                                        break
                                
                                if not dietary_matched:
                                    should_include = False
                                    logger.debug(f"Recipe '{recipe.get('title', 'Unknown')}' excluded by dietary filter: {dietary_filter}")
                                    logger.debug(f"Recipe dietary info: {recipe_dietary}")
                            
                            # Max cooking time filter
                            if should_include and filters.get("max_cooking_time"):
                                try:
                                    max_time = int(filters["max_cooking_time"])
                                    recipe_time = recipe.get('cooking_time') or recipe.get('readyInMinutes')
                                    if recipe_time and int(recipe_time) > max_time:
                                        should_include = False
                                        logger.debug(f"Recipe '{recipe.get('title', 'Unknown')}' excluded by cooking time filter: {recipe_time} > {max_time}")
                                except (ValueError, TypeError):
                                    logger.warning(f"Invalid max_cooking_time value: {filters['max_cooking_time']}")
                            
                            # Max calories filter
                            if should_include and filters.get("max_calories"):
                                try:
                                    max_cal = int(filters["max_calories"])
                                    recipe_calories = recipe.get('calories') or recipe.get('calorieCount')
                                    if recipe_calories and int(recipe_calories) > max_cal:
                                        should_include = False
                                        logger.debug(f"Recipe '{recipe.get('title', 'Unknown')}' excluded by calories filter: {recipe_calories} > {max_cal}")
                                except (ValueError, TypeError):
                                    logger.warning(f"Invalid max_calories value: {filters['max_calories']}")
                            
                            # Min rating filter
                            if should_include and filters.get("min_rating"):
                                try:
                                    min_rating = float(filters["min_rating"])
                                    recipe_rating = recipe.get('avg_rating') or recipe.get('rating')
                                    if recipe_rating and float(recipe_rating) < min_rating:
                                        should_include = False
                                        logger.debug(f"Recipe '{recipe.get('title', 'Unknown')}' excluded by rating filter: {recipe_rating} < {min_rating}")
                                except (ValueError, TypeError):
                                    logger.warning(f"Invalid min_rating value: {filters['min_rating']}")
                            
                            if should_include:
                                filtered_recipes.append(recipe)
                        
                        logger.info(f"🔍 Filtering results: {len(all_recipes)} -> {len(filtered_recipes)} recipes")
                        logger.info(f"🔍 Final filtered count: {len(filtered_recipes)}")
                        all_recipes = filtered_recipes
                    
                    # If no search terms and no filters, return all recipes
                    if not filters:
                        logger.info(f"🔍 No search terms and no filters - returning all {len(all_recipes)} recipes")
                        return all_recipes
                    else:
                        logger.info(f"🔍 No search terms but filters applied - returning {len(all_recipes)} filtered recipes")
                        return all_recipes
            
            # STRICT VALIDATION: Require meaningful search terms
            query_trimmed = query.strip()
            ingredient_trimmed = ingredient.strip()
            
            # REMOVED: Minimum length requirement to allow flexible substring searching
            # Now any search term length will work, including single characters
            # MIN_QUERY_LENGTH = 3
            # if (query_trimmed and len(query_trimmed) < MIN_QUERY_LENGTH) or (ingredient_trimmed and len(ingredient_trimmed) < MIN_QUERY_LENGTH):
            #     logger.warning(f"Search terms too short - query: '{query_trimmed}' ({len(query_trimmed)} chars), ingredient: '{ingredient_trimmed}' ({len(ingredient_trimmed)} chars)")
            #     logger.warning(f"Minimum required length: {MIN_QUERY_LENGTH} characters")
            #     return []  # Return empty results for nonsense searches
            
            # Check if this is primarily an ingredient search vs name search
            is_ingredient_search = bool(ingredient_trimmed)
            is_name_search = bool(query_trimmed)
            is_combined_search = is_ingredient_search and is_name_search
            
            logger.info(f"🔍 SEARCH TYPE DETERMINATION:")
            logger.info(f"  - ingredient.strip() result: '{ingredient_trimmed}'")
            logger.info(f"  - query.strip() result: '{query_trimmed}'")
            logger.info(f"  - bool(ingredient.strip()): {is_ingredient_search}")
            logger.info(f"  - bool(query.strip()): {is_name_search}")
            logger.info(f"  - is_combined_search: {is_combined_search}")
            logger.info(f"  - Final: ingredient_search={is_ingredient_search}, name_search={is_name_search}")
            
            if is_combined_search:
                logger.info(f"🔍 COMBINED SEARCH MODE: Both name and ingredient search provided")
                logger.info(f"  - Name search: '{query_trimmed}' in title/description")
                logger.info(f"  - Ingredient search: '{ingredient_trimmed}' in ingredients field")
                logger.info(f"  - Will return recipes that match EITHER criteria")
            elif is_ingredient_search:
                logger.info(f"🔍 INGREDIENT SEARCH MODE: Looking ONLY in ingredients field for '{ingredient_trimmed}'")
                logger.info(f"  - WILL NOT look at title, description, or any other fields")
                logger.info(f"  - ONLY checking recipe.ingredients array for word matches")
            elif is_name_search:
                logger.info(f"🔍 NAME SEARCH MODE: Looking ONLY in title/description fields for '{query_trimmed}'")
                logger.info(f"  - WILL NOT look at ingredients field at all")
                logger.info(f"  - ONLY checking recipe.title and recipe.description for word matches")
            else:
                logger.warning("⚠️ No search parameters provided - applying filters only")
                # This path is now handled above in the no search terms section
            
            matching_recipes = []
            
            # DEBUG: Log the first few recipes to see their structure
            logger.info(f"🔍 DEBUG: First 3 recipes structure:")
            for i, recipe in enumerate(all_recipes[:3]):
                logger.info(f"  Recipe {i+1}: '{recipe.get('title', 'No title')}'")
                logger.info(f"    - Keys: {list(recipe.keys())}")
                logger.info(f"    - Title: '{recipe.get('title', 'No title')}'")
                logger.info(f"    - Description: '{recipe.get('description', 'No description')}'")
                logger.info(f"    - Ingredients: {recipe.get('ingredients', 'No ingredients')}")
                logger.info(f"    - Type: {type(recipe)}")
                # Add specific debugging for the search term
                if query_trimmed:
                    title_lower = str(recipe.get('title', '')).lower()
                    desc_lower = str(recipe.get('description', '')).lower()
                    logger.info(f"    - 🔍 SEARCH DEBUG for '{query_trimmed}':")
                    logger.info(f"      * Title contains '{query_trimmed}': {query_trimmed in title_lower}")
                    logger.info(f"      * Description contains '{query_trimmed}': {query_trimmed in desc_lower}")
                    logger.info(f"      * Title text: '{title_lower}'")
                    logger.info(f"      * Description text: '{desc_lower}'")
                
                # CRITICAL: Check if this recipe contains the search terms in unexpected places
                if query_trimmed:
                    logger.info(f"    - 🔍 SEARCH TERM '{query_trimmed}' ANALYSIS:")
                    title_contains = query_trimmed.lower() in str(recipe.get('title', '')).lower()
                    desc_contains = query_trimmed.lower() in str(recipe.get('description', '')).lower()
                    ingredients_contains = query_trimmed.lower() in str(recipe.get('ingredients', '')).lower()
                    logger.info(f"      * Title contains '{query_trimmed}': {title_contains}")
                    logger.info(f"      * Description contains '{query_trimmed}': {desc_contains}")
                    logger.info(f"      * Ingredients contains '{query_trimmed}': {ingredients_contains}")
                    
                    # If ingredients contain the search term but we're doing name search, this is the problem!
                    if ingredients_contains and is_name_search:
                        logger.warning(f"      🚨 PROBLEM: Recipe has '{query_trimmed}' in ingredients but we're doing NAME search!")
                        logger.warning(f"      This should NOT happen - name search should ignore ingredients!")
                
                if ingredient_trimmed:
                    logger.info(f"    - 🔍 INGREDIENT TERM '{ingredient_trimmed}' ANALYSIS:")
                    title_contains = ingredient_trimmed.lower() in str(recipe.get('title', '')).lower()
                    desc_contains = ingredient_trimmed.lower() in str(recipe.get('description', '')).lower()
                    ingredients_contains = ingredient_trimmed.lower() in str(recipe.get('ingredients', '')).lower()
                    logger.info(f"      * Title contains '{ingredient_trimmed}': {title_contains}")
                    logger.info(f"      * Description contains '{ingredient_trimmed}': {desc_contains}")
                    logger.info(f"      * Ingredients contains '{ingredient_trimmed}': {ingredients_contains}")
                    
                    # If title/description contain the ingredient term but we're doing ingredient search, this is also a problem!
                    if (title_contains or desc_contains) and is_ingredient_search:
                        logger.warning(f"      🚨 PROBLEM: Recipe has '{ingredient_trimmed}' in title/description but we're doing INGREDIENT search!")
                        logger.warning(f"      This should NOT happen - ingredient search should ignore title/description!")
            
            # CRITICAL: Verify search isolation
            logger.info(f"🔍 SEARCH ISOLATION VERIFICATION:")
            if is_name_search:
                logger.info(f"  - NAME SEARCH: Will ONLY look at title and description fields")
                logger.info(f"  - Will IGNORE: ingredients, summary, instructions, tags, cuisine, etc.")
            elif is_ingredient_search:
                logger.info(f"  - INGREDIENT SEARCH: Will ONLY look at ingredients field")
                logger.info(f"  - Will IGNORE: title, description, summary, instructions, tags, cuisine, etc.")
            elif is_combined_search:
                logger.info(f"  - COMBINED SEARCH: Will look at title/description AND ingredients separately")
                logger.info(f"  - Will IGNORE: summary, instructions, tags, cuisine, etc.")
            
            logger.info(f"🔍 DEBUG: Processing {len(all_recipes)} recipes for search")
            logger.info(f"🔍 DEBUG: Search type: name_search={is_name_search}, ingredient_search={is_ingredient_search}")
            
            for recipe in all_recipes:
                # Calculate relevance score based on search type
                score = 0
                matched_terms = 0
                ingredient_matches = 0
                title_matches = 0
                
                # Debug: Show what recipe we're processing
                if is_name_search:
                    logger.info(f"🔍 Processing recipe: '{recipe.get('title', 'No title')}' for name search '{query_trimmed}'")
                
                # For COMBINED SEARCH: Check both name and ingredient criteria
                if is_combined_search:
                    # ENHANCED: Support substring matching for flexible searches
                    # Instead of splitting into words, use the entire search term as a substring
                    query_lower = query_trimmed.lower()
                    ingredient_lower = ingredient_trimmed.lower()
                    logger.debug(f"🔍 COMBINED SEARCH: Processing recipe '{recipe.get('title', 'No title')}'")
                    logger.debug(f"  - Looking for name substring: '{query_lower}' in title/description")
                    logger.debug(f"  - Looking for ingredient substring: '{ingredient_lower}' in ingredients")
                    
                    # SUBSTRING MATCHING: Check if the search terms appear anywhere in the content
                    # This allows for partial matches like "chi" matching "chicken"
                    
                    # Check title field for name search (substring match)
                    if 'title' in recipe and recipe['title']:
                        title_lower = recipe['title'].lower()
                        
                        # Check if the entire query appears as a substring in the title
                        if query_lower in title_lower:
                            score += 100
                            title_matches = 1
                            logger.debug(f"  - ✅ Name substring '{query_lower}' found in title!")
                    
                    # Check description field for name search (substring match)
                    if 'description' in recipe and recipe['description']:
                        desc_lower = recipe['description'].lower()
                        
                        # Check if the entire query appears as a substring in the description
                        if query_lower in desc_lower:
                            score += 50
                            logger.debug(f"  - ✅ Name substring '{query_lower}' found in description!")
                    
                    # Check ingredients field for ingredient search (substring match)
                    if 'ingredients' in recipe and isinstance(recipe['ingredients'], list):
                        # Track if any ingredient contains the search substring
                        ingredient_found = False
                        
                        for ing in recipe['ingredients']:
                            ing_name = ""
                            if isinstance(ing, dict) and 'name' in ing:
                                ing_name = ing['name'].lower()
                            elif isinstance(ing, str):
                                ing_name = ing.lower()
                            else:
                                continue
                            
                            # Check if the ingredient name contains the search substring
                            if ingredient_lower in ing_name:
                                ingredient_found = True
                                ingredient_matches = 1
                                logger.debug(f"  - ✅ Ingredient substring '{ingredient_lower}' found in ingredient '{ing_name}'!")
                                break
                        
                        # Score based on whether we found the ingredient substring
                        if ingredient_found:
                            score += 100
                            logger.debug(f"  - ✅ Ingredient substring '{ingredient_lower}' found in ingredients!")
                    
                    # Include recipe if it matches EITHER name OR ingredient criteria (substring matches)
                    if title_matches > 0 or ingredient_matches > 0:
                        recipe['search_score'] = score
                        recipe['matched_terms'] = title_matches + ingredient_matches
                        recipe['ingredient_matches'] = ingredient_matches
                        recipe['title_matches'] = title_matches
                        matching_recipes.append(recipe)
                        logger.debug(f"✅ Recipe '{recipe.get('title', 'No title')}' matches combined search criteria")
                    else:
                        logger.debug(f"❌ Recipe '{recipe.get('title', 'No title')}' does NOT match combined search criteria")
                
                # For INGREDIENT SEARCH: ONLY look at ingredients field, ignore everything else
                elif is_ingredient_search:
                    ingredient_lower = ingredient_trimmed.lower()
                    search_context = "CHAINED SEARCH" if base_recipes else "FULL DATABASE"
                    logger.debug(f"🔍 INGREDIENT SEARCH ({search_context}): Processing recipe '{recipe.get('title', 'No title')}'")
                    logger.debug(f"  - Looking for ingredient: '{ingredient_lower}'")
                    logger.debug(f"  - Recipe ingredients field: {recipe.get('ingredients', 'No ingredients')}")
                    
                    # DEBUG: Log the actual recipe data structure to see what we're working with
                    logger.debug(f"  - Recipe keys: {list(recipe.keys())}")
                    logger.debug(f"  - Recipe type: {type(recipe)}")
                    
                    # CRITICAL: Verify we're ONLY looking at ingredients for ingredient search
                    logger.debug(f"  - ⚠️ For ingredient search, we ONLY check the ingredients field")
                    logger.debug(f"  - We IGNORE title, description, and all other fields")
                    
                    # SUBSTRING MATCHING: Check if the ingredient search term appears anywhere in ingredients
                    # This allows for partial matches like "chick" matching "chicken"
                    logger.debug(f"  - Looking for ingredient substring: '{ingredient_lower}'")
                    
                    # ONLY check recipe ingredients field - require SUBSTRING match
                    if 'ingredients' in recipe and isinstance(recipe['ingredients'], list):
                        logger.debug(f"  - Found ingredients list with {len(recipe['ingredients'])} items")
                        
                        # Track if any ingredient contains the search substring
                        ingredient_found = False
                        
                        for ing in recipe['ingredients']:
                            ing_name = ""
                            if isinstance(ing, dict) and 'name' in ing:
                                ing_name = ing['name'].lower()
                                logger.debug(f"  - Checking ingredient dict: '{ing_name}'")
                            elif isinstance(ing, str):
                                ing_name = ing.lower()
                                logger.debug(f"  - Checking ingredient string: '{ing_name}'")
                            else:
                                logger.debug(f"  - Skipping ingredient with unexpected type: {type(ing)}")
                                continue
                            
                            logger.debug(f"  - Checking ingredient: '{ing_name}' for substring '{ingredient_lower}'")
                            
                            # Check if the ingredient name contains the search substring
                            if ingredient_lower in ing_name:
                                ingredient_found = True
                                ingredient_matches = 1
                                logger.debug(f"  - ✅ Ingredient substring '{ingredient_lower}' found in ingredient '{ing_name}'!")
                                break
                        
                        # Score based on whether we found the ingredient substring
                        if ingredient_found:
                            score += 100  # 100 points for ingredient match
                            logger.debug(f"  - ✅ Ingredient substring '{ingredient_lower}' found in ingredients!")
                        else:
                            logger.debug(f"  - ❌ Ingredient substring '{ingredient_lower}' NOT found in any ingredients")
                    else:
                        logger.debug(f"  - No ingredients list found or ingredients is not a list")
                        logger.debug(f"  - Ingredients field type: {type(recipe.get('ingredients'))}")
                    
                    # ONLY include recipes that have ANY ingredient words in the ingredients field
                    if ingredient_matches > 0:
                        recipe['search_score'] = score
                        recipe['matched_terms'] = ingredient_matches
                        recipe['ingredient_matches'] = ingredient_matches
                        recipe['title_matches'] = 0
                        matching_recipes.append(recipe)
                        logger.debug(f"✅ Recipe '{recipe.get('title', 'No title')}' has {ingredient_matches} ingredient words in ingredients field")
                    else:
                        logger.debug(f"❌ Recipe '{recipe.get('title', 'No title')}' does NOT have any ingredient words in ingredients field")
                
                # For NAME SEARCH: ONLY look at title/description fields, ignore ingredients completely
                elif is_name_search:
                    query_lower = query_trimmed.lower()
                    logger.debug(f"🔍 NAME SEARCH: Processing recipe '{recipe.get('title', 'No title')}'")
                    logger.debug(f"  - Looking for query substring: '{query_lower}'")
                    logger.debug(f"  - Recipe title: '{recipe.get('title', 'No title')}'")
                    logger.debug(f"  - Recipe description: '{recipe.get('description', 'No description')}'")
                    logger.debug(f"  - IGNORING ingredients field completely for name search")
                    
                    # DEBUG: Log the actual recipe data structure to see what we're working with
                    logger.debug(f"  - Recipe keys: {list(recipe.keys())}")
                    logger.debug(f"  - Recipe type: {type(recipe)}")
                    
                    # CRITICAL: Double-check that we're NOT looking at ingredients for name search
                    # This is the key fix - ensure name search only looks at title/description
                    title_text = ""
                    description_text = ""
                    
                    # SUBSTRING MATCHING: Check if the search term appears anywhere in title/description
                    # This allows for partial matches like "chi" matching "chicken"
                    
                    # Check title field for substring match
                    if 'title' in recipe and recipe['title']:
                        title_text = str(recipe['title']).lower()
                        logger.debug(f"  - Title to search: '{title_text}'")
                        
                        # Check if the search query appears as a substring in the title
                        if query_lower in title_text:
                            score += 100  # 100 points for title match
                            title_matches = 1
                            logger.info(f"  - ✅ Query substring '{query_lower}' found in title '{title_text}'!")
                        else:
                            logger.info(f"  - ❌ Query substring '{query_lower}' NOT found in title '{title_text}'")
                            logger.info(f"  - DEBUG: '{query_lower}' is NOT a substring of '{title_text}'")
                    
                    # Check description field for substring match (secondary scoring)
                    if 'description' in recipe and recipe['description']:
                        description_text = str(recipe['description']).lower()
                        logger.debug(f"  - Description to search: '{description_text}'")
                        
                        # Check if the search query appears as a substring in the description
                        if query_lower in description_text:
                            score += 50  # 50 points for description match
                            logger.debug(f"  - ✅ Query substring '{query_lower}' found in description!")
                        else:
                            logger.debug(f"  - ❌ Query substring '{query_lower}' NOT found in description")
                    
                    # CRITICAL: Verify we're NOT looking at ingredients for name search
                    if 'ingredients' in recipe:
                        # Double-check that ingredients don't contain the search term
                        ingredients_text = str(recipe.get('ingredients', '')).lower()
                        if query_lower in ingredients_text:
                            logger.debug(f"  - ⚠️ Query '{query_lower}' found in ingredients, but this is name search - ignoring")
                    
                    # CRITICAL: Verify we're NOT looking at any other fields that might contain the search term
                    other_fields_to_check = ['summary', 'instructions', 'tags', 'cuisine', 'cuisines', 'category']
                    for field in other_fields_to_check:
                        if field in recipe:
                            field_text = str(recipe.get(field, '')).lower()
                            if query_lower in field_text:
                                logger.debug(f"  - ⚠️ Query '{query_lower}' found in {field}, but this is name search - ignoring")


                    
                    # Include recipe if it has ANY matching words in title or description
                    if title_matches > 0 or score > 0:
                        recipe['search_score'] = score
                        recipe['matched_terms'] = title_matches
                        recipe['ingredient_matches'] = 0
                        recipe['title_matches'] = title_matches
                        matching_recipes.append(recipe)
                        logger.info(f"✅ Recipe '{recipe.get('title', 'No title')}' MATCHED name search for '{query_trimmed}' (score: {score})")
                    else:
                        logger.info(f"❌ Recipe '{recipe.get('title', 'No title')}' did NOT match name search for '{query_trimmed}' (score: {score}, title_matches: {title_matches})")
                
                # For COMBINED SEARCH: both query and ingredient are provided
                else:
                    # Since we want completely separate searches, treat this as an error case
                    logger.warning(f"Unexpected combined search case: query='{query}', ingredient='{ingredient}'")
                    logger.warning("This should not happen with the current search logic")
                    # Don't add any recipes for unexpected combined searches
                    continue
            
            logger.info(f"🔍 DEBUG: Initial search found {len(matching_recipes)} recipes")
            logger.info(f"🔍 DEBUG: Now applying relevance filtering...")
            
            # STRICT FILTERING: Only return recipes with meaningful matches
            # Filter out recipes with very low relevance scores
            meaningful_recipes = []
            for recipe in matching_recipes:
                score = recipe.get('search_score', 0)
                title_matches = recipe.get('title_matches', 0)
                ingredient_matches = recipe.get('ingredient_matches', 0)
                
                # For ingredient search: require at least 1 ingredient match
                if is_ingredient_search:
                    if ingredient_matches > 0:
                        meaningful_recipes.append(recipe)
                        logger.debug(f"✅ Recipe '{recipe.get('title', 'No title')}' passed ingredient relevance filter")
                    else:
                        logger.debug(f"❌ Recipe '{recipe.get('title', 'No title')}' failed ingredient relevance filter (score: {score})")
                
                # For name search: require at least 1 title match OR high description score
                elif is_name_search:
                    if title_matches > 0 or score >= 50:
                        meaningful_recipes.append(recipe)
                        logger.info(f"✅ Recipe '{recipe.get('title', 'No title')}' passed name relevance filter (score: {score}, title_matches: {title_matches})")
                    else:
                        logger.info(f"❌ Recipe '{recipe.get('title', 'No title')}' failed name relevance filter (score: {score}, title_matches: {title_matches})")
                
                # For combined search: require at least 1 title match OR 1 ingredient match
                elif is_combined_search:
                    if title_matches > 0 or ingredient_matches > 0:
                        meaningful_recipes.append(recipe)
                        logger.debug(f"✅ Recipe '{recipe.get('title', 'No title')}' passed combined relevance filter")
                    else:
                        logger.debug(f"❌ Recipe '{recipe.get('title', 'No title')}' failed combined relevance filter (score: {score}, title_matches: {title_matches}, ingredient_matches: {ingredient_matches})")
                
                # For unexpected cases: don't include
                else:
                    logger.warning(f"⚠️ Recipe '{recipe.get('title', 'No title')}' excluded due to unexpected search type")
            
            # Sort by relevance score (highest first)
            if is_ingredient_search:
                # For ingredient searches, prioritize recipes with more ingredient matches
                meaningful_recipes.sort(key=lambda x: (x.get('search_score', 0), x.get('ingredient_matches', 0), x.get('title_matches', 0)), reverse=True)
            elif is_name_search:
                # For name searches, prioritize recipes with more title matches
                meaningful_recipes.sort(key=lambda x: (x.get('search_score', 0), x.get('title_matches', 0), x.get('ingredient_matches', 0)), reverse=True)
            elif is_combined_search:
                # For combined searches, prioritize recipes with more total matches (title + ingredient)
                meaningful_recipes.sort(key=lambda x: (x.get('search_score', 0), x.get('matched_terms', 0), x.get('title_matches', 0), x.get('ingredient_matches', 0)), reverse=True)
            else:
                # For unexpected cases, sort by overall score
                meaningful_recipes.sort(key=lambda x: (x.get('search_score', 0), x.get('matched_terms', 0)), reverse=True)
            
            logger.info(f"Text search found {len(meaningful_recipes)} recipes with meaningful matches out of {len(matching_recipes)} total matches")
            if is_ingredient_search:
                logger.info(f"🔍 INGREDIENT SEARCH RESULTS: Found {len(meaningful_recipes)} recipes with '{ingredient_trimmed}' in ingredients field")
                logger.info(f"  - ✅ SEARCH WAS COMPLETELY SEPARATE: Only looked at ingredients, ignored title/description")
                if meaningful_recipes:
                    sample_titles = [r.get('title', 'No title')[:50] for r in meaningful_recipes[:3]]
                    logger.info(f"Sample ingredient search results: {sample_titles}")
            elif is_name_search:
                logger.info(f"🔍 NAME SEARCH RESULTS: Found {len(meaningful_recipes)} recipes with '{query_trimmed}' in title/description")
                logger.info(f"  - ✅ SEARCH WAS COMPLETELY SEPARATE: Only looked at title/description, ignored ingredients")
                if meaningful_recipes:
                    sample_titles = [r.get('title', 'No title')[:50] for r in meaningful_recipes[:3]]
                    logger.info(f"Sample name search results: {sample_titles}")
            elif is_combined_search:
                logger.info(f"🔍 COMBINED SEARCH RESULTS: Found {len(meaningful_recipes)} recipes matching combined criteria")
                logger.info(f"  - ✅ COMBINED SEARCH: Returned recipes that match EITHER name OR ingredient criteria")
                logger.info(f"  - Name search: '{query_trimmed}' in title/description")
                logger.info(f"  - Ingredient search: '{ingredient_trimmed}' in ingredients field")
                if meaningful_recipes:
                    sample_titles = [r.get('title', 'No title')[:50] for r in meaningful_recipes[:3]]
                    logger.info(f"Sample combined search results: {sample_titles}")
            
            # Debug: Show what recipes we're returning
            logger.info(f"🔍 SEARCH COMPLETE: Returning {len(meaningful_recipes)} recipes from {len(all_recipes)} total recipes")
            if meaningful_recipes:
                logger.info(f"🔍 DEBUG: Recipes being returned:")
                for i, recipe in enumerate(meaningful_recipes[:5]):  # Show first 5
                    logger.info(f"  {i+1}. '{recipe.get('title', 'No title')}' (score: {recipe.get('search_score', 0)})")
            else:
                logger.warning(f"🔍 DEBUG: No recipes matched search criteria!")
                logger.warning(f"🔍 This explains why you're getting 0 results")
            
            # Apply filters if provided
            if filters:
                logger.info(f"🔍 Applying filters: {filters}")
                filtered_recipes = []
                
                for recipe in meaningful_recipes:
                    should_include = True
                    
                    # Cuisine filter
                    if filters.get("cuisine"):
                        cuisine_filter = filters["cuisine"].lower()
                        recipe_cuisines = []
                        
                        # Check both cuisine and cuisines fields
                        if recipe.get('cuisine'):
                            recipe_cuisines.append(recipe['cuisine'].lower())
                        if recipe.get('cuisines') and isinstance(recipe['cuisines'], list):
                            recipe_cuisines.extend([c.lower() for c in recipe['cuisines'] if c])
                        
                        # Check if any recipe cuisine matches the filter
                        if not any(cuisine_filter in cuisine or cuisine in cuisine_filter for cuisine in recipe_cuisines):
                            should_include = False
                            logger.debug(f"Recipe '{recipe.get('title', 'Unknown')}' excluded by cuisine filter: {cuisine_filter}")
                    
                    # Dietary restrictions filter
                    if should_include and filters.get("dietary_restrictions"):
                        dietary_filter = [d.lower() for d in filters["dietary_restrictions"]]
                        recipe_dietary = []
                        
                        # Check dietaryRestrictions and diets arrays
                        if recipe.get('dietaryRestrictions'):
                            recipe_dietary.extend([d.lower() for d in recipe['dietaryRestrictions'] if d])
                        if recipe.get('diets'):
                            recipe_dietary.extend([d.lower() for d in recipe['diets'] if d])
                        
                        # Check vegetarian and vegan boolean fields
                        if recipe.get('vegetarian') is True:
                            recipe_dietary.append('vegetarian')
                        if recipe.get('vegan') is True:
                            recipe_dietary.append('vegan')
                        
                        # IMPROVED: Check if any recipe dietary info matches the filter
                        # Use more flexible matching to catch variations
                        dietary_matched = False
                        for diet_filter in dietary_filter:
                            for recipe_diet in recipe_dietary:
                                # Check for exact match or partial match
                                if (diet_filter == recipe_diet or 
                                    diet_filter in recipe_diet or 
                                    recipe_diet in diet_filter):
                                    dietary_matched = True
                                    logger.debug(f"✅ Dietary match found: '{diet_filter}' matches '{recipe_diet}'")
                                    break
                            if dietary_matched:
                                break
                        
                        if not dietary_matched:
                            should_include = False
                            logger.debug(f"Recipe '{recipe.get('title', 'Unknown')}' excluded by dietary filter: {dietary_filter}")
                            logger.debug(f"Recipe dietary info: {recipe_dietary}")
                    
                    # Max cooking time filter
                    if should_include and filters.get("max_cooking_time"):
                        try:
                            max_time = int(filters["max_cooking_time"])
                            recipe_time = recipe.get('cooking_time') or recipe.get('readyInMinutes')
                            if recipe_time and int(recipe_time) > max_time:
                                should_include = False
                                logger.debug(f"Recipe '{recipe.get('title', 'Unknown')}' excluded by cooking time filter: {recipe_time} > {max_time}")
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid max_cooking_time value: {filters['max_cooking_time']}")
                    
                    # Max calories filter
                    if should_include and filters.get("max_calories"):
                        try:
                            max_cal = int(filters["max_calories"])
                            recipe_calories = recipe.get('calories') or recipe.get('calorieCount')
                            if recipe_calories and int(recipe_calories) > max_cal:
                                should_include = False
                                logger.debug(f"Recipe '{recipe.get('title', 'Unknown')}' excluded by calories filter: {recipe_calories} > {max_cal}")
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid max_calories value: {filters['max_calories']}")
                    
                    # Min rating filter
                    if should_include and filters.get("min_rating"):
                        try:
                            min_rating = float(filters["min_rating"])
                            recipe_rating = recipe.get('avg_rating') or recipe.get('rating')
                            if recipe_rating and float(recipe_rating) < min_rating:
                                should_include = False
                                logger.debug(f"Recipe '{recipe.get('title', 'Unknown')}' excluded by rating filter: {recipe_rating} < {min_rating}")
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid min_rating value: {filters['min_rating']}")
                    
                    if should_include:
                        filtered_recipes.append(recipe)
                
                logger.info(f"🔍 Filtering results: {len(meaningful_recipes)} -> {len(filtered_recipes)} recipes")
                meaningful_recipes = filtered_recipes
            
            return meaningful_recipes
            
            # Original search logic (commented out since search collection doesn't have full recipes):
            # # Sanitize inputs
            # query = (query or "").strip()
            # ingredient = (ingredient or "").strip()
            # filters = filters or {}
            # 
            # # Build where clause for filtering
            # where = {}
            # if filters:
            #     try:
            #         # Handle cuisine filter
            #         if filters.get("cuisine"):
            #             where["cuisines"] = {"$eq": filters["cuisine"]}
            #         
            #         # Handle other filters...
            #         if filters.get("max_cooking_time"):
            #             try:
            #                 max_time = int(filters["max_cooking_time"])
            #             where["cooking_time"] = {"$lte": max_time}
            #         except (ValueError, TypeError):
            #             logger.warning(f"Invalid max_cooking_time value: {filters['max_cooking_time']}")
            #         
            #         if filters.get("max_calories"):
            #             try:
            #             max_cal = int(filters["max_calories"])
            #             where["calories"] = {"$lte": max_cal}
            #         except (ValueError, TypeError):
            #             logger.warning(f"Invalid max_calories value: {filters['max_calories']}")
            #         
            #         if filters.get("min_rating"):
            #             try:
            #             min_rating = float(filters["min_rating"])
            #             where["avg_rating"] = {"$gte": min_rating}
            #         except (ValueError, TypeError):
            #             logger.warning(f"Invalid max_calories value: {filters['max_calories']}")
            #     except Exception as e:
            #         logger.error(f"Error building where clause: {e}")
            #         # Continue with empty where clause rather than failing
            #         where = {}
            # 
            # # Combine query and ingredient for search
            # search_text = f"{query} {ingredient}".strip()
            # print("search text: ", search_text)
            # # If we have a search query, use semantic search
            # if search_text:
            #     try:
            #         # Search in search collection with error handling - return up to 1000 results
            #         search_results = self.search_collection.query(
            #             query_texts=[search_text],
            #             where=where if where else None,
            #             n_results=1000,  # Increased to return up to 1000 results
            #             include=["metadatas", "distances"]
            #         )
            #     except Exception as e:
            #         logger.error(f"Error during semantic search: {e}")
            #         # Fall back to getting all recipes if search fails
            #         logger.info("Falling back to getting all recipes from cache")
            #         return self._get_all_recipes_from_cache()
            #     
            #     if not search_results.get('metadatas'):
            #         logger.info("No search results found, returning all recipes")
            #         return self._get_all_recipes_from_cache()
            #     
            #     # Get recipe IDs from search results
            #     recipe_ids = []
            #     recipe_scores = {}  # Store scores by recipe ID
            #     
            #     for i, metadata in enumerate(search_results['metadatas']):
            #         try:
            #             recipe_id = metadata.get('id')
            #             if not recipe_id:
            #                 continue
            #             
            #             # TTL is disabled - don't check expiration
            #             # if not self._is_cache_valid(metadata.get('cached_at')):
            #             #     logger.debug(f"Skipping expired recipe: {recipe_id}")
            #             #     continue
            #             
            #             recipe_ids.append(recipe_id)
            #             # Get distance from first query result
            #             distances = search_results.get('distances', [])
            #             if distances and len(distances) > 0 and i < len(distances[0]):
            #                 distance = distances[0][i]
            #                 recipe_scores[recipe_id] = 1 - distance  # Convert distance to similarity
            #             else:
            #                 recipe_scores[recipe_id] = 1.0  # Default score if not found
            #         except Exception as e:
            #             logger.error(f"Error processing search result metadata: {e}")
            #             continue
            #     
            #     if not recipe_ids:
            #         logger.info("No valid recipe IDs found in search results, returning all recipes")
            #         return self._get_all_recipes_from_cache()
            #     
            #     try:
            #         # Get full recipe data
            #         recipe_results = self.recipe_collection.get(
            #             ids=recipe_ids,
            #             include=["documents", "metadatas"]
            #         )
            #     except Exception as e:
            #         logger.error(f"Error fetching recipe details: {e}")
            #         return self._get_all_recipes_from_cache()
            #     
            #     # Process results
            #     all_recipes = []
            #     seen_ids = set()
            #     
            #     if not recipe_results.get('documents'):
            #         return self._get_all_recipes_from_cache()
            #     
            #     for i, doc in enumerate(recipe_results['documents']):
            #         try:
            #             # Skip empty or invalid documents
            #             if not doc or not isinstance(doc, (str, dict)):
            #                 logger.debug(f"Skipping invalid document at index {i}")
            #                 continue
            #             
            #             # Parse JSON if needed
            #             if isinstance(doc, str):
            #                 try:
            #                     doc = doc.strip()
            #                     if not doc:  # Skip empty strings
            #                     continue
            #                     recipe = json.loads(doc)
            #                 except json.JSONDecodeError as e:
            #                     logger.error(f"Error decoding recipe JSON at index {i}: {e}")
            #                     continue
            #             else:
            #                 recipe = doc
            #             
            #             # Validate recipe structure
            #             if not isinstance(recipe, dict) or not recipe.get('id'):
            #                 logger.debug(f"Skipping invalid recipe at index {i}")
            #                 continue
            #             
            #             metadata = recipe_results['metadatas'][i] if i < len(recipe_results['metadatas']) else {}
            #             
            #             recipe_id = recipe.get('id')
            #             if not recipe_id or recipe_id in seen_ids:
            #                 logger.debug(f"Skipping recipe {recipe_id}: already seen")
            #                 continue
            #             # TTL is disabled - don't check expiration
            #             # if not self._is_cache_valid(metadata.get('cached_at')):
            #             #     logger.debug(f"Skipping recipe {recipe_id}: expired")
            #             #     continue
            #             
            #             # Calculate relevance score
            #             try:
            #                 score = recipe_scores.get(recipe_id, 0.5)  # Default score if not found
            #                 # Apply additional scoring logic
            #                 score = self._calculate_relevance_score(score, recipe, query, ingredient)
            #                 recipe['relevance_score'] = score
            #             except Exception as e:
            #                 logger.error(f"Error calculating relevance score for recipe {recipe_id}: {e}")
            #                 score = 1.0
            #             
            #             # Add score to recipe
            #             recipe['relevance_score'] = score
            #             all_recipes.append(recipe)
            #             seen_ids.add(recipe_id)
            #             
            #         except Exception as e:
            #             logger.error(f"Unexpected error processing recipe at index {i}: {e}", exc_info=True)
            #             continue
            #     
            #     # Sort by relevance score
            #     try:
            #         all_recipes.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            #         return all_recipes
            #     except Exception as e:
            #         logger.error(f"Error sorting recipes: {e}")
            #         return all_recipes
            # else:
            #     # No search query, return all recipes
            #     return self._get_all_recipes_from_cache()
            
        except Exception as e:
            logger.error(f"Error in get_cached_recipes: {e}")
            return []

    def _calculate_relevance_score(self, base_score: float, recipe: Dict[str, Any], query: str, ingredient: str) -> float:
        """Calculate recipe relevance score"""
        score = base_score
        
        # Boost exact title matches
        if query and query.lower() in recipe.get('title', '').lower():
            score += 0.3
        
        # Boost ingredient matches
        if ingredient:
            recipe_ingredients = [ing.get('name', '').lower() for ing in recipe.get('ingredients', [])]
            if ingredient.lower() in recipe_ingredients:
                score += 0.2
        
        # Boost by rating
        if recipe.get('avg_rating'):
            score += (float(recipe['avg_rating']) / 5.0) * 0.1
        
        # Normalize score
        return min(max(score, 0.0), 1.0)

    def cache_recipes(self, recipes: List[Dict[Any, Any]], query: str = "", ingredient: str = "", filters: Optional[Dict[str, Any]] = None) -> bool:
        """
        Cache recipes in ChromaDB with TTL support
        
        Args:
            recipes: List of recipe dictionaries to cache
            query: Search query that resulted in these recipes (for search context)
            ingredient: Ingredient filter that was used (for search context)
            filters: Dictionary of filters that were applied
            
        Returns:
            bool: True if caching was successful, False otherwise
        """
        if not self.recipe_collection or not recipes:
            return False
            
        try:
            # Process filters if provided
            where = {}
            if filters:
                try:
                    if "min_rating" in filters and filters["min_rating"] is not None:
                        min_rating = float(filters["min_rating"])
                        where["avg_rating"] = {"$gte": min_rating}
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid min_rating value: {filters.get('min_rating')}")
            
            # Process each recipe
            for recipe in recipes:
                try:
                    recipe_id = str(recipe.get('id'))
                    if not recipe_id:
                        logger.warning("Skipping recipe with missing ID")
                        continue
                        
                    # Extract metadata and search terms
                    metadata = self._extract_recipe_metadata(recipe)
                    search_terms = self._extract_search_terms(recipe)
                    
                    # Store the full recipe
                    self.recipe_collection.upsert(
                        ids=[recipe_id],
                        documents=[json.dumps(recipe)],
                        metadatas=[metadata]
                    )
                    
                    # If we have a search query, index the search terms
                    search_context = f"{query} {ingredient}".strip()
                    if search_context:
                        self.search_collection.upsert(
                            ids=[f"{recipe_id}_{hash(search_context) % 10**8}"],
                            documents=[search_terms],
                            metadatas=[{
                                "recipe_id": recipe_id,
                                "search_context": search_context,
                                "indexed_at": datetime.now().isoformat()
                            }]
                        )
                        
                    logger.debug(f"Cached recipe: {recipe.get('title', 'Untitled')} (ID: {recipe_id})")
                    
                except Exception as recipe_error:
                    logger.error(f"Error caching recipe {recipe.get('id')}: {recipe_error}")
                    continue
            
            logger.info(f"Successfully cached {len(recipes)} recipes")
            return True
            
        except Exception as e:
            logger.error(f"Error in cache_recipes: {e}")
            return False

    def get_recipes_by_ids(self, recipe_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get multiple recipes by their IDs from the cache
        
        Args:
            recipe_ids: List of recipe IDs to retrieve
            
        Returns:
            List of recipe dictionaries (or None for missing/invalid recipes)
        """
        if not self.recipe_collection or not recipe_ids:
            logger.debug("No recipe collection or empty IDs list provided")
            return [None] * len(recipe_ids) if recipe_ids else []
            
        try:
            # Get all requested recipes in one batch
            results = self.recipe_collection.get(
                ids=recipe_ids,
                include=['documents', 'metadatas']
            )
            
            if not results or 'documents' not in results:
                logger.warning(f"No documents found in cache for recipe IDs: {recipe_ids}")
                return [None] * len(recipe_ids)
            
            # Create a mapping of ID to document/metadata for easier lookup
            id_to_recipe = {}
            for i, recipe_id in enumerate(recipe_ids):
                try:
                    # Skip if we've already processed this ID
                    if recipe_id in id_to_recipe:
                        continue
                        
                    # Get the document and metadata (if available)
                    doc = results['documents'][i] if i < len(results['documents']) else None
                    meta = results['metadatas'][i] if (results.get('metadatas') and i < len(results['metadatas'])) else {}
                    
                    # Skip if document is missing or empty
                    if not doc or not isinstance(doc, str):
                        logger.debug(f"Missing or invalid document for recipe ID: {recipe_id}")
                        id_to_recipe[recipe_id] = None
                        continue
                    
                    # Try to parse the document as JSON
                    try:
                        recipe = json.loads(doc)
                        if not isinstance(recipe, dict):
                            raise ValueError("Recipe is not a dictionary")
                            
                        # Check if cache is still valid
                        if not self._is_cache_valid(meta.get('cached_at')):
                            logger.debug(f"Cache entry expired for recipe ID: {recipe_id}")
                            # TTL is disabled - don't clean up expired recipes
                            # asyncio.create_task(self._async_cleanup_recipe(recipe_id))
                            id_to_recipe[recipe_id] = None
                            continue
                            
                        id_to_recipe[recipe_id] = recipe
                        
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"Invalid JSON in cache for recipe {recipe_id}: {str(e)}")
                        # Schedule for cleanup
                        asyncio.create_task(self._async_cleanup_recipe(recipe_id))
                        id_to_recipe[recipe_id] = None
                        
                except Exception as e:
                    logger.error(f"Error processing recipe {recipe_id}: {str(e)}", exc_info=True)
                    id_to_recipe[recipe_id] = None
            
            # Return results in the same order as requested
            return [id_to_recipe.get(rid) for rid in recipe_ids]
            
        except Exception as e:
            logger.error(f"Error getting recipes by IDs: {str(e)}", exc_info=True)
            return [None] * len(recipe_ids) if recipe_ids else []
            
    async def _async_cleanup_recipe(self, recipe_id: str) -> None:
        """Helper method to asynchronously clean up a recipe from the cache"""
        try:
            if self.recipe_collection:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.recipe_collection.delete(ids=[recipe_id])
                )
                logger.debug(f"Cleaned up invalid/expired recipe: {recipe_id}")
        except Exception as e:
            logger.error(f"Error cleaning up recipe {recipe_id}: {str(e)}")
            
    def cache_recipe(self, recipe: Dict[Any, Any]) -> bool:
        """Cache a single recipe in ChromaDB with TTL support"""
        if not self.recipe_collection or not recipe:
            return False
        
        try:
            recipe_id = str(recipe['id'])
            
            # Check if recipe already exists in cache
            existing = self.recipe_collection.get(ids=[recipe_id])
            if existing and existing.get('documents'):
                logger.debug(f"Recipe {recipe_id} already in cache, skipping")
                return True
                
            metadata = self._extract_recipe_metadata(recipe)
            search_terms = self._extract_search_terms(recipe)
            
            self.recipe_collection.upsert(
                ids=[recipe_id],
                documents=[json.dumps(recipe)],
                metadatas=[metadata],
                embeddings=[search_terms]
            )
            
            logger.debug(f"Cached recipe: {recipe.get('title', 'Untitled')} (ID: {recipe_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error caching recipe: {e}")
            return False

    def get_recipe_by_id(self, recipe_id: str) -> Optional[Dict[Any, Any]]:
        """
        Get a recipe by ID from cache with TTL support.
        
        Args:
            recipe_id: The ID of the recipe to retrieve
            
        Returns:
            The recipe dictionary if found and valid, None otherwise
        """
        if not self.recipe_collection:
            logger.warning("Recipe collection not initialized")
            return None
        
        try:
            # Get the document and metadata from the collection
            results = self.recipe_collection.get(
                ids=[recipe_id],
                include=["documents", "metadatas"]
            )
            
            # Check if we got any results
            if not results or 'documents' not in results or not results['documents']:
                logger.debug(f"No cache entry found for recipe ID: {recipe_id}")
                return None
                
            # Get the first document and its metadata
            document = results['documents'][0]
            metadata = results['metadatas'][0] if results.get('metadatas') else {}
            
            # Check if the document is empty or None
            if not document or not isinstance(document, str):
                logger.warning(f"Empty or invalid document for recipe ID: {recipe_id}")
                self.recipe_collection.delete(ids=[recipe_id])
                return None
                
            # Try to parse the document as JSON
            try:
                recipe = json.loads(document)
                if not isinstance(recipe, dict):
                    raise ValueError("Recipe is not a dictionary")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Invalid JSON in cache for recipe {recipe_id}: {str(e)}")
                # Remove the invalid entry
                self.recipe_collection.delete(ids=[recipe_id])
                return None
                
            # Check if cache is still valid
            # TTL is disabled - don't delete expired recipes
            # if not self._is_cache_valid(metadata.get('cached_at')):
            #     logger.info(f"Cache entry expired for recipe ID: {recipe_id}")
            #     self.recipe_collection.delete(ids=[recipe_id])
            #     return None
            
            # Merge metadata into recipe data for frontend compatibility
            # This ensures tags and other metadata are available in the main recipe object
            for key, value in metadata.items():
                if key not in recipe or recipe[key] is None or recipe[key] == '':
                    recipe[key] = value
                    
            logger.debug(f"Successfully retrieved recipe from cache: {recipe.get('title', 'Untitled')} (ID: {recipe_id})")
            return recipe
            
        except Exception as e:
            logger.error(f"Error retrieving recipe {recipe_id} from cache: {str(e)}", exc_info=True)
            try:
                # Attempt to clean up the problematic entry
                self.recipe_collection.delete(ids=[recipe_id])
            except Exception as cleanup_error:
                logger.error(f"Failed to clean up invalid cache entry {recipe_id}: {str(cleanup_error)}")
            return None

    def clear_expired_cache(self) -> int:
        """Clear expired cache entries and return number of entries cleared"""
        # TTL is disabled - no recipes expire, so nothing to clear
        logger.info("TTL is disabled - no recipes will expire from cache")
        return 0
        
        # Original cleanup logic (commented out):
        # cleared_count = 0
        # try:
        #     # Clear expired search results
        #     search_results = self.search_collection.get(
        #         include=["metadatas", "ids"]
        #     )
        #     for i, metadata in enumerate(search_results['metadatas']):
        #         if not self._is_cache_valid(metadata.get('cached_at')):
        #             self.search_collection.delete(ids=[search_results['ids'][i]])
        #             cleared_count += 1
        #     
        #     # Clear expired recipes
        #     recipe_results = self.recipe_collection.get(
        #         include=["metadatas", "ids"]
        #     )
        #     for i, metadata in enumerate(recipe_results['metadatas']):
        #         if not self._is_cache_valid(metadata.get('cached_at')):
        #             self.recipe_collection.delete(ids=[recipe_results['ids'][i]])
        #             cleared_count += 1
        #     
        #     logger.info(f"Cleared {cleared_count} expired cache entries")
        #     return cleared_count
        #     
        # except Exception as e:
        #     logger.error(f"Error clearing expired cache: {e}")
        #     return cleared_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = {
            "total_recipes": 0,
            "valid_recipes": 0,
            "total_searches": 0,
            "valid_searches": 0,
            "cache_size_mb": 0,
            "last_cleanup": None
        }
        
        try:
            if not self.client:
                return stats
                
            # Get recipe collection stats
            try:
                recipe_count = self.recipe_collection.count()
                stats["total_recipes"] = recipe_count
                
                # Count valid recipes (not expired)
                if recipe_count > 0:
                    # TTL is disabled - all recipes are valid
                    stats["valid_recipes"] = recipe_count
                    
                    # Original TTL logic (commented out):
                    # all_recipes = self.recipe_collection.get(include=['metadatas'])
                    # valid_count = sum(
                    #     1 for meta in all_recipes['metadatas']
                    #     if meta and self._is_cache_valid(meta.get('cached_at', ''))
                    # )
                    # stats["valid_recipes"] = valid_count
            except Exception as e:
                logger.warning(f"Could not get recipe collection stats: {e}")
                
            # Get search collection stats
            try:
                search_count = self.search_collection.count()
                stats["total_searches"] = search_count
                
                # Count valid searches (not expired)
                if search_count > 0:
                    # TTL is disabled - all searches are valid
                    stats["valid_searches"] = search_count
                    
                    # Original TTL logic (commented out):
                    # all_searches = self.search_collection.get(include=['metadatas'])
                    # valid_count = sum(
                    #     1 for meta in all_searches['metadatas']
                    #     if meta and self._is_cache_valid(meta.get('cached_at', ''))
                    # )
                    # stats["valid_searches"] = valid_count
            except Exception as e:
                logger.warning(f"Could not get search collection stats: {e}")
                
            # Calculate cache size
            try:
                import os
                cache_path = "./chroma_db"
                if os.path.exists(cache_path):
                    total_size = 0
                    for dirpath, dirnames, filenames in os.walk(cache_path):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            if os.path.exists(filepath):
                                total_size += os.path.getsize(filepath)
                    stats["cache_size_mb"] = round(total_size / (1024 * 1024), 2)
            except Exception as e:
                logger.warning(f"Could not calculate cache size: {e}")
                
            # Calculate total valid entries
            stats["total_valid_entries"] = (
                stats["valid_recipes"] + 
                stats["valid_searches"]
            )
            
            # Calculate total expired entries
            stats["total_expired_entries"] = (
                (stats["total_recipes"] - stats["valid_recipes"]) +
                (stats["total_searches"] - stats["valid_searches"])
            )
            
            # Get last cleanup time if available
            cleanup_meta = self.client.get_collection("recipe_search_cache").get()
            if cleanup_meta and cleanup_meta.get("last_cleanup"):
                stats["last_cleanup"] = cleanup_meta["last_cleanup"]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return stats

    def get_recipe_count(self) -> Dict[str, Any]:
        """Get the count of recipes in the cache"""
        try:
            if not self.client or not self.recipe_collection:
                return {"total": 0, "valid": 0, "expired": 0}
                
            total_count = self.recipe_collection.count()
            
            # Count valid recipes (not expired)
            valid_count = 0
            if total_count > 0:
                all_recipes = self.recipe_collection.get(include=['metadatas'])
                valid_count = sum(
                    1 for meta in all_recipes['metadatas']
                    if meta and self._is_cache_valid(meta.get('cached_at', ''))
                )
            
            expired_count = total_count - valid_count
            
            return {
                "total": total_count,
                "valid": valid_count,
                "expired": expired_count
            }
            
        except Exception as e:
            logger.error(f"Error getting recipe count: {e}")
            return {"total": 0, "valid": 0, "expired": 0}

    def _get_all_recipes_from_cache(self, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all recipes from cache with optional filtering"""
        try:
            if not self.client or not self.recipe_collection:
                logger.warning("ChromaDB collections not initialized")
                return []
            
            # Get all recipes from the recipe collection
            try:
                recipe_results = self.recipe_collection.get(
                    where=where if where else None,
                    include=["documents", "metadatas"]
                )
            except Exception as e:
                logger.error(f"Error fetching all recipes: {e}")
                return []
            
            if not recipe_results.get('documents'):
                return []
            
            # Process results
            all_recipes = []
            seen_ids = set()
            
            for i, doc in enumerate(recipe_results['documents']):
                try:
                    # Skip empty or invalid documents
                    if not doc or not isinstance(doc, (str, dict)):
                        continue
                        
                    # Parse JSON if needed
                    if isinstance(doc, str):
                        try:
                            doc = doc.strip()
                            if not doc:  # Skip empty strings
                                continue
                            recipe = json.loads(doc)
                        except json.JSONDecodeError as e:
                            logger.error(f"Error decoding recipe JSON at index {i}: {e}")
                            continue
                    else:
                        recipe = doc
                        
                    # Validate recipe structure
                    if not isinstance(recipe, dict) or not recipe.get('id'):
                        continue
                        
                    metadata = recipe_results['metadatas'][i] if i < len(recipe_results['metadatas']) else {}
                    
                    recipe_id = recipe.get('id')
                    if not recipe_id or recipe_id in seen_ids:
                        continue
                    # TTL is disabled - don't check expiration
                    # if not self._is_cache_valid(metadata.get('cached_at')):
                    #     logger.debug(f"Skipping recipe {recipe_id}: expired")
                    #     continue
                    
                    all_recipes.append(recipe)
                    seen_ids.add(recipe_id)
                    
                except Exception as e:
                    logger.error(f"Unexpected error processing recipe at index {i}: {e}", exc_info=True)
                    continue
            
            # Only log once per request, not for every recipe
            logger.debug(f"Retrieved {len(all_recipes)} recipes from cache")
            return all_recipes
            
        except Exception as e:
            logger.error(f"Error in _get_all_recipes_from_cache: {e}")
            return [] 

    def _expand_cuisine_filter(self, cuisine_filter):
        """
        FIXED: Return exact cuisine matches only, no auto-expansion.
        This prevents 'Italian' from including 'Southern' recipes.
        """
        if not cuisine_filter:
            return cuisine_filter
        
        # Handle single string - return as-is
        if isinstance(cuisine_filter, str):
            return [cuisine_filter]
        
        # Handle list - return as-is
        elif isinstance(cuisine_filter, list):
            return [c for c in cuisine_filter if c]
        
        # Return as-is for other types
        return cuisine_filter

    def _is_recipe_vegetarian_by_ingredients(self, recipe):
        """
        FIXED: Robust vegetarian detection that properly catches meat in ingredients and names
        """
        # Comprehensive meat indicators that would make a recipe non-vegetarian
        meat_indicators = [
            'chicken', 'beef', 'pork', 'lamb', 'fish', 'salmon', 'tuna', 'shrimp', 'prawn', 
            'meat', 'bacon', 'ham', 'sausage', 'turkey', 'duck', 'goose', 'venison', 
            'rabbit', 'quail', 'pheasant', 'veal', 'mackerel', 'haddock', 'clam', 'oyster',
            'mussel', 'scallop', 'crab', 'lobster', 'anchovy', 'sardine', 'trout', 'cod',
            'halibut', 'sea bass', 'tilapia', 'catfish', 'swordfish', 'mahi mahi',
            'steak', 'burger', 'hot dog', 'hotdog', 'pepperoni', 'salami', 'prosciutto',
            'chorizo', 'pastrami', 'corned beef', 'roast beef', 'ground beef', 'mince',
            'liver', 'kidney', 'heart', 'tongue', 'tripe', 'oxtail', 'short ribs',
            'ribeye', 'sirloin', 'tenderloin', 'brisket', 'flank', 'skirt steak',
            'lamb chops', 'lamb shank', 'pork chops', 'pork belly', 'pork shoulder',
            'chicken breast', 'chicken thigh', 'chicken wing', 'chicken leg', 'chicken drumstick',
            'fish fillet', 'fish steak', 'fish cake', 'fish ball', 'fish sauce',
            'anchovy paste', 'fish stock', 'chicken stock', 'beef stock', 'meat stock',
            'bone broth', 'chicken broth', 'beef broth', 'meat broth'
        ]
        
        # Get recipe name/title for checking
        recipe_name = ''
        if recipe.get('title'):
            recipe_name = str(recipe['title']).lower()
        elif recipe.get('name'):
            recipe_name = str(recipe['name']).lower()
        
        # Get ingredients from various possible fields
        ingredients = []
        
        # Check ingredients array
        if recipe.get('ingredients') and isinstance(recipe['ingredients'], list):
            for ing in recipe['ingredients']:
                if isinstance(ing, dict) and 'name' in ing:
                    ingredients.append(str(ing['name']).lower())
                elif isinstance(ing, str):
                    ingredients.append(ing.lower())
        
        # Check extendedIngredients array (Spoonacular format)
        if recipe.get('extendedIngredients') and isinstance(recipe['extendedIngredients'], list):
            for ing in recipe['extendedIngredients']:
                if isinstance(ing, dict) and 'name' in ing:
                    ingredients.append(str(ing['name']).lower())
        
        # Check instructions for any meat mentions
        instructions = recipe.get('instructions', '')
        if isinstance(instructions, list):
            instructions = ' '.join(str(step) for step in instructions)
        instructions = str(instructions).lower()
        
        # Combine all text for checking - prioritize recipe name and ingredients
        all_text = recipe_name + ' ' + ' '.join(ingredients) + ' ' + instructions
        
        # IMPROVED: Use word boundary checking to avoid false positives
        # This prevents "chicken" from matching "chickpea" or "chickenpox"
        import re
        
        # Check for meat indicators with word boundaries
        for meat in meat_indicators:
            # Use word boundary regex to match whole words only
            pattern = r'\b' + re.escape(meat) + r'\b'
            if re.search(pattern, all_text):
                logger.debug(f"❌ Meat detected in recipe '{recipe_name}': {meat}")
                return False
        
        # ADDITIONAL SAFETY CHECK: Look for common meat-containing recipe patterns
        meat_patterns = [
            r'\bchicken\s+\w+',  # chicken parmesan, chicken marsala, etc.
            r'\bbeef\s+\w+',      # beef stew, beef stroganoff, etc.
            r'\bpork\s+\w+',      # pork chops, pork belly, etc.
            r'\bfish\s+\w+',      # fish tacos, fish curry, etc.
            r'\bsteak\s+\w+',     # steak fajitas, steak salad, etc.
            r'\bmeat\s+\w+',      # meat sauce, meat pie, etc.
        ]
        
        for pattern in meat_patterns:
            if re.search(pattern, all_text):
                logger.debug(f"❌ Meat pattern detected in recipe '{recipe_name}': {pattern}")
                return False
        
        logger.debug(f"✅ Recipe '{recipe_name}' passed vegetarian check")
        return True

    def _is_recipe_vegan_by_ingredients(self, recipe):
        """
        Check if a recipe is vegan by analyzing its ingredients
        """
        # Animal product indicators that would make a recipe non-vegan
        animal_indicators = [
            'milk', 'cheese', 'butter', 'cream', 'egg', 'yogurt', 'honey', 'gelatin', 
            'lard', 'tallow', 'whey', 'casein', 'parmesan', 'pecorino', 'mascarpone', 
            'creme fraiche', 'sour cream', 'condensed milk', 'evaporated milk', 'half and half',
            'heavy cream', 'light cream', 'whipping cream', 'buttermilk', 'kefir', 'cottage cheese',
            'ricotta', 'mozzarella', 'cheddar', 'gouda', 'brie', 'camembert', 'feta', 'blue cheese',
            'goat cheese', 'cream cheese', 'american cheese', 'provolone', 'swiss cheese'
        ]
        
        # First check if it's vegetarian
        if not self._is_recipe_vegetarian_by_ingredients(recipe):
            return False
        
        # Get ingredients from various possible fields
        ingredients = []
        
        # Check ingredients array
        if recipe.get('ingredients') and isinstance(recipe['ingredients'], list):
            for ing in recipe['ingredients']:
                if isinstance(ing, dict) and 'name' in ing:
                    ingredients.append(str(ing['name']).lower())
                elif isinstance(ing, str):
                    ingredients.append(ing.lower())
        
        # Check extendedIngredients array (Spoonacular format)
        if recipe.get('extendedIngredients') and isinstance(recipe['extendedIngredients'], list):
            for ing in recipe['extendedIngredients']:
                if isinstance(ing, dict) and 'name' in ing:
                    ingredients.append(str(ing['name']).lower())
        
        # Check instructions for any animal product mentions
        instructions = recipe.get('instructions', '')
        if isinstance(instructions, list):
            instructions = ' '.join(str(step) for step in instructions)
        instructions = str(instructions).lower()
        
        # Combine all text for checking
        all_text = ' '.join(ingredients) + ' ' + instructions
        
        # Check for animal product indicators
        for animal in animal_indicators:
            if animal in all_text:
                return False
        
        return True