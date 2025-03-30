
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
  const [ingredientTerm, setIngredientTerm] = useState('');
  const [externalSearchTerm, setExternalSearchTerm] = useState('');
  const [externalIngredientTerm, setExternalIngredientTerm] = useState('');
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
    
    // Determine if we need external search
    const shouldSearchExternally = 
      (searchTerm.trim() !== '' || ingredientTerm.trim() !== '') && 
      (searchTerm.trim() !== externalSearchTerm || ingredientTerm.trim() !== externalIngredientTerm);
    
    if (shouldSearchExternally) {
      setExternalSearchTerm(searchTerm);
      setExternalIngredientTerm(ingredientTerm);
    }
  }, [recipes, searchTerm, ingredientTerm, dietaryFilter, cuisineFilter]);

  // Query for external recipes
  const { data: externalData, isLoading: isExternalLoading, isError, error } = useQuery({
    queryKey: ['recipes', externalSearchTerm, externalIngredientTerm],
    queryFn: () => fetchRecipes(externalSearchTerm, externalIngredientTerm),
    enabled: !!(externalSearchTerm || externalIngredientTerm),
    retry: 1,
    staleTime: 60000, // Cache results for 1 min
  });
  
  useEffect(() => {
    if (externalData) {
        console.log("External recipe data:", externalData);
        console.log("Results:", externalData.results);
    }
  }, [externalData]);

  // Handle API errors
  useEffect(() => {
    if (isError) {
      toast({
        title: "Error fetching external recipes",
        description: `${(error as Error).message}`,
        variant: "destructive",
      });
    }
  }, [isError, error, toast]);

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
  };

  const handleIngredientSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setIngredientTerm(e.target.value);
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setIngredientTerm('');
    setDietaryFilter('');
    setCuisineFilter('');
    setExternalSearchTerm('');
    setExternalIngredientTerm('');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Recipe Collection</h1>
        
        <FilterBar 
          searchTerm={searchTerm}
          ingredientTerm={ingredientTerm}
          dietaryFilter={dietaryFilter}
          cuisineFilter={cuisineFilter}
          cuisines={cuisines}
          onSearchChange={handleSearch}
          onIngredientChange={handleIngredientSearch}
          onDietaryFilterChange={(e) => setDietaryFilter(e.target.value)}
          onCuisineFilterChange={(e) => setCuisineFilter(e.target.value)}
          onClearFilters={handleClearFilters}
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

        {/* No results message */}
        {!isExternalLoading && filteredRecipes.length === 0 && (!externalData?.results || externalData.results.length === 0) && (
          <div className="text-center py-12">
            <p className="text-gray-500">No recipes found. Try adjusting your search criteria.</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default RecipesPage;
