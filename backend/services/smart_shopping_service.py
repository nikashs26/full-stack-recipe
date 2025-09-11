import json
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import uuid
import re

# Import ChromaDB - required for the application to work
import chromadb

class SmartShoppingService:
    """
    Intelligent shopping list service using ChromaDB for ingredient relationships and optimization
    """
    
    def __init__(self):
        import os
        chroma_path = os.environ.get('CHROMA_DB_PATH', './chroma_db')
        
        # For Railway/Render deployment, use persistent volume
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            chroma_path = os.environ.get('CHROMA_DB_PATH', '/app/data/chroma_db')
        elif os.environ.get('RENDER_ENVIRONMENT'):
            chroma_path = os.environ.get('CHROMA_DB_PATH', '/opt/render/project/src/chroma_db')
        
        chroma_path = os.path.abspath(chroma_path)
        try:
            os.makedirs(chroma_path, exist_ok=True)
        except PermissionError:
            # Directory might already exist with correct permissions
            if not os.path.exists(chroma_path):
                raise PermissionError(f"Cannot create ChromaDB directory at {chroma_path}. Please ensure the directory exists and has correct permissions.")
        # Import ChromaDB singleton to prevent multiple instances
        from utils.chromadb_singleton import get_chromadb_client
        
        # Use the singleton ChromaDB client
        self.client = get_chromadb_client()
        
        # Collection for ingredient knowledge base
        self.ingredient_collection = self.client.get_or_create_collection(
            name="ingredients",
            metadata={"description": "Ingredient knowledge base with relationships and substitutions"}
        )
        
        # Collection for shopping lists
        self.shopping_list_collection = self.client.get_or_create_collection(
            name="shopping_lists",
            metadata={"description": "User shopping lists with context"}
        )
        
        # Collection for store layouts and optimization
        self.store_layout_collection = self.client.get_or_create_collection(
            name="store_layouts",
            metadata={"description": "Store layouts for shopping optimization"}
        )
        
        # Initialize ingredient knowledge base
        self._initialize_ingredient_knowledge()
    
    def _initialize_ingredient_knowledge(self) -> None:
        """
        Initialize the ingredient knowledge base with common ingredients and their relationships
        """
        # Check if already initialized
        existing = self.ingredient_collection.get(limit=1)
        if existing and existing['documents']:
            return
        
        # Common ingredient categories and relationships
        ingredient_data = [
            {
                "name": "tomatoes",
                "category": "vegetables",
                "season": "summer",
                "substitutes": ["canned tomatoes", "tomato paste", "sun-dried tomatoes"],
                "pairs_with": ["basil", "mozzarella", "olive oil", "garlic"],
                "store_section": "produce",
                "storage_tips": "Keep at room temperature until ripe, then refrigerate"
            },
            {
                "name": "chicken breast",
                "category": "protein",
                "substitutes": ["chicken thighs", "turkey breast", "tofu"],
                "pairs_with": ["herbs", "lemon", "garlic", "vegetables"],
                "store_section": "meat",
                "storage_tips": "Refrigerate and use within 2-3 days"
            },
            {
                "name": "olive oil",
                "category": "oils",
                "substitutes": ["vegetable oil", "canola oil", "avocado oil"],
                "pairs_with": ["garlic", "herbs", "vegetables"],
                "store_section": "condiments",
                "storage_tips": "Store in cool, dark place"
            },
            {
                "name": "onions",
                "category": "vegetables",
                "season": "all",
                "substitutes": ["shallots", "scallions", "leeks"],
                "pairs_with": ["garlic", "herbs", "most proteins"],
                "store_section": "produce",
                "storage_tips": "Store in cool, dry place"
            },
            {
                "name": "garlic",
                "category": "aromatics",
                "season": "all",
                "substitutes": ["garlic powder", "shallots"],
                "pairs_with": ["onions", "herbs", "most dishes"],
                "store_section": "produce",
                "storage_tips": "Store in cool, dry place"
            }
        ]
        
        # Add to ChromaDB
        for ingredient in ingredient_data:
            self._add_ingredient_to_knowledge_base(ingredient)
    
    def _add_ingredient_to_knowledge_base(self, ingredient_data: Dict[str, Any]) -> None:
        """
        Add an ingredient to the knowledge base
        """
        # Create searchable text
        searchable_text = f"""
        Ingredient: {ingredient_data['name']}
        Category: {ingredient_data['category']}
        Season: {ingredient_data.get('season', 'all')}
        Substitutes: {', '.join(ingredient_data.get('substitutes', []))}
        Pairs with: {', '.join(ingredient_data.get('pairs_with', []))}
        Store section: {ingredient_data.get('store_section', 'unknown')}
        Storage: {ingredient_data.get('storage_tips', '')}
        """
        
        metadata = {
            "name": ingredient_data['name'],
            "category": ingredient_data['category'],
            "season": ingredient_data.get('season', 'all'),
            "substitutes": json.dumps(ingredient_data.get('substitutes', [])),
            "pairs_with": json.dumps(ingredient_data.get('pairs_with', [])),
            "store_section": ingredient_data.get('store_section', 'unknown'),
            "storage_tips": ingredient_data.get('storage_tips', ''),
            "is_vegetarian": ingredient_data.get('category') != 'meat',
            "is_vegan": ingredient_data.get('category') not in ['meat', 'dairy']
        }
        
        self.ingredient_collection.upsert(
            documents=[searchable_text],
            metadatas=[metadata],
            ids=[f"ingredient_{ingredient_data['name'].replace(' ', '_')}"]
        )
    
    def create_smart_shopping_list(self, user_id: str, meal_plans: List[Dict[str, Any]], dietary_restrictions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create an intelligent shopping list from meal plans
        """
        # Extract all ingredients from meal plans
        all_ingredients = []
        recipe_context = {}
        
        for meal_plan in meal_plans:
            for day, meals in meal_plan.items():
                for meal_type, meal in meals.items():
                    if meal and meal.get('ingredients'):
                        meal_id = meal.get('id', f"{day}_{meal_type}")
                        recipe_context[meal_id] = {
                            "name": meal.get('name', ''),
                            "cuisine": meal.get('cuisine', ''),
                            "day": day,
                            "meal_type": meal_type
                        }
                        
                        for ingredient in meal['ingredients']:
                            all_ingredients.append({
                                "name": ingredient,
                                "recipe_id": meal_id,
                                "recipe_name": meal.get('name', ''),
                                "meal_type": meal_type,
                                "day": day
                            })
        
        # Process and optimize ingredients
        optimized_list = self._optimize_ingredient_list(all_ingredients, dietary_restrictions)
        
        # Group by store sections for easier shopping
        grouped_list = self._group_by_store_section(optimized_list)
        
        # Add suggestions and tips
        suggestions = self._generate_shopping_suggestions(optimized_list)
        
        # Save shopping list
        shopping_list_id = str(uuid.uuid4())
        self._save_shopping_list(user_id, shopping_list_id, grouped_list, recipe_context)
        
        return {
            "shopping_list_id": shopping_list_id,
            "grouped_ingredients": grouped_list,
            "total_items": len(optimized_list),
            "suggestions": suggestions,
            "recipe_context": recipe_context
        }
    
    def _optimize_ingredient_list(self, ingredients: List[Dict[str, Any]], dietary_restrictions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Optimize ingredient list by consolidating similar items and suggesting substitutions
        """
        # Group similar ingredients
        ingredient_groups = {}
        
        for ingredient in ingredients:
            ingredient_name = ingredient['name'].lower().strip()
            
            # Find similar ingredients in knowledge base
            similar_results = self.ingredient_collection.query(
                query_texts=[ingredient_name],
                n_results=3,
                include=['metadatas', 'distances']
            )
            
            # Use the best match or original name
            best_match = ingredient_name
            metadata = None
            
            if similar_results and similar_results['metadatas']:
                for i, meta in enumerate(similar_results['metadatas'][0]):
                    if similar_results['distances'][0][i] < 0.3:  # Close match
                        best_match = meta['name']
                        metadata = meta
                        break
            
            # Group ingredients
            if best_match not in ingredient_groups:
                ingredient_groups[best_match] = {
                    "name": best_match,
                    "recipes": [],
                    "quantity_needed": 1,
                    "metadata": metadata,
                    "substitutes": [],
                    "store_section": "unknown"
                }
            
            ingredient_groups[best_match]["recipes"].append({
                "recipe_id": ingredient['recipe_id'],
                "recipe_name": ingredient['recipe_name'],
                "meal_type": ingredient['meal_type'],
                "day": ingredient['day']
            })
            ingredient_groups[best_match]["quantity_needed"] += 1
            
            # Add metadata if available
            if metadata:
                ingredient_groups[best_match]["store_section"] = metadata.get('store_section', 'unknown')
                substitutes = json.loads(metadata.get('substitutes', '[]'))
                ingredient_groups[best_match]["substitutes"] = substitutes
        
        # Apply dietary restrictions
        if dietary_restrictions:
            for ingredient_name, ingredient_data in ingredient_groups.items():
                if ingredient_data["metadata"]:
                    # Check if ingredient conflicts with dietary restrictions
                    if "vegetarian" in dietary_restrictions and not ingredient_data["metadata"].get("is_vegetarian"):
                        # Suggest vegetarian substitute
                        substitutes = ingredient_data["substitutes"]
                        vegetarian_subs = [sub for sub in substitutes if "tofu" in sub or "plant" in sub]
                        if vegetarian_subs:
                            ingredient_data["suggested_substitute"] = vegetarian_subs[0]
                    
                    if "vegan" in dietary_restrictions and not ingredient_data["metadata"].get("is_vegan"):
                        # Suggest vegan substitute
                        substitutes = ingredient_data["substitutes"]
                        vegan_subs = [sub for sub in substitutes if "plant" in sub or "coconut" in sub]
                        if vegan_subs:
                            ingredient_data["suggested_substitute"] = vegan_subs[0]
        
        return list(ingredient_groups.values())
    
    def _group_by_store_section(self, ingredients: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group ingredients by store section for optimized shopping
        """
        sections = {
            "produce": [],
            "meat": [],
            "dairy": [],
            "pantry": [],
            "frozen": [],
            "condiments": [],
            "unknown": []
        }
        
        for ingredient in ingredients:
            section = ingredient.get("store_section", "unknown")
            if section not in sections:
                section = "unknown"
            sections[section].append(ingredient)
        
        # Remove empty sections
        return {section: items for section, items in sections.items() if items}
    
    def _generate_shopping_suggestions(self, ingredients: List[Dict[str, Any]]) -> List[str]:
        """
        Generate helpful shopping suggestions
        """
        suggestions = []
        
        # Check for seasonal ingredients
        seasonal_ingredients = [ing for ing in ingredients if ing.get("metadata") and ing["metadata"].get("season") == "summer"]
        if seasonal_ingredients:
            suggestions.append(f"🌞 Great time to buy: {', '.join([ing['name'] for ing in seasonal_ingredients[:3]])}")
        
        # Check for ingredients that pair well together
        paired_ingredients = []
        for ingredient in ingredients:
            if ingredient.get("metadata"):
                pairs_with = json.loads(ingredient["metadata"].get("pairs_with", "[]"))
                for pair in pairs_with:
                    if any(pair.lower() in other['name'].lower() for other in ingredients):
                        paired_ingredients.append(f"{ingredient['name']} + {pair}")
        
        if paired_ingredients:
            suggestions.append(f"🤝 Perfect pairings in your list: {', '.join(paired_ingredients[:2])}")
        
        # Storage tips
        storage_tips = []
        for ingredient in ingredients:
            if ingredient.get("metadata") and ingredient["metadata"].get("storage_tips"):
                storage_tips.append(f"{ingredient['name']}: {ingredient['metadata']['storage_tips']}")
        
        if storage_tips:
            suggestions.append(f"💡 Storage tip: {storage_tips[0]}")
        
        return suggestions
    
    def _save_shopping_list(self, user_id: str, shopping_list_id: str, grouped_list: Dict[str, List[Dict[str, Any]]], recipe_context: Dict[str, Any]) -> None:
        """
        Save shopping list to ChromaDB
        """
        # Create searchable text
        all_ingredients = []
        for section, items in grouped_list.items():
            for item in items:
                all_ingredients.append(item['name'])
        
        searchable_text = f"Shopping list: {', '.join(all_ingredients)}"
        
        metadata = {
            "user_id": user_id,
            "shopping_list_id": shopping_list_id,
            "created_at": datetime.now().isoformat(),
            "total_items": len(all_ingredients),
            "sections": json.dumps(list(grouped_list.keys())),
            "recipe_count": len(recipe_context)
        }
        
        self.shopping_list_collection.add(
            documents=[searchable_text],
            metadatas=[metadata],
            ids=[shopping_list_id]
        )
    
    def get_ingredient_substitutions(self, ingredient_name: str, dietary_restrictions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get possible substitutions for an ingredient
        """
        # Search for the ingredient
        results = self.ingredient_collection.query(
            query_texts=[ingredient_name],
            n_results=1,
            include=['metadatas']
        )
        
        if not results or not results['metadatas']:
            return []
        
        metadata = results['metadatas'][0][0]
        substitutes = json.loads(metadata.get('substitutes', '[]'))
        
        # Filter by dietary restrictions
        if dietary_restrictions:
            filtered_substitutes = []
            for substitute in substitutes:
                # This is a simplified check - in a real system, you'd have more sophisticated logic
                if "vegetarian" in dietary_restrictions and "meat" not in substitute.lower():
                    filtered_substitutes.append(substitute)
                elif "vegan" in dietary_restrictions and not any(word in substitute.lower() for word in ["cheese", "milk", "butter", "egg"]):
                    filtered_substitutes.append(substitute)
                else:
                    filtered_substitutes.append(substitute)
            substitutes = filtered_substitutes
        
        return [{"name": sub, "reason": "Common substitute"} for sub in substitutes]
    
    def find_missing_ingredients(self, user_pantry: List[str], shopping_list: List[str]) -> List[str]:
        """
        Find ingredients that are missing from user's pantry
        """
        pantry_items = set(item.lower() for item in user_pantry)
        needed_items = []
        
        for item in shopping_list:
            # Check if item or similar item is in pantry
            item_lower = item.lower()
            if item_lower not in pantry_items:
                # Check for similar items using semantic search
                similar_results = self.ingredient_collection.query(
                    query_texts=[item],
                    n_results=3,
                    include=['metadatas', 'distances']
                )
                
                found_in_pantry = False
                if similar_results and similar_results['metadatas']:
                    for i, meta in enumerate(similar_results['metadatas'][0]):
                        if similar_results['distances'][0][i] < 0.2:  # Very close match
                            if meta['name'].lower() in pantry_items:
                                found_in_pantry = True
                                break
                
                if not found_in_pantry:
                    needed_items.append(item)
        
        return needed_items
    
    def get_shopping_list_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get user's shopping list history
        """
        results = self.shopping_list_collection.get(
            where={"user_id": user_id},
            include=['metadatas', 'documents'],
            limit=limit
        )
        
        if not results or not results['metadatas']:
            return []
        
        history = []
        for i, metadata in enumerate(results['metadatas']):
            history.append({
                "shopping_list_id": metadata['shopping_list_id'],
                "created_at": metadata['created_at'],
                "total_items": metadata['total_items'],
                "sections": json.loads(metadata['sections']),
                "recipe_count": metadata['recipe_count'],
                "preview": results['documents'][i][:100] + "..." if len(results['documents'][i]) > 100 else results['documents'][i]
            })
        
        return history 