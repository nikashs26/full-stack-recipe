
const API_URL = "http://localhost:5000";

export const fetchRecipes = async (query: string) => {
    try {
        const response = await fetch(`${API_URL}/recipes?query=${encodeURIComponent(query)}`);
        if (!response.ok) {
            throw new Error("API request failed");
        }
        return await response.json();
    } catch (error) {
        console.error("Error fetching recipes:", error);
        throw error;
    }
};
