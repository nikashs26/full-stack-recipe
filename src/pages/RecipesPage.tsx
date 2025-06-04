import React, { useState, useEffect } from 'react';
import { useToast } from "@/hooks/use-toast";
import { useQuery, useQueryClient } from '@tanstack/react-query';
import Header from '../components/Header';
import FilterBar from '../components/FilterBar';
import RecipeCard from '../components/RecipeCard';
import { loadRecipes, saveRecipes, deleteRecipe as deleteRecipeFromStorage, getLocalRecipes } from '../utils/storage';
import { filterRecipes, getUniqueCuisines, formatExternalRecipeCuisine, formatRecipeForDisplay } from '../utils/recipeUtils';
import { fetchRecipes } from '../lib/spoonacular';
import { Recipe } from '../types/recipe';
import { SpoonacularRecipe } from '../types/spoonacular';
import { Loader2, Search, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import ManualRecipeCard from '../components/ManualRecipeCard';
import { fetchManualRecipes } from '../lib/manualRecipes';
import { checkAndSeedInitialRecipes } from '../lib/seedManualRecipes';

// Define a type that combines Recipe and SpoonacularRecipe with isExternal flag
type CombinedRecipe = (Recipe & { isExternal?: boolean }) | (SpoonacularRecipe & { isExternal: boolean });

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
  const [filteredExternalRecipes, setFilteredExternalRecipes] = useState<SpoonacularRecipe[]>([]);
  const [combinedRecipes, setCombinedRecipes] = useState<CombinedRecipe[]>([]);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch manual recipes with React Query
  const { data: manualRecipes = [], isLoading: isLoadingManual, error: manualError, refetch: refetchManual } = useQuery({
    queryKey: ['manual-recipes'],
    queryFn: fetchManualRecipes,
    retry: 1,
    staleTime: 60000
  });

  // Seed recipes on first load
  useEffect(() => {
    const seedRecipes = async () => {
      try {
        console.log('Attempting to seed initial recipes...');
        await checkAndSeedInitialRecipes();
        // Refetch manual recipes after seeding
        refetchManual();
      } catch (error) {
        console.error('Failed to seed recipes:', error);
      }
    };
    
    seedRecipes();
  }, [refetchManual]);

  useEffect(() => {
    if (manualError) {
      console.error('Error loading manual recipes:', manualError);
      toast({
        title: "Error loading popular recipes",
        description: "Could not load popular recipes from database",
        variant: "destructive",
      });
    }
  }, [manualError, toast]);

  // Fetch local recipes and load them into state
  useEffect(() => {
    const loadLocalRecipes = async () => {
      try {
        const localRecipes = getLocalRecipes();
        if (Array.isArray(localRecipes)) {
          setRecipes(localRecipes);
          setCuisines(getUniqueCuisines(localRecipes));
        }
        
        const loadedRecipes = await loadRecipes();
        if (Array.isArray(loadedRecipes)) {
          setRecipes(loadedRecipes);
          setCuisines(getUniqueCuisines(loadedRecipes));
        }
      } catch (error) {
        console.error("Error loading local recipes:", error);
      }
    };
    
    loadLocalRecipes();
    
    // Trigger an external search on first load to populate external recipes
    setExternalSearchTerm('');
  }, []);

  useEffect(() => {
    if (Array.isArray(recipes)) {
      const filtered = filterRecipes(recipes, searchTerm, dietaryFilter, cuisineFilter, ingredientTerm);
      setFilteredRecipes(filtered);
      setSearchError(null);
      
      // Only update external search when using the main search bar
      if (searchTerm || externalSearchTerm === '') {
        setExternalSearchTerm(searchTerm);
      }
    }
  }, [recipes, searchTerm, dietaryFilter, cuisineFilter, ingredientTerm]);

  // Combine local and external recipes into one unified list
  useEffect(() => {
    try {
      const externalWithFlag = filteredExternalRecipes
        .filter(recipe => recipe)
        .map(recipe => ({
          ...recipe,
          isExternal: true
        }));
      
      const localWithFlag = filteredRecipes
        .filter(recipe => recipe)
        .map(recipe => ({
          ...recipe,
          isExternal: false
        }));
      
      const combined = [...localWithFlag, ...externalWithFlag];
      setCombinedRecipes(combined);
    } catch (error) {
      console.error("Error combining recipes:", error);
      setCombinedRecipes([]);
    }
  }, [filteredRecipes, filteredExternalRecipes]);

  const handleDeleteRecipe = (id: string) => {
    if (!id) {
      console.error("Attempted to delete recipe with invalid ID");
      return;
    }
    
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
    if (e.target.value.trim()) {
      queryClient.invalidateQueries({ queryKey: ['recipes', externalSearchTerm, e.target.value] });
    }
  };

  const retrySearch = () => {
    if (externalSearchTerm || ingredientTerm) {
      setSearchError(null);
      queryClient.invalidateQueries({ queryKey: ['recipes', externalSearchTerm, ingredientTerm] });
    }
  };

  const { data: externalData, isLoading: isExternalLoading, isError, error } = useQuery({
    queryKey: ['recipes', externalSearchTerm, ingredientTerm],
    queryFn: () => {
      console.log("Executing query function for:", externalSearchTerm, ingredientTerm);
      return fetchRecipes(externalSearchTerm, ingredientTerm);
    },
    enabled: true,
    retry: 1,
    staleTime: 60000
  });

  useEffect(() => {
    if (isError && error instanceof Error) {
      console.error("Query error detected:", error);
      setSearchError(error.message || "Failed to fetch external recipes");
      toast({
        title: "Search Error",
        description: error.message || "There was a problem searching for recipes. Please try again.",
        variant: "destructive",
      });
    }
  }, [isError, error, toast]);

  useEffect(() => {
    if (externalData?.results) {
      try {
        let filteredExternal = [...externalData.results].filter(recipe => recipe);
        
        if (dietaryFilter) {
          filteredExternal = filteredExternal.filter(recipe => 
            recipe.diets && Array.isArray(recipe.diets) && recipe.diets.some(diet => {
              if (!diet) return false;
              return diet.toLowerCase().includes(dietaryFilter.toLowerCase());
            })
          );
        }
        
        if (cuisineFilter) {
          filteredExternal = filteredExternal.filter(recipe => 
            recipe.cuisines && Array.isArray(recipe.cuisines) && recipe.cuisines.some(cuisine => {
              if (!cuisine) return false;
              return cuisine.toLowerCase() === cuisineFilter.toLowerCase();
            })
          );
        }
        
        console.log("Setting filtered external recipes:", filteredExternal.length);
        setFilteredExternalRecipes(filteredExternal);
      } catch (error) {
        console.error("Error filtering external recipes:", error);
        setFilteredExternalRecipes([]);
      }
    } else {
      setFilteredExternalRecipes([]);
    }
  }, [externalData, dietaryFilter, cuisineFilter]);

  const forceApiSearch = () => {
    if (searchTerm.trim()) {
      setExternalSearchTerm(searchTerm);
      queryClient.invalidateQueries({ queryKey: ['recipes', searchTerm, ingredientTerm] });
    } else if (ingredientTerm.trim()) {
      setExternalSearchTerm('');
      queryClient.invalidateQueries({ queryKey: ['recipes', '', ingredientTerm] });
    } else {
      toast({
        title: "Search terms required",
        description: "Please enter a recipe name or ingredient to search",
      });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Recipe Collection</h1>
          <button 
            onClick={forceApiSearch}
            className="ml-2 text-xs bg-blue-500 hover:bg-blue-600 text-white py-1 px-2 rounded"
          >
            Search API Now
          </button>
        </div>
        
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

        {/* Popular Recipes Section */}
        {isLoadingManual ? (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Popular Recipes</h2>
            <div className="flex justify-center items-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
              <span className="ml-2 text-gray-600">Loading popular recipes...</span>
            </div>
          </div>
        ) : manualRecipes.length > 0 ? (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Popular Recipes</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {manualRecipes.map((recipe) => (
                <ManualRecipeCard 
                  key={recipe.id}
                  recipe={recipe}
                />
              ))}
            </div>
          </div>
        ) : (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Popular Recipes</h2>
            <div className="text-center py-8">
              <p className="text-gray-600">No popular recipes available. They should load automatically.</p>
            </div>
          </div>
        )}

        {combinedRecipes.length > 0 ? (
          <div className="grid grid-cols-1 gap-y-8">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Discovered Recipes</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {combinedRecipes.map((recipe, index) => (
                  <RecipeCard 
                    key={`recipe-${index}-${recipe?.id || index}`}
                    recipe={recipe}
                    onDelete={handleDeleteRecipe}
                    isExternal={!!recipe.isExternal}
                  />
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            {!isExternalLoading && (
              <div className="text-center py-12">
                <Search className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-lg font-medium text-gray-900">No recipes found</h3>
                <p className="mt-1 text-gray-500">
                  We couldn't find any recipes matching your search. Try different search terms or filters.
                </p>
              </div>
            )}
          </>
        )}

        {isExternalLoading && (
          <div className="flex justify-center items-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary mr-2" />
            <span className="text-gray-600">Searching for recipes...</span>
          </div>
        )}
      </main>
    </div>
  );
};

export default RecipesPage;
