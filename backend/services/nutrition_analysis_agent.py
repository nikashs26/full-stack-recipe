import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class NutritionAnalysisAgent:
    """
    AI Agent that analyzes recipes using LLMs to extract nutritional information.
    This utility should only be run once to assign macros to each recipe.
    """
    
    def __init__(self):
        """Initialize the nutrition analysis agent with available LLM services"""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.hf_api_key = os.getenv('HUGGING_FACE_API_KEY')
        
        # Only use Ollama since it's working locally
        self.llm_services = [
            ('ollama', self._analyze_with_ollama)
        ]
        
        logger.info("Nutrition Analysis Agent initialized - using Ollama only")
    
    async def analyze_recipe_nutrition(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single recipe to extract nutritional information.
        
        Args:
            recipe: Recipe dictionary containing ingredients, instructions, etc.
            
        Returns:
            Dictionary with nutritional information and analysis metadata
        """
        try:
            logger.info(f"Analyzing nutrition for recipe: {recipe.get('title', 'Unknown')}")
            
            # Prepare recipe data for analysis
            recipe_text = self._prepare_recipe_for_analysis(recipe)
            
            # Try each LLM service in order
            for service_name, service_func in self.llm_services:
                try:
                    logger.info(f"Attempting analysis with {service_name}")
                    nutrition_data = await service_func(recipe_text, recipe)
                    
                    if nutrition_data and self._validate_nutrition_data(nutrition_data):
                        logger.info(f"Successfully analyzed recipe with {service_name}")
                        return {
                            'recipe_id': recipe.get('id'),
                            'title': recipe.get('title'),
                            'nutrition': nutrition_data,
                            'analyzed_at': datetime.utcnow().isoformat(),
                            'llm_service': service_name,
                            'status': 'success'
                        }
                        
                except Exception as e:
                    logger.warning(f"Failed to analyze with {service_name}: {e}")
                    continue
            
            # If all services fail, return error
            logger.error("All LLM services failed for recipe analysis")
            return {
                'recipe_id': recipe.get('id'),
                'title': recipe.get('title'),
                'status': 'error',
                'error': 'All LLM services failed',
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Unexpected error analyzing recipe: {e}")
            return {
                'recipe_id': recipe.get('id'),
                'title': recipe.get('title'),
                'status': 'error',
                'error': str(e),
                'analyzed_at': datetime.utcnow().isoformat()
            }
    
    async def analyze_multiple_recipes(self, recipes: List[Dict[str, Any]], 
                                     batch_size: int = 5) -> List[Dict[str, Any]]:
        """
        Analyze multiple recipes in batches to avoid overwhelming LLM services.
        
        Args:
            recipes: List of recipe dictionaries
            batch_size: Number of recipes to process simultaneously
            
        Returns:
            List of nutrition analysis results
        """
        logger.info(f"Starting batch analysis of {len(recipes)} recipes")
        
        results = []
        
        # Process recipes in batches
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: recipes {i+1}-{min(i+batch_size, len(recipes))}")
            
            # Create tasks for concurrent processing
            tasks = [self.analyze_recipe_nutrition(recipe) for recipe in batch]
            
            # Execute batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing recipe {i+j+1}: {result}")
                    results.append({
                        'recipe_id': batch[j].get('id'),
                        'title': batch[j].get('title'),
                        'status': 'error',
                        'error': str(result),
                        'analyzed_at': datetime.utcnow().isoformat()
                    })
                else:
                    results.append(result)
            
            # Small delay between batches to be respectful to LLM services
            if i + batch_size < len(recipes):
                await asyncio.sleep(1)
        
        logger.info(f"Completed analysis of {len(recipes)} recipes")
        return results
    
    def _prepare_recipe_for_analysis(self, recipe: Dict[str, Any]) -> str:
        """
        Prepare recipe data in a format suitable for LLM analysis.
        
        Args:
            recipe: Recipe dictionary
            
        Returns:
            Formatted string for LLM analysis
        """
        title = recipe.get('title', 'Unknown Recipe')
        servings = recipe.get('servings', 1)
        
        # Extract ingredients
        ingredients = []
        if 'ingredients' in recipe:
            for ingredient in recipe['ingredients']:
                if isinstance(ingredient, dict):
                    amount = ingredient.get('amount', '')
                    unit = ingredient.get('unit', '')
                    name = ingredient.get('name', '')
                    if name:
                        ingredients.append(f"{amount} {unit} {name}".strip())
                elif isinstance(ingredient, str):
                    ingredients.append(ingredient)
        
        # Extract instructions
        instructions = []
        if 'instructions' in recipe:
            if isinstance(recipe['instructions'], list):
                instructions = recipe['instructions']
            elif isinstance(recipe['instructions'], str):
                instructions = [recipe['instructions']]
        
        # Format for LLM
        recipe_text = f"""
Recipe: {title}
Servings: {servings}

Ingredients:
{chr(10).join(f"- {ingredient}" for ingredient in ingredients)}

Instructions:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(instructions))}

