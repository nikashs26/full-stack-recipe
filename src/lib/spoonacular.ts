
const API_URL = "http://localhost:5000";

export const fetchRecipes = async (query: string) => {
    try {
        const response = await fetch(`${API_URL}/recipes?query=${encodeURIComponent(query)}`);
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new Error(errorData?.error || "Failed to fetch recipes");
        }
        const data = await response.json();
        console.log("API response:", data); // Debug log
        return data;
    } catch (error) {
        console.error("Error fetching recipes:", error);
        // Return empty results rather than throwing to prevent app breaking
        return { results: [] };
    }
};
