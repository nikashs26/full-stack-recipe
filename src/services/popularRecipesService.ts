import { getPopularRecipes, getPersonalPopularRecipes, RecipePopularity } from '../utils/clickTracking';
import { Recipe, ExtendedRecipe } from '../types/recipe';

export interface PopularRecipe extends Recipe {
  popularity: RecipePopularity;
}

/**
 * Fetch popular recipes and combine with recipe data
 */
export async function fetchPopularRecipes(limit: number = 8, userId?: string): Promise<PopularRecipe[]> {
  try {
    // Get popular recipes based on clicks and reviews
    let popularRecipes: RecipePopularity[];
    
    if (userId) {
      // Get personal popular recipes
      console.log('👤 Fetching personal popular recipes for user:', userId);
      popularRecipes = await getPersonalPopularRecipes(userId, limit);
    } else {
      // Get global popular recipes
      console.log('🌍 Fetching global popular recipes');
      popularRecipes = await getPopularRecipes(limit);
    }
    
    if (popularRecipes.length === 0) {
      console.log('No popular recipes found, returning empty array');
      return [];
    }

    console.log('Found popular recipes:', popularRecipes);

    // Fetch the actual recipe data for each popular recipe
    const recipesWithData: PopularRecipe[] = [];

    for (const popularRecipe of popularRecipes) {
      try {
        let recipeData: Recipe | null = null;

        // Try to fetch from different sources based on recipe type
        switch (popularRecipe.recipe_type) {
          case 'manual':
            // Fetch from manual recipes table
            const { data: manualData } = await fetch('/api/manual-recipes/' + popularRecipe.recipe_id);
            if (manualData) {
              recipeData = manualData;
            }
            break;
          
          case 'external':
            // Fetch from backend API
            const response = await fetch(`http://localhost:5003/get_recipe_by_id?id=${popularRecipe.recipe_id}`);
            if (response.ok) {
              recipeData = await response.json();
            }
            break;
          
          default:
            // Try backend API as fallback
            const fallbackResponse = await fetch(`http://localhost:5003/get_recipe_by_id?id=${popularRecipe.recipe_id}`);
            if (fallbackResponse.ok) {
              recipeData = await fallbackResponse.json();
            }
            break;
        }

        if (recipeData) {
          recipesWithData.push({
            ...recipeData,
            popularity: popularRecipe
          });
        }
      } catch (error) {
        console.error(`Error fetching recipe data for ${popularRecipe.recipe_id}:`, error);
      }
    }

    console.log('Popular recipes with data:', recipesWithData);
    return recipesWithData;

  } catch (error) {
    console.error('Error fetching popular recipes:', error);
    return [];
  }
}

/**
 * Get popular recipes for the homepage
 */
export async function getHomepagePopularRecipes(userId?: string): Promise<Recipe[]> {
  try {
    const popularRecipes = await fetchPopularRecipes(4, userId); // Show 4 popular recipes on homepage
    
    // If we don't have enough popular recipes, fall back to a default selection
    if (popularRecipes.length < 4) {
      console.log('Not enough popular recipes, using fallback');
      return [];
    }

    return popularRecipes;
  } catch (error) {
    console.error('Error getting homepage popular recipes:', error);
    return [];
  }
} 