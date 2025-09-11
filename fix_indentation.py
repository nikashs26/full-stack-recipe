#!/usr/bin/env python3
"""
Script to fix indentation issues in service files
"""

import os
import re

# List of service files to fix
service_files = [
    'backend/services/recipe_cache_service.py',
    'backend/services/user_service.py',
    'backend/services/review_service.py',
    'backend/services/folder_service.py',
    'backend/services/smart_shopping_service.py',
    'backend/services/user_preferences_service.py',
    'backend/services/recipe_search_service.py'
]

# Pattern to find and fix indentation
pattern = r'            from chromadb\.config import Settings\n            settings = Settings\(\n                is_persistent=True,\n                persist_directory=chroma_path\n            \)\n            self\.client = chromadb\.PersistentClient\(settings=settings\)'
replacement = '''        from chromadb.config import Settings
        settings = Settings(
            is_persistent=True,
            persist_directory=chroma_path
        )
        self.client = chromadb.PersistentClient(settings=settings)'''

for service_file in service_files:
    if os.path.exists(service_file):
        print(f"Fixing {service_file}...")
        
        with open(service_file, 'r') as f:
            content = f.read()
        
        # Check if the pattern exists
        if re.search(pattern, content):
            # Replace the pattern
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            
            with open(service_file, 'w') as f:
                f.write(new_content)
            
            print(f"  ✅ Fixed indentation in {service_file}")
        else:
            print(f"  ⚠️ Pattern not found in {service_file}")
    else:
        print(f"  ❌ File not found: {service_file}")

print("\n🎉 Indentation fixes completed!")
