#!/usr/bin/env python3
"""
Test script for the NutritionAnalysisAgent.
This script tests the agent with sample recipes to ensure it works correctly.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the services directory to the Python path
sys.path.append(str(Path(__file__).parent / 'services'))

from nutrition_analysis_agent import NutritionAnalysisAgent

async def test_nutrition_agent():
    """Test the nutrition analysis agent with sample recipes"""
    
    print("🧪 Testing Nutrition Analysis Agent...")
    
    # Initialize the agent
    agent = NutritionAnalysisAgent()
    
    # Sample recipes for testing
    test_recipes = [
        {
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
        },
        {
            'id': 'test-002',
            'title': 'Simple Pasta',
            'servings': 2,
            'ingredients': [
                {'amount': 8, 'unit': 'oz', 'name': 'spaghetti'},
                {'amount': 2, 'unit': 'tbsp', 'name': 'olive oil'},
                {'amount': 2, 'unit': 'cloves', 'name': 'garlic'},
                {'amount': 1/4, 'unit': 'cup', 'name': 'parmesan cheese'}
            ],
            'instructions': [
                'Boil pasta according to package directions',
                'Heat oil and sauté garlic',
                'Toss pasta with oil and cheese'
            ]
        },
        {
            'id': 'test-003',
            'title': 'Greek Salad',
            'servings': 4,
            'ingredients': [
                {'amount': 2, 'unit': 'cups', 'name': 'mixed greens'},
                {'amount': 1, 'unit': 'cup', 'name': 'cherry tomatoes'},
                {'amount': 1/2, 'unit': 'cup', 'name': 'cucumber'},
                {'amount': 1/4, 'unit': 'cup', 'name': 'olives'},
                {'amount': 2, 'unit': 'tbsp', 'name': 'olive oil'}
            ],
            'instructions': [
                'Wash and chop vegetables',
                'Combine in bowl',
                'Drizzle with olive oil'
            ]
        }
    ]
    
    print(f"📋 Testing with {len(test_recipes)} sample recipes...")
    
    # Test single recipe analysis
    print("\n🔍 Testing single recipe analysis...")
    single_result = await agent.analyze_recipe_nutrition(test_recipes[0])
    print("Single recipe result:")
    print(json.dumps(single_result, indent=2))
    
    # Test batch analysis
    print("\n📦 Testing batch analysis...")
    batch_results = await agent.analyze_multiple_recipes(test_recipes, batch_size=2)
    print("Batch analysis results:")
    print(json.dumps(batch_results, indent=2))
    
    # Save results
    print("\n💾 Saving test results...")
    output_file = agent.save_nutrition_results(batch_results, "test_nutrition_results.json")
    print(f"Results saved to: {output_file}")
    
    # Print summary
    successful = len([r for r in batch_results if r.get('status') == 'success'])
    total = len(batch_results)
    print(f"\n✅ Test Summary:")
    print(f"   Total recipes: {total}")
    print(f"   Successful analyses: {successful}")
    print(f"   Success rate: {successful/total:.1%}")
    
    if successful == total:
        print("🎉 All tests passed! The nutrition analysis agent is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs for details.")
    
    return batch_results

def test_recipe_preparation():
    """Test the recipe preparation function"""
    print("\n🔧 Testing recipe preparation...")
    
    agent = NutritionAnalysisAgent()
    
    sample_recipe = {
        'id': 'test-prep',
        'title': 'Test Recipe',
        'servings': 2,
        'ingredients': [
            {'amount': 1, 'unit': 'cup', 'name': 'flour'},
            {'amount': 2, 'unit': 'eggs', 'name': 'eggs'}
        ],
        'instructions': ['Mix ingredients', 'Bake at 350F']
    }
    
    prepared_text = agent._prepare_recipe_for_analysis(sample_recipe)
    print("Prepared recipe text:")
    print(prepared_text)
    
    return prepared_text

def test_response_parsing():
    """Test the LLM response parsing function"""
    print("\n🔍 Testing response parsing...")
    
    agent = NutritionAnalysisAgent()
    
    # Test valid JSON response
    valid_response = '{"calories": 350, "carbohydrates": 45, "fat": 12, "protein": 8}'
    parsed = agent._parse_llm_response(valid_response)
    print(f"Valid JSON parsing: {parsed}")
    
    # Test response with markdown
    markdown_response = '```json\n{"calories": 400, "carbohydrates": 50, "fat": 15, "protein": 10}\n```'
    parsed = agent._parse_llm_response(markdown_response)
    print(f"Markdown JSON parsing: {parsed}")
    
    # Test response with text
    text_response = 'Based on the recipe, here are the nutritional values: {"calories": 300, "carbohydrates": 35, "fat": 10, "protein": 6} per serving.'
    parsed = agent._parse_llm_response(text_response)
    print(f"Text with JSON parsing: {parsed}")
    
    return parsed

async def main():
    """Main test function"""
    print("🚀 Starting Nutrition Analysis Agent Tests\n")
    
    try:
        # Test recipe preparation
        test_recipe_preparation()
        
        # Test response parsing
        test_response_parsing()
        
        # Test full agent functionality
        results = await test_nutrition_agent()
        
        print("\n✨ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 