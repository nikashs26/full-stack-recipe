#!/usr/bin/env python3
"""
Test script to verify user persistence functionality
"""

import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_user_backup_restore():
    """Test the user backup and restore functionality"""
    print("🧪 Testing user backup and restore functionality...")
    
    try:
        from backend.services.user_service import UserService
        from backend.services.user_backup_service import UserBackupService
        
        # Initialize services
        user_service = UserService()
        backup_service = UserBackupService()
        
        print("✅ Services initialized successfully")
        
        # Test 1: Export users (should be empty initially)
        users_data = backup_service.export_users_from_chromadb(user_service)
        print(f"📊 Current users in ChromaDB: {len(users_data)}")
        
        # Test 2: Create test backup data
        test_users = [
            {
                "user_id": "test_user_1",
                "email": "test1@example.com",
                "password_hash": "hashed_password_1",
                "full_name": "Test User 1",
                "is_verified": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            },
            {
                "user_id": "test_user_2", 
                "email": "test2@example.com",
                "password_hash": "hashed_password_2",
                "full_name": "Test User 2",
                "is_verified": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        ]
        
        # Test 3: File backup
        file_success = backup_service.create_persistent_user_file(test_users)
        print(f"📁 File backup test: {'✅ Success' if file_success else '❌ Failed'}")
        
        # Test 4: Environment variable backup
        env_success = backup_service.backup_users_to_env(test_users)
        print(f"🔧 Environment backup test: {'✅ Success' if env_success else '❌ Failed'}")
        
        # Test 5: Restore from file
        restored_users = backup_service.restore_from_persistent_file()
        print(f"📥 File restore test: {'✅ Success' if len(restored_users) == 2 else '❌ Failed'} ({len(restored_users)} users)")
        
        # Test 6: Full backup process
        if users_data:  # Only if there are real users
            backup_success = user_service.backup_users_for_persistence()
            print(f"🔄 Full backup test: {'✅ Success' if backup_success else '❌ Failed'}")
        
        print("\n🎯 Test Summary:")
        print(f"   - File backup: {'✅' if file_success else '❌'}")
        print(f"   - Env backup: {'✅' if env_success else '❌'}")
        print(f"   - File restore: {'✅' if len(restored_users) == 2 else '❌'}")
        print(f"   - Real users: {len(users_data)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_user_backup_restore()
    print(f"\n{'🎉 All tests passed!' if success else '💥 Tests failed!'}")
    sys.exit(0 if success else 1)
