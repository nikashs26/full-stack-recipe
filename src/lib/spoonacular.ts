
const API_URL = "http://localhost:5000";

export const fetchRecipes = async (query: string) => {
    console.log(`Fetching recipes for query: "${query}"`);
    try {
        // Add a timeout to ensure the fetch doesn't hang indefinitely
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
        
        const response = await fetch(
            `${API_URL}/recipes?query=${encodeURIComponent(query)}`, 
            { signal: controller.signal }
        );
        clearTimeout(timeoutId);
        
        console.log(`API response status: ${response.status}`);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            console.error("Error response:", errorData);
            throw new Error(errorData?.error || `Failed to fetch recipes (Status: ${response.status})`);
        }
        
        const data = await response.json();
        console.log("API response data received:", data);
        
        // Validate the response structure
        if (!data || typeof data !== 'object') {
            console.error("Invalid API response format", data);
            return { results: [] };
        }
        
        // Check if we have results
        if (!data.results || !Array.isArray(data.results) || data.results.length === 0) {
            console.log("No external recipes found in response");
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
        // Return empty results rather than throwing to prevent app breaking
        return { results: [], error: error.message };
    }
};
