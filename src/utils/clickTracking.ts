// ChromaDB-based click tracking using localStorage as fallback

export interface RecipeClick {
  id: string;
  recipe_id: string;
  recipe_type: string;
  user_id: string | null;
  clicked_at: string;
  ip_address: string | null;
  user_agent: string | null;
}

export interface RecipePopularity {
  recipe_id: string;
  recipe_type: string;
  total_clicks: number;
  total_reviews: number;
  average_rating: number;
  popularity_score: number;
}

/**
 * Track when a user clicks on a recipe using localStorage
 */
export async function trackRecipeClick(
  recipeId: string, 
  recipeType: 'local' | 'external' | 'manual' | 'spoonacular',
  userId?: string | null
): Promise<void> {
  try {
    // Get user agent
    const userAgent = navigator.userAgent;
    
    // Create the click record
    const clickData = {
      id: `${recipeId}_${Date.now()}`,
      recipe_id: recipeId,
      recipe_type: recipeType,
      user_id: userId || null,
      clicked_at: new Date().toISOString(),
      ip_address: null,
      user_agent: userAgent
    };

    console.log('Tracking recipe click:', clickData);

    // Store in localStorage
    const existingClicks = JSON.parse(localStorage.getItem('recipe_clicks') || '[]');
    existingClicks.push(clickData);
    
    // Keep only last 1000 clicks to prevent localStorage from getting too large
    if (existingClicks.length > 1000) {
      existingClicks.splice(0, existingClicks.length - 1000);
    }
    
    localStorage.setItem('recipe_clicks', JSON.stringify(existingClicks));
    console.log('Recipe click tracked successfully in localStorage');

  } catch (error) {
    console.error('Exception tracking recipe click:', error);
    // Don't throw error to avoid breaking the user experience
  }
}

/**
 * Get recipe popularity data including clicks and reviews from localStorage
 */
export async function getRecipePopularity(
  recipeId: string,
  recipeType: string
): Promise<RecipePopularity | null> {
  try {
    // Get clicks from localStorage
    const clicksData = JSON.parse(localStorage.getItem('recipe_clicks') || '[]');
    const recipeClicks = clicksData.filter((click: any) => 
      click.recipe_id === recipeId && click.recipe_type === recipeType
    );

    // Get reviews from localStorage (if they exist)
    const reviewsData = JSON.parse(localStorage.getItem('recipe_reviews') || '[]');
    const recipeReviews = reviewsData.filter((review: any) => 
      review.recipe_id === recipeId && review.recipe_type === recipeType
    );

    const totalClicks = recipeClicks.length;
    const totalReviews = recipeReviews.length;
    
    // Calculate average rating
    let averageRating = 0;
    if (totalReviews > 0) {
      const totalRating = recipeReviews.reduce((sum: number, review: any) => sum + (review.rating || 0), 0);
      averageRating = totalRating / totalReviews;
    }

    // Calculate popularity score with enhanced formula
    // Formula: (clicks * 0.25) + (reviews * 0.35) + (average_rating * 0.25) + (engagement_bonus * 0.15)
    // Engagement bonus rewards recipes with both clicks AND reviews
    const engagementBonus = (totalClicks > 0 && totalReviews > 0) ? 
      Math.min(totalClicks, totalReviews) * 0.5 : 0;
    
    const popularityScore = (totalClicks * 0.25) + (totalReviews * 0.35) + (averageRating * 0.25) + engagementBonus;

    return {
      recipe_id: recipeId,
      recipe_type: recipeType,
      total_clicks: totalClicks,
      total_reviews: totalReviews,
      average_rating: averageRating,
      popularity_score: popularityScore
    };
  } catch (error) {
    console.error('Exception getting recipe popularity:', error);
    return null;
  }
}

/**
 * Clear all old click tracking data (useful when recipes are removed/changed)
 */
export function clearOldClickTrackingData() {
  try {
    localStorage.removeItem('recipe_clicks');
    console.log('🧹 Cleared old click tracking data');
    return true;
  } catch (error) {
    console.error('Error clearing click tracking data:', error);
    return false;
  }
}

/**
 * Get popular recipes based on current recipe data (not old click tracking)
 */
