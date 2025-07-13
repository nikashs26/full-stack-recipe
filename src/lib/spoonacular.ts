// URLs for API endpoints - fallback to mock data when not available
const API_DB_RECIPES = "http://localhost:5001/recipes";
const API_URL = "http://localhost:5001/get_recipes";
const API_URL_RECIPE_BY_ID = "http://localhost:5001/get_recipe_by_id";

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
    diets: ["Vegatarian"],
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
}

];

export const fetchRecipes = async (query: string = "", ingredient: string = "") => {
    console.log(`Fetching recipes with query: "${query}" and ingredient: "${ingredient}"`);
    
    if (!query && !ingredient) {
        console.log("No search criteria provided, returning empty results");
        return { results: [] };
    }
    
    // Try the API endpoint first which will prioritize MongoDB before making API calls
    try {
        // Build the URL with appropriate parameters
        let url = `${API_URL}?`;
        if (query) url += `query=${encodeURIComponent(query)}&`;
        if (ingredient) url += `ingredient=${encodeURIComponent(ingredient)}&`;
        
        console.log("Calling recipe API URL:", url);
        
        // Short timeout to prevent UI hanging
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 20000); // Increased timeout to 20 seconds
        
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

            console.log(`Found ${data.results.length} recipes from MongoDB/API`);
            return data;
        } catch (fetchError) {
            // API fetch failed, use fallback data
            console.log("API fetch failed, using fallback data", fetchError);
            
            // Filter the fallback data based on the search query
            const filteredResults = FALLBACK_RECIPES.filter(recipe => {
                const matchesQuery = query ? 
                    recipe.title.toLowerCase().includes(query.toLowerCase()) : 
                    true;
                    
                const matchesIngredient = ingredient ? 
                    // This is a simplification as we don't have ingredients in our fallback data
                    true : 
                    true;
                    
                return matchesQuery && matchesIngredient;
            });
            
            return { 
                results: filteredResults,
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
            results: FALLBACK_RECIPES,
            status: "fallback",
            message: "Using fallback data as API is unavailable" 
        };
    }
};

export const fetchRecipeById = async (recipeId: number | string) => {
    console.log(`Fetching recipe details for ID: ${recipeId}`);
    
    if (!recipeId) {
        console.error("Recipe ID is required");
        throw new Error("Recipe ID is required");
    }
    
    // First check if the recipe exists in our fallback data
    const fallbackRecipe = FALLBACK_RECIPES.find(r => r.id.toString() === recipeId.toString());
    
    // Try the API endpoint directly - MongoDB will be checked first
    try {
        // Timeout setup to prevent hanging requests
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5-second timeout
        
        const url = `${API_URL_RECIPE_BY_ID}?id=${recipeId}`;
        console.log("Fetching recipe details from:", url);
        
        try {
            const response = await fetch(url, { signal: controller.signal });
            clearTimeout(timeoutId);
            
            console.log(`API response status for recipe ${recipeId}: ${response.status}`);

            if (!response.ok) {
                throw new Error(`Failed to fetch recipe details (Status: ${response.status})`);
            }
            
            const data = await response.json();
            console.log("Recipe details received:", data);
            
            if (!data || typeof data !== 'object') {
                console.error("Invalid API response format for recipe details", data);
                throw new Error("Invalid recipe data received");
            }

            return data;
        } catch (fetchError) {
            console.log("API fetch failed for recipe details, using fallback data if available", fetchError);
            
            if (fallbackRecipe) {
                // Create a more complete recipe object from our minimal fallback data
                return {
                    ...fallbackRecipe,
                    instructions: "This is fallback recipe data as the API is unavailable.",
                    extendedIngredients: [
                        { name: "Ingredient 1", amount: 1, unit: "cup", originalString: "1 cup of Ingredient 1" },
                        { name: "Ingredient 2", amount: 2, unit: "tbsp", originalString: "2 tbsp of Ingredient 2" }
                    ],
                    analyzedInstructions: [{
                        name: "",
                        steps: [
                            { number: 1, step: "This is a placeholder step 1." },
                            { number: 2, step: "This is a placeholder step 2." }
                        ]
                    }]
                };
            } else {
                throw new Error("Recipe not found in fallback data");
            }
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.error("Request timeout while fetching recipe details");
        } else {
            console.error("Error fetching recipe details:", error);
        }
        
        // If we have a fallback recipe, return it
        if (fallbackRecipe) {
            return {
                ...fallbackRecipe,
                instructions: "This is fallback recipe data as the API is unavailable.",
                extendedIngredients: [
                    { name: "Ingredient 1", amount: 1, unit: "cup", originalString: "1 cup of Ingredient 1" },
                    { name: "Ingredient 2", amount: 2, unit: "tbsp", originalString: "2 tbsp of Ingredient 2" }
                ],
                analyzedInstructions: [{
                    name: "",
                    steps: [
                        { number: 1, step: "This is a placeholder step 1." },
                        { number: 2, step: "This is a placeholder step 2." }
                    ]
                }]
            };
        } else {
            throw new Error("Recipe not found and API is unavailable");
        }
    }
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
        console.log(`Fetched ${data.results?.length || 0} recipes from MongoDB`);
        return data;
    } catch (error) {
        console.error("Error fetching recipes from MongoDB:", error);
        
        // Try to get from local storage as backup
        try {
            const localRecipes = localStorage.getItem('dietary-delight-recipes');
            return { results: localRecipes ? JSON.parse(localRecipes) : [] };
        } catch (localError) {
            console.error("Error getting recipes from local storage:", localError);
            return { results: [] };
        }
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
