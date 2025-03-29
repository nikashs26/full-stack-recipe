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
    const filtered = filterRecipes(recipes, searchTerm, dietaryFilter, cuisineFilter);
    setFilteredRecipes(filtered);
    
    // Only trigger external search if search term exists AND no local results
    if (searchTerm.trim() !== '' && filtered.length === 0) {
      console.log(`Setting external search term to "${searchTerm}" because no local results found`);
      setExternalSearchTerm(searchTerm);
    } else {
      setExternalSearchTerm('');
    }
  }, [recipes, searchTerm, dietaryFilter, cuisineFilter]);

  // Query for external recipes
  const { data: externalData, isLoading: isExternalLoading, isError, error } = useQuery({
    queryKey: ['recipes', externalSearchTerm],
    queryFn: () => {
      console.log(`Executing query for "${externalSearchTerm}"`);
      return fetchRecipes(externalSearchTerm);
    },
    enabled: !!externalSearchTerm,
    retry: 1,
    staleTime: 60000, // Cache results for 1 minute
  });

  // Handle errors
  useEffect(() => {
    if (isError) {
      console.error("External recipe query error:", error);
      toast({
        title: "Error fetching external recipes",
        description: `${(error as Error).message}`,
        variant: "destructive",
      });
    }
  }, [isError, error, toast]);

  // Debug log for external data
  useEffect(() => {
    if (externalData) {
      console.log("External recipe data received:", externalData);
      console.log("Results array:", externalData.results);
      console.log("Number of results:", externalData.results?.length || 0);
    }
  }, [externalData]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    console.log(`Search term changed to: "${value}"`);
    setSearchTerm(value);
    // Reset external search if user clears the search
    if (!value.trim()) {
      setExternalSearchTerm('');
    }
  };

  const handleDietaryFilter = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setDietaryFilter(e.target.value);
  };

  const handleCuisineFilter = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setCuisineFilter(e.target.value);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setDietaryFilter('');
    setCuisineFilter('');
    setExternalSearchTerm('');
  };

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

  // Function to convert Spoonacular recipe to our format for display
  const formatExternalRecipe = (recipe: SpoonacularRecipe): Recipe => ({
    id: `ext-${recipe.id}`,
    name: recipe.title,
    cuisine: "External",
    dietaryRestrictions: [],
    ingredients: [],
    instructions: [],
    image: recipe.image || '/placeholder.svg', // Fallback image
    ratings: [],
    comments: []
  });

  // Check if we have external results
  const hasExternalResults = externalData?.results && externalData.results.length > 0;
  
  console.log("Has external results:", hasExternalResults);
  if (hasExternalResults) {
    console.log("First external recipe:", externalData.results[0]);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Recipe Collection</h1>
        
        <FilterBar 
          searchTerm={searchTerm}
          dietaryFilter={dietaryFilter}
          cuisineFilter={cuisineFilter}
          cuisines={cuisines}
          onSearchChange={handleSearch}
          onDietaryFilterChange={handleDietaryFilter}
          onCuisineFilterChange={handleCuisineFilter}
          onClearFilters={clearFilters}
        />
        
        {/* Show local recipes if available */}
        {filteredRecipes.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredRecipes.map(recipe => (
              <RecipeCard 
                key={recipe.id} 
                recipe={recipe}
                onDelete={handleDeleteRecipe}
              />
            ))}
          </div>
        ) : (
          <>
            {/* Show loading state when searching externally */}
            {isExternalLoading ? (
              <div className="flex justify-center items-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <span className="ml-2 text-gray-600">Searching external recipes...</span>
              </div>
            ) : hasExternalResults ? (
              /* Show external results if available */
              <div>
                <h2 className="text-xl font-medium text-gray-800 mt-8 mb-4">External Recipes</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {externalData.results.map((recipe: SpoonacularRecipe) => (
                    <RecipeCard 
                      key={`ext-${recipe.id}`} 
                      recipe={formatExternalRecipe(recipe)}
                      onDelete={() => {}}
                      isExternal={true}
                    />
                  ))}
                </div>
              </div>
            ) : searchTerm ? (
              /* No results found */
              <div className="text-center py-12">
                <h2 className="text-xl font-medium text-gray-600">No recipes found</h2>
                <p className="text-gray-500 mt-2">Try adjusting your search or filters</p>
              </div>
            ) : (
              /* Empty state */
              <div className="text-center py-12">
                <h2 className="text-xl font-medium text-gray-600">No recipes available</h2>
                <p className="text-gray-500 mt-2">Start by adding your first recipe</p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default RecipesPage;
