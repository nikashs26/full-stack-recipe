const API_DB_RECIPES = "http://127.0.0.1:5000/recipes";
const API_DB_RECIPE_BY_ID = "http://127.0.0.1:5000/recipes";
const API_URL = "http://127.0.0.1:5000/get_recipes";
const API_URL_RECIPE_BY_ID = "http://127.0.0.1:5000/get_recipe_by_id";

export const fetchRecipes = async (query: string = "", ingredient: string = "") => {
    console.log(`Fetching recipes with query: "${query}" and ingredient: "${ingredient}"`);
    
    // Always try MongoDB first
    try {
        const params = new URLSearchParams();
        if (query) params.append('query', query);
        if (ingredient) params.append('ingredient', ingredient);
        
        const url = `${API_DB_RECIPES}${params.toString() ? '?' + params.toString() : ''}`;
        console.log("Trying MongoDB URL:", url);
        
        const response = await fetch(url, { 
            signal: AbortSignal.timeout(3000) // Short timeout for DB calls
        });
        
        if (!response.ok) {
            throw new Error(`Failed to fetch recipes from database (Status: ${response.status})`);
        }
        
        const data = await response.json();
        console.log(`Found ${data.results?.length || 0} recipes in database`);
        
        if (data.results?.length > 0) {
            return data;
        }
        
        // If no results from MongoDB but we have search terms, fall back to API
        if ((query || ingredient) && data.results?.length === 0) {
            console.log("No results from MongoDB, falling back to API");
            return fetchFromAPI(query, ingredient);
        }
        
        return data;
    } catch (error) {
        console.error("Error fetching recipes from database:", error);
        
        // Only fallback to API if we have search terms
        if (query || ingredient) {
            console.log("Error with MongoDB, falling back to API");
            return fetchFromAPI(query, ingredient);
        }
        
        return { results: [] };
    }
};

const fetchFromAPI = async (query: string = "", ingredient: string = "") => {
    try {
        // Short timeout to prevent UI hanging
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5-second timeout
        
        // Build the URL with appropriate parameters
        let url = `${API_URL}?`;
        if (query) url += `query=${encodeURIComponent(query)}&`;
        if (ingredient) url += `ingredient=${encodeURIComponent(ingredient)}&`;
        
        console.log("Trying API URL:", url);
        
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

        console.log(`Found ${data.results.length} external recipes`);
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
    
    // Try MongoDB first
    try {
        console.log(`Trying to fetch recipe ${recipeId} from MongoDB`);
        const url = `${API_DB_RECIPE_BY_ID}/${recipeId}`;
        
        const response = await fetch(url, { 
            signal: AbortSignal.timeout(3000) // Short timeout for DB calls
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log("Recipe details received from MongoDB:", data);
            return data;
        }
        
        // If not found in MongoDB, fall back to API
        console.log(`Recipe ${recipeId} not found in MongoDB, trying API`);
    } catch (error) {
        console.error("Error fetching recipe from MongoDB:", error);
    }
    
    // Fallback to API
    try {
        // Timeout setup to prevent hanging requests
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5-second timeout
        
        const url = `${API_URL_RECIPE_BY_ID}?id=${recipeId}`;
        
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
            console.log("Recipe details received from API:", data);
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
