#!/usr/bin/env python3
"""
Debug script to investigate cuisine distribution issues
"""

import requests
import json
from typing import Dict, Any

def debug_cuisine_distribution(base_url: str = "http://localhost:5000", limit: int = 8):
    """Debug the cuisine distribution issue"""
    
    print(f"🔍 Debugging cuisine distribution with limit={limit}")
    print(f"📍 Base URL: {base_url}")
    print("=" * 60)
    
    try:
        # Test the debug endpoint
        url = f"{base_url}/api/smart-features/recommendations/debug?limit={limit}"
        
        print(f"🔗 Testing debug endpoint: {url}")
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 'success':
                result_data = data.get('data', {})
                
                print("✅ Debug data retrieved successfully!")
                
                # Show user preferences
                user_prefs = result_data.get('user_preferences', {})
                print(f"\n👤 User Preferences:")
                print(f"   • Favorite Cuisines: {user_prefs.get('favoriteCuisines', [])}")
                print(f"   • Favorite Foods: {user_prefs.get('favoriteFoods', [])}")
                print(f"   • Dietary Restrictions: {user_prefs.get('dietaryRestrictions', [])}")
                
                # Show request details
                print(f"\n📊 Request Details:")
                print(f"   • Requested Limit: {result_data.get('requested_limit', 0)}")
                print(f"   • Total Recipes Generated: {result_data.get('total_recipes', 0)}")
                print(f"   • Expected Cuisines: {result_data.get('analysis', {}).get('expected_cuisines', 0)}")
                print(f"   • Expected Per Cuisine: {result_data.get('analysis', {}).get('expected_per_cuisine', 0)}")
                
                # Show cuisine distribution
                cuisine_dist = result_data.get('cuisine_distribution', {})
                if cuisine_dist:
                    print(f"\n🌍 Cuisine Distribution:")
                    for cuisine, count in sorted(cuisine_dist.items()):
                        print(f"   • {cuisine}: {count} recipes")
                
                # Show balance metrics
                balance_metrics = result_data.get('balance_metrics', {})
                if balance_metrics:
                    print(f"\n⚖️ Balance Metrics:")
                    print(f"   • Max cuisine count: {balance_metrics.get('max_cuisine_count', 0)}")
                    print(f"   • Min cuisine count: {balance_metrics.get('min_cuisine_count', 0)}")
                    print(f"   • Balance ratio: {balance_metrics.get('balance_ratio', 0)}")
                    print(f"   • Is balanced: {balance_metrics.get('is_balanced', False)}")
                
                # Show favorite food matches
                fav_matches = result_data.get('favorite_food_matches', [])
                if fav_matches:
                    print(f"\n🍔 Favorite Food Matches ({len(fav_matches)}):")
                    for match in fav_matches:
                        print(f"   • {match['recipe']} (matches '{match['favorite_food']}' from {match['cuisine']})")
                else:
                    print(f"\n🍔 Favorite Food Matches: None found")
                
                # Show detailed cuisine analysis
                cuisine_details = result_data.get('cuisine_details', {})
                if cuisine_details:
                    print(f"\n🔍 Detailed Cuisine Analysis:")
                    for cuisine, recipes in cuisine_details.items():
                        print(f"\n   📍 {cuisine} ({len(recipes)} recipes):")
                        for recipe in recipes:
                            print(f"      • {recipe['title']}")
                            print(f"        - Index: {recipe['index']}")
                            print(f"        - Original Cuisine: {recipe['original_cuisine']}")
                            print(f"        - Detected Cuisine: {recipe['detected_cuisine']}")
                            print(f"        - Normalized Cuisine: {recipe['normalized_cuisine']}")
                
                # Analyze the distribution issue
                print(f"\n🎯 Distribution Analysis:")
                if len(user_prefs.get('favoriteCuisines', [])) == 2:
                    print("   • You have 2 favorite cuisines")
                    expected_per_cuisine = limit // 2
                    print(f"   • Expected: {expected_per_cuisine} recipes per cuisine")
                    
                    if cuisine_dist:
                        counts = list(cuisine_dist.values())
                        if len(counts) >= 2:
                            max_count = max(counts)
                            min_count = min(counts)
                            difference = max_count - min_count
                            
                            print(f"   • Actual: {cuisine_dist}")
                            print(f"   • Max difference: {difference}")
                            
                            if difference > 1:
                                print(f"   ❌ UNFAIR DISTRIBUTION DETECTED!")
                                print(f"   ❌ One cuisine has {max_count} recipes, another has {min_count}")
                                
                                # Try to identify the problem
                                if max_count > expected_per_cuisine + 1:
                                    print(f"   🔍 Problem: One cuisine is getting too many recipes")
                                if min_count < expected_per_cuisine - 1:
                                    print(f"   🔍 Problem: One cuisine is getting too few recipes")
                                
                                print(f"   💡 This suggests the cuisine detection or filtering is not working properly")
                            else:
                                print(f"   ✅ Distribution looks fair!")
                
                return True
                
            else:
                print(f"❌ API returned error status: {data.get('message', 'Unknown error')}")
                return False
                
        elif response.status_code == 401:
            print("❌ Authentication required - please log in first")
            return False
        elif response.status_code == 404:
            print("❌ User preferences not found - please set preferences first")
            return False
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure the backend server is running")
        return False
    except Exception as e:
        print(f"❌ Error debugging recommendations: {e}")
        return False

def test_multiple_limits_debug(base_url: str = "http://localhost:5000"):
    """Test multiple limits to see if the issue persists"""
    
    print("\n" + "=" * 60)
    print("🧪 Testing multiple limits to debug distribution issues")
    print("=" * 60)
    
    limits = [6, 8, 10]
    
    for limit in limits:
        print(f"\n🔍 Testing limit={limit}")
        success = debug_cuisine_distribution(base_url, limit)
        
        if not success:
            print(f"⚠️ Failed to debug limit={limit}")
            break
        
        print(f"✅ Debug completed for limit={limit}")

if __name__ == "__main__":
    print("🚀 Starting Cuisine Distribution Debug")
    print("This will help identify why you're getting 7 of one cuisine and 1 of another")
    print("Make sure you're logged in and have set user preferences!")
    
    # Debug single limit
    debug_cuisine_distribution()
    
    # Test multiple limits
    test_multiple_limits_debug()
