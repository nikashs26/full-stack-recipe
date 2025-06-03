import React, { useState, useEffect } from 'react';
import { useToast } from "@/hooks/use-toast";
import { useQuery, useQueryClient } from '@tanstack/react-query';
import Header from '../components/Header';
import FilterBar from '../components/FilterBar';
import RecipeCard from '../components/RecipeCard';
import { loadRecipes, saveRecipes, deleteRecipe as deleteRecipeFromStorage, getLocalRecipes } from '../utils/storage';
import { filterRecipes, getUniqueCuisines, formatExternalRecipeCuisine, formatRecipeForDisplay } from '../utils/recipeUtils';
import { fetchRecipes, getAllRecipesFromDB } from '../lib/spoonacular';
import { Recipe } from '../types/recipe';
import { SpoonacularRecipe } from '../types/spoonacular';
import { Loader2, Search, AlertCircle, Database } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
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
  const [dbStatus, setDbStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [manualRecipes, setManualRecipes] = useState<any[]>([]);

  useEffect(() => {
    const localRecipes = getLocalRecipes();
    if (Array.isArray(localRecipes)) {
      setRecipes(localRecipes);
      setCuisines(getUniqueCuisines(localRecipes));
    }
    
    const fetchData = async () => {
      try {
        try {
          const dbResponse = await getAllRecipesFromDB();
          if (dbResponse && dbResponse.results && dbResponse.results.length > 0) {
            console.log("Successfully connected to MongoDB with results:", dbResponse.results.length);
            setDbStatus('connected');
            toast({
              title: "MongoDB Connected",
              description: `Successfully connected to MongoDB database with ${dbResponse.results.length} recipes`,
            });
          } else {
            console.log("MongoDB connected but no recipes found");
            setDbStatus('connected');
            toast({
              title: "MongoDB Connected",
              description: "Successfully connected to MongoDB database, but no recipes found",
            });
          }
        } catch (error) {
          console.error("MongoDB connection check failed:", error);
          setDbStatus('disconnected');
          toast({
            title: "MongoDB Disconnected",
            description: "Could not connect to MongoDB. Using local storage only.",
            variant: "destructive",
          });
        }
        
        try {
          const loadedRecipes = await loadRecipes();
          if (Array.isArray(loadedRecipes)) {
            setRecipes(loadedRecipes);
            setCuisines(getUniqueCuisines(loadedRecipes));
          }
        } catch (loadError) {
          console.error("Error loading recipes:", loadError);
        }
      } catch (error) {
        console.error("Error in fetchData:", error);
      }
    };
    
    fetchData();
    
    // Always trigger an external search on first load to populate external recipes
    setExternalSearchTerm('');
  }, [toast]);

  // Add useEffect to load manual recipes and seed if needed
  useEffect(() => {
    const loadManualRecipes = async () => {
      try {
        // Check and seed initial recipes if none exist
        await checkAndSeedInitialRecipes();
        
        // Then load all manual recipes
        const recipes = await fetchManualRecipes();
        setManualRecipes(recipes);
      } catch (error) {
        console.error('Error loading manual recipes:', error);
      }
    };
    
    loadManualRecipes();
  }, []);

  useEffect(() => {
    if (Array.isArray(recipes)) {
      const filtered = filterRecipes(recipes, searchTerm, dietaryFilter, cuisineFilter, ingredientTerm);
      setFilteredRecipes(filtered);
      setSearchError(null);
      
      // Only update external search when using the main search bar or when
      // empty to populate initial results - don't trigger external search for ingredient searches
      if (searchTerm || externalSearchTerm === '') {
        setExternalSearchTerm(searchTerm);
      }
    }
  }, [recipes, searchTerm, dietaryFilter, cuisineFilter, ingredientTerm]);

  // Combine local and external recipes into one unified list
  useEffect(() => {
    try {
      // Make sure to handle potential undefined values in the map functions
      const externalWithFlag = filteredExternalRecipes
        .filter(recipe => recipe) // Filter out any null/undefined recipes
        .map(recipe => ({
          ...recipe,
          isExternal: true
        }));
      
      const localWithFlag = filteredRecipes
        .filter(recipe => recipe) // Filter out any null/undefined recipes
        .map(recipe => ({
          ...recipe,
          isExternal: false
        }));
      
      const combined = [...localWithFlag, ...externalWithFlag];
      setCombinedRecipes(combined);
    } catch (error) {
      console.error("Error combining recipes:", error);
      // Set combined recipes to a safe default if there's an error
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
    // When ingredient search is used, trigger external API search
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
    enabled: true, // Always enable the query to show external recipes
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
        let filteredExternal = [...externalData.results].filter(recipe => recipe); // Filter out any null recipes
        
        if (dietaryFilter) {
          filteredExternal = filteredExternal.filter(recipe => 
            recipe.diets && Array.isArray(recipe.diets) && recipe.diets.some(diet => {
              // Safe null check before calling toLowerCase
              if (!diet) return false;
              return diet.toLowerCase().includes(dietaryFilter.toLowerCase());
            })
          );
        }
        
        if (cuisineFilter) {
          filteredExternal = filteredExternal.filter(recipe => 
            recipe.cuisines && Array.isArray(recipe.cuisines) && recipe.cuisines.some(cuisine => {
              // Safe null check before calling toLowerCase
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
          <div className="flex items-center gap-2">
            {dbStatus === 'checking' && (
              <Badge variant="outline" className="flex items-center gap-1 bg-yellow-50">
                <Loader2 className="h-3 w-3 animate-spin" /> Checking DB
              </Badge>
            )}
            {dbStatus === 'connected' && (
              <Badge variant="outline" className="flex items-center gap-1 bg-green-50 text-green-700">
                <Database className="h-3 w-3" /> MongoDB Connected
              </Badge>
            )}
            {dbStatus === 'disconnected' && (
              <Badge variant="outline" className="flex items-center gap-1 bg-red-50 text-red-700">
                <AlertCircle className="h-3 w-3" /> MongoDB Disconnected
              </Badge>
            )}
            <button 
              onClick={forceApiSearch}
              className="ml-2 text-xs bg-blue-500 hover:bg-blue-600 text-white py-1 px-2 rounded"
            >
              Search API Now
            </button>
          </div>
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

        {/* Manual Recipes Section */}
        {manualRecipes.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Your Manual Recipes</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {manualRecipes.map((recipe) => (
                <ManualRecipeCard 
                  key={recipe.id}
                  recipe={recipe}
                />
              ))}
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
            <span className="text-gray-600">
              {dbStatus === 'connected' 
                ? 'Searching in MongoDB and external sources...' 
                : 'Searching for recipes...'}
            </span>
          </div>
        )}
      </main>
    </div>
  );
};

export default RecipesPage;
