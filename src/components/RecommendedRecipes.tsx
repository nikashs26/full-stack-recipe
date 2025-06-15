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

  // Query external recipes based on user preferences - avoid fallback data
  const externalQueries = useQuery({
    queryKey: ['recommendedExternalRecipes', preferences],
    queryFn: async () => {
      if (!preferences) {
        // Try to get popular recipes without fallback
        const response = await fetchRecipes('popular', '');
        return response?.results || [];
      }

      const allExternalRecipes: SpoonacularRecipe[] = [];
      const { favoriteCuisines = [], dietaryRestrictions = [] } = preferences;

      // Fetch recipes for favorite cuisines
      if (favoriteCuisines.length > 0) {
        for (const cuisine of favoriteCuisines.slice(0, 3)) {
          try {
            console.log(`Fetching recipes for cuisine: ${cuisine}`);
            const response = await fetchRecipes('', cuisine);
            if (response?.results && Array.isArray(response.results)) {
              // Filter out hardcoded fallback recipes
              const realRecipes = response.results.filter(recipe => 
                recipe.id > 1000 && // Fallback recipes have low IDs
                recipe.title && 
                !recipe.title.toLowerCase().includes('fallback') &&
                recipe.image && 
                recipe.image.includes('http')
              );
              allExternalRecipes.push(...realRecipes.slice(0, 6));
            }
          } catch (error) {
            console.error(`Error fetching recipes for cuisine "${cuisine}":`, error);
          }
        }
      }

      // Fetch recipes for dietary restrictions
      if (dietaryRestrictions.length > 0) {
        for (const diet of dietaryRestrictions.slice(0, 2)) {
          try {
            console.log(`Fetching recipes for diet: ${diet}`);
            const response = await fetchRecipes(diet, '');
            if (response?.results && Array.isArray(response.results)) {
              const realRecipes = response.results.filter(recipe => 
                recipe.id > 1000 &&
                recipe.title && 
                !recipe.title.toLowerCase().includes('fallback') &&
                recipe.image && 
                recipe.image.includes('http')
              );
              allExternalRecipes.push(...realRecipes.slice(0, 4));
            }
          } catch (error) {
            console.error(`Error fetching recipes for diet "${diet}":`, error);
          }
        }
      }

      // If no preferences or limited results, try getting popular recipes
      if (allExternalRecipes.length < 3) {
        try {
          console.log('Fetching popular recipes as fallback');
          const response = await fetchRecipes('popular', '');
          if (response?.results && Array.isArray(response.results)) {
            const realRecipes = response.results.filter(recipe => 
              recipe.id > 1000 &&
              recipe.title && 
              !recipe.title.toLowerCase().includes('fallback') &&
              recipe.image && 
              recipe.image.includes('http')
            );
            allExternalRecipes.push(...realRecipes.slice(0, 6));
          }
        } catch (error) {
          console.error('Error fetching popular recipes:', error);
        }
      }
      
      console.log(`Found ${allExternalRecipes.length} external recipes for recommendations`);
      return allExternalRecipes;
    },
    enabled: true,
    staleTime: 300000,
  });

  // Combine and filter recipes
  const recommendedRecipes = React.useMemo(() => {
    const combinedRecipes: any[] = [];

    // Add local recipes (first 2)
    if (Array.isArray(allRecipes) && allRecipes.length > 0) {
      const localToAdd = allRecipes.slice(0, 2).map(recipe => ({ 
        ...recipe, 
        isExternal: false,
        type: 'local'
      }));
      combinedRecipes.push(...localToAdd);
    }

    // Add manual recipes (first 2)
    if (Array.isArray(manualRecipes) && manualRecipes.length > 0) {
      const manualToAdd = manualRecipes.slice(0, 2).map(recipe => ({ 
        ...recipe, 
        isExternal: false,
        type: 'manual'
      }));
      combinedRecipes.push(...manualToAdd);
    }

    // Add external recipes (prioritize based on preferences)
    if (externalQueries.data && Array.isArray(externalQueries.data)) {
      let filteredExternal = externalQueries.data;

      // Apply preference-based filtering if preferences exist
      if (preferences?.favoriteCuisines?.length > 0) {
        filteredExternal = externalQueries.data.filter((recipe: SpoonacularRecipe) => {
          const recipeCuisines = recipe.cuisines || [];
          const recipeTitle = recipe.title?.toLowerCase() || '';
          
          return preferences.favoriteCuisines.some(prefCuisine => 
            recipeCuisines.some(cuisine => 
              cuisine?.toLowerCase().includes(prefCuisine.toLowerCase())
            ) || 
            recipeTitle.includes(prefCuisine.toLowerCase())
          );
        });
      }

      // Apply dietary restriction filtering if specified
      if (preferences?.dietaryRestrictions?.length > 0) {
        filteredExternal = filteredExternal.filter((recipe: SpoonacularRecipe) => {
          const recipeDiets = recipe.diets || [];
          return preferences.dietaryRestrictions.some(prefDiet => 
            recipeDiets.some(diet => 
              diet?.toLowerCase().includes(prefDiet.toLowerCase())
            )
          );
        });
      }

      // If filtering removed too many recipes, use the original list
      const externalToAdd = (filteredExternal.length >= 3 ? filteredExternal : externalQueries.data)
        .slice(0, 6)
        .map(recipe => ({ 
          ...recipe, 
          isExternal: true,
          type: 'external'
        }));
      
      combinedRecipes.push(...externalToAdd);
    }

    // Remove duplicates and return first 9
    const uniqueRecipes = combinedRecipes.filter((recipe, index, self) => 
      index === self.findIndex(r => r.id === recipe.id && r.type === recipe.type)
    );

    return uniqueRecipes.slice(0, 9);
  }, [allRecipes, manualRecipes, externalQueries.data, preferences]);

  if (!preferences) {
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
