#!/usr/bin/env python3
"""
Script to save vegetarian preferences for all existing users
"""

from services.user_preferences_service import UserPreferencesService

def save_vegetarian_preferences_for_all_users():
    """Save vegetarian preferences for all existing users"""
    ups = UserPreferencesService()
    
    # Get all user IDs
    all_users = ups.collection.get()
    user_ids = all_users.get('ids', [])
    
    print(f"Found {len(user_ids)} users in database:")
    for user_id in user_ids:
        print(f"  - {user_id}")
    
    # Vegetarian preferences template
    vegetarian_prefs = {
        'dietaryRestrictions': ['vegetarian'],
        'favoriteCuisines': ['Italian', 'Mediterranean'],
        'cookingSkillLevel': 'beginner',
        'healthGoals': ['General wellness'],
        'maxCookingTime': '30 minutes',
        'favoriteFoods': ['pasta', 'salad', 'quinoa'],
        'includeBreakfast': True,
        'includeLunch': True,
        'includeDinner': True,
        'includeSnacks': False,
        'targetCalories': 2000,
        'targetProtein': 150,
        'targetCarbs': 200,
        'targetFat': 65
    }
    
    # Save vegetarian preferences for each user
    for user_id in user_ids:
        print(f"\nSaving vegetarian preferences for user: {user_id}")
        ups.save_preferences(user_id, vegetarian_prefs)
        
        # Verify the save worked
        saved_prefs = ups.get_preferences(user_id)
        if saved_prefs and saved_prefs.get('dietaryRestrictions') == ['vegetarian']:
            print(f"  ✅ Successfully saved vegetarian preferences for {user_id}")
        else:
            print(f"  ❌ Failed to save preferences for {user_id}")
    
    print(f"\n✅ Completed saving vegetarian preferences for {len(user_ids)} users")

if __name__ == "__main__":
    save_vegetarian_preferences_for_all_users() 