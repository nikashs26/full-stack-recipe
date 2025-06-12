import { SpoonacularSearchResponse } from '../types/spoonacular';

const API_KEY = process.env.NEXT_PUBLIC_SPOONACULAR_API_KEY;

export const fetchRecipes = async (query: string = '', cuisine: string = ''): Promise<SpoonacularSearchResponse> => {
  const baseUrl = 'https://api.spoonacular.com/recipes/complexSearch';
  
  // Build search parameters - increase number to get more results
  const params = new URLSearchParams({
    apiKey: API_KEY,
    number: '12', // Increased from default to get more results
    addRecipeInformation: 'true',
    fillIngredients: 'true',
    instructionsRequired: 'false', // Don't require instructions to get more results
    sort: 'popularity', // Sort by popularity to get better results
  });

  // Add query if provided
  if (query && query.trim()) {
    params.append('query', query.trim());
  }

  // Add cuisine filter if provided
  if (cuisine && cuisine.trim()) {
    params.append('cuisine', cuisine.trim());
  }

  // If no specific search, use popular terms to get good results
  if (!query && !cuisine) {
    params.set('query', 'chicken,pasta,beef,vegetarian'); // Multiple popular terms
    params.set('number', '20'); // Even more results for general browsing
  }

  const url = `${baseUrl}?${params.toString()}`;
  
  console.log(`Fetching recipes from: ${url}`);
  
  try {
    const response = await fetch(url);
    
    if (!response.ok) {
      console.error(`API request failed with status: ${response.status}`);
      throw new Error(`Failed to fetch recipes (Status: ${response.status})`);
    }
    
    const data = await response.json();
    console.log(`Received ${data.results?.length || 0} recipes from API`);
    
    // Ensure all recipes have proper image URLs
    if (data.results) {
      data.results = data.results.map((recipe: any) => ({
        ...recipe,
        image: recipe.image || `https://images.unsplash.com/photo-1546554137-f86b9593a222?w=400&h=300&fit=crop`,
        readyInMinutes: recipe.readyInMinutes || 30,
        cuisines: recipe.cuisines || ['International'],
        diets: recipe.diets || []
      }));
    }
    
    return data;
  } catch (error) {
    console.error('Error fetching recipes:', error);
    
    // Return better fallback data when API fails
    return {
      results: [
        {
          id: 716429,
          title: "Pasta with Garlic, Scallions, and Broccoli",
          image: "https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=400&h=300&fit=crop",
          imageType: "jpg",
          readyInMinutes: 25,
          summary: "A delicious and healthy pasta dish perfect for any occasion.",
          cuisines: ["Italian"],
          diets: ["vegetarian"]
        },
        {
          id: 715538,
          title: "Bruschetta with Tomato and Basil",
          image: "https://images.unsplash.com/photo-1572441713132-51c75654db73?w=400&h=300&fit=crop",
          imageType: "jpg",
          readyInMinutes: 15,
          summary: "Classic Italian appetizer with fresh tomatoes and basil.",
          cuisines: ["Italian"],
          diets: ["vegetarian"]
        },
        {
          id: 782585,
          title: "Cannellini Bean and Sausage Soup",
          image: "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400&h=300&fit=crop",
          imageType: "jpg",
          readyInMinutes: 30,
          summary: "Hearty Italian soup with beans and sausage.",
          cuisines: ["Italian"],
          diets: []
        },
        {
          id: 715415,
          title: "Red Lentil Soup with Chicken and Turnips",
          image: "https://images.unsplash.com/photo-1547592180-85f173990554?w=400&h=300&fit=crop",
          imageType: "jpg",
          readyInMinutes: 25,
          summary: "Quick and nutritious soup perfect for busy weeknights.",
          cuisines: ["Middle Eastern"],
          diets: ["gluten free"]
        },
        {
          id: 716406,
          title: "Asparagus and Pea Soup",
          image: "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400&h=300&fit=crop",
          imageType: "jpg",
          readyInMinutes: 20,
          summary: "Light and fresh spring soup.",
          cuisines: ["European"],
          diets: ["vegetarian", "vegan"]
        },
        {
          id: 644387,
          title: "Garlicky Kale",
          image: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=300&fit=crop",
          imageType: "jpg",
          readyInMinutes: 15,
          summary: "Quick and healthy sautéed kale with garlic.",
          cuisines: ["American"],
          diets: ["vegetarian", "vegan"]
        },
        {
          id: 123456,
          title: "Grilled Chicken Breast",
          image: "https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=400&h=300&fit=crop",
          imageType: "jpg",
          readyInMinutes: 20,
          summary: "Simple and delicious grilled chicken perfect for any meal.",
          cuisines: ["American"],
          diets: ["gluten free"]
        },
        {
          id: 789012,
          title: "Chicken Stir Fry",
          image: "https://images.unsplash.com/photo-1603360946369-dc9bb6258143?w=400&h=300&fit=crop",
          imageType: "jpg",
          readyInMinutes: 15,
          summary: "Quick and healthy chicken stir fry with vegetables.",
          cuisines: ["Asian"],
          diets: ["gluten free"]
        }
      ],
      offset: 0,
      number: 8,
      totalResults: 8
    };
  }
};
