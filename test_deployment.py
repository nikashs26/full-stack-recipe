#!/usr/bin/env python3
"""
Deployment test script to verify all dependencies and imports work correctly
"""

import sys
import os

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")

# Test core dependencies
dependencies = [
    ('flask', 'Flask'),
    ('chromadb', 'ChromaDB'),
    ('numpy', 'NumPy'),
    ('requests', 'Requests'),
    ('bcrypt', 'Bcrypt'),
    ('jwt', 'PyJWT'),
    ('pymongo', 'PyMongo'),
    ('gunicorn', 'Gunicorn'),
    ('dotenv', 'python-dotenv')
]

print("\n=== Testing Core Dependencies ===")
for module, name in dependencies:
    try:
        __import__(module)
        print(f"✓ {name} imported successfully")
    except ImportError as e:
        print(f"✗ {name} import failed: {e}")

# Test application imports
print("\n=== Testing Application Imports ===")
try:
    from backend.config.logging_config import configure_logging
    print("✓ Logging config imported successfully")
except ImportError as e:
    print(f"✗ Logging config import failed: {e}")

try:
    from backend.services.recipe_cache_service import RecipeCacheService
    print("✓ Recipe cache service imported successfully")
except ImportError as e:
    print(f"✗ Recipe cache service import failed: {e}")

try:
    from backend.services.email_service import EmailService
    print("✓ Email service imported successfully")
except ImportError as e:
    print(f"✗ Email service import failed: {e}")

# Test route imports
print("\n=== Testing Route Imports ===")
routes = [
    'backend.routes.recipe_routes',
    'backend.routes.auth_routes',
    'backend.routes.preferences',
    'backend.routes.meal_planner',
    'backend.routes.ai_meal_planner',
    'backend.routes.health',
    'backend.routes.review_routes',
    'backend.routes.folder_routes',
    'backend.routes.smart_features'
]

for route in routes:
    try:
        __import__(route)
        print(f"✓ {route} imported successfully")
    except ImportError as e:
        print(f"✗ {route} import failed: {e}")

print("\n=== Deployment Test Complete ===")
print("If all imports succeeded, the deployment should work correctly.")