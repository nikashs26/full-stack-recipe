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
  const [ingredientTerm, setIngredientTerm] = useState('');
  const [cuisines, setCuisines] = useState<string[]>([]);
  const { toast } = useToast();

  useEffect(() => {
    const loadedRecipes = loadRecipes();
    setRecipes(loadedRecipes);
    setCuisines(getUniqueCuisines(loadedRecipes));
  }, []);

  useEffect(() => {
    const filtered = filterRecipes(recipes, searchTerm, dietaryFilter, cuisineFilter, ingredientTerm);
    setFilteredRecipes(filtered);
    
    if (searchTerm.trim() !== '' && filtered.length === 0) {
      setExternalSearchTerm(searchTerm);
    } else {
      setExternalSearchTerm('');
    }
  }, [recipes, searchTerm, dietaryFilter, cuisineFilter, ingredientTerm]);

  const { data: externalData, isLoading: isExternalLoading, isError, error } = useQuery({
    queryKey: ['recipes', externalSearchTerm],
    queryFn: () => fetchRecipes(externalSearchTerm),
    enabled: !!externalSearchTerm,
    retry: 1,
    staleTime: 60000,
  });

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

  const loadMoreRecipes = async () => {
    if (!searchTerm.trim()) return;

    try {
      const response = await fetch(`http://localhost:5000/get_recipes?query=${encodeURIComponent(searchTerm)}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Error response: ${response.status} ${response.statusText}`, errorText);
        throw new Error(`Error fetching recipes: ${response.statusText}`);
      }

      let data;
      try {
        data = await response.json();
      } catch (parseError) {
        console.error("JSON parsing error:", parseError);
        console.error("Response text:", await response.text());
        throw new Error("Failed to parse response as JSON");
      }

      if (!data || !data.results) {
        console.error("Invalid data structure:", data);
        throw new Error("Invalid response format from API");
      }

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

  const handleIngredientChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setIngredientTerm(e.target.value);
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
          }}
          ingredientTerm={ingredientTerm}
          onIngredientChange={handleIngredientChange}
        />

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
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <span className="ml-2 text-gray-600">Searching external recipes...</span>
          </div>
        )}

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
