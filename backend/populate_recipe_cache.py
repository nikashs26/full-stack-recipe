from services.recipe_cache_service import RecipeCacheService
import json

# Sample recipes with high-quality data
SAMPLE_RECIPES = [
    {
        "id": 1001,
        "title": "Classic Spaghetti Carbonara",
        "image": "https://images.unsplash.com/photo-1612874742237-6526221588e3?auto=format&fit=crop&w=800",
        "summary": "A traditional Italian pasta dish made with eggs, cheese, pancetta and black pepper.",
        "readyInMinutes": 30,
        "servings": 4,
        "cuisines": ["Italian"],
        "diets": ["pescatarian"],
        "dishTypes": ["main course", "dinner"],
        "instructions": "1. Cook spaghetti in salted water.\n2. Fry pancetta until crispy.\n3. Mix eggs, cheese, and pepper.\n4. Combine pasta with egg mixture and pancetta.",
        "extendedIngredients": [
            {"id": 11420, "name": "spaghetti", "amount": 400, "unit": "grams"},
            {"id": 10410123, "name": "pancetta", "amount": 150, "unit": "grams"},
            {"id": 1123, "name": "eggs", "amount": 3, "unit": "large"},
            {"id": 1033, "name": "parmesan cheese", "amount": 100, "unit": "grams"}
        ]
    },
    {
        "id": 1002,
        "title": "Vegetarian Buddha Bowl",
        "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800",
        "summary": "A healthy and colorful bowl packed with quinoa, roasted vegetables, and tahini dressing.",
        "readyInMinutes": 45,
        "servings": 2,
        "cuisines": ["American", "Healthy"],
        "diets": ["vegetarian", "vegan", "gluten-free"],
        "dishTypes": ["lunch", "main course"],
        "instructions": "1. Cook quinoa.\n2. Roast vegetables.\n3. Prepare tahini dressing.\n4. Assemble bowls.",
        "extendedIngredients": [
            {"id": 20137, "name": "quinoa", "amount": 200, "unit": "grams"},
            {"id": 11507, "name": "sweet potato", "amount": 1, "unit": "large"},
            {"id": 11098, "name": "kale", "amount": 200, "unit": "grams"},
            {"id": 12698, "name": "tahini", "amount": 30, "unit": "ml"}
        ]
    },
    {
        "id": 1003,
        "title": "Spicy Bean Burrito",
        "image": "https://images.unsplash.com/photo-1584031036380-3fb6f2d51903?auto=format&fit=crop&w=800",
        "summary": "A hearty Mexican-style burrito filled with spiced beans, rice, and fresh vegetables.",
        "readyInMinutes": 25,
        "servings": 4,
        "cuisines": ["Mexican"],
        "diets": ["vegetarian"],
        "dishTypes": ["lunch", "dinner"],
        "instructions": "1. Cook rice.\n2. Heat and season beans.\n3. Warm tortillas.\n4. Assemble burritos with toppings.",
        "extendedIngredients": [
            {"id": 16034, "name": "black beans", "amount": 400, "unit": "grams"},
            {"id": 20444, "name": "rice", "amount": 200, "unit": "grams"},
            {"id": 11252, "name": "lettuce", "amount": 1, "unit": "head"},
            {"id": 11529, "name": "tomato", "amount": 2, "unit": "medium"}
        ]
    },
    {
        "id": 1004,
        "title": "Thai Green Curry",
        "image": "https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?auto=format&fit=crop&w=800",
        "summary": "A fragrant and creamy Thai curry with vegetables and your choice of protein.",
        "readyInMinutes": 35,
        "servings": 4,
        "cuisines": ["Thai", "Asian"],
        "diets": ["gluten-free"],
        "dishTypes": ["main course"],
        "instructions": "1. Sauté curry paste.\n2. Add coconut milk.\n3. Cook vegetables.\n4. Serve with rice.",
        "extendedIngredients": [
            {"id": 93605, "name": "green curry paste", "amount": 50, "unit": "grams"},
            {"id": 12118, "name": "coconut milk", "amount": 400, "unit": "ml"},
            {"id": 11450, "name": "bamboo shoots", "amount": 200, "unit": "grams"},
            {"id": 11819, "name": "thai basil", "amount": 30, "unit": "grams"}
        ]
    },
    {
        "id": 1005,
        "title": "Mediterranean Chickpea Salad",
        "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800",
        "summary": "A refreshing salad with chickpeas, cucumber, tomatoes, and feta cheese.",
        "readyInMinutes": 15,
        "servings": 4,
        "cuisines": ["Mediterranean", "Greek"],
        "diets": ["vegetarian", "gluten-free"],
        "dishTypes": ["salad", "side dish", "lunch"],
        "instructions": "1. Drain chickpeas.\n2. Chop vegetables.\n3. Make dressing.\n4. Combine and toss.",
        "extendedIngredients": [
            {"id": 16057, "name": "chickpeas", "amount": 400, "unit": "grams"},
            {"id": 11206, "name": "cucumber", "amount": 1, "unit": "large"},
            {"id": 1019, "name": "feta cheese", "amount": 100, "unit": "grams"},
            {"id": 4053, "name": "olive oil", "amount": 60, "unit": "ml"}
        ]
    }
]

def main():
    print("Initializing recipe cache service...")
    recipe_cache = RecipeCacheService()
    
    print("\nClearing existing cache...")
    recipe_cache.clear_cache()
    
    print("\nPopulating cache with sample recipes...")
    for recipe in SAMPLE_RECIPES:
        # Add common search terms to help with matching
        search_terms = [
            recipe["title"].lower(),
            *recipe["cuisines"],
            *recipe["diets"],
            *recipe["dishTypes"],
            *[ing["name"] for ing in recipe["extendedIngredients"]]
        ]
        
        # Cache the recipe with its search terms
        recipe_cache.cache_recipes([recipe], " ".join(search_terms), "")
        print(f"Cached recipe: {recipe['title']}")
        
        # Also cache by cuisine
        for cuisine in recipe["cuisines"]:
            recipe_cache.cache_recipes([recipe], cuisine.lower(), "")
            print(f"  - Cached under cuisine: {cuisine}")
            
        # Cache by diet
        for diet in recipe["diets"]:
            recipe_cache.cache_recipes([recipe], diet.lower(), "")
            print(f"  - Cached under diet: {diet}")
            
        # Cache by main ingredients
        for ingredient in recipe["extendedIngredients"]:
            recipe_cache.cache_recipes([recipe], "", ingredient["name"].lower())
            print(f"  - Cached with ingredient: {ingredient['name']}")
    
    print("\nVerifying cache contents...")
    # Test some common searches
    test_queries = [
        ("pasta", ""),
        ("vegetarian", ""),
        ("thai", ""),
        ("", "beans"),
        ("mediterranean", ""),
        ("quick", ""),
        ("healthy", "")
    ]
    
    for query, ingredient in test_queries:
        results = recipe_cache.get_cached_recipes(query, ingredient)
        print(f"\nSearch for '{query}' with ingredient '{ingredient}':")
        print(f"Found {len(results)} results")
        if results:
            print("Matching recipes:")
            for recipe in results:
                print(f"- {recipe['title']}")
        else:
            print("No matching recipes found")
    
    # Get cache statistics
    stats = recipe_cache.get_cache_stats()
    print("\nCache Statistics:")
    print(f"Total cache entries: {stats['total_cache_entries']}")
    print(f"Total cached recipes: {stats['total_cached_recipes']}")

if __name__ == "__main__":
    main() 