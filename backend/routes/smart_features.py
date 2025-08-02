from flask import Blueprint, request, jsonify
from services.recipe_search_service import RecipeSearchService
from services.meal_history_service import MealHistoryService
from services.smart_shopping_service import SmartShoppingService
from services.user_preferences_service import UserPreferencesService
import logging
from middleware.auth_middleware import get_current_user_id, require_auth

logger = logging.getLogger(__name__)

smart_features_bp = Blueprint('smart_features', __name__)

# Initialize services
recipe_search_service = RecipeSearchService()
meal_history_service = MealHistoryService()
smart_shopping_service = SmartShoppingService()
user_preferences_service = UserPreferencesService()

@smart_features_bp.route('/search/semantic', methods=['POST'])
def semantic_recipe_search():
    """
    Semantic recipe search endpoint
    
    Example queries:
    - "healthy dinner for weight loss"
    - "quick breakfast with eggs"
    - "comfort food for cold weather"
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                "error": "Request must be JSON",
                "success": False
            }), 400
            
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({
                "error": "Invalid request format",
                "success": False
            }), 400
        
        # Get and validate parameters
        query = data.get('query', '').strip()
        if not query:
            return jsonify({
                "error": "Query is required",
                "success": False
            }), 400
            
        # Validate filters
        filters = data.get('filters', {})
        if not isinstance(filters, dict):
            return jsonify({
                "error": "Filters must be an object",
                "success": False
            }), 400
            
        # Validate and bound limit
        try:
            limit = int(data.get('limit', 10))
            limit = max(1, min(limit, 50))  # Bound between 1 and 50
        except (ValueError, TypeError):
            limit = 10
        
        # Perform semantic search with error handling
        try:
            results = recipe_search_service.semantic_search(query, filters, limit)
            
            if not isinstance(results, list):
                return jsonify({
                    "error": "Invalid search results format",
                    "success": False
                }), 500
            
            return jsonify({
                "success": True,
                "query": query,
                "results": results,
                "total": len(results),
                "filters_applied": filters,
                "limit_used": limit
            }), 200
            
        except Exception as search_error:
            logger.error(f"Semantic search error: {search_error}")
            return jsonify({
                "error": "Failed to perform semantic search",
                "details": str(search_error),
                "success": False
            }), 500
            
    except Exception as e:
        logger.error(f"Semantic search endpoint error: {e}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "success": False
        }), 500

@smart_features_bp.route('/search/similar/<recipe_id>', methods=['GET'])
def find_similar_recipes(recipe_id):
    """
    Find recipes similar to a given recipe
    """
    try:
        limit = request.args.get('limit', 5, type=int)
        
        results = recipe_search_service.find_similar_recipes(recipe_id, limit)
        
        return jsonify({
            "success": True,
            "recipe_id": recipe_id,
            "similar_recipes": results,
            "total": len(results)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/recommendations', methods=['GET'])
# @require_auth  # Temporarily disabled for testing
def get_personalized_recommendations():
    """
    Get personalized recipe recommendations based on user preferences
    """
    try:
        # For testing, use a default user ID instead of requiring authentication
        user_id = get_current_user_id() or "test_user_123"
        print(f"🔍 Recommendations endpoint - User ID: {user_id}")
        
        limit = request.args.get('limit', 8, type=int)
        print(f"📊 Requested limit: {limit}")
        
        # For testing, create default preferences with burger as favorite food
        if user_id == "test_user_123":
            preferences = {
                "favoriteFoods": ["burger"],
                "favoriteCuisines": [],
                "foodsToAvoid": [],
                "dietaryRestrictions": []
            }
            print(f"🧪 Using test preferences: {preferences}")
        else:
            # Get user preferences from the database
            preferences = user_preferences_service.get_preferences(user_id)
            print(f"📋 Retrieved preferences: {preferences}")
        
        if not preferences:
            print("⚠️ No preferences found")
            return jsonify({
                "success": True,
                "recommendations": [],
                "message": "No preferences found. Please set your preferences first."
            }), 200
        
        # Log the preferences being used for debugging
        print(f"✅ Using preferences for user {user_id}: {preferences}")
        
        results = recipe_search_service.get_recipe_recommendations(preferences, limit)
        print(f"🎯 Generated {len(results)} recommendations")
        
        return jsonify({
            "success": True,
            "recommendations": results,
            "preferences_used": preferences,
            "total": len(results)
        }), 200
        
    except Exception as e:
        print(f"❌ Error in recommendations endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/meal-history/log', methods=['POST'])
def log_meal_generation():
    """
    Log when a meal plan is generated
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'demo_user')
        meal_plan = data.get('meal_plan', {})
        preferences_used = data.get('preferences_used', {})
        
        meal_history_service.log_meal_generated(user_id, meal_plan, preferences_used)
        
        return jsonify({
            "success": True,
            "message": "Meal generation logged successfully"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/meal-history/feedback', methods=['POST'])
def log_meal_feedback():
    """
    Log user feedback on meals
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'demo_user')
        meal_id = data.get('meal_id', '')
        feedback_type = data.get('feedback_type', '')  # 'liked', 'disliked', 'cooked', 'skipped'
        rating = data.get('rating')
        notes = data.get('notes')
        
        if not meal_id or not feedback_type:
            return jsonify({"error": "meal_id and feedback_type are required"}), 400
        
        meal_history_service.log_meal_feedback(user_id, meal_id, feedback_type, rating, notes)
        
        return jsonify({
            "success": True,
            "message": "Feedback logged successfully"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/meal-history/patterns/<user_id>', methods=['GET'])
def get_meal_patterns(user_id):
    """
    Get user's meal patterns and preferences from history
    """
    try:
        days_back = request.args.get('days_back', 30, type=int)
        
        patterns = meal_history_service.get_user_meal_patterns(user_id, days_back)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "patterns": patterns,
            "days_analyzed": days_back
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/meal-history/suggestions', methods=['GET'])
def get_personalized_meal_suggestions():
    """
    Get personalized meal suggestions based on history
    """
    try:
        user_id = request.args.get('user_id', 'demo_user')
        meal_type = request.args.get('meal_type', 'dinner')
        exclude_recent = request.args.get('exclude_recent', 'true').lower() == 'true'
        
        suggestions = meal_history_service.get_personalized_meal_suggestions(user_id, meal_type, exclude_recent)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "meal_type": meal_type,
            "suggestions": suggestions
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/meal-history/trending', methods=['GET'])
def get_trending_meals():
    """
    Get trending meals based on recent positive feedback
    """
    try:
        days_back = request.args.get('days_back', 7, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        trending = meal_history_service.get_trending_meals(days_back, limit)
        
        return jsonify({
            "success": True,
            "trending_meals": trending,
            "days_analyzed": days_back
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/shopping/smart-list', methods=['POST'])
def create_smart_shopping_list():
    """
    Create an intelligent shopping list from meal plans
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'demo_user')
        meal_plans = data.get('meal_plans', [])
        dietary_restrictions = data.get('dietary_restrictions', [])
        
        if not meal_plans:
            return jsonify({"error": "meal_plans are required"}), 400
        
        shopping_list = smart_shopping_service.create_smart_shopping_list(
            user_id, meal_plans, dietary_restrictions
        )
        
        return jsonify({
            "success": True,
            "shopping_list": shopping_list
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/shopping/substitutions', methods=['GET'])
def get_ingredient_substitutions():
    """
    Get possible substitutions for an ingredient
    """
    try:
        ingredient_name = request.args.get('ingredient', '')
        dietary_restrictions = request.args.getlist('dietary_restrictions')
        
        if not ingredient_name:
            return jsonify({"error": "ingredient parameter is required"}), 400
        
        substitutions = smart_shopping_service.get_ingredient_substitutions(
            ingredient_name, dietary_restrictions
        )
        
        return jsonify({
            "success": True,
            "ingredient": ingredient_name,
            "substitutions": substitutions,
            "dietary_restrictions": dietary_restrictions
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/shopping/missing-ingredients', methods=['POST'])
def find_missing_ingredients():
    """
    Find ingredients that are missing from user's pantry
    """
    try:
        data = request.get_json()
        user_pantry = data.get('user_pantry', [])
        shopping_list = data.get('shopping_list', [])
        
        missing_ingredients = smart_shopping_service.find_missing_ingredients(
            user_pantry, shopping_list
        )
        
        return jsonify({
            "success": True,
            "missing_ingredients": missing_ingredients,
            "pantry_items": len(user_pantry),
            "shopping_list_items": len(shopping_list)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/shopping/history/<user_id>', methods=['GET'])
def get_shopping_history(user_id):
    """
    Get user's shopping list history
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        
        history = smart_shopping_service.get_shopping_list_history(user_id, limit)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "history": history,
            "total": len(history)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/recipes/index', methods=['POST'])
def index_recipe():
    """
    Index a recipe for semantic search
    """
    try:
        data = request.get_json()
        recipe = data.get('recipe', {})
        
        if not recipe:
            return jsonify({"error": "recipe data is required"}), 400
        
        recipe_search_service.index_recipe(recipe)
        
        return jsonify({
            "success": True,
            "message": "Recipe indexed successfully",
            "recipe_id": recipe.get('id')
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/recipes/bulk-index', methods=['POST'])
def bulk_index_recipes():
    """
    Index multiple recipes at once
    """
    try:
        data = request.get_json()
        recipes = data.get('recipes', [])
        
        if not recipes:
            return jsonify({"error": "recipes array is required"}), 400
        
        recipe_search_service.bulk_index_recipes(recipes)
        
        return jsonify({
            "success": True,
            "message": f"Successfully indexed {len(recipes)} recipes",
            "total_indexed": len(recipes)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smart_features_bp.route('/analytics/meal-success-rate', methods=['GET'])
def get_meal_success_rate():
    """
    Get success metrics for a specific meal
    """
    try:
        user_id = request.args.get('user_id', 'demo_user')
        meal_id = request.args.get('meal_id', '')
        
        if not meal_id:
            return jsonify({"error": "meal_id parameter is required"}), 400
        
        success_rate = meal_history_service.get_meal_success_rate(user_id, meal_id)
        
        return jsonify({
            "success": True,
            "meal_id": meal_id,
            "success_metrics": success_rate
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 