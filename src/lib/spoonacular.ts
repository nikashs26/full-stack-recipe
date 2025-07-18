// URLs for API endpoints - fallback to mock data when not available
const API_DB_RECIPES = "http://localhost:5003/recipes";
const API_URL = "http://localhost:5003/get_recipes";
const API_URL_RECIPE_BY_ID = "http://localhost:5003/get_recipe_by_id";

// Fallback data for when the API is unavailable
const FALLBACK_RECIPES = [
  {
    id: 101,
    title: "Beef Tacos",
    image: "https://spoonacular.com/recipeImages/beef-tacos-642539.jpg",
    cuisines: ["Mexican"],
    diets: ["carnivore"],
    readyInMinutes: 30
  },
  {
    id: 102,
    title: "Vegetable Curry",
    image: "https://spoonacular.com/recipeImages/vegetable-curry-642129.jpg",
    cuisines: ["Indian"],
    diets: ["Vegetarian"],
    readyInMinutes: 45
  },
  {
    id: 103,
    title: "Chicken Alfredo",
    image: "https://www.billyparisi.com/wp-content/uploads/2025/03/chicken-alfredo-5.jpg",
    cuisines: ["Italian"],
    diets: ["Non-Vegetarian"],
    readyInMinutes: 25
  },
  {
    id: 104,
    title: "Super Cheesy Burger",
    image: "https://thescranline.com/wp-content/uploads/2023/12/CHEESEBURGERS-WEB-07.jpg",
    cuisines: ["American"],
    diets: ["Non-Vegetarian"],
    readyInMinutes: 40
  },
  {
    id: 105,
    title: "Chicken 65",
    image: "https://popmenucloud.com/cdn-cgi/image/width%3D3840%2Cheight%3D3840%2Cfit%3Dscale-down%2Cformat%3Dauto%2Cquality%3D60/zvmbjaxg/1f1b9169-865a-47f1-b9b0-092c8f7549d4.png",
    cuisines: ["Indian"],
    diets: ["Non-Vegetarian"],
    readyInMinutes: 35
  },
  {
    id: 106,
    title: "Caesar Salad",
    image: "https://natashaskitchen.com/wp-content/uploads/2019/01/Caesar-Salad-Recipe-3.jpg",
    cuisines: ["American"],
    diets: ["Vegetarian"],
    readyInMinutes: 15
  },
  {
    id: 107,
    title: "Spaghetti Carbonara",
    image: "https://www.recipetineats.com/wp-content/uploads/2019/05/Spaghetti-Carbonara_9.jpg",
    cuisines: ["Italian"],
    diets: ["Non-Vegetarian"],
    readyInMinutes: 20
  },
  {
    id: 108,
    title: "Thai Green Curry",
    image: "https://www.recipetineats.com/wp-content/uploads/2014/12/Thai-Green-Curry_1.jpg",
    cuisines: ["Thai"],
    diets: ["Vegetarian"],
    readyInMinutes: 30
  },
  {
    id: 109,
    title: "BBQ Pulled Pork",
    image: "https://www.recipetineats.com/wp-content/uploads/2017/05/Slow-Cooker-Pulled-Pork_9.jpg",
    cuisines: ["American"],
    diets: ["Non-Vegetarian"],
    readyInMinutes: 480
  },
  {
    id: 110,
    title: "Margherita Pizza",
    image: "https://www.recipetineats.com/wp-content/uploads/2020/05/Margherita-Pizza_9.jpg",
    cuisines: ["Italian"],
    diets: ["Vegetarian"],
    readyInMinutes: 25
  },
  {
    id: 111,
    title: "Chicken Tikka Masala",
    image: "https://www.recipetineats.com/wp-content/uploads/2019/01/Chicken-Tikka-Masala_9.jpg",
    cuisines: ["Indian"],
    diets: ["Non-Vegetarian"],
    readyInMinutes: 45
  },
  {
    id: 112,
    title: "Greek Salad",
    image: "https://www.recipetineats.com/wp-content/uploads/2016/04/Greek-Salad_7.jpg",
    cuisines: ["Mediterranean"],
    diets: ["Vegetarian"],
    readyInMinutes: 15
  },
  {
    id: 113,
    title: "Classic Mac and Cheese",
    image: "https://www.recipetineats.com/wp-content/uploads/2014/04/Baked-Mac-and-Cheese_1.jpg",
    cuisines: ["American"],
    diets: ["Vegetarian"],
    readyInMinutes: 35
  },
  {
    id: 114,
    title: "Buffalo Wings",
    image: "https://www.recipetineats.com/wp-content/uploads/2019/07/Buffalo-Wings_8.jpg",
    cuisines: ["American"],
    diets: ["Non-Vegetarian"],
    readyInMinutes: 45
  },
  {
    id: 115,
    title: "Grilled Cheese Sandwich",
    image: "https://www.recipetineats.com/wp-content/uploads/2016/02/Grilled-Cheese_7.jpg",
    cuisines: ["American"],
    diets: ["Vegetarian"],
    readyInMinutes: 10
  },
  {
    id: 116,
    title: "Pancakes",
    image: "https://www.recipetineats.com/wp-content/uploads/2018/05/Pancakes_9.jpg",
    cuisines: ["American"],
    diets: ["Vegetarian"],
    readyInMinutes: 20
  },
  {
    id: 117,
    title: "Meatloaf",
    image: "https://www.recipetineats.com/wp-content/uploads/2018/03/Meatloaf_8.jpg",
    cuisines: ["American"],
    diets: ["Non-Vegetarian"],
    readyInMinutes: 90
  },
  {
    id: 118,
    title: "Coleslaw",
    image: "https://www.recipetineats.com/wp-content/uploads/2019/06/Coleslaw_8.jpg",
    cuisines: ["American"],
    diets: ["Vegetarian"],
    readyInMinutes: 15
  }
];

