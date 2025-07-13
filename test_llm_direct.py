#!/usr/bin/env python3
"""
Direct LLM Testing Script
Run this to send prompts directly to your LLM without going through the full meal planner system.
"""

import requests
import json
import sys

def test_ollama_direct(prompt, model="llama3.2:latest"):
    """Send a prompt directly to Ollama"""
    print(f"🚀 Testing Ollama with model: {model}")
    print(f"📝 Prompt: {prompt}")
    print("=" * 50)
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            llm_response = result.get('response', '')
            print(f"✅ Success! Response length: {len(llm_response)} characters")
            print("📄 LLM Response:")
            print("-" * 30)
            print(llm_response)
            print("-" * 30)
            return llm_response
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None

def test_meal_plan_prompt():
    """Test with a meal planning prompt"""
    prompt = """Generate a 7-day weekly meal plan for someone with these preferences:
- Vegetarian diet
- Likes Italian and Mediterranean cuisine
- Allergic to nuts
- Prefers quick meals (30 minutes or less)
- Wants healthy, balanced nutrition

Format the response as JSON with this structure:
{
    "week_plan": {
        "monday": {"breakfast": "...", "lunch": "...", "dinner": "..."},
        "tuesday": {"breakfast": "...", "lunch": "...", "dinner": "..."},
        ...
    },
    "shopping_list": ["ingredient1", "ingredient2", ...],
    "prep_tips": ["tip1", "tip2", ...]
}

Make sure all recipes are vegetarian, nut-free, and can be prepared in 30 minutes or less."""
    
    return test_ollama_direct(prompt)

def test_simple_prompt():
    """Test with a simple prompt"""
    prompt = "Explain how to make a simple vegetarian pasta dish in 3 steps."
    return test_ollama_direct(prompt)

def test_custom_prompt():
    """Test with a custom prompt from user input"""
    print("Enter your custom prompt (press Enter twice to finish):")
    lines = []
    while True:
        line = input()
        if line == "" and lines:
            break
        lines.append(line)
    
    prompt = "\n".join(lines)
    return test_ollama_direct(prompt)

def main():
    print("🧪 Direct LLM Testing Tool")
    print("=" * 40)
    
    while True:
        print("\nChoose an option:")
        print("1. Test simple prompt")
        print("2. Test meal plan prompt")
        print("3. Test custom prompt")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            test_simple_prompt()
        elif choice == "2":
            test_meal_plan_prompt()
        elif choice == "3":
            test_custom_prompt()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main() 