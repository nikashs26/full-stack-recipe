import asyncio
import chromadb
from services.nutrition_analysis_agent import NutritionAnalysisAgent

async def test_nutrition_on_real_recipes():
    """Test nutrition analysis on a few real recipes from the database"""
    
    print("🧪 Testing Nutrition Agent on Real Recipes...")
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    recipe_collection = client.get_collection("recipe_details_cache")
    
    print(f"📊 Total recipes in database: {recipe_collection.count()}")
    
    # Get just 3 recipes to test
    results = recipe_collection.get(limit=3, include=['documents', 'metadatas'])
    
    if not results['documents']:
        print("❌ No recipes found in database")
        return
    
    print(f"📋 Testing with {len(results['documents'])} recipes...")
    
    # Initialize nutrition agent
    nutrition_agent = NutritionAnalysisAgent()
    
    # Test each recipe
    for i, doc in enumerate(results['documents']):
        try:
            # Parse recipe data
            recipe_data = {
                'id': results['metadatas'][i].get('id', f'recipe_{i}'),
                'title': results['metadatas'][i].get('title', f'Recipe {i}'),
                'ingredients': results['metadatas'][i].get('ingredients', ''),
                'instructions': doc if doc else ''
            }
            
            print(f"\n🍽️  Analyzing: {recipe_data['title']}")
            
            # Analyze nutrition
            result = await nutrition_agent.analyze_recipe_nutrition(recipe_data)
            
            if result['status'] == 'success':
                nutrition = result['nutrition']
                print(f"   ✅ Calories: {nutrition.get('calories', 'N/A')} kcal")
                print(f"   ✅ Protein: {nutrition.get('protein', 'N/A')}g")
                print(f"   ✅ Carbs: {nutrition.get('carbohydrates', 'N/A')}g")
                print(f"   ✅ Fat: {nutrition.get('fat', 'N/A')}g")
                print(f"   🔧 Analyzed by: {result['llm_service']}")
            else:
                print(f"   ❌ Analysis failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Error processing recipe {i}: {e}")
    
    print("\n🎉 Nutrition analysis test complete!")

if __name__ == "__main__":
    asyncio.run(test_nutrition_on_real_recipes()) 