export const fetchRecipes = async (query: string = "", ingredient: string = "") => {
    console.log(`Fetching recipes with query: "${query}" and ingredient: "${ingredient}"`);
    
    // Try the API endpoint first which will prioritize MongoDB before making API calls
    try {
        // Build the URL with appropriate parameters
        let url = `${API_URL}?`;
        if (query) url += `query=${encodeURIComponent(query)}&`;
        if (ingredient) url += `ingredient=${encodeURIComponent(ingredient)}&`;
        
        console.log("Calling recipe API URL:", url);
        
        // Short timeout to prevent UI hanging
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
        
        try {
            const response = await fetch(
                url.slice(0, -1), // Remove trailing & or ?
                { signal: controller.signal }
            );

            clearTimeout(timeoutId); // Prevent timeout from executing if request succeeds
            
            console.log(`API response status: ${response.status}`);

            if (!response.ok) {
                throw new Error(`Failed to fetch recipes (Status: ${response.status})`);
            }
            
            // Try to parse the JSON response safely
            const data = await response.json();
            console.log("API response data received:", data);
        
            if (!data || typeof data !== 'object') {
                console.error("Invalid API response format", data);
                throw new Error("Invalid API response format");
            }

            // If data.results is missing, create it as an empty array
            if (!Array.isArray(data.results)) {
                data.results = [];
            }

            // If we have valid results from API, return them
            if (data.results.length > 0) {
                console.log(`Found ${data.results.length} recipes from MongoDB/API`);
                return data;
            }

            // If no results from API, use fallback data
            console.log("No results from API, using fallback data");
            return { 
                results: filterFallbackRecipes(query, ingredient),
                status: "fallback",
                message: "Using fallback data as no API results found" 
            };
        } catch (fetchError) {
            // API fetch failed, use fallback data
            console.log("API fetch failed, using fallback data", fetchError);
            
            return { 
                results: filterFallbackRecipes(query, ingredient),
                status: "fallback",
                message: "Using fallback data as API is unavailable" 
            };
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.error("Request timeout while fetching recipes");
        } else {
            console.error("Error fetching recipes:", error);
        }
        
        // Return fallback data when API fails
        return { 
            results: filterFallbackRecipes(query, ingredient),
            status: "fallback",
            message: "Using fallback data as API is unavailable" 
        };
    }
};

// Helper function to filter fallback recipes
const filterFallbackRecipes = (query: string = "", ingredient: string = "") => {
    if (!query && !ingredient) {
        // Return all fallback recipes if no search criteria
        return FALLBACK_RECIPES;
    }
    
    return FALLBACK_RECIPES.filter(recipe => {
        const matchesQuery = query ? 
            recipe.title.toLowerCase().includes(query.toLowerCase()) ||
            recipe.cuisines.some(cuisine => cuisine.toLowerCase().includes(query.toLowerCase())) : 
            true;
            
        const matchesIngredient = ingredient ? 
            // This is a simplification as we don't have ingredients in our fallback data
            recipe.title.toLowerCase().includes(ingredient.toLowerCase()) : 
            true;
        
        // Use actual cuisine data for filtering
        if (query) {
            const recipeCuisines = recipe.cuisines || [];
            
            // Primary check: Does the recipe's cuisine array contain the requested cuisine?
            const directCuisineMatch = recipeCuisines.some(cuisine => 
                cuisine.toLowerCase() === query.toLowerCase()
            );
            
            // Secondary check: Does the recipe title contain the cuisine/query?
            const titleMatch = recipe.title.toLowerCase().includes(query.toLowerCase());
            
            // If it's a direct match, accept it
            if (directCuisineMatch || titleMatch) {
                console.log(`✅ Fallback recipe "${recipe.title}" matches ${query} (cuisines: ${recipeCuisines.join(', ')})`);
                return matchesIngredient;
            }
            
            // If no direct match, reject it
            console.log(`❌ Fallback recipe "${recipe.title}" does not match ${query} (cuisines: ${recipeCuisines.join(', ')})`);
            return false;
        }
            
        return matchesQuery && matchesIngredient;
    });
};

