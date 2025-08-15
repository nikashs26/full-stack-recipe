#!/usr/bin/env python3
"""
Test if there are search limits causing the cuisine counting issue
"""
import requests
import json

BASE_URL = "http://localhost:5003"

def test_search_limits():
    """Test if there are search limits causing the issue"""
    
    print("=== Testing Search Limits ===\n")
    
    # Test 1: Check if there's a limit issue
    print("1. Testing different limit values...")
    
    test_limits = [100, 500, 1000, 2000, 5000]
    
    for limit in test_limits:
        response = requests.get(f"{BASE_URL}/get_recipes?cuisine=indian,italian&limit={limit}")
        if response.status_code == 200:
            data = response.json()
            count = data.get('total', 0)
            print(f"   Limit {limit}: {count} recipes")
        else:
            print(f"   Limit {limit}: Error {response.status_code}")
    
    # Test 2: Check if there's an offset issue
    print(f"\n2. Testing different offset values...")
    
    test_offsets = [0, 100, 200, 500]
    
    for offset in test_offsets:
        response = requests.get(f"{BASE_URL}/get_recipes?cuisine=indian,italian&limit=1000&offset={offset}")
        if response.status_code == 200:
            data = response.json()
            count = data.get('total', 0)
            results_count = len(data.get('results', []))
            print(f"   Offset {offset}: Total {count}, Results {results_count}")
        else:
            print(f"   Offset {offset}: Error {response.status_code}")
    
    # Test 3: Check if there's a backend search issue
    print(f"\n3. Testing backend search behavior...")
    
    # Test with no filters
    response = requests.get(f"{BASE_URL}/get_recipes?limit=1000")
    if response.status_code == 200:
        data = response.json()
        total_all = data.get('total', 0)
        print(f"   All recipes (no filters): {total_all}")
        
        # Test individual cuisines
        indian_response = requests.get(f"{BASE_URL}/get_recipes?cuisine=indian&limit=1000")
        italian_response = requests.get(f"{BASE_URL}/get_recipes?cuisine=italian&limit=1000")
        
        if indian_response.status_code == 200 and italian_response.status_code == 200:
            indian_data = indian_response.json()
            italian_data = italian_response.json()
            
            indian_count = indian_data.get('total', 0)
            italian_count = italian_data.get('total', 0)
            
            print(f"   Individual counts: Indian {indian_count}, Italian {italian_count}")
            print(f"   Sum of individual counts: {indian_count + italian_count}")
            print(f"   Combined search count: 116")
            print(f"   Missing in combined search: {indian_count + italian_count - 116}")
            
            # Check if the issue is with the search logic
            if indian_count + italian_count > 116:
                print(f"   ⚠️  The backend is not correctly implementing OR logic!")
                print(f"   Expected: {indian_count + italian_count} recipes")
                print(f"   Actual: 116 recipes")
                print(f"   Missing: {indian_count + italian_count - 116} recipes")

if __name__ == "__main__":
    test_search_limits()
