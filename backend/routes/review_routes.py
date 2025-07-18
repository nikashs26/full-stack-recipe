from flask import Blueprint, request, jsonify
from services.review_service import ReviewService
from middleware.auth_middleware import require_auth, get_current_user_id

review_bp = Blueprint('reviews', __name__)
review_service = ReviewService()

@review_bp.route('/reviews', methods=['POST'])
@require_auth
def add_review():
    """Add a new review (requires authentication)"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['recipe_id', 'recipe_type', 'text', 'rating']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        recipe_id = data['recipe_id']
        recipe_type = data['recipe_type']
        text = data['text'].strip()
        rating = data['rating']
        author = data.get('author', 'Anonymous').strip() or 'Anonymous'
        
        # Validate recipe_type
        if recipe_type not in ['local', 'external', 'manual']:
            return jsonify({"error": "Invalid recipe_type. Must be 'local', 'external', or 'manual'"}), 400
        
        # Validate rating
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({"error": "Rating must be an integer between 1 and 5"}), 400
        
        # Validate text
        if not text:
            return jsonify({"error": "Review text cannot be empty"}), 400
        
        # Add the review
        review = review_service.add_review(
            user_id=user_id,
            recipe_id=recipe_id,
            recipe_type=recipe_type,
            author=author,
            text=text,
            rating=rating
        )
        
        return jsonify({
            "success": True,
            "message": "Review added successfully",
            "review": review
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Failed to add review: {str(e)}"}), 500

@review_bp.route('/reviews/<recipe_type>/<recipe_id>', methods=['GET'])
def get_reviews_by_recipe(recipe_type, recipe_id):
    """Get all reviews for a specific recipe (no authentication required)"""
    try:
        # Validate recipe_type
        if recipe_type not in ['local', 'external', 'manual']:
            return jsonify({"error": "Invalid recipe_type. Must be 'local', 'external', or 'manual'"}), 400
        
        reviews = review_service.get_reviews_by_recipe(recipe_id, recipe_type)
        stats = review_service.get_recipe_stats(recipe_id, recipe_type)
        
        return jsonify({
            "success": True,
            "reviews": reviews,
            "stats": stats
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get reviews: {str(e)}"}), 500

@review_bp.route('/reviews/my-reviews', methods=['GET'])
@require_auth
def get_my_reviews():
    """Get all reviews by the current authenticated user"""
    try:
        user_id = get_current_user_id()
        reviews = review_service.get_reviews_by_user(user_id)
        
        return jsonify({
            "success": True,
            "reviews": reviews,
            "total": len(reviews)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get user reviews: {str(e)}"}), 500

@review_bp.route('/reviews/<review_id>', methods=['DELETE'])
@require_auth
def delete_review(review_id):
    """Delete a review (only by the user who created it)"""
    try:
        user_id = get_current_user_id()
        
        success = review_service.delete_review(review_id, user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Review deleted successfully"
            }), 200
        else:
            return jsonify({
                "error": "Review not found or you don't have permission to delete it"
            }), 404
            
    except Exception as e:
        return jsonify({"error": f"Failed to delete review: {str(e)}"}), 500

@review_bp.route('/reviews/stats/<recipe_type>/<recipe_id>', methods=['GET'])
def get_recipe_review_stats(recipe_type, recipe_id):
    """Get review statistics for a specific recipe (no authentication required)"""
    try:
        # Validate recipe_type
        if recipe_type not in ['local', 'external', 'manual']:
            return jsonify({"error": "Invalid recipe_type. Must be 'local', 'external', or 'manual'"}), 400
        
        stats = review_service.get_recipe_stats(recipe_id, recipe_type)
        
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get review stats: {str(e)}"}), 500 