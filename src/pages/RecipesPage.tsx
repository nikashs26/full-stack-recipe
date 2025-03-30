import React, { useState, useEffect } from 'react';
import { useToast } from "@/hooks/use-toast";
import { useQuery } from '@tanstack/react-query';
import Header from '../components/Header';
import FilterBar from '../components/FilterBar';
import RecipeCard from '../components/RecipeCard';
import { loadRecipes, saveRecipes, deleteRecipe as deleteRecipeFromStorage } from '../utils/storage';
import { filterRecipes, getUniqueCuisines } from '../utils/recipeUtils';
import { fetchRecipes } from '../lib/spoonacular';
import { Recipe } from '../types/recipe';
import { SpoonacularRecipe } from '../types/spoonacular';
import { Loader2 } from 'lucide-react';

const RecipesPage: React.FC = () => {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [filteredRecipes, setFilteredRecipes] = useState<Recipe[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [externalSearchTerm, setExternalSearchTerm] = useState('');
  const [dietaryFilter, setDietaryFilter] = useState('');
  const [cuisineFilter, setCuisineFilter] = useState('');
  const [ingredientTerm, setIngredientTerm] = useState('');  // Added state for ingredientTerm
  const [cuisines, setCuisines] = useState<string[]>([]);
  const { toast } = useToast();

  // Load recipes on component mount
  useEffect(() => {
    const loadedRecipes = loadRecipes();
    setRecipes(loadedRecipes);
    setCuisines(getUniqueCuisines(loadedRecipes));
  }, []);

  // Update filtered recipes when filters change
  useEffect(() => {
    const filtered = filterRecipes(recipes, searchTerm, dietaryFilter, cuisineFilter, ingredientTerm);  // Updated to pass ingredientTerm
    setFilteredRecipes(filtered);
    
    // Trigger external search if needed
    if (searchTerm.trim() !== '' && filtered.length === 0) {
      setExternalSearchTerm(searchTerm);
    } else {
      setExternalSearchTerm('');
    }
  }, [recipes, searchTerm, dietaryFilter, cuisineFilter, ingredientTerm]);  // Added ingredientTerm to dependency array

  // Query for external recipes
  const { data: externalData, isLoading: isExternalLoading, isError, error } = useQuery({
    queryKey: ['recipes', externalSearchTerm],
    queryFn: () => fetchRecipes(externalSearchTerm),
    enabled: !!externalSearchTerm,
    retry: 1,
    staleTime: 60000, // Cache results for 1 min
  });

  // Function to format external Spoonacular recipe
  const formatExternalRecipe = (recipe: SpoonacularRecipe): Recipe => ({
    id: `ext-${recipe.id}`,
    name: recipe.title,
    cuisine: "External",
    dietaryRestrictions: [],
    ingredients: [],
    instructions: [],
    image: recipe.image || '/placeholder.svg',
    ratings: [],
    comments: []
  });

  // Load more external recipes when button is clicked
  const loadMoreRecipes = async () => {
    if (!searchTerm.trim()) return;  // Don't fetch if searchTerm is empty
  
    try {
      // Show loading state if desired
      
      // Fetch more recipes from your backend
      const response = await fetch(`http://localhost:5000/get_recipes?query=${encodeURIComponent(searchTerm)}`);
      
      // Check if the response is OK
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Error response: ${response.status} ${response.statusText}`, errorText);
        throw new Error(`Error fetching recipes: ${response.statusText}`);
      }
      
      // Safely parse the response data as JSON
      let data;
      try {
        data = await response.json();
      } catch (parseError) {
        console.error("JSON parsing error:", parseError);
        console.error("Response text:", await response.text());
        throw new Error("Failed to parse response as JSON");
      }
      
      // Validate the data structure
      if (!data || !data.results) {
        console.error("Invalid data structure:", data);
        throw new Error("Invalid response format from API");
      }
      
      // Add the newly fetched recipes to the existing list
      setFilteredRecipes(prevRecipes => [
        ...prevRecipes,
        ...data.results.map(formatExternalRecipe)
      ]);
    } catch (error) {
      console.error("Error fetching more recipes:", error);
      toast({
        title: "Error",
        description: error.message || "There was an issue loading more recipes.",
        variant: "destructive",
      });
    }
  };
  

  // Delete local recipes
  const handleDeleteRecipe = (id: string) => {
    if (window.confirm('Are you sure you want to delete this recipe?')) {
      deleteRecipeFromStorage(id);
      const updatedRecipes = recipes.filter(recipe => recipe.id !== id);
      setRecipes(updatedRecipes);
      setCuisines(getUniqueCuisines(updatedRecipes));
      toast({
        title: "Recipe deleted",
        description: "The recipe has been successfully deleted.",
      });
    }
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    if (!e.target.value.trim()) setExternalSearchTerm('');
  };

  // Handler for ingredient change
  const handleIngredientChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setIngredientTerm(e.target.value);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Recipe Collection</h1>
        
        {/* Pass the required props for ingredient term */}
        <FilterBar 
          searchTerm={searchTerm}
          dietaryFilter={dietaryFilter}
          cuisineFilter={cuisineFilter}
          cuisines={cuisines}
          onSearchChange={handleSearch}
          onDietaryFilterChange={(e) => setDietaryFilter(e.target.value)}
          onCuisineFilterChange={(e) => setCuisineFilter(e.target.value)}
          onClearFilters={() => {
            setSearchTerm('');
            setDietaryFilter('');
            setCuisineFilter('');
            setIngredientTerm('');  // Clear ingredient filter too
            setExternalSearchTerm('');
          }}
          ingredientTerm={ingredientTerm}  // Pass ingredientTerm
          onIngredientChange={handleIngredientChange}  // Pass handler
        />

        {/* Display both local and external recipes */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Show local recipes first */}
          {filteredRecipes.map(recipe => (
            <RecipeCard 
              key={recipe.id} 
              recipe={recipe}
              onDelete={handleDeleteRecipe}
            />
          ))}

          {/* Show external recipes if available */}
          {externalData?.results?.map((recipe: SpoonacularRecipe) => (
            <RecipeCard 
              key={`ext-${recipe.id}`} 
              recipe={formatExternalRecipe(recipe)}
              onDelete={() => {}}
              isExternal={true}
            />
          ))}
        </div>

        {/* Loading state */}
        {isExternalLoading && (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <span className="ml-2 text-gray-600">Searching external recipes...</span>
          </div>
        )}

        {/* "Load More Recipes" button */}
        {externalData?.results?.length > 0 && (
          <div className="flex justify-center mt-6">
            <button 
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition"
              onClick={loadMoreRecipes}
            >
              Load More Recipes
            </button>
          </div>
        )}
      </main>
    </div>
  );
};

export default RecipesPage;
