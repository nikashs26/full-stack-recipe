#!/usr/bin/env python3
"""
Manual User Backup Script for Render Persistence
Run this script to manually backup all user accounts to a persistent file
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def backup_users():
    """Backup all user accounts to persistent storage"""
    try:
        from backend.services.user_service import UserService
        
        print("🔄 Starting user backup...")
        user_service = UserService()
        
        # Perform backup
        success = user_service.backup_users_for_persistence()
        
        if success:
            print("✅ User backup completed successfully!")
            return True
        else:
            print("❌ User backup failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during backup: {e}")
        return False

if __name__ == "__main__":
    success = backup_users()
    sys.exit(0 if success else 1)
