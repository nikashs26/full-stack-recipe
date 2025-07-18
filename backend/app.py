from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv
from services.recipe_cache_service import RecipeCacheService
from routes.recipe_routes import register_recipe_routes
from routes.auth_routes import auth_bp
from routes.preferences import preferences_bp
from routes.meal_planner import meal_planner_bp

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure CORS - allow requests from localhost:8081 only
CORS(app, 
    resources={
        r"/*": {
            "origins": ["http://localhost:8081"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 3600
        }
    },
    supports_credentials=True
)

# Initialize services
recipe_cache = RecipeCacheService()

# Register routes
app = register_recipe_routes(app, recipe_cache)
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(preferences_bp, url_prefix='/api')
app.register_blueprint(meal_planner_bp, url_prefix='/api')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5003))
    app.run(host="0.0.0.0", port=port, debug=True)
