import { Recipe } from '../types/recipe';
import { getQualityBasedRecipesNormalized, fetchNormalizedRecipes, NormalizedRecipe } from './recipeDataService';
import { getPopularRecipesFromCurrentData } from '../utils/clickTracking';

export interface PopularRecipe extends Recipe {
  popularity?: any;
}

/**
 * Fetch popular recipes and combine with recipe data
 */
export async function fetchPopularRecipes(limit: number = 8, userId?: string, existingRecipes?: Recipe[]): Promise<PopularRecipe[]> {
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

    // Fetch the actual recipe data for each popular recipe using the shared service
    const recipesWithData: PopularRecipe[] = [];

    for (const popularRecipe of popularRecipes) {
      try {
        let recipeData: Recipe | null = null;

        // First try to find in existing recipes if provided (avoid duplicate API calls)
        if (existingRecipes && existingRecipes.length > 0) {
          const existingRecipe = existingRecipes.find(r => r.id === popularRecipe.recipe_id);
          if (existingRecipe) {
            recipeData = existingRecipe;
            console.log(`✅ Found recipe ${popularRecipe.recipe_id} in existing data`);
          }
        }

        // If not found in existing data, try to fetch from different sources based on recipe type
        if (!recipeData) {
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
                  const response = await fetch('/manual-recipes/' + popularRecipe.recipe_id);
                  if (response.ok) {
                    const manualData = await response.json();
                    if (manualData) {
                      recipeData = manualData;
                    }
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
              
              // If not found in localStorage, try the shared service (but only if we don't have existing data)
              if (!recipeData) {
                try {
                  const { recipes } = await fetchNormalizedRecipes('', '', { pageSize: 1000 });
                  const foundRecipe = recipes.find((r: any) => r.id === popularRecipe.recipe_id);
                  if (foundRecipe) {
                    // Convert NormalizedRecipe to Recipe format
                    recipeData = {
                      ...foundRecipe,
                      name: foundRecipe.title,
                      dietaryRestrictions: foundRecipe.diets,
                      imageUrl: foundRecipe.image,
                      readyInMinutes: foundRecipe.ready_in_minutes,
                      type: foundRecipe.type as any
                    } as Recipe;
                    console.log(`✅ Found recipe ${popularRecipe.recipe_id} via shared service`);
                  }
                } catch (sharedServiceError) {
                  console.log(`Could not fetch from shared service for recipe ${popularRecipe.recipe_id}`);
                }
              }
              
              // If still not found, try fallback API
              if (!recipeData) {
                try {
                  const fallbackResponse = await fetch(`http://localhost:5003/get_recipe_by_id?id=${popularRecipe.recipe_id}`);
                  if (fallbackResponse.ok) {
                    const fallbackData = await fallbackResponse.json();
                    if (fallbackData) {
                      recipeData = {
                        ...fallbackData,
                        name: fallbackData.title,
                        dietaryRestrictions: fallbackData.diets || fallbackData.dietary_restrictions,
                        imageUrl: fallbackData.image,
                        readyInMinutes: fallbackData.ready_in_minutes || fallbackData.readyInMinutes,
                        type: fallbackData.source === 'TheMealDB' ? 'external' : 'manual'
                      } as Recipe;
                      console.log(`✅ Found recipe ${popularRecipe.recipe_id} via fallback API`);
                    }
                  }
                } catch (fallbackError) {
                  console.log(`Could not fetch from fallback API for recipe ${popularRecipe.recipe_id}`);
                }
              }
              break;
            
            default:
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
              
              // If not found in localStorage, try the shared service
              if (!recipeData) {
                try {
                  const { recipes } = await fetchNormalizedRecipes('', '', { pageSize: 1000 });
                  const foundRecipe = recipes.find((r: any) => r.id === popularRecipe.recipe_id);
                  if (foundRecipe) {
                    // Convert NormalizedRecipe to Recipe format
                    recipeData = {
                      ...foundRecipe,
                      name: foundRecipe.title,
                      dietaryRestrictions: foundRecipe.diets,
                      imageUrl: foundRecipe.image,
                      readyInMinutes: foundRecipe.ready_in_minutes,
                      type: foundRecipe.type as any
                    } as Recipe;
                    console.log(`✅ Found recipe ${popularRecipe.recipe_id} via shared service`);
                  }
                } catch (sharedServiceError) {
                  console.log(`Could not fetch from shared service for recipe ${popularRecipe.recipe_id}`);
                }
              }
              
              // If still not found, try fallback API
              if (!recipeData) {
                try {
                  const fallbackResponse = await fetch(`http://localhost:5003/get_recipe_by_id?id=${popularRecipe.recipe_id}`);
                  if (fallbackResponse.ok) {
                    const fallbackData = await fallbackResponse.json();
                    if (fallbackData) {
                      recipeData = {
                        ...fallbackData,
                        name: fallbackData.title,
                        dietaryRestrictions: fallbackData.diets || fallbackData.dietary_restrictions,
                        imageUrl: fallbackData.image,
                        readyInMinutes: fallbackData.ready_in_minutes || fallbackData.readyInMinutes,
                        type: fallbackData.source === 'TheMealDB' ? 'external' : 'manual'
                      } as Recipe;
                      console.log(`✅ Found recipe ${popularRecipe.recipe_id} via fallback API`);
                    }
                  }
                } catch (fallbackError) {
                  console.log(`Could not fetch from fallback API for recipe ${popularRecipe.recipe_id}`);
                }
              }
              break;
          }
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
export async function getHomepagePopularRecipes(userId?: string, existingRecipes?: Recipe[]): Promise<Recipe[]> {
  try {
    const popularRecipes = await fetchPopularRecipes(4, userId, existingRecipes); // Pass existing recipes to avoid duplicates
    
    // If we have enough popular recipes based on clicks/ratings, use them
    if (popularRecipes.length >= 4) {
      console.log('✅ Using popularity-based recipes:', popularRecipes.length);
      return popularRecipes;
    }
    
    // DO NOT fall back to random quality-based recipes - this causes nonsense recipes to appear
    // Instead, return fewer recipes or empty array to avoid showing random content
    console.log('⚠️ Not enough popularity data, but NOT falling back to random quality-based recipes');
    console.log('⚠️ This prevents showing nonsense recipes with fallback images');
    return [];
    
  } catch (error) {
    console.error('Error getting homepage popular recipes:', error);
    // DO NOT fall back to random quality-based recipes on error
    // This prevents showing nonsense recipes with fallback images
    console.log('⚠️ Error occurred, but NOT falling back to random quality-based recipes');
    return [];
  }
}

/**
 * Get recipes based on quality indicators when popularity data isn't available
 * This function is now deprecated in favor of getQualityBasedRecipesNormalized
 */
export async function getQualityBasedRecipes(limit: number = 4, userId?: string): Promise<Recipe[]> {
  console.warn('getQualityBasedRecipes is deprecated, use getQualityBasedRecipesNormalized instead');
  const normalizedRecipes = await getQualityBasedRecipesNormalized(limit);
  
  // Convert NormalizedRecipe to Recipe format
  return normalizedRecipes.map(normalizedRecipe => ({
    ...normalizedRecipe,
    name: normalizedRecipe.title,
    dietaryRestrictions: normalizedRecipe.diets,
    imageUrl: normalizedRecipe.image,
    readyInMinutes: normalizedRecipe.ready_in_minutes,
    type: normalizedRecipe.type as any
  })) as Recipe[];
} 