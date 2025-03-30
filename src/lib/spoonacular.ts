const API_URL = "http://127.0.0.1:8080/get_recipes";

export const fetchRecipes = async (query: string) => {
    console.log(`Fetching recipes for query: "${query}"`);
    
    try {
        // Timeout setup to prevent hanging requests
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10-second timeout
        
        // ✅ FIXED: Removed "/recipes" since API_URL already contains "/get_recipes"
        const response = await fetch(
            `${API_URL}?query=${encodeURIComponent(query)}`, 
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