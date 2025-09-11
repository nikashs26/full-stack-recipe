#!/usr/bin/env python3
"""
Script to update all services to use ChromaDB Settings configuration
"""

import os
import re

# List of service files to update
service_files = [
    'backend/services/recipe_search_service.py',
    'backend/services/user_preferences_service.py',
    'backend/services/smart_shopping_service.py',
    'backend/services/meal_history_service.py',
    'backend/services/folder_service.py',
    'backend/services/review_service.py'
]

# Pattern to find and replace
old_pattern = r'self\.client = chromadb\.PersistentClient\(path=chroma_path\)'
new_code = '''# Use Settings configuration (recommended approach)
            from chromadb.config import Settings
            settings = Settings(
                is_persistent=True,
                persist_directory=chroma_path
            )
            self.client = chromadb.PersistentClient(settings=settings)'''

for service_file in service_files:
    if os.path.exists(service_file):
        print(f"Updating {service_file}...")
        
        with open(service_file, 'r') as f:
            content = f.read()
        
        # Check if the pattern exists
        if re.search(old_pattern, content):
            # Replace the pattern
            new_content = re.sub(old_pattern, new_code, content)
            
            with open(service_file, 'w') as f:
                f.write(new_content)
            
            print(f"  ✅ Updated {service_file}")
        else:
            print(f"  ⚠️ Pattern not found in {service_file}")
    else:
        print(f"  ❌ File not found: {service_file}")

print("\n🎉 All services updated!")
