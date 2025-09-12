#!/usr/bin/env python3
"""
User Backup Service for Render Persistence
This service ensures user accounts persist across Render deployments by:
1. Saving user data to external storage (environment variables or external DB)
2. Restoring user data on startup
3. Periodic backup of user accounts
"""

import json
import os
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class UserBackupService:
    """
    Service to backup and restore user accounts for Render deployment persistence
    """
    
    def __init__(self):
        self.backup_env_prefix = "USER_BACKUP_"
        
    def backup_users_to_env(self, users_data: List[Dict[str, Any]]) -> bool:
        """
        Backup users to environment variables (for small datasets)
        This is a temporary solution for Render persistence
        """
        try:
            # Only use env backup for small datasets (< 10 users)
            if len(users_data) > 10:
                logger.warning(f"⚠️ Too many users ({len(users_data)}) for env backup, skipping")
                return False
            
            # Compress and encode user data
            users_json = json.dumps(users_data, separators=(',', ':'))  # Compact JSON
            users_b64 = base64.b64encode(users_json.encode('utf-8')).decode('utf-8')
            
            # For Render, we can output this as an environment variable suggestion
            if os.environ.get('RENDER_ENVIRONMENT'):
                print(f"\n🔧 RENDER PERSISTENCE BACKUP:")
                print(f"Set this environment variable in your Render dashboard:")
                print(f"USER_BACKUP_DATA={users_b64}")
                print(f"📦 Backup data size: {len(users_b64)} chars ({len(users_data)} users)")
                print("ℹ️ Copy the above environment variable to your Render dashboard\n")
            
            logger.info(f"🔄 Generated backup for {len(users_data)} users (size: {len(users_b64)} chars)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to backup users: {e}")
            return False
    
    def restore_users_from_env(self) -> List[Dict[str, Any]]:
        """
        Restore users from environment variables
        This is a temporary solution for Render persistence
        """
        try:
            # Check for backup data in environment variables
            backup_data = os.environ.get('USER_BACKUP_DATA', '').strip()
            
            if not backup_data:
                logger.info("📭 No USER_BACKUP_DATA environment variable found")
                return []
            
            # Decode and parse the backup data
            users_json = base64.b64decode(backup_data.encode('utf-8')).decode('utf-8')
            users_data = json.loads(users_json)
            
            logger.info(f"📥 Restored {len(users_data)} users from environment variables")
            return users_data
            
        except Exception as e:
            logger.error(f"❌ Failed to restore users from environment: {e}")
            return []
    
    def export_users_from_chromadb(self, user_service) -> List[Dict[str, Any]]:
        """
        Export all users from ChromaDB for backup
        """
        try:
            if not user_service.users_collection:
                logger.warning("⚠️ No users collection available for backup")
                return []
            
            # Get all users
            results = user_service.users_collection.get(
                include=['documents', 'metadatas']
            )
            
            users_data = []
            for i, doc in enumerate(results['documents']):
                try:
                    user_data = json.loads(doc)
                    users_data.append(user_data)
                except Exception as e:
                    logger.error(f"❌ Failed to parse user document {i}: {e}")
                    continue
            
            logger.info(f"📤 Exported {len(users_data)} users from ChromaDB")
            return users_data
            
        except Exception as e:
            logger.error(f"❌ Failed to export users from ChromaDB: {e}")
            return []
    
    def import_users_to_chromadb(self, user_service, users_data: List[Dict[str, Any]]) -> bool:
        """
        Import users data back into ChromaDB
        """
        try:
            if not user_service.users_collection:
                logger.warning("⚠️ No users collection available for import")
                return False
            
            if not users_data:
                logger.info("📭 No users data to import")
                return True
            
            imported_count = 0
            for user_data in users_data:
                try:
                    # Check if user already exists
                    existing = user_service.users_collection.get(
                        where={"email": user_data["email"]},
                        include=['metadatas']
                    )
                    
                    if existing['metadatas']:
                        logger.debug(f"⏭️ User {user_data['email']} already exists, skipping")
                        continue
                    
                    # Import user
                    user_metadata = {
                        "user_id": user_data["user_id"],
                        "email": user_data["email"],
                        "is_verified": user_data.get("is_verified", True),
                        "type": "user",
                        "created_at": user_data.get("created_at", datetime.utcnow().isoformat())
                    }
                    
                    user_service.users_collection.upsert(
                        documents=[json.dumps(user_data)],
                        metadatas=[user_metadata],
                        ids=[user_data["user_id"]]
                    )
                    
                    imported_count += 1
                    logger.debug(f"✅ Imported user: {user_data['email']}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to import user {user_data.get('email', 'unknown')}: {e}")
                    continue
            
            logger.info(f"📥 Successfully imported {imported_count} users to ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to import users to ChromaDB: {e}")
            return False
    
    def create_persistent_user_file(self, users_data: List[Dict[str, Any]]) -> bool:
        """
        Create a persistent user backup file that survives deployments
        Save to project root where it might persist in git or be manually managed
        """
        try:
            # Save to project root with timestamp
            backup_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                     f"user_backup_{datetime.now().strftime('%Y%m%d')}.json")
            
            backup_data = {
                "backup_timestamp": datetime.utcnow().isoformat(),
                "user_count": len(users_data),
                "users": users_data
            }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"💾 Created persistent user backup: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create persistent user file: {e}")
            return False
    
    def restore_from_persistent_file(self) -> List[Dict[str, Any]]:
        """
        Restore users from the most recent persistent backup file
        """
        try:
            # Look for backup files in project root
            project_root = os.path.dirname(os.path.dirname(__file__))
            backup_files = []
            
            for file in os.listdir(project_root):
                if file.startswith("user_backup_") and file.endswith(".json"):
                    backup_files.append(os.path.join(project_root, file))
            
            if not backup_files:
                logger.info("📭 No persistent user backup files found")
                return []
            
            # Use the most recent backup
            latest_backup = max(backup_files, key=os.path.getmtime)
            
            with open(latest_backup, 'r') as f:
                backup_data = json.load(f)
            
            users_data = backup_data.get("users", [])
            logger.info(f"📥 Restored {len(users_data)} users from {latest_backup}")
            
            return users_data
            
        except Exception as e:
            logger.error(f"❌ Failed to restore from persistent file: {e}")
            return []