export async function getPopularRecipesFromCurrentData(limit: number = 10): Promise<RecipePopularity[]> {
  try {
    // Get current recipe data from backend API
    const response = await fetch('http://localhost:5003/get_recipes');
    if (!response.ok) {
      console.error('Failed to fetch recipes from backend for popularity calculation');
      return [];
    }
    
    const data = await response.json();
    const recipeData = data.results || [];
    
    if (recipeData.length === 0) {
      console.log('No current recipe data found from backend');
      return [];
    }

    console.log('📊 Processing backend recipe data for popularity:', recipeData.length, 'recipes');

    // Calculate popularity based on reviews from the backend review system
    const popularityData: RecipePopularity[] = [];
    
    // Process each recipe to get its review data
    for (const recipe of recipeData) {
      try {
        // Fetch reviews for this recipe from the backend
        // Look for both 'external' and 'local' types since existing reviews may have been saved with the wrong type
        let totalReviews = 0;
        let totalRating = 0;
        
        // Try external type first (correct type for backend recipes)
        const externalReviewsResponse = await fetch(`http://localhost:5003/api/reviews/external/${recipe.id}`);
        if (externalReviewsResponse.ok) {
          const externalReviewsData = await externalReviewsResponse.json();
          const externalReviews = externalReviewsData.reviews || [];
          totalReviews += externalReviews.length;
          totalRating += externalReviews.reduce((sum: number, review: any) => sum + (review.rating || 0), 0);
        }
        
        // Also check local type (for existing reviews that were saved with wrong type)
        const localReviewsResponse = await fetch(`http://localhost:5003/api/reviews/local/${recipe.id}`);
        if (localReviewsResponse.ok) {
          const localReviewsData = await localReviewsResponse.json();
          const localReviews = localReviewsData.reviews || [];
          totalReviews += localReviews.length;
          totalRating += localReviews.reduce((sum: number, review: any) => sum + (review.rating || 0), 0);
        }
        
        if (totalReviews > 0) {
          const averageRating = totalRating / totalReviews;
          
          // Calculate popularity score based on reviews and rating
          // Formula: (reviews * 0.7) + (average_rating * 0.3)
          // This heavily prioritizes recipes with more reviews first
          const popularityScore = (totalReviews * 0.7) + (averageRating * 0.3);
          
          popularityData.push({
            recipe_id: recipe.id,
            recipe_type: 'external', // Backend recipes are external
            total_clicks: 0, // No click data for current recipes
            total_reviews: totalReviews,
            average_rating: averageRating,
            popularity_score: popularityScore
          });
        }
      } catch (error) {
        // If we can't fetch reviews for a recipe, skip it
        console.log(`Could not fetch reviews for recipe ${recipe.id}:`, error);
        continue;
      }
    }

    // Sort by popularity score (highest first)
    // This will naturally prioritize recipes with more reviews first due to the formula
    const sortedRecipes = popularityData
      .sort((a, b) => {
        // First sort by review count (highest first)
        if (a.total_reviews !== b.total_reviews) {
          return b.total_reviews - a.total_reviews;
        }
        // If review counts are equal, sort by average rating (highest first)
        return b.average_rating - a.average_rating;
      })
      .slice(0, limit);

    console.log('🏆 Top popular recipes from backend data:', sortedRecipes.map(r => ({
      recipe_id: r.recipe_id,
      reviews: r.total_reviews,
      avg_rating: r.average_rating.toFixed(1),
      score: r.popularity_score.toFixed(2)
    })));

    return sortedRecipes;

  } catch (error) {
    console.error('Exception getting popular recipes from backend data:', error);
    return [];
  }
}

/**
 * Global function to clear old data and refresh popular recipes
 * Call this in browser console: clearOldDataAndRefresh()
 */
(window as any).clearOldDataAndRefresh = function() {
  try {
    // Clear old click tracking data
    localStorage.removeItem('recipe_clicks');
    console.log('🧹 Cleared old click tracking data');
    
    // Force page refresh to reload popular recipes
    window.location.reload();
    
    return 'Old data cleared and page refreshed!';
  } catch (error) {
    console.error('Error clearing data:', error);
    return 'Error clearing data: ' + error.message;
  }
};