export const fetchRecipeById = async (recipeId: number | string) => {
    console.log(`Fetching recipe by ID: ${recipeId}`);
    
    // Check if this is a fallback recipe ID
    const fallbackRecipe = FALLBACK_RECIPES.find(recipe => recipe.id === parseInt(recipeId.toString()));
    if (fallbackRecipe) {
        console.log("Found fallback recipe, returning detailed information");
        return getDetailedFallbackRecipe(fallbackRecipe);
    }
    
    try {
        // Try to fetch from API first
        const response = await fetch(`${API_URL_RECIPE_BY_ID}?id=${recipeId}`, {
            signal: AbortSignal.timeout(10000)
        });
        
        console.log(`Recipe API response status: ${response.status}`);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch recipe (Status: ${response.status})`);
        }
        
        const data = await response.json();
        console.log("Recipe API response received:", data);
        
        if (data && data.id) {
            return data;
        } else {
            throw new Error("Invalid recipe data received from API");
        }
    } catch (error) {
        console.error("Error fetching recipe by ID:", error);
        
        // Return a detailed fallback recipe if API fails
        return getDetailedFallbackRecipe({
            id: parseInt(recipeId.toString()),
            title: "Recipe Not Available",
            image: "https://via.placeholder.com/312x231?text=Recipe+Not+Available",
            cuisines: ["International"],
            diets: ["Various"],
            readyInMinutes: 30
        });
    }
};

// Helper function to create detailed recipe information for fallback recipes
const getDetailedFallbackRecipe = (recipe: any) => {
    const detailedRecipes = {
        101: {
            ...recipe,
            summary: "Delicious beef tacos with fresh toppings and warm tortillas. A classic Mexican dish that's perfect for any occasion.",
            ingredients: [
                { name: "Ground beef", amount: 1, unit: "lb" },
                { name: "Taco seasoning", amount: 1, unit: "packet" },
                { name: "Corn tortillas", amount: 8, unit: "pieces" },
                { name: "Lettuce", amount: 2, unit: "cups shredded" },
                { name: "Tomatoes", amount: 2, unit: "medium diced" },
                { name: "Cheese", amount: 1, unit: "cup shredded" },
                { name: "Sour cream", amount: 0.5, unit: "cup" }
            ],
            instructions: [
                "Brown the ground beef in a large skillet over medium-high heat.",
                "Add taco seasoning and water according to packet directions.",
                "Simmer for 5 minutes until sauce thickens.",
                "Warm tortillas in microwave or on griddle.",
                "Fill tortillas with beef mixture and desired toppings.",
                "Serve immediately with lime wedges."
            ]
        },
        102: {
            ...recipe,
            summary: "A flavorful and aromatic vegetable curry packed with nutrients and spices. Perfect for vegetarians and curry lovers.",
            ingredients: [
                { name: "Mixed vegetables", amount: 3, unit: "cups chopped" },
                { name: "Coconut milk", amount: 1, unit: "can" },
                { name: "Curry powder", amount: 2, unit: "tbsp" },
                { name: "Onion", amount: 1, unit: "large diced" },
                { name: "Garlic", amount: 3, unit: "cloves minced" },
                { name: "Ginger", amount: 1, unit: "tbsp fresh grated" },
                { name: "Vegetable oil", amount: 2, unit: "tbsp" }
            ],
            instructions: [
                "Heat oil in a large pot over medium heat.",
                "Sauté onion, garlic, and ginger until fragrant.",
                "Add curry powder and cook for 1 minute.",
                "Add vegetables and coconut milk.",
                "Simmer for 20-25 minutes until vegetables are tender.",
                "Season with salt and pepper to taste.",
                "Serve over rice or with naan bread."
            ]
        },
        103: {
            ...recipe,
            summary: "Creamy chicken alfredo pasta with tender chicken and rich parmesan sauce. A comforting Italian-American classic.",
            ingredients: [
                { name: "Chicken breast", amount: 2, unit: "pieces" },
                { name: "Fettuccine pasta", amount: 12, unit: "oz" },
                { name: "Heavy cream", amount: 1, unit: "cup" },
                { name: "Parmesan cheese", amount: 1, unit: "cup grated" },
                { name: "Butter", amount: 4, unit: "tbsp" },
                { name: "Garlic", amount: 3, unit: "cloves minced" }
            ],
            instructions: [
                "Cook pasta according to package directions.",
                "Season and cook chicken until golden brown.",
                "Slice chicken and set aside.",
                "Melt butter in the same pan, add garlic.",
                "Add cream and simmer until slightly thickened.",
                "Stir in parmesan cheese until melted.",
                "Toss pasta with sauce and top with chicken."
            ]
        },
        106: {
            ...recipe,
            summary: "Classic Caesar salad with crisp romaine lettuce, parmesan cheese, and creamy dressing.",
            ingredients: [
                { name: "Romaine lettuce", amount: 2, unit: "heads" },
                { name: "Parmesan cheese", amount: 0.5, unit: "cup grated" },
                { name: "Croutons", amount: 1, unit: "cup" },
                { name: "Caesar dressing", amount: 0.5, unit: "cup" },
                { name: "Lemon", amount: 1, unit: "piece" }
            ],
            instructions: [
                "Wash and chop romaine lettuce.",
                "Toss lettuce with Caesar dressing.",
                "Add croutons and parmesan cheese.",
                "Squeeze fresh lemon juice over salad.",
                "Serve immediately."
            ]
        }
    };
    
    return detailedRecipes[recipe.id] || {
        ...recipe,
        summary: `A delicious ${recipe.title.toLowerCase()} recipe with authentic flavors and fresh ingredients.`,
        ingredients: [
            { name: "Main ingredient", amount: 1, unit: "portion" },
            { name: "Seasonings", amount: 1, unit: "as needed" },
            { name: "Additional ingredients", amount: 1, unit: "as required" }
        ],
        instructions: [
            "Prepare all ingredients according to recipe requirements.",
            "Follow traditional cooking methods for this dish.",
            "Season to taste and serve hot.",
            "Enjoy your homemade meal!"
        ]
    };
};

// Function to fetch all recipes from MongoDB
export const getAllRecipesFromDB = async () => {
    try {
        console.log("Fetching all recipes from MongoDB");
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // Increased timeout to 10 seconds
        
        const response = await fetch(API_DB_RECIPES, { signal: controller.signal });
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch recipes from MongoDB (Status: ${response.status})`);
        }
        
        const data = await response.json();
        
        // If MongoDB returns empty results, try to get popular recipes from Spoonacular
        if (!data.results || data.results.length === 0) {
            console.log("MongoDB returned empty results, fetching popular recipes from Spoonacular");
            try {
                const spoonacularResponse = await fetch(API_URL);
                if (spoonacularResponse.ok) {
                    const spoonacularData = await spoonacularResponse.json();
                    console.log(`Fetched ${spoonacularData.results?.length || 0} popular recipes from Spoonacular`);
                    return spoonacularData;
                }
            } catch (spoonacularError) {
                console.error("Error fetching from Spoonacular:", spoonacularError);
            }
        }
        
        console.log(`Fetched ${data.results?.length || 0} recipes from MongoDB`);
        return data;
    } catch (error) {
        console.error("Error fetching recipes from MongoDB:", error);
        
        // If MongoDB fails, try to get popular recipes from Spoonacular
        console.log("MongoDB failed, trying Spoonacular API");
        try {
            const spoonacularResponse = await fetch(API_URL);
            if (spoonacularResponse.ok) {
                const spoonacularData = await spoonacularResponse.json();
                console.log(`Fetched ${spoonacularData.results?.length || 0} popular recipes from Spoonacular as fallback`);
                return spoonacularData;
            }
        } catch (spoonacularError) {
            console.error("Error fetching from Spoonacular:", spoonacularError);
        }
        
        // If both fail, return fallback recipes
        console.log("Both MongoDB and Spoonacular failed, returning fallback recipes");
        return {
            results: FALLBACK_RECIPES.slice(0, 12) // Return first 12 fallback recipes
        };
    }
};

