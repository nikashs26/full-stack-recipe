
const API_URL = "http://localhost:5000";

export const fetchRecipes = async (query: string) => {
    console.log(`Fetching recipes for query: "${query}"`);
    try {
        const response = await fetch(`${API_URL}/recipes?query=${encodeURIComponent(query)}`);
        console.log(`API response status: ${response.status}`);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            console.error("Error response:", errorData);
            throw new Error(errorData?.error || `Failed to fetch recipes (Status: ${response.status})`);
        }
        
        const data = await response.json();
        console.log("API response data:", data);
        
        // Check if we have results
        if (!data.results || data.results.length === 0) {
            console.log("No external recipes found");
            return { results: [] };
        }
        
        console.log(`Found ${data.results.length} external recipes`);
        return data;
    } catch (error) {
        console.error("Error fetching recipes:", error);
        // Return empty results rather than throwing to prevent app breaking
        return { results: [] };
    }
};
