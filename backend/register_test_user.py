import requests
import json

# Base URL for the API
BASE_URL = 'http://localhost:5003/api'

def verify_test_user():
    """Verify the test user's email using the dev endpoint"""
    print("Attempting to verify test user's email...")
    try:
        response = requests.post(
            f'{BASE_URL}/auth/dev-verify-user',
            json={'email': 'test@example.com'},
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Verification response status: {response.status_code}")
        print(f"Verification response: {response.text}")
        
        if response.status_code == 200:
            print("User verified successfully!")
            return True
        else:
            print("Failed to verify user")
            return False
            
    except Exception as e:
        print(f"Error verifying user: {e}")
        return False

def register_test_user():
    """Register a test user or log in if already exists"""
    user_data = {
        'email': 'test@example.com',
        'password': 'Test123!',
        'full_name': 'Test User'
    }
    
    # First try to verify the user
    if verify_test_user():
        print("Test user verified, attempting to log in...")
        token = login_test_user()
        if token:
            return token
    
    print("Login failed, attempting to register...")
    
    try:
        # Try to register the user
        response = requests.post(
            f'{BASE_URL}/auth/register',
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # If user already exists, try to log in again
        if response.status_code == 400 and 'already exists' in response.text:
            print("User already exists but login failed. Please check the password or verify the email.")
            return None
            
        response.raise_for_status()
        print("User registered successfully!")
        
        # Try to verify the email using dev endpoint
        print("Attempting to verify email...")
        dev_verify_response = requests.post(
            f'{BASE_URL}/auth/dev-verify-user',
            json={'email': user_data['email']},
            headers={'Content-Type': 'application/json'}
        )
        
        if dev_verify_response.status_code == 200:
            print("User verified successfully!")
            # Now try to log in
            return login_test_user()
        else:
            print(f"Failed to verify user: {dev_verify_response.text}")
            return None
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        if e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error registering user: {e}")
        return None

def login_test_user():
    """Log in as test user"""
    login_data = {
        'email': 'test@example.com',
        'password': 'Test123!'
    }
    
    try:
        print(f"Attempting to log in with email: {login_data['email']}")
        response = requests.post(
            f'{BASE_URL}/auth/login',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Print the full response for debugging
        print(f"Login response status: {response.status_code}")
        print(f"Login response body: {response.text}")
        
        response.raise_for_status()
        
        token = response.json().get('token')
        if token:
            print("Logged in successfully!")
            return token
        else:
            print("No token received in login response")
            return None
            
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error during login: {e}")
        if e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error logging in: {e}")
        return None

def setup_test_preferences(token):
    """Set up test preferences for the user"""
    print("\nSetting up test preferences...")
    
    preferences = {
        "dietaryRestrictions": ["vegetarian"],
        "favoriteCuisines": ["italian", "indian", "mediterranean"],
        "allergens": ["peanuts"],
        "cookingSkillLevel": "intermediate",
        "favoriteFoods": ["pasta", "curry", "salad"],
        "healthGoals": ["weight loss", "high protein"],
        "maxCookingTime": 60,
        "dislikedIngredients": ["cilantro", "olives"],
        "preferredProteinSources": ["chicken", "tofu", "lentils"],
        "preferredCarbSources": ["brown rice", "quinoa", "sweet potatoes"],
        "preferredMealTypes": ["breakfast", "lunch", "dinner", "snack"],
        "cookingEquipment": ["oven", "stove", "blender", "food processor"],
        "mealPrepDay": "sunday",
        "mealsPerDay": 3,
        "snacksPerDay": 2,
        "preferredCookingMethods": ["baking", "grilling", "stir-frying"],
        "spiceLevel": "medium"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/preferences',
            json=preferences,
            headers=headers
        )
        
        print(f"Preferences response status: {response.status_code}")
        print(f"Preferences response: {response.text}")
        
        if response.status_code == 200:
            print("Successfully set up test preferences!")
            return True
        else:
            print("Failed to set up preferences")
            return False
            
    except Exception as e:
        print(f"Error setting up preferences: {e}")
        return False

def test_ai_meal_plan(token):
    """Test the AI meal plan endpoint with auth token"""
    # First, ensure we have preferences set up
    if not setup_test_preferences(token):
        print("Failed to set up preferences, cannot test meal plan")
        return
        
    # Test data for the request
    test_data = {
        "budget": 100,
        "dietary_goals": ["weight loss", "high protein"],
        "currency": "$"
    }
    
    # Make the request to our endpoint with auth token
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    try:
        print("\nSending request to AI meal plan endpoint...")
        response = requests.post(
            f'{BASE_URL}/ai/meal_plan',
            json=test_data,
            headers=headers
        )
        
        # Print the response
        print(f"Status Code: {response.status_code}")
        if response.text:
            try:
                print("Response:")
                print(json.dumps(response.json(), indent=2))
            except json.JSONDecodeError:
                print("Response (raw):")
                print(response.text)
        else:
            print("No response body")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # First register or log in the test user
    token = register_test_user()
    
    if token:
        # Then test the AI meal plan endpoint
        test_ai_meal_plan(token)
    else:
        print("Failed to authenticate test user")