export const getRecipeFromDB = async (recipeId: string) => {
    try {
        console.log(`Fetching recipe ${recipeId} from MongoDB`);
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(`${API_DB_RECIPES}/${recipeId}`, { signal: controller.signal });
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch recipe from MongoDB (Status: ${response.status})`);
        }
        
        const data = await response.json();
        console.log(`Fetched recipe ${recipeId} from MongoDB:`, data);
        return data;
    } catch (error) {
        console.error(`Error fetching recipe ${recipeId} from MongoDB:`, error);
        
        // Try to get from local storage as backup
        try {
            const localRecipes = localStorage.getItem('dietary-delight-recipes');
            const recipes = localRecipes ? JSON.parse(localRecipes) : [];
            const recipe = recipes.find((r: any) => r.id === recipeId);
            return recipe || null;
        } catch (localError) {
            console.error(`Error getting recipe ${recipeId} from local storage:`, localError);
            return null;
        }
    }
};

export const saveRecipeToDB = async (recipe: any) => {
    try {
        console.log(`Saving recipe ${recipe.id || recipe.title} to MongoDB:`, recipe);
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // Increased timeout to 10 seconds
        
        const response = await fetch(API_DB_RECIPES, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(recipe),
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Failed to save recipe to MongoDB (Status: ${response.status}):`, errorText);
            throw new Error(`Failed to save recipe to MongoDB (Status: ${response.status}): ${errorText}`);
        }
        
        const data = await response.json();
        console.log(`Saved recipe to MongoDB:`, data);
        return data;
    } catch (error) {
        console.error("Error saving recipe to MongoDB:", error);
        
        // Save to local storage as backup
        try {
            const localRecipes = localStorage.getItem('dietary-delight-recipes');
            const recipes = localRecipes ? JSON.parse(localRecipes) : [];
            const existingIndex = recipes.findIndex((r: any) => r.id === recipe.id);
            
            if (existingIndex >= 0) {
                recipes[existingIndex] = recipe;
            } else {
                recipes.push(recipe);
            }
            
            localStorage.setItem('dietary-delight-recipes', JSON.stringify(recipes));
            return { success: true, message: "Recipe saved to local storage" };
        } catch (localError) {
            console.error("Error saving recipe to local storage:", localError);
            return { success: false, error: localError.message };
        }
    }
};

