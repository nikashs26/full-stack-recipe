#!/usr/bin/env python3
"""
Test script to verify Ollama integration with the meal planner
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Add the current directory to the path so we can import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.free_llm_meal_planner import FreeLLMMealPlannerAgent
from services.user_preferences_service import UserPreferencesService

def test_ollama_connection():
    """Test if Ollama is running and accessible"""
    print("🔍 Testing Ollama connection...")
    
    ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    print(f"📍 Ollama URL: {ollama_url}")
    
    try:
        # Test basic connection
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        if response.status_code == 200:
            print("✅ Ollama server is running and accessible")
            
            # Check available models
            models = response.json().get('models', [])
            if models:
                print(f"📚 Available models: {[model['name'] for model in models]}")
            else:
                print("⚠️ No models found. You may need to pull a model first.")
                print("💡 Try: ollama pull llama3.2:latest")
            
            return True
        else:
            print(f"❌ Ollama server returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama server")
        print("💡 Make sure Ollama is running: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error testing Ollama connection: {e}")
        return False

def test_meal_plan_generation():
    """Test meal plan generation with sample preferences"""
    print("\n🍽️ Testing meal plan generation...")
    
    # Sample user preferences
    sample_preferences = {
        "dietaryRestrictions": ["vegetarian"],
        "favoriteCuisines": ["Italian", "Indian", "Mexican"],
        "favoriteFoods": ["pasta", "curry", "tacos"],
        "allergens": ["nuts"],
        "cookingSkillLevel": "intermediate",
        "maxCookingTime": "45 minutes",
        "includeBreakfast": True,
        "includeLunch": True,
        "includeDinner": True,
        "includeSnacks": False
    }
    
    try:
        # Initialize services
        user_preferences_service = UserPreferencesService()
        meal_planner = FreeLLMMealPlannerAgent(user_preferences_service)
        
        # Test the meal plan generation
        print("🚀 Generating meal plan...")
        result = meal_planner._generate_with_ollama(sample_preferences)
        
        if result:
            print("✅ Meal plan generated successfully!")
            print(f"📋 Generated {len(result)} days")
            
            # Show a sample day
            for day, meals in result.items():
                if isinstance(meals, dict):
                    print(f"\n📅 {day.title()}:")
                    for meal_type, meal in meals.items():
                        if isinstance(meal, dict) and 'name' in meal:
                            print(f"  🍽️ {meal_type}: {meal['name']}")
                    break  # Just show first day
            
            return True
        else:
            print("❌ Failed to generate meal plan")
            return False
            
    except Exception as e:
        print(f"❌ Error testing meal plan generation: {e}")
        return False

def test_simple_prompt():
    """Test with a simple prompt to see if Ollama responds"""
    print("\n🧪 Testing simple Ollama prompt...")
    
    ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    
    simple_prompt = "Create a simple meal plan for Monday with breakfast, lunch, and dinner. Format as JSON."
    
    try:
        payload = {
            "model": "llama3.2:latest",
            "prompt": simple_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "max_tokens": 500
            }
        }
        
        print("🚀 Sending simple prompt to Ollama...")
        response = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            meal_plan_text = result.get('response', '')
            print("✅ Ollama responded successfully!")
            print(f"📝 Response length: {len(meal_plan_text)} characters")
            print(f"📄 Response preview: {meal_plan_text[:200]}...")
            return True
        else:
            print(f"❌ Ollama request failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing simple prompt: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Ollama Meal Planner Integration")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Test 1: Connection
    connection_ok = test_ollama_connection()
    
    if not connection_ok:
        print("\n❌ Ollama connection failed. Please fix this first.")
        print("\n💡 Troubleshooting steps:")
        print("1. Install Ollama: https://ollama.ai/")
        print("2. Start Ollama: ollama serve")
        print("3. Pull a model: ollama pull llama3.2:latest")
        print("4. Check if Ollama is running: ollama list")
        return
    
    # Test 2: Simple prompt
    simple_ok = test_simple_prompt()
    
    if not simple_ok:
        print("\n❌ Simple prompt test failed. Ollama may not be working properly.")
        return
    
    # Test 3: Full meal plan generation
    meal_plan_ok = test_meal_plan_generation()
    
    if meal_plan_ok:
        print("\n🎉 All tests passed! Ollama integration is working.")
        print("\n💡 You can now use the AI meal planner in your app.")
    else:
        print("\n⚠️ Meal plan generation failed, but Ollama is accessible.")
        print("This might be due to model issues or prompt formatting.")

if __name__ == "__main__":
    main()
