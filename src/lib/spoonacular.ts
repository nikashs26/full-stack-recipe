
const API_DB_RECIPES = "http://127.0.0.1:5000/recipes";
const API_DB_RECIPE_BY_ID = "http://127.0.0.1:5000/recipes";
const API_URL = "http://127.0.0.1:5000/get_recipes";
const API_URL_RECIPE_BY_ID = "http://127.0.0.1:5000/get_recipe_by_id";

export const fetchRecipes = async (query: string = "", ingredient: string = "") => {
    console.log(`Fetching recipes with query: "${query}" and ingredient: "${ingredient}"`);
    
    // Try the API endpoint first which will prioritize MongoDB before making API calls
    try {
        // Build the URL with appropriate parameters
        let url = `${API_URL}?`;
        if (query) url += `query=${encodeURIComponent(query)}&`;
        if (ingredient) url += `ingredient=${encodeURIComponent(ingredient)}&`;
        
        console.log("Trying recipe API URL:", url);
        
        // Short timeout to prevent UI hanging
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10-second timeout
        
        const response = await fetch(
            url.slice(0, -1), // Remove trailing & or ?
            { signal: controller.signal }
        );

        clearTimeout(timeoutId); // Prevent timeout from executing if request succeeds
        
        console.log(`API response status: ${response.status}`);

        if (!response.ok) {
            try {
                const errorData = await response.json();
                console.error("Error response:", errorData);
                throw new Error(errorData?.error || `Failed to fetch recipes (Status: ${response.status})`);
            } catch (parseError) {
                // If we can't parse as JSON, it might be HTML or plain text
                const textResponse = await response.text();
                console.error("Non-JSON error response:", textResponse.substring(0, 200));
                throw new Error(`Failed to fetch recipes (Status: ${response.status})`);
            }
        }
        
        // Try to parse the JSON response safely
        let data;
        try {
            data = await response.json();
            console.log("API response data received:", data);
        } catch (parseError) {
            console.error("JSON parsing error:", parseError);
            const textResponse = await response.text();
            console.error("Invalid JSON response:", textResponse.substring(0, 200));
            throw new Error("Failed to parse API response as JSON");
        }
    
        if (!data || typeof data !== 'object' || !Array.isArray(data.results)) {
            console.error("Invalid API response format", data);
            return { results: [] };
        }

        console.log(`Found ${data.results.length} recipes`);
        return data;
    } catch (error) {
        if (error.name === 'AbortError') {
            console.error("Request timeout while fetching recipes");
            throw new Error("Request timed out while fetching recipes");
        }
        console.error("Error fetching recipes:", error);
        throw error;
    }
};

export const fetchRecipeById = async (recipeId: number) => {
    console.log(`Fetching recipe details for ID: ${recipeId}`);
    
    if (!recipeId) {
        console.error("Recipe ID is required");
        throw new Error("Recipe ID is required");
    }
    
    // Try the API endpoint directly - MongoDB will be checked first
    try {
        // Timeout setup to prevent hanging requests
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10-second timeout
        
        const url = `${API_URL_RECIPE_BY_ID}?id=${recipeId}`;
        console.log("Fetching recipe details from:", url);
        
        const response = await fetch(url, { signal: controller.signal });
        clearTimeout(timeoutId);
        
        console.log(`API response status for recipe ${recipeId}: ${response.status}`);

        if (!response.ok) {
            try {
                const errorData = await response.json();
                console.error("Error response:", errorData);
                throw new Error(errorData?.error || `Failed to fetch recipe details (Status: ${response.status})`);
            } catch (parseError) {
                // If we can't parse as JSON, it might be HTML or plain text
                const textResponse = await response.text();
                console.error("Non-JSON error response:", textResponse.substring(0, 200));
                throw new Error(`Failed to fetch recipe details (Status: ${response.status})`);
            }
        }
        
        // Try to parse the JSON response safely
        let data;
        try {
            data = await response.json();
            console.log("Recipe details received:", data);
        } catch (parseError) {
            console.error("JSON parsing error:", parseError);
            const textResponse = await response.text();
            console.error("Invalid JSON response:", textResponse.substring(0, 200));
            throw new Error("Failed to parse API response as JSON");
        }
        
        if (!data || typeof data !== 'object') {
            console.error("Invalid API response format for recipe details", data);
            throw new Error("Invalid recipe data received");
        }

        return data;
    } catch (error) {
        if (error.name === 'AbortError') {
            console.error("Request timeout while fetching recipe details");
            throw new Error("Request timed out while fetching recipe details");
        }
        console.error("Error fetching recipe details:", error);
        throw error;
    }
};

// Keep the saveRecipeToDB and deleteRecipeFromDB functions
export const saveRecipeToDB = async (recipe: any) => {
    try {
        const response = await fetch(API_DB_RECIPES, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(recipe),
        });
        
        if (!response.ok) {
            throw new Error(`Failed to save recipe (Status: ${response.status})`);
        }
        
        return await response.json();
    } catch (error) {
        console.error("Error saving recipe to database:", error);
        throw error;
    }
};

export const deleteRecipeFromDB = async (recipeId: string) => {
    try {
        const response = await fetch(`${API_DB_RECIPES}/${recipeId}`, {
            method: 'DELETE',
        });
        
        if (!response.ok) {
            throw new Error(`Failed to delete recipe (Status: ${response.status})`);
        }
        
        return await response.json();
    } catch (error) {
        console.error("Error deleting recipe from database:", error);
        throw error;
    }
};
