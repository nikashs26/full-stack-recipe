
import React, { useState, useEffect } from 'react';
import { useToast } from "@/hooks/use-toast";
import { useQuery, useQueryClient } from '@tanstack/react-query';
import Header from '../components/Header';
import FilterBar from '../components/FilterBar';
import RecipeCard from '../components/RecipeCard';
import { loadRecipes, saveRecipes, deleteRecipe as deleteRecipeFromStorage } from '../utils/storage';
import { filterRecipes, getUniqueCuisines } from '../utils/recipeUtils';
import { fetchRecipes } from '../lib/spoonacular';
import { Recipe } from '../types/recipe';
import { SpoonacularRecipe } from '../types/spoonacular';
import { Loader2, Search, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

const RecipesPage: React.FC = () => {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [filteredRecipes, setFilteredRecipes] = useState<Recipe[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [externalSearchTerm, setExternalSearchTerm] = useState('');
  const [dietaryFilter, setDietaryFilter] = useState('');
  const [cuisineFilter, setCuisineFilter] = useState('');
  const [ingredientTerm, setIngredientTerm] = useState('');
  const [searchError, setSearchError] = useState<string | null>(null);
  const [cuisines, setCuisines] = useState<string[]>([]);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  useEffect(() => {
    const loadedRecipes = loadRecipes();
    setRecipes(loadedRecipes);
    setCuisines(getUniqueCuisines(loadedRecipes));
  }, []);

  useEffect(() => {
    const filtered = filterRecipes(recipes, searchTerm, dietaryFilter, cuisineFilter, ingredientTerm);
    setFilteredRecipes(filtered);
    setSearchError(null);
    
    if (searchTerm.trim() !== '' && filtered.length === 0) {
      setExternalSearchTerm(searchTerm);
    } else {
      setExternalSearchTerm('');
    }
  }, [recipes, searchTerm, dietaryFilter, cuisineFilter, ingredientTerm]);

  const { data: externalData, isLoading: isExternalLoading, isError, error } = useQuery({
    queryKey: ['recipes', externalSearchTerm, ingredientTerm],
    queryFn: () => fetchRecipes(externalSearchTerm, ingredientTerm),
    enabled: !!externalSearchTerm || !!ingredientTerm,
    retry: 1,
    staleTime: 60000,
    meta: {
      onError: (error: Error) => {
        console.error("Query error:", error);
        setSearchError(error.message || "Failed to fetch external recipes");
        toast({
          title: "Search Error",
          description: error.message || "There was a problem searching for recipes. Please try again.",
          variant: "destructive",
        });
      }
    }
  });

  // Handle errors from the query manually if needed
  useEffect(() => {
    if (isError && error instanceof Error) {
      console.error("Query error:", error);
      setSearchError(error.message || "Failed to fetch external recipes");
      toast({
        title: "Search Error",
        description: error.message || "There was a problem searching for recipes. Please try again.",
        variant: "destructive",
      });
    }
  }, [isError, error, toast]);

  const formatExternalRecipe = (recipe: SpoonacularRecipe): SpoonacularRecipe => {
    return {
      ...recipe,
      id: recipe.id || 0,
      title: recipe.title || "Untitled Recipe",
      image: recipe.image || '/placeholder.svg',
      cuisines: recipe.cuisines || [],
      diets: recipe.diets || [],
      readyInMinutes: recipe.readyInMinutes || 0
    };
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

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    if (!e.target.value.trim()) {
      setExternalSearchTerm('');
      setSearchError(null);
    }
  };

  const handleIngredientChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setIngredientTerm(e.target.value);
  };

  const retrySearch = () => {
    if (externalSearchTerm) {
      setSearchError(null);
      queryClient.invalidateQueries({ queryKey: ['recipes', externalSearchTerm, ingredientTerm] });
    }
  };

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
          onDietaryFilterChange={(e) => setDietaryFilter(e.target.value)}
          onCuisineFilterChange={(e) => setCuisineFilter(e.target.value)}
          onClearFilters={() => {
            setSearchTerm('');
            setDietaryFilter('');
            setCuisineFilter('');
            setIngredientTerm('');
            setExternalSearchTerm('');
            setSearchError(null);
          }}
          ingredientTerm={ingredientTerm}
          onIngredientChange={handleIngredientChange}
        />

        {searchError && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>
              {searchError}
              <button 
                onClick={retrySearch}
                className="ml-2 underline font-medium"
              >
                Try again
              </button>
            </AlertDescription>
          </Alert>
        )}

        {filteredRecipes.length === 0 && !externalSearchTerm && !isExternalLoading && !searchError && (
          <div className="text-center py-12">
            <Search className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-lg font-medium text-gray-900">No recipes found</h3>
            <p className="mt-1 text-gray-500">Try adjusting your search or filters to find recipes.</p>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredRecipes.map(recipe => (
            <RecipeCard 
              key={recipe.id} 
              recipe={recipe}
              onDelete={handleDeleteRecipe}
            />
          ))}

          {externalData?.results?.map((recipe: SpoonacularRecipe) => (
            <RecipeCard 
              key={`ext-${recipe.id}`} 
              recipe={formatExternalRecipe(recipe)}
              onDelete={() => {}}
              isExternal={true}
            />
          ))}
        </div>

        {isExternalLoading && (
          <div className="flex justify-center items-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary mr-2" />
            <span className="text-gray-600">Searching for recipes...</span>
          </div>
        )}

        {!isExternalLoading && externalData?.results?.length === 0 && externalSearchTerm && !searchError && (
          <div className="text-center py-12">
            <Search className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-lg font-medium text-gray-900">No external recipes found</h3>
            <p className="mt-1 text-gray-500">
              We couldn't find any external recipes matching your search. Try a different term.
            </p>
          </div>
        )}
      </main>
    </div>
  );
};

export default RecipesPage;