export const updateRecipeInDB = async (recipeId: string, recipe: any) => {
    try {
        console.log(`Updating recipe ${recipeId} in MongoDB`);
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(`${API_DB_RECIPES}/${recipeId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(recipe),
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`Failed to update recipe in MongoDB (Status: ${response.status})`);
        }
        
        const data = await response.json();
        console.log(`Updated recipe in MongoDB:`, data);
        
        // Also update in local storage
        return saveRecipeToDB({...recipe, id: recipeId});
    } catch (error) {
        console.error(`Error updating recipe ${recipeId} in MongoDB:`, error);
        return saveRecipeToDB({...recipe, id: recipeId}); // Fall back to saving in localStorage
    }
};

export const deleteRecipeFromDB = async (recipeId: string) => {
    try {
        console.log(`Deleting recipe ${recipeId} from MongoDB`);
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(`${API_DB_RECIPES}/${recipeId}`, {
            method: 'DELETE',
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`Failed to delete recipe from MongoDB (Status: ${response.status})`);
        }
        
        const data = await response.json();
        console.log(`Deleted recipe from MongoDB:`, data);
        
        // Also delete from local storage
        try {
            const localRecipes = localStorage.getItem('dietary-delight-recipes');
            const recipes = localRecipes ? JSON.parse(localRecipes) : [];
            const filteredRecipes = recipes.filter((r: any) => r.id !== recipeId);
            
            localStorage.setItem('dietary-delight-recipes', JSON.stringify(filteredRecipes));
            return { success: true, message: "Recipe deleted from MongoDB and local storage" };
        } catch (localError) {
            console.error("Error deleting recipe from local storage:", localError);
            return { success: true, message: "Recipe deleted from MongoDB only" };
        }
    } catch (error) {
        console.error(`Error deleting recipe ${recipeId} from MongoDB:`, error);
        
        // Try to delete from local storage as backup
        try {
            const localRecipes = localStorage.getItem('dietary-delight-recipes');
            const recipes = localRecipes ? JSON.parse(localRecipes) : [];
            const filteredRecipes = recipes.filter((r: any) => r.id !== recipeId);
            
            localStorage.setItem('dietary-delight-recipes', JSON.stringify(filteredRecipes));
            return { success: true, message: "Recipe deleted from local storage" };
        } catch (localError) {
            console.error("Error deleting recipe from local storage:", localError);
            return { success: false, error: localError.message };
        }
    }
};
