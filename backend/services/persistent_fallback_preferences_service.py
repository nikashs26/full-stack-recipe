"""
Persistent fallback user preferences service that uses JSON files when ChromaDB is not available
This ensures user preferences persist across app restarts even without ChromaDB
"""

import json
import os
from typing import Dict, Any, Optional

class PersistentFallbackUserPreferencesService:
    """
    Persistent fallback user preferences service using JSON files
    This is used when ChromaDB is not available but we still want persistence
    """
    
    def __init__(self):
        print("⚠️ Using persistent fallback user preferences service (JSON files)")
        
        # Create data directory
        self.data_dir = os.environ.get('FALLBACK_DATA_DIR', './fallback_data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # File path
        self.preferences_file = os.path.join(self.data_dir, 'user_preferences.json')
        
        # Load existing data
        self.preferences = self._load_json_file(self.preferences_file, {})
        
        print(f"📁 Loaded preferences for {len(self.preferences)} users from {self.preferences_file}")
    
    def _load_json_file(self, filepath: str, default: Any = None) -> Any:
        """Load data from JSON file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading {filepath}: {e}")
        return default if default is not None else {}
    
    def _save_json_file(self, filepath: str, data: Any) -> bool:
        """Save data to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error saving {filepath}: {e}")
            return False
    
    def save_preferences(self, user_id: str, preferences: dict):
        """Save user preferences"""
        self.preferences[user_id] = preferences
        self._save_json_file(self.preferences_file, self.preferences)
        print(f"💾 Saved preferences for user {user_id}")
    
    def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences"""
        return self.preferences.get(user_id)
    
    def delete_preferences(self, user_id: str) -> bool:
        """Delete user preferences"""
        if user_id in self.preferences:
            del self.preferences[user_id]
            self._save_json_file(self.preferences_file, self.preferences)
            return True
        return False
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all user preferences"""
        return self.preferences.copy()
