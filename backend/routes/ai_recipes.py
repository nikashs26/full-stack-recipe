from flask import Blueprint, request, jsonify
import logging
from services.ai_recipe_generator import AIRecipeGenerator
from services.recipe_database_service import RecipeDatabaseService
from services.user_preferences_service import UserPreferencesService
from middleware.auth_middleware import get_current_user_id

logger = logging.getLogger(__name__)

ai_recipes_bp = Blueprint('ai_recipes', __name__)

# Initialize services
ai_generator = AIRecipeGenerator()
recipe_db_service = RecipeDatabaseService()
user_preferences_service = UserPreferencesService()

@ai_recipes_bp.route('/ai-recipes/trending', methods=['GET'])
def get_trending_recipes():
    """
    Get AI-generated trending recipes based on current food trends
    Query params: count (default 20)
    """
    try:
        count = request.args.get('count', 20, type=int)
        count = min(count, 50)  # Limit to prevent abuse
        
        # Get user preferences if authenticated
        user_preferences = None
        try:
            user_id = get_current_user_id()
            if user_id:
                user_preferences = user_preferences_service.get_preferences(user_id)
        except:
            pass  # Not authenticated, use no preferences
        
        # Generate trending recipes
        trending_recipes = ai_generator.generate_trending_recipes(count, user_preferences)
        
        logger.info(f"Generated {len(trending_recipes)} trending recipes")
        
        return jsonify({
            "success": True,
            "recipes": trending_recipes,
            "count": len(trending_recipes),
            "type": "trending",
            "personalized": user_preferences is not None
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating trending recipes: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to generate trending recipes",
            "recipes": []
        }), 500

@ai_recipes_bp.route('/ai-recipes/seasonal', methods=['GET'])
def get_seasonal_recipes():
    """
    Get AI-generated seasonal recipes
    Query params: season (spring/summer/fall/winter), count (default 15)
    """
    try:
        season = request.args.get('season', None)
        count = request.args.get('count', 15, type=int)
        count = min(count, 50)
        
        # Validate season if provided
        valid_seasons = ['spring', 'summer', 'fall', 'winter']
        if season and season.lower() not in valid_seasons:
            return jsonify({
                "success": False,
                "error": f"Invalid season. Must be one of: {', '.join(valid_seasons)}"
            }), 400
        
        # Generate seasonal recipes
        seasonal_recipes = ai_generator.generate_seasonal_recipes(season, count)
        
        logger.info(f"Generated {len(seasonal_recipes)} seasonal recipes for {season or 'auto-detected season'}")
        
        return jsonify({
            "success": True,
            "recipes": seasonal_recipes,
            "count": len(seasonal_recipes),
            "type": "seasonal",
            "season": season
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating seasonal recipes: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to generate seasonal recipes",
            "recipes": []
        }), 500

@ai_recipes_bp.route('/ai-recipes/personalized', methods=['GET'])
def get_personalized_recipes():
    """
    Get AI-generated personalized recipes (requires authentication)
    Query params: count (default 10)
    """
    try:
        # Get authenticated user
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Authentication required for personalized recipes"
            }), 401
        
        count = request.args.get('count', 10, type=int)
        count = min(count, 30)
        
        # Get user preferences
        user_preferences = user_preferences_service.get_preferences(user_id)
        if not user_preferences:
            return jsonify({
                "success": False,
                "error": "User preferences required. Please set your preferences first.",
                "redirect_to": "/preferences"
            }), 400
        
        # Generate personalized recipes
        personalized_recipes = ai_generator.generate_personalized_recipes(user_preferences, count)
        
        logger.info(f"Generated {len(personalized_recipes)} personalized recipes for user {user_id}")
        
        return jsonify({
            "success": True,
            "recipes": personalized_recipes,
            "count": len(personalized_recipes),
            "type": "personalized",
            "user_preferences": user_preferences
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating personalized recipes: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to generate personalized recipes",
            "recipes": []
        }), 500

