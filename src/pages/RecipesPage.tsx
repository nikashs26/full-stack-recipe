import React, { useState, useEffect } from 'react';
import { useToast } from "@/hooks/use-toast";
import { useQuery, useQueryClient } from '@tanstack/react-query';
import Header from '../components/Header';
import FilterBar from '../components/FilterBar';
import RecipeCard from '../components/RecipeCard';
import { loadRecipes, saveRecipes, deleteRecipe as deleteRecipeFromStorage, getLocalRecipes } from '../utils/storage';
import { filterRecipes, getUniqueCuisines } from '../utils/recipeUtils';
import { fetchRecipes, getAllRecipesFromDB } from '../lib/spoonacular';
import { Recipe } from '../types/recipe';
import { SpoonacularRecipe } from '../types/spoonacular';
import { Loader2, Search, AlertCircle, Database } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";

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
  const [dbStatus, setDbStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const { toast } = useToast();
  const queryClient = useQueryClient();

  useEffect(() => {
    const localRecipes = getLocalRecipes();
    if (Array.isArray(localRecipes)) {
      setRecipes(localRecipes);
      setCuisines(getUniqueCuisines(localRecipes));
    }
    
    const fetchData = async () => {
      try {
        try {
          await getAllRecipesFromDB();
          setDbStatus('connected');
          toast({
            title: "MongoDB Connected",
            description: "Successfully connected to MongoDB database",
          });
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
  }, [toast]);

  useEffect(() => {
    if (Array.isArray(recipes)) {
      const filtered = filterRecipes(recipes, searchTerm, dietaryFilter, cuisineFilter, ingredientTerm);
      setFilteredRecipes(filtered);
      setSearchError(null);
      
      if (searchTerm.trim() !== '' && filtered.length === 0) {
        setExternalSearchTerm(searchTerm);
      } else {
        setExternalSearchTerm('');
      }
    }
  }, [recipes, searchTerm, dietaryFilter, cuisineFilter, ingredientTerm]);

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

  const { data: externalData, isLoading: isExternalLoading, isError, error } = useQuery({
    queryKey: ['recipes', externalSearchTerm, ingredientTerm],
    queryFn: () => {
      console.log("Executing query function for:", externalSearchTerm, ingredientTerm);
      return fetchRecipes(externalSearchTerm, ingredientTerm);
    },
    enabled: !!(externalSearchTerm || ingredientTerm),
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
      let filteredExternal = [...externalData.results];
      
      if (dietaryFilter) {
        filteredExternal = filteredExternal.filter(recipe => 
          recipe.diets && recipe.diets.some(diet => 
            diet.toLowerCase().includes(dietaryFilter.toLowerCase())
          )
        );
      }
      
      if (cuisineFilter) {
        filteredExternal = filteredExternal.filter(recipe => 
          recipe.cuisines && recipe.cuisines.some(cuisine => 
            cuisine.toLowerCase() === cuisineFilter.toLowerCase()
          )
        );
      }
      
      console.log("Setting filtered external recipes:", filteredExternal.length);
      setFilteredExternalRecipes(filteredExternal);
    } else {
      setFilteredExternalRecipes([]);
    }
  }, [externalData, dietaryFilter, cuisineFilter]);

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

  const forceApiSearch = () => {
    if (searchTerm.trim() || ingredientTerm.trim()) {
      setExternalSearchTerm(searchTerm);
      queryClient.invalidateQueries({ queryKey: ['recipes', searchTerm, ingredientTerm] });
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

        {filteredRecipes.length === 0 && filteredExternalRecipes.length === 0 && !isExternalLoading && !searchError && (
          <div className="text-center py-12">
            <Search className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-lg font-medium text-gray-900">No recipes found</h3>
            <p className="mt-1 text-gray-500">Try adjusting your search or filters to find recipes.</p>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.isArray(filteredRecipes) && filteredRecipes.map(recipe => (
            <RecipeCard 
              key={recipe.id} 
              recipe={recipe}
              onDelete={handleDeleteRecipe}
            />
          ))}

          {Array.isArray(filteredExternalRecipes) && filteredExternalRecipes.map((recipe: SpoonacularRecipe) => (
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
            <span className="text-gray-600">
              {dbStatus === 'connected' 
                ? 'Searching in MongoDB and external sources...' 
                : 'Searching for recipes...'}
            </span>
          </div>
        )}

        {!isExternalLoading && externalData?.results?.length === 0 && externalSearchTerm && !searchError && (
          <div className="text-center py-12">
            <Search className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-lg font-medium text-gray-900">No recipes found</h3>
            <p className="mt-1 text-gray-500">
              We couldn't find any recipes matching your search in {dbStatus === 'connected' ? 'MongoDB or external sources' : 'external sources'}. Try a different term.
            </p>
          </div>
        )}
      </main>
    </div>
  );
};

export default RecipesPage;
