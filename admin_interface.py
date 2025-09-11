#!/usr/bin/env python3
"""
Admin Interface for User Management
This script provides a simple command-line interface to manage users on Render
"""

import requests
import json
import os
import sys
from typing import Dict, Any, List

class AdminInterface:
    def __init__(self, base_url: str, admin_token: str):
        self.base_url = base_url.rstrip('/')
        self.admin_token = admin_token
        self.headers = {
            'X-Admin-Token': admin_token,
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make a request to the admin API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=data)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"   Error details: {error_data}")
                except:
                    print(f"   Response text: {e.response.text}")
            return {"error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return self._make_request('GET', '/api/admin/stats')
    
    def get_users(self, page: int = 1, per_page: int = 20, verified_only: bool = False, search: str = "") -> Dict[str, Any]:
        """Get users with pagination and filtering"""
        params = {
            'page': page,
            'per_page': per_page,
            'verified_only': verified_only,
            'search': search
        }
        return self._make_request('GET', '/api/admin/users', params)
    
    def get_user_details(self, user_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific user"""
        return self._make_request('GET', f'/api/admin/users/{user_id}')
    
    def verify_user(self, user_id: str) -> Dict[str, Any]:
        """Manually verify a user"""
        return self._make_request('POST', f'/api/admin/users/{user_id}/verify')
    
    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete a user and their data"""
        return self._make_request('DELETE', f'/api/admin/users/{user_id}')
    
    def seed_recipes(self, path: str = None, limit: int = 5000) -> Dict[str, Any]:
        """Seed recipes from a JSON file"""
        data = {}
        if path:
            data['path'] = path
        if limit:
            data['limit'] = limit
        return self._make_request('POST', '/api/admin/seed', data)

def print_users(users_data: Dict[str, Any]):
    """Print users in a formatted table"""
    if 'error' in users_data:
        print(f"❌ Error: {users_data['error']}")
        return
    
    users = users_data.get('users', [])
    pagination = users_data.get('pagination', {})
    
    if not users:
        print("📭 No users found")
        return
    
    print(f"\n👥 Users (Page {pagination.get('page', 1)} of {pagination.get('total_pages', 1)})")
    print("=" * 80)
    print(f"{'ID':<12} {'Email':<25} {'Name':<20} {'Verified':<8} {'Created':<12}")
    print("-" * 80)
    
    for user in users:
        user_id = user.get('user_id', '')[:12]
        email = user.get('email', '')[:25]
        name = user.get('full_name', '')[:20]
        verified = "✅" if user.get('is_verified', False) else "❌"
        created = user.get('created_at', '')[:10] if user.get('created_at') else 'Unknown'
        
        print(f"{user_id:<12} {email:<25} {name:<20} {verified:<8} {created:<12}")
    
    print(f"\nTotal: {pagination.get('total_count', 0)} users")

def print_stats(stats_data: Dict[str, Any]):
    """Print system statistics"""
    if 'error' in stats_data:
        print(f"❌ Error: {stats_data['error']}")
        return
    
    stats = stats_data.get('stats', {})
    
    print("\n📊 System Statistics")
    print("=" * 40)
    
    users = stats.get('users', {})
    print(f"👥 Users: {users.get('total', 0)} total")
    print(f"   ✅ Verified: {users.get('verified', 0)}")
    print(f"   ❌ Unverified: {users.get('unverified', 0)}")
    
    recipes = stats.get('recipes', {})
    print(f"🍽️  Recipes: {recipes.get('total', 0)}")
    
    preferences = stats.get('preferences', {})
    print(f"⚙️  User Preferences: {preferences.get('total', 0)}")
    
    print(f"🕐 Last Updated: {stats_data.get('timestamp', 'Unknown')}")

def main():
    """Main CLI interface"""
    # Configuration
    base_url = os.getenv('RENDER_URL', 'https://dietary-delight.onrender.com')
    admin_token = os.getenv('ADMIN_TOKEN')
    
    if not admin_token:
        print("❌ Error: ADMIN_TOKEN environment variable not set")
        print("   Set it with: export ADMIN_TOKEN='your-admin-token'")
        print("   Or get it from your Render environment variables")
        sys.exit(1)
    
    admin = AdminInterface(base_url, admin_token)
    
    if len(sys.argv) < 2:
        print("🔧 Admin Interface for User Management")
        print("=" * 50)
        print("Usage:")
        print("  python admin_interface.py stats                    # Show system statistics")
        print("  python admin_interface.py users [page] [per_page]  # List users")
        print("  python admin_interface.py user <user_id>           # Get user details")
        print("  python admin_interface.py verify <user_id>         # Verify a user")
        print("  python admin_interface.py delete <user_id>         # Delete a user")
        print("  python admin_interface.py seed [path] [limit]      # Seed recipes")
        print("\nEnvironment variables:")
        print("  RENDER_URL - Your Render backend URL (default: https://dietary-delight.onrender.com)")
        print("  ADMIN_TOKEN - Your admin token from Render environment")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        if command == 'stats':
            stats_data = admin.get_stats()
            print_stats(stats_data)
        
        elif command == 'users':
            page = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            per_page = int(sys.argv[3]) if len(sys.argv) > 3 else 20
            users_data = admin.get_users(page=page, per_page=per_page)
            print_users(users_data)
        
        elif command == 'user':
            if len(sys.argv) < 3:
                print("❌ Error: User ID required")
                sys.exit(1)
            user_id = sys.argv[2]
            user_data = admin.get_user_details(user_id)
            if 'error' in user_data:
                print(f"❌ Error: {user_data['error']}")
            else:
                user = user_data.get('user', {})
                print(f"\n👤 User Details: {user.get('email', 'Unknown')}")
                print("=" * 50)
                print(f"ID: {user.get('user_id', 'Unknown')}")
                print(f"Email: {user.get('email', 'Unknown')}")
                print(f"Name: {user.get('full_name', 'Unknown')}")
                print(f"Verified: {'✅' if user.get('is_verified', False) else '❌'}")
                print(f"Created: {user.get('created_at', 'Unknown')}")
                print(f"Last Login: {user.get('last_login', 'Unknown')}")
                print(f"Updated: {user.get('updated_at', 'Unknown')}")
                
                preferences = user.get('preferences')
                if preferences:
                    print(f"\n⚙️  Preferences:")
                    for key, value in preferences.items():
                        print(f"   {key}: {value}")
        
        elif command == 'verify':
            if len(sys.argv) < 3:
                print("❌ Error: User ID required")
                sys.exit(1)
            user_id = sys.argv[2]
            result = admin.verify_user(user_id)
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"✅ {result.get('message', 'User verified successfully')}")
        
        elif command == 'delete':
            if len(sys.argv) < 3:
                print("❌ Error: User ID required")
                sys.exit(1)
            user_id = sys.argv[2]
            confirm = input(f"⚠️  Are you sure you want to delete user {user_id}? (yes/no): ")
            if confirm.lower() == 'yes':
                result = admin.delete_user(user_id)
                if 'error' in result:
                    print(f"❌ Error: {result['error']}")
                else:
                    print(f"✅ {result.get('message', 'User deleted successfully')}")
            else:
                print("❌ Deletion cancelled")
        
        elif command == 'seed':
            path = sys.argv[2] if len(sys.argv) > 2 else None
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
            result = admin.seed_recipes(path=path, limit=limit)
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"✅ {result.get('imported', 0)} recipes imported successfully")
        
        else:
            print(f"❌ Unknown command: {command}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
