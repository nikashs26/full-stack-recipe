
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { loadRecipes } from '../utils/storage';
import { fetchRecipes } from '../lib/spoonacular';
import { fetchManualRecipes } from '../lib/manualRecipes';
import { useAuth } from '../context/AuthContext';
import RecipeCard from './RecipeCard';
import ManualRecipeCard from './ManualRecipeCard';
import { Recipe } from '../types/recipe';
import { SpoonacularRecipe } from '../types/spoonacular';
import { ThumbsUp, Loader2 } from 'lucide-react';

const RecommendedRecipes: React.FC = () => {
  const { user } = useAuth();
  
  // Query for local recipes
  const { data: allRecipes = [], isLoading: isLocalLoading } = useQuery({
    queryKey: ['localRecipes'],
    queryFn: loadRecipes,
  });

  // Query for manual recipes
  const { data: manualRecipes = [], isLoading: isManualLoading } = useQuery({
    queryKey: ['manualRecipes'],
    queryFn: fetchManualRecipes,
  });

  const preferences = user?.preferences;

  // Query external recipes based on user preferences
  const externalQueries = useQuery({
    queryKey: ['recommendedExternalRecipes', preferences],
    queryFn: async () => {
      if (!preferences) return [];

      const allExternalRecipes: SpoonacularRecipe[] = [];
      const { favoriteCuisines = [] } = preferences;

      // Fetch recipes for favorite cuisines with more generous search
      if (favoriteCuisines.length > 0) {
        for (const cuisine of favoriteCuisines.slice(0, 3)) {
          try {
            const response = await fetchRecipes('', cuisine);
            if (response?.results) {
              allExternalRecipes.push(...response.results.slice(0, 8));
            }
          } catch (error) {
            console.error(`Error fetching recipes for cuisine "${cuisine}":`, error);
          }
        }
      }

      // If no preferences or limited results, fetch popular recipes
      if (allExternalRecipes.length < 6) {
        try {
          const response = await fetchRecipes('popular', '');
          if (response?.results) {
            allExternalRecipes.push(...response.results.slice(0, 12));
          }
        } catch (error) {
          console.error(`Error fetching popular recipes:`, error);
        }
      }
      
      return allExternalRecipes;
    },
    enabled: true, // Always fetch some recommendations
    staleTime: 300000,
  });

  // Combine and filter recipes
  const recommendedRecipes = React.useMemo(() => {
    const combinedRecipes: any[] = [];

    // Add local recipes (first 3)
    if (Array.isArray(allRecipes) && allRecipes.length > 0) {
      const localToAdd = allRecipes.slice(0, 3).map(recipe => ({ 
        ...recipe, 
        isExternal: false,
        type: 'local'
      }));
      combinedRecipes.push(...localToAdd);
    }

    // Add manual recipes (first 3)
    if (Array.isArray(manualRecipes) && manualRecipes.length > 0) {
      const manualToAdd = manualRecipes.slice(0, 3).map(recipe => ({ 
        ...recipe, 
        isExternal: false,
        type: 'manual'
      }));
      combinedRecipes.push(...manualToAdd);
    }

    // Add external recipes
    if (externalQueries.data && Array.isArray(externalQueries.data)) {
      // Simple filtering - just check if cuisine preference matches
      const filtered = preferences?.favoriteCuisines?.length > 0
        ? externalQueries.data.filter((recipe: SpoonacularRecipe) => 
            !preferences.favoriteCuisines || 
            preferences.favoriteCuisines.some(c => 
              recipe.cuisines?.some(cuisine => 
                cuisine?.toLowerCase().includes(c.toLowerCase())
              ) || 
              recipe.title?.toLowerCase().includes(c.toLowerCase())
            )
          )
        : externalQueries.data;

      const externalToAdd = (filtered || externalQueries.data).slice(0, 6).map(recipe => ({ 
        ...recipe, 
        isExternal: true,
        type: 'external'
      }));
      combinedRecipes.push(...externalToAdd);
    }

    // Remove duplicates and return first 9
    const uniqueRecipes = combinedRecipes.filter((recipe, index, self) => 
      index === self.findIndex(r => r.id === recipe.id)
    );

    return uniqueRecipes.slice(0, 9);
  }, [allRecipes, manualRecipes, externalQueries.data, preferences]);

  if (!user?.preferences) {
    return null;
  }

  const isLoading = isLocalLoading || isManualLoading || externalQueries.isLoading;

  // Skip recipe delete functionality on homepage
  const handleDeleteRecipe = () => {
    // Intentionally empty
  };

  return (
    <section className="mb-16">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold text-gray-900 flex items-center">
          <ThumbsUp className="mr-2 h-6 w-6 text-recipe-secondary" />
          Recommended for You
        </h2>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">
            Based on your preferences
          </span>
          <Link to="/recipes" className="text-recipe-primary hover:text-recipe-primary/80">
            View all →
          </Link>
        </div>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-64 bg-gray-200 animate-pulse rounded-lg flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ))
        ) : recommendedRecipes.length > 0 ? (
          recommendedRecipes.map((recipe, i) => {
            if (recipe.type === 'manual') {
              return (
                <ManualRecipeCard 
                  key={`manual-${recipe.id}-${i}`}
                  recipe={recipe}
                />
              );
            }
            return (
              <RecipeCard 
                key={`recommended-${recipe.id}-${i}`}
                recipe={recipe}
                isExternal={!!recipe.isExternal}
                onDelete={handleDeleteRecipe}
              />
            );
          })
        ) : (
          <div className="col-span-full text-center py-12 border border-dashed border-gray-300 rounded-lg">
            <p className="text-gray-500 mb-4">No recommended recipes available</p>
            <Link 
              to="/preferences" 
              className="text-recipe-primary hover:text-recipe-primary/80 underline"
            >
              Set your preferences to get recommendations
            </Link>
          </div>
        )}
      </div>
    </section>
  );
};

export default RecommendedRecipes;