/**
 * Get the most popular recipes based on clicks and reviews
 */
export async function getPopularRecipes(limit: number = 10): Promise<RecipePopularity[]> {
  try {
    // Get all clicks data from localStorage
    const clicksData = JSON.parse(localStorage.getItem('recipe_clicks') || '[]');

    // Get recipe data from backend API
    const response = await fetch('http://localhost:5003/get_recipes');
    if (!response.ok) {
      console.error('Failed to fetch recipes from backend for popularity calculation');
      return [];
    }
    
    const data = await response.json();
    const recipeData = data.results || [];

    console.log('📊 Popularity data from localStorage and backend:', {
      totalClicks: clicksData?.length || 0,
      totalRecipes: recipeData?.length || 0,
      uniqueRecipesWithClicks: new Set(clicksData?.map((c: any) => `${c.recipe_id}-${c.recipe_type}`)).size
    });

    // Group clicks by recipe
    const clicksByRecipe = new Map<string, number>();
    clicksData?.forEach((click: any) => {
      const key = `${click.recipe_id}-${click.recipe_type}`;
      clicksByRecipe.set(key, (clicksByRecipe.get(key) || 0) + 1);
    });

    // Calculate popularity for each recipe
    const popularityData: RecipePopularity[] = [];
    
    // Process each recipe to get its review data and clicks
    for (const recipe of recipeData) {
      try {
        // Get clicks for this recipe
        const recipeKey = `${recipe.id}-external`;
        const totalClicks = clicksByRecipe.get(recipeKey) || 0;
        
        // Fetch reviews for this recipe from the backend
        const reviewsResponse = await fetch(`http://localhost:5003/api/reviews/external/${recipe.id}`);
        let totalReviews = 0;
        let averageRating = 0;
        
        if (reviewsResponse.ok) {
          const reviewsData = await reviewsResponse.json();
          const reviews = reviewsData.reviews || [];
          
          if (reviews.length > 0) {
            totalReviews = reviews.length;
            const totalRating = reviews.reduce((sum: number, review: any) => sum + (review.rating || 0), 0);
            averageRating = totalRating / totalReviews;
          }
        }
        
        // Calculate popularity score with enhanced formula
        // Formula: (clicks * 0.25) + (reviews * 0.35) + (average_rating * 0.25) + (engagement_bonus * 0.15)
        // Engagement bonus rewards recipes with both clicks AND reviews
        const engagementBonus = (totalClicks > 0 && totalReviews > 0) ? 
          Math.min(totalClicks, totalReviews) * 0.5 : 0;
        
        const popularityScore = (totalClicks * 0.25) + (totalReviews * 0.35) + (averageRating * 0.25) + engagementBonus;

        popularityData.push({
          recipe_id: recipe.id,
          recipe_type: 'external',
          total_clicks: totalClicks,
          total_reviews: totalReviews,
          average_rating: averageRating,
          popularity_score: popularityScore
        });
      } catch (error) {
        // If we can't process a recipe, skip it
        console.log(`Could not process recipe ${recipe.id} for popularity:`, error);
        continue;
      }
    }

    // Sort by popularity score and return top recipes
    const sortedRecipes = popularityData
      .sort((a, b) => {
        // First sort by review count (highest first)
        if (a.total_reviews !== b.total_reviews) {
          return b.total_reviews - a.total_reviews;
        }
        // If review counts are equal, sort by average rating (highest first)
        return b.average_rating - a.average_rating;
      })
      .slice(0, limit);

    console.log('🏆 Top popular recipes:', sortedRecipes.map(r => ({
      recipe_id: r.recipe_id,
      clicks: r.total_clicks,
      reviews: r.total_reviews,
      avg_rating: r.average_rating.toFixed(1),
      score: r.popularity_score.toFixed(2),
      breakdown: {
        clicks_score: (r.total_clicks * 0.25).toFixed(2),
        reviews_score: (r.total_reviews * 0.35).toFixed(2),
        rating_score: (r.average_rating * 0.25).toFixed(2),
        engagement_bonus: (r.total_clicks > 0 && r.total_reviews > 0 ? Math.min(r.total_clicks, r.total_reviews) * 0.5 : 0).toFixed(2)
      }
    })));

    return sortedRecipes;

  } catch (error) {
    console.error('Exception getting popular recipes:', error);
    return [];
  }
}

