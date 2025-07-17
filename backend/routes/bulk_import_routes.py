from flask import Blueprint, request, jsonify
import logging
from services.recipe_bulk_loader import RecipeBulkLoader
from services.free_recipe_sources import FreeRecipeSourcesImporter
from middleware.auth_middleware import require_auth, get_current_user_id

logger = logging.getLogger(__name__)

def create_bulk_import_routes(recipes_collection, mongo_available):
    bulk_import_bp = Blueprint('bulk_import', __name__)
    
    @bulk_import_bp.route('/bulk-import/spoonacular', methods=['POST'])
    @require_auth
    def bulk_import_spoonacular():
        """
        Bulk import thousands of recipes from Spoonacular API
        Body: {
            "target_count": 1000,
            "categories": {
                "italian": 100,
                "healthy": 50,
                "vegetarian": 75
            }
        }
        """
        try:
            data = request.get_json() or {}
            target_count = data.get('target_count', 1000)
            categories = data.get('categories', {})
            
            loader = RecipeBulkLoader(recipes_collection if mongo_available else None)
            
            if categories:
                # Load by specific categories
                result = loader.load_recipes_by_categories(categories)
            else:
                # Load popular recipes across all categories
                result = loader.bulk_load_popular_recipes(target_count)
            
            return jsonify({
                "success": result.get("success", False),
                "message": f"Successfully imported {result.get('total_loaded', 0)} recipes",
                "details": result
            }), 200
            
        except Exception as e:
            logger.error(f"Bulk import from Spoonacular failed: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @bulk_import_bp.route('/bulk-import/free-sources', methods=['POST'])
    @require_auth
    def bulk_import_free_sources():
        """
        Import recipes from free datasets and sources
        Body: {
            "sources": ["recipe1m", "curated", "synthetic"],
            "synthetic_count": 500
        }
        """
        try:
            data = request.get_json() or {}
            sources = data.get('sources', ['curated'])
            synthetic_count = data.get('synthetic_count', 500)
            
            importer = FreeRecipeSourcesImporter(recipes_collection if mongo_available else None)
            
            total_imported = 0
            results = []
            
            for source in sources:
                if source == "recipe1m":
                    result = importer.import_from_recipe1m_dataset()
                    results.append({"source": "Recipe1M+ Dataset", "result": result})
                    total_imported += result.get("total_imported", 0)
                
                elif source == "curated":
                    result = importer.import_curated_recipe_collection()
                    results.append({"source": "Curated Collection", "result": result})
                    total_imported += result.get("total_imported", 0)
                
                elif source == "synthetic":
                    result = importer.generate_synthetic_recipes(synthetic_count)
                    results.append({"source": "Synthetic Recipes", "result": result})
                    total_imported += result.get("total_generated", 0)
            
            return jsonify({
                "success": total_imported > 0,
                "message": f"Successfully imported {total_imported} recipes from {len(sources)} sources",
                "total_imported": total_imported,
                "details": results
            }), 200
            
        except Exception as e:
            logger.error(f"Bulk import from free sources failed: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @bulk_import_bp.route('/bulk-import/file', methods=['POST'])
    @require_auth
    def bulk_import_from_file():
        """
        Import recipes from uploaded JSON or CSV file
        """
        try:
            if 'file' not in request.files:
                return jsonify({"error": "No file uploaded"}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            # Save uploaded file temporarily
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
                file.save(temp_file.name)
                temp_file_path = temp_file.name
            
            try:
                importer = FreeRecipeSourcesImporter(recipes_collection if mongo_available else None)
                
                if file.filename.lower().endswith('.json'):
                    result = importer.import_from_json_file(temp_file_path)
                elif file.filename.lower().endswith('.csv'):
                    result = importer.import_from_csv_file(temp_file_path)
                else:
                    return jsonify({"error": "Unsupported file format. Use JSON or CSV."}), 400
                
                return jsonify({
                    "success": result.get("success", False),
                    "message": f"Successfully imported {result.get('total_imported', 0)} recipes from {file.filename}",
                    "details": result
                }), 200
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except Exception as e:
            logger.error(f"File import failed: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @bulk_import_bp.route('/bulk-import/quick-start', methods=['POST'])
    @require_auth
    def quick_start_recipe_collection():
        """
        Quick start: Import a good mix of recipes to get started
        This will import ~2000-3000 diverse, high-quality recipes
        """
        try:
            logger.info("Starting quick-start recipe collection import")
            
            total_imported = 0
            results = []
            
            # Strategy 1: Import curated free sources first (fastest, no API limits)
            importer = FreeRecipeSourcesImporter(recipes_collection if mongo_available else None)
            
            # Import from free curated sources
            curated_result = importer.import_curated_recipe_collection()
            results.append({"source": "Curated Free Sources", "result": curated_result})
            total_imported += curated_result.get("total_imported", 0)
            
            # Generate synthetic recipes for variety
            synthetic_result = importer.generate_synthetic_recipes(1000)
            results.append({"source": "Synthetic Recipes", "result": synthetic_result})
            total_imported += synthetic_result.get("total_generated", 0)
            
            # Strategy 2: Import from Spoonacular for high-quality recipes
            loader = RecipeBulkLoader(recipes_collection if mongo_available else None)
            
            # Import popular recipes by category
            popular_categories = {
                "italian": 150,
                "mexican": 100,
                "indian": 100,
                "asian": 100,
                "american": 100,
                "mediterranean": 100,
                "vegetarian": 150,
                "healthy": 150,
                "dessert": 100,
                "breakfast": 100,
                "dinner": 150,
                "quick": 100
            }
            
            spoonacular_result = loader.load_recipes_by_categories(popular_categories)
            results.append({"source": "Spoonacular Categories", "result": spoonacular_result})
            total_imported += spoonacular_result.get("total_loaded", 0)
            
            return jsonify({
                "success": total_imported > 0,
                "message": f"Quick-start completed! Imported {total_imported} recipes across multiple sources",
                "total_imported": total_imported,
                "summary": {
                    "free_sources": curated_result.get("total_imported", 0),
                    "synthetic": synthetic_result.get("total_generated", 0),
                    "spoonacular": spoonacular_result.get("total_loaded", 0)
                },
                "details": results
            }), 200
            
        except Exception as e:
            logger.error(f"Quick-start import failed: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @bulk_import_bp.route('/bulk-import/status', methods=['GET'])
    def get_import_status():
        """
        Get current status of recipe database
        """
        try:
            if not mongo_available or not recipes_collection:
                return jsonify({
                    "mongo_available": False,
                    "total_recipes": 0,
                    "message": "MongoDB not available"
                }), 200
            
            # Count total recipes
            total_count = recipes_collection.count_documents({})
            
            # Count by source
            sources = {}
            pipeline = [
                {"$group": {"_id": "$source", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            for doc in recipes_collection.aggregate(pipeline):
                source = doc["_id"] or "Unknown"
                sources[source] = doc["count"]
            
            # Count by cuisine
            cuisines = {}
            cuisine_pipeline = [
                {"$unwind": "$cuisines"},
                {"$group": {"_id": "$cuisines", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            
            for doc in recipes_collection.aggregate(cuisine_pipeline):
                cuisine = doc["_id"] or "Unknown"
                cuisines[cuisine] = doc["count"]
            
            return jsonify({
                "mongo_available": True,
                "total_recipes": total_count,
                "sources": sources,
                "top_cuisines": cuisines,
                "recommendations": {
                    "can_start_using": total_count >= 100,
                    "good_diversity": total_count >= 500,
                    "excellent_collection": total_count >= 1000
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Failed to get import status: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    return bulk_import_bp 