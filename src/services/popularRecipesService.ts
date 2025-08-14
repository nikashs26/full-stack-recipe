import { Recipe } from '../types/recipe';
import { getPopularRecipes, getPersonalPopularRecipes, getPopularRecipesFromCurrentData } from '../utils/clickTracking';

export interface PopularRecipe extends Recipe {
  popularity?: any;
}

/**
 * Fetch popular recipes and combine with recipe data
 */
export async function fetchPopularRecipes(limit: number = 8, userId?: string): Promise<PopularRecipe[]> {
  try {
    // Get popular recipes based on current recipe data (not old click tracking)
    let popularRecipes: any[];
    
    if (userId) {
      // For now, use the same function for both personal and global
      console.log('👤 Fetching popular recipes from current data for user:', userId);
      popularRecipes = await getPopularRecipesFromCurrentData(limit);
    } else {
      // Get global popular recipes from current data
      console.log('🌍 Fetching popular recipes from current data');
      popularRecipes = await getPopularRecipesFromCurrentData(limit);
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
            // Try to get from localStorage first (dietary-delight-recipes)
            try {
              const localRecipes = JSON.parse(localStorage.getItem('dietary-delight-recipes') || '[]');
              const localRecipe = localRecipes.find((r: any) => r.id === popularRecipe.recipe_id);
              if (localRecipe) {
                recipeData = localRecipe;
                console.log(`✅ Found recipe ${popularRecipe.recipe_id} in localStorage`);
              }
            } catch (localError) {
              console.log(`Could not read from localStorage for recipe ${popularRecipe.recipe_id}`);
            }
            
            // If not found in localStorage, try manual recipes endpoint
            if (!recipeData) {
              try {
                const { data: manualData } = await fetch('/manual-recipes/' + popularRecipe.recipe_id);
                if (manualData) {
                  recipeData = manualData;
                }
              } catch (endpointError) {
                console.log(`Could not fetch from manual-recipes endpoint for recipe ${popularRecipe.recipe_id}`);
              }
            }
            break;
          
          case 'external':
            // Try to get from localStorage first
            try {
              const localRecipes = JSON.parse(localStorage.getItem('dietary-delight-recipes') || '[]');
              const localRecipe = localRecipes.find((r: any) => r.id === popularRecipe.recipe_id);
              if (localRecipe) {
                recipeData = localRecipe;
                console.log(`✅ Found recipe ${popularRecipe.recipe_id} in localStorage`);
              }
            } catch (localError) {
              console.log(`Could not read from localStorage for recipe ${popularRecipe.recipe_id}`);
            }
            
            // If not found in localStorage, try backend API
            if (!recipeData) {
              try {
                const response = await fetch(`http://localhost:5003/get_recipe_by_id?id=${popularRecipe.recipe_id}`);
                if (response.ok) {
                  recipeData = await response.json();
                }
              } catch (apiError) {
                console.log(`Could not fetch from backend API for recipe ${popularRecipe.recipe_id}`);
              }
            }
            break;
          
          default:
            // Try localStorage first, then backend API as fallback
            try {
              const localRecipes = JSON.parse(localStorage.getItem('dietary-delight-recipes') || '[]');
              const localRecipe = localRecipes.find((r: any) => r.id === popularRecipe.recipe_id);
              if (localRecipe) {
                recipeData = localRecipe;
                console.log(`✅ Found recipe ${popularRecipe.recipe_id} in localStorage`);
              }
            } catch (localError) {
              console.log(`Could not read from localStorage for recipe ${popularRecipe.recipe_id}`);
            }
            
            if (!recipeData) {
              try {
                const fallbackResponse = await fetch(`http://localhost:5003/get_recipe_by_id?id=${popularRecipe.recipe_id}`);
                if (fallbackResponse.ok) {
                  recipeData = await fallbackResponse.json();
                }
              } catch (fallbackError) {
                console.log(`Could not fetch from fallback API for recipe ${popularRecipe.recipe_id}`);
              }
            }
            break;
        }

        if (recipeData) {
          recipesWithData.push({
            ...recipeData,
            popularity: popularRecipe
          });
          console.log(`✅ Added recipe ${popularRecipe.recipe_id} to popular recipes`);
        } else {
          console.log(`❌ Could not find recipe data for ${popularRecipe.recipe_id}`);
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
    
    // If we have enough popular recipes based on clicks/ratings, use them
    if (popularRecipes.length >= 4) {
      console.log('✅ Using popularity-based recipes:', popularRecipes.length);
      return popularRecipes;
    }
    
    // Fallback: Get recipes with quality indicators instead of random selection
    console.log('🔄 Not enough popularity data, using quality-based selection');
    return await getQualityBasedRecipes(4, userId);
    
  } catch (error) {
    console.error('Error getting homepage popular recipes:', error);
    // Even on error, try to get quality-based recipes
    return await getQualityBasedRecipes(4, userId);
  }
}

/**
 * Get recipes based on quality indicators when popularity data isn't available
 */
export async function getQualityBasedRecipes(limit: number = 4, userId?: string): Promise<Recipe[]> {
  try {
    console.log('🔍 Fetching quality-based recipes...');
    
    // Get all available recipes
    const response = await fetch('http://localhost:5003/get_recipes');
    if (!response.ok) {
      console.error('Failed to fetch recipes for quality selection');
      return [];
    }
    
    const data = await response.json();
    const allRecipes = data.results || [];
    
    if (allRecipes.length === 0) {
      console.log('No recipes available for quality selection');
      return [];
    }
    
    // Score recipes based on quality indicators
    const scoredRecipes = allRecipes.map(recipe => {
      let score = 0;
      
      // Recipe completeness score (0-30 points)
      if (recipe.title) score += 10;
      if (recipe.description && recipe.description.length > 50) score += 5;
      if (recipe.ingredients && recipe.ingredients.length >= 5) score += 10;
      if (recipe.instructions && recipe.instructions.length > 100) score += 5;
      
      // Image quality score (0-20 points)
      if (recipe.image && recipe.image !== 'placeholder') score += 20;
      
      // Nutritional info score (0-25 points)
      if (recipe.nutrition) {
        if (recipe.nutrition.calories) score += 5;
        if (recipe.nutrition.protein) score += 5;
        if (recipe.nutrition.carbs) score += 5;
        if (recipe.nutrition.fat) score += 5;
        if (recipe.nutrition.fiber) score += 5;
      }
      
      // Recipe type diversity bonus (0-15 points)
      if (recipe.cuisine && recipe.cuisine !== 'Unknown') score += 10;
      if (recipe.dietaryRestrictions && recipe.dietaryRestrictions.length > 0) score += 5;
      
      // User engagement indicators (0-10 points)
      if (recipe.ratings && Array.isArray(recipe.ratings) && recipe.ratings.length > 0) {
        const avgRating = recipe.ratings.reduce((sum: number, r: any) => sum + (r.score || 0), 0) / recipe.ratings.length;
        score += Math.min(10, avgRating * 2); // Max 10 points for 5-star rating
      }
      
      return { ...recipe, qualityScore: score };
    });
    
    // Sort by quality score and ensure diversity
    const sortedByQuality = scoredRecipes.sort((a, b) => b.qualityScore - a.qualityScore);
    
    // Select diverse recipes (different cuisines, meal types)
    const selectedRecipes: Recipe[] = [];
    const selectedCuisines = new Set<string>();
    const selectedMealTypes = new Set<string>();
    
    // First pass: select highest quality recipes with diverse cuisines
    for (const recipe of sortedByQuality) {
      if (selectedRecipes.length >= limit) break;
      
      const cuisine = recipe.cuisine || 'Unknown';
      const mealType = recipe.mealType || 'main';
      
      // Prefer recipes with different cuisines
      if (!selectedCuisines.has(cuisine) || selectedRecipes.length < limit / 2) {
        selectedRecipes.push(recipe);
        selectedCuisines.add(cuisine);
        selectedMealTypes.add(mealType);
      }
    }
    
    // If we still need more recipes, fill with remaining high-quality ones
    if (selectedRecipes.length < limit) {
      for (const recipe of sortedByQuality) {
        if (selectedRecipes.length >= limit) break;
        if (!selectedRecipes.find(r => r.id === recipe.id)) {
          selectedRecipes.push(recipe);
        }
      }
    }
    
    console.log('🎯 Quality-based recipe selection:', {
      total: allRecipes.length,
      selected: selectedRecipes.length,
      cuisines: Array.from(selectedCuisines),
      avgQualityScore: selectedRecipes.reduce((sum, r) => sum + (r as any).qualityScore, 0) / selectedRecipes.length
    });
    
    return selectedRecipes;
    
  } catch (error) {
    console.error('Error getting quality-based recipes:', error);
    return [];
  }
} 