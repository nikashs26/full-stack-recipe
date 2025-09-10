
from flask import request, jsonify
from datetime import datetime
from bson import ObjectId
import json

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

def register_folder_routes(app, folders_collection, recipes_collection, mongo_available):
    @app.route("/folders", methods=["GET"])
    def get_folders():
        if not mongo_available:
            return jsonify({"error": "MongoDB not available"}), 503
        
        try:
            folders = list(folders_collection.find({}, {'_id': 0}))
            return jsonify({"folders": folders})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/folders", methods=["POST"])
    def create_folder():
        if not mongo_available:
            return jsonify({"error": "MongoDB not available"}), 503
        
        try:
            folder_data = request.json
            if not folder_data or "name" not in folder_data:
                return jsonify({"error": "Folder name is required"}), 400
            
            folder = {
                "id": str(ObjectId()),
                "name": folder_data["name"],
                "description": folder_data.get("description", ""),
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat()
            }
            
            folders_collection.insert_one(folder)
            return jsonify({"message": "Folder created", "folder": folder})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/folders/<folder_id>", methods=["PUT"])
    def update_folder(folder_id):
        if not mongo_available:
            return jsonify({"error": "MongoDB not available"}), 503
        
        try:
            folder_data = request.json
            if not folder_data:
                return jsonify({"error": "Folder data is required"}), 400
            
            folder_data["updatedAt"] = datetime.utcnow().isoformat()
            
            result = folders_collection.update_one(
                {"id": folder_id},
                {"$set": folder_data}
            )
            
            if result.matched_count == 0:
                return jsonify({"error": "Folder not found"}), 404
            
            return jsonify({"message": "Folder updated"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/folders/<folder_id>", methods=["DELETE"])
    def delete_folder(folder_id):
        if not mongo_available:
            return jsonify({"error": "MongoDB not available"}), 503
        
        try:
            # First, remove folder reference from all recipes
            recipes_collection.update_many(
                {"folderId": folder_id},
                {"$unset": {"folderId": ""}}
            )
            
            # Then delete the folder
            result = folders_collection.delete_one({"id": folder_id})
            
            if result.deleted_count == 0:
                return jsonify({"error": "Folder not found"}), 404
            
            return jsonify({"message": "Folder deleted"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/folders/<folder_id>/recipes", methods=["GET"])
    def get_folder_recipes(folder_id):
        if not mongo_available:
            return jsonify({"error": "MongoDB not available"}), 503
        
        try:
            recipes = list(recipes_collection.find({"folderId": folder_id}, {'_id': 0}))
            return jsonify({"recipes": recipes})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
