#!/usr/bin/env python3
"""
Test script to check recommendation balance and distribution
"""

import requests
import json
from typing import Dict, Any

def test_recommendations_balance(base_url: str = "http://localhost:5000", limit: int = 8):
    """Test the recommendation balance endpoint"""
    
    print(f"🧪 Testing recommendation balance with limit={limit}")
    print(f"📍 Base URL: {base_url}")
    print("=" * 50)
    
    try:
        # Test the balance endpoint
        url = f"{base_url}/api/smart-features/recommendations/test-balance?limit={limit}"
        
        print(f"🔗 Testing endpoint: {url}")
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 'success':
                result_data = data.get('data', {})
                
                print("✅ Recommendations generated successfully!")
                print(f"📊 Total recipes: {result_data.get('total_recipes', 0)}")
                
                # Show cuisine distribution
                cuisine_dist = result_data.get('cuisine_distribution', {})
                if cuisine_dist:
                    print("\n🌍 Cuisine Distribution:")
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
                    
                    # Provide feedback on balance
                    ratio = balance_metrics.get('balance_ratio', 0)
                    if ratio <= 1.5:
                        print("   🎯 Excellent balance!")
                    elif ratio <= 2.0:
                        print("   ✅ Good balance")
                    elif ratio <= 3.0:
                        print("   ⚠️ Moderate imbalance")
                    else:
                        print("   ❌ Significant imbalance")
                
                # Show favorite food matches
                fav_matches = result_data.get('favorite_food_matches', [])
                if fav_matches:
                    print(f"\n🍔 Favorite Food Matches ({len(fav_matches)}):")
                    for match in fav_matches:
                        print(f"   • {match['recipe']} (matches '{match['favorite_food']}' from {match['cuisine']})")
                else:
                    print(f"\n🍔 Favorite Food Matches: None found")
                
                # Show sample recommendations
                recommendations = result_data.get('recommendations', [])
                if recommendations:
                    print(f"\n📝 Sample Recommendations:")
                    for i, recipe in enumerate(recommendations[:3], 1):
                        title = recipe.get('title') or recipe.get('name', 'Unknown')
                        cuisine = recipe.get('cuisine', 'Unknown')
                        print(f"   {i}. {title} ({cuisine})")
                
                # Analyze fair distribution
                if cuisine_dist and len(cuisine_dist) > 1:
                    print(f"\n🎯 Fair Distribution Analysis:")
                    counts = list(cuisine_dist.values())
                    max_count = max(counts)
                    min_count = min(counts)
                    difference = max_count - min_count
                    
                    if difference == 0:
                        print("   ✅ Perfectly fair distribution!")
                    elif difference == 1:
                        print("   ✅ Very fair distribution (max difference: 1)")
                    elif difference == 2:
                        print("   ⚠️ Moderately fair distribution (max difference: 2)")
                    else:
                        print(f"   ❌ Unfair distribution (max difference: {difference})")
                    
                    # Check if we have at least 2 favorite foods
                    if len(fav_matches) >= 2:
                        print("   ✅ Good favorite food inclusion (≥2 matches)")
                    elif len(fav_matches) == 1:
                        print("   ⚠️ Limited favorite food inclusion (1 match)")
                    else:
                        print("   ❌ Poor favorite food inclusion (0 matches)")
                
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
        print(f"❌ Error testing recommendations: {e}")
        return False

def test_fair_distribution(base_url: str = "http://localhost:5000"):
    """Test recommendations with different limits to check fair distribution"""
    
    print("\n" + "=" * 60)
    print("🎯 Testing FAIR cuisine distribution across different limits")
    print("=" * 60)
    
    # Test with limits that should show fair distribution
    limits = [6, 8, 10, 12]
    results = {}
    
    for limit in limits:
        print(f"\n🔍 Testing limit={limit}")
        success = test_recommendations_balance(base_url, limit)
        results[limit] = success
        
        if not success:
            print(f"⚠️ Failed to test limit={limit}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Fair Distribution Test Summary:")
    print("=" * 60)
    
    successful_tests = sum(1 for success in results.values() if success)
    total_tests = len(results)
    
    print(f"✅ Successful tests: {successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("🎉 All tests passed! Fair distribution appears to be working.")
        print("\nExpected Results:")
        print("   • Each cuisine should get roughly equal recipes")
        print("   • At least 2 favorite foods should be included")
        print("   • Max/min cuisine difference should be ≤1 for good balance")
    else:
        print("⚠️ Some tests failed. Check the backend logs for issues.")
    
    return results

def test_specific_scenarios(base_url: str = "http://localhost:5000"):
    """Test specific scenarios to validate the fair distribution logic"""
    
    print("\n" + "=" * 60)
    print("🎭 Testing specific scenarios for fair distribution")
    print("=" * 60)
    
    scenarios = [
        {"limit": 8, "description": "Standard 8-recipe limit"},
        {"limit": 6, "description": "Small limit to test tight distribution"},
        {"limit": 12, "description": "Larger limit to test scaling"}
    ]
    
    for scenario in scenarios:
        print(f"\n🎯 Testing: {scenario['description']}")
        print(f"   Limit: {scenario['limit']}")
        
        try:
            url = f"{base_url}/api/smart-features/recommendations/test-balance?limit={scenario['limit']}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    result_data = data.get('data', {})
                    cuisine_dist = result_data.get('cuisine_distribution', {})
                    fav_matches = result_data.get('favorite_food_matches', [])
                    
                    print(f"   ✅ Generated {len(result_data.get('recommendations', []))} recipes")
                    print(f"   🌍 Cuisines: {len(cuisine_dist)}")
                    print(f"   🍔 Favorite foods: {len(fav_matches)}")
                    
                    # Check distribution fairness
                    if len(cuisine_dist) > 1:
                        counts = list(cuisine_dist.values())
                        max_diff = max(counts) - min(counts)
                        if max_diff <= 1:
                            print(f"   🎯 Fair distribution: ✓ (max diff: {max_diff})")
                        else:
                            print(f"   ⚠️ Unfair distribution: ✗ (max diff: {max_diff})")
                else:
                    print(f"   ❌ API error: {data.get('message', 'Unknown')}")
            else:
                print(f"   ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Recommendation Balance Tests")
    print("Make sure you're logged in and have set user preferences!")
    
    # Test single limit
    test_recommendations_balance()
    
    # Test fair distribution across multiple limits
    test_fair_distribution()
    
    # Test specific scenarios
    test_specific_scenarios()