@ai_recipes_bp.route('/ai-recipes/search', methods=['GET'])
def search_ai_recipes():
    """
    Search for AI-generated recipes based on query
    Query params: q (query), cuisine, diet, count (default 20)
    """
    try:
        query = request.args.get('q', '').strip()
        cuisine = request.args.get('cuisine', '').strip()
        diet = request.args.get('diet', '').strip()
        count = request.args.get('count', 20, type=int)
        count = min(count, 50)
        
        if not query and not cuisine and not diet:
            return jsonify({
                "success": False,
                "error": "At least one search parameter (q, cuisine, or diet) is required"
            }), 400
        
        # Get user preferences if authenticated
        user_preferences = None
        try:
            user_id = get_current_user_id()
            if user_id:
                user_preferences = user_preferences_service.get_preferences(user_id)
        except:
            pass
        
        # Search using the enhanced recipe database service
        search_results = recipe_db_service.search_massive_recipe_database(
            query=query,
            cuisine=cuisine,
            diet=diet,
            limit=count,
            user_preferences=user_preferences
        )
        
        logger.info(f"Found {len(search_results)} recipes for search: query='{query}', cuisine='{cuisine}', diet='{diet}'")
        
        return jsonify({
            "success": True,
            "recipes": search_results,
            "count": len(search_results),
            "type": "search",
            "search_params": {
                "query": query,
                "cuisine": cuisine,
                "diet": diet
            },
            "personalized": user_preferences is not None
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching AI recipes: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to search recipes",
            "recipes": []
        }), 500

@ai_recipes_bp.route('/ai-recipes/generate-custom', methods=['POST'])
def generate_custom_recipe():
    """
    Generate a custom recipe based on specific requirements
    Body: {
        "trend": "air fryer recipes",
        "cuisine": "Italian",
        "dietary_restrictions": ["vegetarian"],
        "cooking_skill": "beginner",
        "max_time": "30 minutes",
        "health_goals": ["heart health"]
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body required"
            }), 400
        
        # Extract parameters
        trend = data.get('trend', '')
        cuisine = data.get('cuisine', '')
        dietary_restrictions = data.get('dietary_restrictions', [])
        cooking_skill = data.get('cooking_skill', 'intermediate')
        max_time = data.get('max_time', '30 minutes')
        health_goals = data.get('health_goals', [])
        
        # Build user preferences from request
        custom_preferences = {
            'dietaryRestrictions': dietary_restrictions,
            'favoriteCuisines': [cuisine] if cuisine else [],
            'cookingSkillLevel': cooking_skill,
            'maxCookingTime': max_time,
            'healthGoals': health_goals
        }
        
        # Generate recipe based on the trend or use personalized generation
        if trend:
            recipe = ai_generator._generate_recipe_for_trend(trend, custom_preferences)
            if recipe:
                recipes = [recipe]
            else:
                recipes = []
        else:
            recipes = ai_generator.generate_personalized_recipes(custom_preferences, 1)
        
        if not recipes:
            return jsonify({
                "success": False,
                "error": "Failed to generate recipe with given parameters"
            }), 500
        
        logger.info(f"Generated custom recipe: {recipes[0].get('title', 'Untitled')}")
        
        return jsonify({
            "success": True,
            "recipe": recipes[0],
            "type": "custom",
            "parameters": custom_preferences
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating custom recipe: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to generate custom recipe"
        }), 500

@ai_recipes_bp.route('/ai-recipes/recommendations', methods=['GET'])
def get_smart_recommendations():
    """
    Get smart recipe recommendations using AI and external APIs
    Query params: count (default 12)
    """
    try:
        count = request.args.get('count', 12, type=int)
        count = min(count, 30)
        
        # Get user preferences if authenticated
        user_preferences = None
        try:
            user_id = get_current_user_id()
            if user_id:
                user_preferences = user_preferences_service.get_preferences(user_id)
        except:
            pass
        
        if user_preferences:
            # Use personalized recommendations
            recommendations = recipe_db_service.get_personalized_recommendations(user_preferences, count)
        else:
            # Use trending recommendations for non-authenticated users
            recommendations = recipe_db_service.get_trending_recipes(count)
        
        logger.info(f"Generated {len(recommendations)} smart recommendations")
        
        return jsonify({
            "success": True,
            "recipes": recommendations,
            "count": len(recommendations),
            "type": "smart_recommendations",
            "personalized": user_preferences is not None
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting smart recommendations: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get recommendations",
            "recipes": []
        }), 500

@ai_recipes_bp.route('/ai-recipes/stats', methods=['GET'])
def get_generation_stats():
    """
    Get statistics about AI recipe generation capabilities
    """
    try:
        stats = recipe_db_service.get_recipe_stats()
        
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting generation stats: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get stats"
        }), 500

@ai_recipes_bp.route('/ai-recipes/trending-topics', methods=['GET'])
def get_trending_topics():
    """
    Get current trending food topics that can be used for recipe generation
    """
    try:
        topics = ai_generator.trending_topics
        cuisines = ai_generator.cuisine_styles
        techniques = ai_generator.cooking_techniques
        
        return jsonify({
            "success": True,
            "trending_topics": topics,
            "cuisine_styles": cuisines,
            "cooking_techniques": techniques
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting trending topics: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get trending topics"
        }), 500 