/**
 * Get personal popular recipes (only recipes the current user has interacted with)
 */
export async function getPersonalPopularRecipes(userId: string, limit: number = 10): Promise<RecipePopularity[]> {
  try {
    // Get clicks by this user from localStorage
    const clicksData = JSON.parse(localStorage.getItem('recipe_clicks') || '[]');
    const userClicks = clicksData.filter((click: any) => click.user_id === userId);

    // Get recipe data from backend API
    const response = await fetch('http://localhost:5003/get_recipes');
    if (!response.ok) {
      console.error('Failed to fetch recipes from backend for personal popularity calculation');
      return [];
    }
    
    const data = await response.json();
    const recipeData = data.results || [];

    console.log('👤 Personal popularity data from localStorage and backend:', {
      userClicks: userClicks?.length || 0,
      totalRecipes: recipeData?.length || 0,
      userId
    });

    // Group clicks by recipe
    const clicksByRecipe = new Map<string, number>();
    userClicks?.forEach((click: any) => {
      const key = `${click.recipe_id}-${click.recipe_type}`;
      clicksByRecipe.set(key, (clicksByRecipe.get(key) || 0) + 1);
    });

    // Calculate popularity for each recipe
    const popularityData: RecipePopularity[] = [];
    
    // Process each recipe to get its review data and clicks
    for (const recipe of recipeData) {
      try {
        // Get clicks for this recipe by this user
        const recipeKey = `${recipe.id}-external`;
        const totalClicks = clicksByRecipe.get(recipeKey) || 0;
        
        // Fetch reviews for this recipe from the backend
        const reviewsResponse = await fetch(`http://localhost:5003/api/reviews/external/${recipe.id}`);
        let totalReviews = 0;
        let averageRating = 0;
        
        if (reviewsResponse.ok) {
          const reviewsData = await reviewsResponse.json();
          const reviews = reviewsData.reviews || [];
          
          if (reviews.length > 0) {
            totalReviews = reviews.length;
            const totalRating = reviews.reduce((sum: number, review: any) => sum + (review.rating || 0), 0);
            averageRating = totalRating / totalReviews;
          }
        }
        
        // Calculate popularity score with enhanced formula
        // Formula: (clicks * 0.25) + (reviews * 0.35) + (average_rating * 0.25) + (engagement_bonus * 0.15)
        // Engagement bonus rewards recipes with both clicks AND reviews
        const engagementBonus = (totalClicks > 0 && totalReviews > 0) ? 
          Math.min(totalClicks, totalReviews) * 0.5 : 0;
        
        const popularityScore = (totalClicks * 0.25) + (totalReviews * 0.35) + (averageRating * 0.25) + engagementBonus;

        popularityData.push({
          recipe_id: recipe.id,
          recipe_type: 'external',
          total_clicks: totalClicks,
          total_reviews: totalReviews,
          average_rating: averageRating,
          popularity_score: popularityScore
        });
      } catch (error) {
        // If we can't process a recipe, skip it
        console.log(`Could not process recipe ${recipe.id} for personal popularity:`, error);
        continue;
      }
    }

    // Sort by popularity score and return top recipes
    return popularityData
      .sort((a, b) => {
        // First sort by review count (highest first)
        if (a.total_reviews !== b.total_reviews) {
          return b.total_reviews - a.total_reviews;
        }
        // If review counts are equal, sort by average rating (highest first)
        return b.average_rating - a.average_rating;
      })
      .slice(0, limit);

  } catch (error) {
    console.error('Exception getting personal popular recipes:', error);
    return [];
  }
}

/**
 * Hook to track recipe clicks
 */
export function useRecipeClickTracking() {
  const trackClick = async (recipeId: string, recipeType: 'local' | 'external' | 'manual' | 'spoonacular') => {
    await trackRecipeClick(recipeId, recipeType, null); // No user tracking for now
  };

  return { trackClick };
} 