Please analyze this recipe and provide the following nutritional information per serving:
- Calories (kcal)
- Carbohydrates (g)
- Fat (g)
- Protein (g)

Provide the response in JSON format with these exact keys: calories, carbohydrates, fat, protein
"""
        return recipe_text.strip()
    
    async def _analyze_with_openai(self, recipe_text: str, recipe: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze recipe using OpenAI API"""
        if not self.openai_api_key:
            raise Exception("OpenAI API key not configured")
        
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.openai_api_key)
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a nutrition expert. Analyze recipes and provide accurate nutritional information per serving. Always respond with valid JSON containing calories, carbohydrates, fat, and protein values."},
                    {"role": "user", "content": recipe_text}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            return self._parse_llm_response(content)
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            raise
    
    async def _analyze_with_ollama(self, recipe_text: str, recipe: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze recipe using Ollama (local LLM)"""
        try:
            import aiohttp
            
            # Check if Ollama is available
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags", timeout=5) as response:
                    if response.status != 200:
                        raise Exception("Ollama server not available")
                
                payload = {
                    "model": "llama3.2:latest",
                    "prompt": f"""You are a nutrition expert. Analyze this recipe and provide nutritional information per serving in JSON format.

{recipe_text}

Respond only with valid JSON containing: calories, carbohydrates, fat, protein""",
                    "stream": False
                }
                
                async with session.post(f"{self.ollama_url}/api/generate", json=payload, timeout=30) as response:
                    if response.status != 200:
                        raise Exception(f"Ollama API error: {response.status}")
                    
                    result = await response.json()
                    content = result.get('response', '')
                    
                    if not content:
                        raise Exception("Empty response from Ollama")
                    
                    logger.info(f"Ollama response: {content[:100]}...")
                    return self._parse_llm_response(content)
            
        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            raise
    
    async def _analyze_with_huggingface(self, recipe_text: str, recipe: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze recipe using Hugging Face Inference API"""
        if not self.hf_api_key:
            raise Exception("Hugging Face API key not configured")
        
        try:
            # Use a suitable model for text generation
            model = "microsoft/DialoGPT-medium"  # Alternative: "gpt2" or other text generation models
            
            headers = {"Authorization": f"Bearer {self.hf_api_key}"}
            
            payload = {
                "inputs": f"""You are a nutrition expert. Analyze this recipe and provide nutritional information per serving in JSON format.

{recipe_text}

Respond only with valid JSON containing: calories, carbohydrates, fat, protein. Make sure the macors add up correctly (1g of protein is 4 calories, 1g of carbs is 4 calories, 1g of fat is 9 calories)""",
                "parameters": {
                    "max_length": 200,
                    "temperature": 0.1,
                    "return_full_text": False
                }
            }
            
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Hugging Face API error: {response.status_code}")
            
            result = response.json()
            content = result[0].get('generated_text', '') if isinstance(result, list) else str(result)
            
            return self._parse_llm_response(content)
            
        except Exception as e:
            logger.error(f"Hugging Face analysis failed: {e}")
            raise
    
    def _parse_llm_response(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse the LLM response to extract nutritional information.
        
        Args:
            content: Raw response from LLM
            
        Returns:
            Parsed nutrition data or None if parsing fails
        """
        try:
            # Try to extract JSON from the response
            content = content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            content = content.strip()
            
            # Try to parse as JSON
            try:
                nutrition_data = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON-like content
                import re
                json_match = re.search(r'\{[^}]*\}', content)
                if json_match:
                    nutrition_data = json.loads(json_match.group())
                else:
                    raise Exception("No valid JSON found in response")
            
            # Validate required fields
            required_fields = ['calories', 'carbohydrates', 'fat', 'protein']
            if not all(field in nutrition_data for field in required_fields):
                raise Exception(f"Missing required fields: {required_fields}")
            
            # Convert to numeric values and validate
            parsed_data = {}
            for field in required_fields:
                value = nutrition_data[field]
                if isinstance(value, str):
                    # Extract numeric value from string
                    import re
                    numeric_match = re.search(r'\d+(?:\.\d+)?', value)
                    if numeric_match:
                        value = float(numeric_match.group())
                    else:
                        raise Exception(f"Could not extract numeric value from {field}: {value}")
                
                if not isinstance(value, (int, float)) or value < 0:
                    raise Exception(f"Invalid value for {field}: {value}")
                
                parsed_data[field] = round(float(value), 1)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Raw response content: {content}")
            return None
    
    def _validate_nutrition_data(self, nutrition_data: Dict[str, Any]) -> bool:
        """
        Validate that nutrition data is reasonable.
        
        Args:
            nutrition_data: Parsed nutrition data
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Check that all required fields are present
            required_fields = ['calories', 'carbohydrates', 'fat', 'protein']
            if not all(field in nutrition_data for field in required_fields):
                return False
            
            # Check that values are reasonable
            calories = nutrition_data['calories']
            carbs = nutrition_data['carbohydrates']
            fat = nutrition_data['fat']
            protein = nutrition_data['protein']
            
            # Basic sanity checks
            if calories < 0 or calories > 5000:  # Reasonable range for a serving
                return False
            
            if carbs < 0 or carbs > 200:
                return False
                
            if fat < 0 or fat > 100:
                return False
                
            if protein < 0 or protein > 100:
                return False
            
            # Check that macros add up reasonably (allowing for some variance)
            total_macros = carbs * 4 + fat * 9 + protein * 4  # Calories from macros
            if abs(total_macros - calories) > calories * 0.5:  # Allow 50% variance
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Nutrition data validation failed: {e}")
            return False
    
    def save_nutrition_results(self, results: List[Dict[str, Any]], 
                              output_file: str = "nutrition_analysis_results.json") -> str:
        """
        Save nutrition analysis results to a JSON file.
        
        Args:
            results: List of nutrition analysis results
            output_file: Output file path
            
        Returns:
            Path to saved file
        """
        try:
            # Create summary statistics
            successful_analyses = [r for r in results if r.get('status') == 'success']
            failed_analyses = [r for r in results if r.get('status') == 'error']
            
            summary = {
                'total_recipes': len(results),
                'successful_analyses': len(successful_analyses),
                'failed_analyses': len(failed_analyses),
                'success_rate': len(successful_analyses) / len(results) if results else 0,
                'generated_at': datetime.utcnow().isoformat(),
                'results': results
            }
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Nutrition analysis results saved to {output_file}")
            logger.info(f"Success rate: {summary['success_rate']:.1%}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise


# Example usage and testing
async def main():
    """Example usage of the NutritionAnalysisAgent"""
    
    # Sample recipe for testing
    sample_recipe = {
        'id': 'test-001',
        'title': 'Chicken Stir Fry',
        'servings': 4,
        'ingredients': [
            {'amount': 1, 'unit': 'lb', 'name': 'chicken breast'},
            {'amount': 2, 'unit': 'cups', 'name': 'broccoli'},
            {'amount': 1, 'unit': 'tbsp', 'name': 'olive oil'},
            {'amount': 2, 'unit': 'tbsp', 'name': 'soy sauce'}
        ],
        'instructions': [
            'Cut chicken into bite-sized pieces',
            'Stir fry chicken in oil until cooked',
            'Add broccoli and soy sauce',
            'Cook until vegetables are tender'
        ]
    }
    
    # Initialize agent
    agent = NutritionAnalysisAgent()
    
    # Analyze single recipe
    print("Analyzing single recipe...")
    result = await agent.analyze_recipe_nutrition(sample_recipe)
    print(json.dumps(result, indent=2))
    
    # Analyze multiple recipes
    print("\nAnalyzing multiple recipes...")
    recipes = [sample_recipe] * 3  # Duplicate for testing
    results = await agent.analyze_multiple_recipes(recipes, batch_size=2)
    
    # Save results
    output_file = agent.save_nutrition_results(results)
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main()) 