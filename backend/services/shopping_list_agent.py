import requests
import os
import json
from typing import List, Dict, Any
from collections import defaultdict
from services.recipe_service import RecipeService # Assuming RecipeService can fetch recipe details by ID

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GOOGLE_API_KEY}"

class ShoppingListAgent:
    def __init__(self, recipe_service: RecipeService):
        self.recipe_service = recipe_service

    def generate_shopping_list(self, weekly_plan: Dict[str, Any]) -> Dict[str, Any]:
        if not GOOGLE_API_KEY:
            print("Error: GOOGLE_API_KEY not set. Cannot use LLM for shopping list generation.")
            return {"error": "LLM API key not configured. Please set GOOGLE_API_KEY environment variable.", "shopping_list": {}}

        all_raw_ingredients: List[str] = []
        all_recipes_map = {recipe["id"]: recipe for recipe in self.recipe_service.get_all_recipes()} 

        for day, meals in weekly_plan.items():
            for meal_type, recipe_info in meals.items():
                if recipe_info and recipe_info.get("id") and recipe_info["id"] != "none":
                    recipe_id = recipe_info["id"]
                    recipe = all_recipes_map.get(recipe_id)

                    if recipe:
                        all_raw_ingredients.extend(recipe.get("ingredients", []))
                    else:
                        print(f"Warning: Recipe with ID {recipe_id} not found in RecipeService for {day} {meal_type}. It won't be included in shopping list.")

        if not all_raw_ingredients:
            return {"shopping_list": {}, "message": "No ingredients found in the meal plan to generate a list."}

        # Construct the prompt for the LLM
        prompt = f"""You are an intelligent shopping list generator. Your task is to take a raw list of ingredients, deduplicate them, aggregate quantities where possible, and categorize them into common shopping sections. Return the result as a JSON object with categories as keys and a list of aggregated ingredient strings (with quantities) as values. If an ingredient appears multiple times, try to combine their quantities. If units are missing or inconsistent, use common sense to aggregate. Output only the JSON. Do not include any other text. Also, remove duplicate categories.

Example Output Format:
{{
    "Produce": ["2 large onions", "1 head lettuce", "3 bell peppers"],
    "Dairy": ["1 gallon milk", "1 block cheddar cheese"],
    "Meat/Poultry": ["1 lb ground beef", "2 chicken breasts"],
    "Pantry Staples": ["1 jar pasta sauce", "500g spaghetti"],
    "Other": ["1 bottle wine"]
}}

Here is the raw list of ingredients from a meal plan:
{all_raw_ingredients}
"""

        headers = {
            'Content-Type': 'application/json',
        }
        data = {
            'contents': [{'parts': [{'text': prompt}]}]
        }

        try:
            print("Sending ingredients to LLM for shopping list generation...")
            response = requests.post(GEMINI_API_URL, headers=headers, json=data, timeout=30)
            response.raise_for_status() # Raise an exception for HTTP errors
            
            llm_response = response.json()
            # Extract the text content from the LLM response
            generated_text = llm_response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '{}')
            
            # Clean the generated text to ensure it's valid JSON
            # Sometimes LLMs might include ```json markers or other surrounding text
            if generated_text.startswith('```json'):
                generated_text = generated_text[len('```json'):]
            if generated_text.endswith('```'):
                generated_text = generated_text[:-len('```')]
            generated_text = generated_text.strip()

            # Parse the JSON string
            parsed_shopping_list = json.loads(generated_text)
            print("Successfully generated shopping list using LLM.")
            return {"shopping_list": parsed_shopping_list}

        except requests.exceptions.RequestException as e:
            print(f"LLM API request failed: {e}")
            return {"error": f"LLM API request failed: {e}", "shopping_list": {}}
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"LLM Raw Response: {generated_text}")
            return {"error": f"Failed to parse LLM response: {e}", "shopping_list": {}}
        except Exception as e:
            print(f"An unexpected error occurred during LLM shopping list generation: {e}")
            return {"error": f"An unexpected error occurred: {e}", "shopping_list": {}} 