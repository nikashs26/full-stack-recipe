import React, { useState } from "react";
import { fetchRecipes } from "src/lib/spoonacular.ts";

const RecipeSearch = () => {
    const [query, setQuery] = useState("");
    const [recipes, setRecipes] = useState<any[]>([]);
    const [error, setError] = useState<string | null>(null);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        try {
            const data = await fetchRecipes(query);
            setRecipes(data.results || []);
        } catch (err) {
            setError("Failed to fetch recipes. Please try again.");
        }
    };

    return (
        <div>
            <h1>Recipe Finder</h1>
            <form onSubmit={handleSearch}>
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search for a recipe..."
                        required
                    />
                    <button type="submit">Search</button>
            </form>

            {error && <p style={{ color: "red" }}>{error}</p>}

            <ul>
                {recipes.map((recipe) => (
                    <li key={recipe.id}>{recipe.title}</li>
                ))}
            </ul>
        </div>
    );
};

export default RecipeSearch;
