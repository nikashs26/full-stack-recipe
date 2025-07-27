
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
import { UserPreferences } from '../types/auth';
import { ThumbsUp, Loader2 } from 'lucide-react';

const RecommendedRecipes: React.FC = () => {
  const { user } = useAuth();
  
  // Query for local recipes
  const { data: allRecipes = [], isLoading: isLocalLoading } = useQuery({
    queryKey: ['localRecipes'],
    queryFn: loadRecipes,
  });

  // Query for manual recipes - use an empty search term to get all recipes
  const { data: manualRecipes = [], isLoading: isManualLoading } = useQuery({
    queryKey: ['recommendedManualRecipes'],
    queryFn: () => fetchManualRecipes(''), // Empty string to get all recipes
    placeholderData: (previousData) => previousData || [],
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Safely access user preferences with fallback to empty arrays
  const favoriteCuisines = user?.preferences?.favoriteCuisines || [];
  const dietaryRestrictions = user?.preferences?.dietaryRestrictions || [];
  
  console.log('RecommendedRecipes - User preferences:', { favoriteCuisines, dietaryRestrictions });

  // Query external recipes based on user preferences
  const externalQueries = useQuery({
    queryKey: ['recommendedExternalRecipes', favoriteCuisines, dietaryRestrictions],
    queryFn: async () => {
      console.log('Fetching external recipes with:', { favoriteCuisines, dietaryRestrictions });
      
      if (favoriteCuisines.length === 0 && dietaryRestrictions.length === 0) {
        console.log('No specific preferences, fetching popular recipes');
        const response = await fetchRecipes('popular', '');
        return response?.results || [];
      }

      const allExternalRecipes: SpoonacularRecipe[] = [];
      
      console.log('Favorite cuisines:', favoriteCuisines);
      console.log('Dietary restrictions:', dietaryRestrictions);

      // Fetch recipes for favorite cuisines
      if (favoriteCuisines.length > 0) {
        const cuisineRecipes = new Map(); // Use a map to deduplicate recipes by ID
        
        for (const cuisine of favoriteCuisines) {
          try {
            console.log(`Fetching recipes for cuisine: ${cuisine}`);
            const response = await fetchRecipes(cuisine, '');
            
            if (response?.results && Array.isArray(response.results)) {
              // Process each recipe from the response
              response.results.forEach(recipe => {
                if (!recipe.id) return;
                
                const recipeCuisines = Array.isArray(recipe.cuisines) 
                  ? recipe.cuisines.map(c => c?.toLowerCase())
                  : [];
                
                const recipeTitle = recipe.title?.toLowerCase() || '';
                
                // Check if recipe matches the cuisine
                const matchesCuisine = recipeCuisines.includes(cuisine.toLowerCase()) ||
                                     recipeTitle.includes(cuisine.toLowerCase());
                
                if (matchesCuisine) {
                  // Add cuisine to recipe's cuisines if not already present
                  if (!recipeCuisines.includes(cuisine.toLowerCase())) {
                    recipe.cuisines = [...recipeCuisines, cuisine.toLowerCase()];
                  }
                  
                  // Add to our map (automatically handles duplicates by ID)
                  cuisineRecipes.set(recipe.id, recipe);
                }
              });
              
              console.log(`Found ${response.results.length} total recipes for ${cuisine}, ` +
                        `${cuisineRecipes.size} unique recipes across all cuisines so far`);
            }
          } catch (error) {
            console.error(`Error fetching ${cuisine} recipes:`, error);
          }
        }
        
        // Add all unique recipes to our results
        allExternalRecipes.push(...Array.from(cuisineRecipes.values()));
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
              console.log(`Found ${realRecipes.length} real recipes for ${diet}`);
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
    enabled: favoriteCuisines.length > 0 || dietaryRestrictions.length > 0,
    staleTime: 300000,
  });

  // Combine and filter recipes
  const recommendedRecipes = React.useMemo(() => {
    console.log('Building recommended recipes list');
    const combinedRecipes: any[] = [];

    // Add local recipes (first 2)
    if (Array.isArray(allRecipes) && allRecipes.length > 0) {
      const localToAdd = allRecipes.slice(0, 2).map(recipe => ({ 
        ...recipe, 
        isExternal: false,
        type: 'local'
      }));
      console.log(`Adding ${localToAdd.length} local recipes`);
      combinedRecipes.push(...localToAdd);
    }

    // Add manual recipes (first 2)
    if (Array.isArray(manualRecipes) && manualRecipes.length > 0) {
      const manualToAdd = manualRecipes.slice(0, 2).map(recipe => ({ 
        ...recipe, 
        isExternal: false,
        type: 'manual'
      }));
      console.log(`Adding ${manualToAdd.length} manual recipes`);
      combinedRecipes.push(...manualToAdd);
    }

    // Add external recipes
    if (externalQueries.data && Array.isArray(externalQueries.data)) {
      let filteredExternal = externalQueries.data;

      // Apply preference-based filtering if favorite cuisines exist
      if (favoriteCuisines.length > 0) {
        filteredExternal = externalQueries.data.filter((recipe: SpoonacularRecipe) => {
          const recipeCuisines = recipe.cuisines || [];
          const recipeTitle = recipe.title?.toLowerCase() || '';
          
          return favoriteCuisines.some(cuisine => 
            recipeCuisines.some(recipeCuisine => 
              recipeCuisine?.toLowerCase().includes(cuisine.toLowerCase())
            ) || 
            recipeTitle.includes(cuisine.toLowerCase())
          );
        });
      }

      // Apply dietary restriction filtering if specified
      if (dietaryRestrictions.length > 0) {
        filteredExternal = filteredExternal.filter((recipe: SpoonacularRecipe) => {
          const recipeDiets = recipe.diets || [];
          
          // Check if recipe meets at least one dietary preference
          return dietaryRestrictions.some(diet => {
            const dietLower = diet.toLowerCase();
            return recipeDiets.some(recipeDiet => {
              const recipeDietLower = recipeDiet?.toLowerCase() || '';
              // Enhanced matching for dietary restrictions
              if (dietLower === 'vegetarian' && recipeDietLower.includes('vegetarian')) return true;
              if (dietLower === 'vegan' && recipeDietLower.includes('vegan')) return true;
              if (dietLower === 'gluten-free' && (recipeDietLower.includes('gluten') && recipeDietLower.includes('free'))) return true;
              if (dietLower === 'dairy-free' && (recipeDietLower.includes('dairy') && recipeDietLower.includes('free'))) return true;
              if (dietLower === 'keto' && (recipeDietLower.includes('ketogenic') || recipeDietLower.includes('keto'))) return true;
              if (dietLower === 'paleo' && (recipeDietLower.includes('paleo') || recipeDietLower.includes('paleolithic'))) return true;
              return false;
            });
          });
        });
      }

      const externalToAdd = (filteredExternal.length >= 3 ? filteredExternal : externalQueries.data)
        .slice(0, 6)
        .map(recipe => ({ 
          ...recipe, 
          isExternal: true,
          type: 'external'
        }));
      
      console.log(`Adding ${externalToAdd.length} external recipes`);
      combinedRecipes.push(...externalToAdd);
    }

    // Remove duplicates and return first 9
    const uniqueRecipes = combinedRecipes.filter((recipe, index, self) => 
      index === self.findIndex(r => r.id === recipe.id && r.type === recipe.type)
    );

    console.log(`Final recommended recipes count: ${uniqueRecipes.length}`);
    return uniqueRecipes.slice(0, 9);
  }, [allRecipes, manualRecipes, externalQueries.data, favoriteCuisines, dietaryRestrictions]);

  // Don't show recommendations if no preferences are set
  if (favoriteCuisines.length === 0 && dietaryRestrictions.length === 0) {
    console.log('No preferences found, not showing recommendations');
    return null;
  }

  const isLoading = isLocalLoading || isManualLoading || externalQueries.isLoading;
  console.log('Loading states:', { isLocalLoading, isManualLoading, externalLoading: externalQueries.isLoading });

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
              Update your preferences to get better recommendations
            </Link>
          </div>
        )}
      </div>
    </section>
  );
};

export default RecommendedRecipes;
