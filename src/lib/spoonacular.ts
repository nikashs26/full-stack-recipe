
const API_URL = "http://127.0.0.1:8080/get_recipes";
const API_URL_RECIPE_BY_ID = "http://127.0.0.1:8080/get_recipe_by_id";

export const fetchRecipes = async (query: string = "", ingredient: string = "") => {
    console.log(`Fetching recipes with query: "${query}" and ingredient: "${ingredient}"`);
    
    // Validate that at least one parameter is provided
    if (!query && !ingredient) {
        console.error("Either query or ingredient must be provided");
        return { results: [] };
    }
    
    try {
        // Timeout setup to prevent hanging requests
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10-second timeout
        
        // Build the URL with appropriate parameters
        let url = `${API_URL}?`;
        if (query) url += `query=${encodeURIComponent(query)}&`;
        if (ingredient) url += `ingredient=${encodeURIComponent(ingredient)}&`;
        
        const response = await fetch(
            url.slice(0, -1), // Remove trailing & or ?
            { signal: controller.signal }
        );

        clearTimeout(timeoutId); // Prevent timeout from executing if request succeeds
        
        console.log(`API response status: ${response.status}`);

        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            console.error("Error response:", errorData);
            throw new Error(errorData?.error || `Failed to fetch recipes (Status: ${response.status})`);
        }
        
        const data = await response.json();
        console.log("API response data received:", data);

    
        if (!data || typeof data !== 'object' || !Array.isArray(data.results)) {
            console.error("Invalid API response format", data);
            return { results: [] };
        }

        console.log(`Found ${data.results.length} external recipes`);
        return data;
    } catch (error) {
        if (error.name === 'AbortError') {
            console.error("Request timeout while fetching recipes");
            return { results: [], error: "Request timed out" };
        }
        console.error("Error fetching recipes:", error);
        return { results: [], error: error.message };
    }
};

export const fetchRecipeById = async (recipeId: number) => {
    console.log(`Fetching recipe details for ID: ${recipeId}`);
    
    if (!recipeId) {
        console.error("Recipe ID is required");
        throw new Error("Recipe ID is required");
    }
    
    try {
        // Timeout setup to prevent hanging requests
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15-second timeout
        
        const url = `${API_URL_RECIPE_BY_ID}?id=${recipeId}`;
        
        const response = await fetch(url, { signal: controller.signal });
        clearTimeout(timeoutId);
        
        console.log(`API response status for recipe ${recipeId}: ${response.status}`);

        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            console.error("Error response:", errorData);
            throw new Error(errorData?.error || `Failed to fetch recipe details (Status: ${response.status})`);
        }
        
        const data = await response.json();
        console.log("Recipe details received:", data);
        
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
