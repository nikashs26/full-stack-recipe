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
 * Get the most popular recipes based on clicks and reviews
 */
export async function getPopularRecipes(limit: number = 10): Promise<RecipePopularity[]> {
  try {
    // Get all clicks data from localStorage
    const clicksData = JSON.parse(localStorage.getItem('recipe_clicks') || '[]');

    // Get all reviews data from localStorage
    const reviewsData = JSON.parse(localStorage.getItem('recipe_reviews') || '[]');

    console.log('📊 Popularity data from localStorage:', {
      totalClicks: clicksData?.length || 0,
      totalReviews: reviewsData?.length || 0,
      uniqueRecipesWithClicks: new Set(clicksData?.map((c: any) => `${c.recipe_id}-${c.recipe_type}`)).size,
      uniqueRecipesWithReviews: new Set(reviewsData?.map((r: any) => `${r.recipe_id}-${r.recipe_type}`)).size
    });

    // Group clicks by recipe
    const clicksByRecipe = new Map<string, number>();
    clicksData?.forEach((click: any) => {
      const key = `${click.recipe_id}-${click.recipe_type}`;
      clicksByRecipe.set(key, (clicksByRecipe.get(key) || 0) + 1);
    });

    // Group reviews by recipe
    const reviewsByRecipe = new Map<string, { count: number; totalRating: number }>();
    reviewsData?.forEach((review: any) => {
      const key = `${review.recipe_id}-${review.recipe_type}`;
      const existing = reviewsByRecipe.get(key) || { count: 0, totalRating: 0 };
      existing.count += 1;
      existing.totalRating += (review.rating || 0);
      reviewsByRecipe.set(key, existing);
    });

    // Calculate popularity for each recipe
    const popularityData: RecipePopularity[] = [];
    
    // Combine all unique recipes from both clicks and reviews
    const allRecipeKeys = new Set([
      ...clicksByRecipe.keys(),
      ...reviewsByRecipe.keys()
    ]);

    console.log('🔍 All recipe keys:', Array.from(allRecipeKeys));

    allRecipeKeys.forEach(key => {
      const [recipeId, recipeType] = key.split('-');
      const totalClicks = clicksByRecipe.get(key) || 0;
      const reviewData = reviewsByRecipe.get(key);
      const totalReviews = reviewData?.count || 0;
      const averageRating = reviewData ? reviewData.totalRating / reviewData.count : 0;
      
      // Calculate popularity score with enhanced formula
      // Formula: (clicks * 0.25) + (reviews * 0.35) + (average_rating * 0.25) + (engagement_bonus * 0.15)
      // Engagement bonus rewards recipes with both clicks AND reviews
      const engagementBonus = (totalClicks > 0 && totalReviews > 0) ? 
        Math.min(totalClicks, totalReviews) * 0.5 : 0;
      
      const popularityScore = (totalClicks * 0.25) + (totalReviews * 0.35) + (averageRating * 0.25) + engagementBonus;

      popularityData.push({
        recipe_id: recipeId,
        recipe_type: recipeType,
        total_clicks: totalClicks,
        total_reviews: totalReviews,
        average_rating: averageRating,
        popularity_score: popularityScore
      });
    });

    // Sort by popularity score and return top recipes
    const sortedRecipes = popularityData
      .sort((a, b) => b.popularity_score - a.popularity_score)
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

    // Get reviews by this user from localStorage
    const reviewsData = JSON.parse(localStorage.getItem('recipe_reviews') || '[]');
    const userReviews = reviewsData.filter((review: any) => review.author === userId);

    console.log('👤 Personal popularity data from localStorage:', {
      userClicks: userClicks?.length || 0,
      userReviews: userReviews?.length || 0,
      userId
    });

    // Group clicks by recipe
    const clicksByRecipe = new Map<string, number>();
    userClicks?.forEach((click: any) => {
      const key = `${click.recipe_id}-${click.recipe_type}`;
      clicksByRecipe.set(key, (clicksByRecipe.get(key) || 0) + 1);
    });

    // Group reviews by recipe
    const reviewsByRecipe = new Map<string, { count: number; totalRating: number }>();
    userReviews?.forEach((review: any) => {
      const key = `${review.recipe_id}-${review.recipe_type}`;
      const existing = reviewsByRecipe.get(key) || { count: 0, totalRating: 0 };
      existing.count += 1;
      existing.totalRating += (review.rating || 0);
      reviewsByRecipe.set(key, existing);
    });

    // Calculate popularity for each recipe
    const popularityData: RecipePopularity[] = [];
    
    // Combine all unique recipes from both clicks and reviews
    const allRecipeKeys = new Set([
      ...clicksByRecipe.keys(),
      ...reviewsByRecipe.keys()
    ]);

    allRecipeKeys.forEach(key => {
      const [recipeId, recipeType] = key.split('-');
      const totalClicks = clicksByRecipe.get(key) || 0;
      const reviewData = reviewsByRecipe.get(key);
      const totalReviews = reviewData?.count || 0;
      const averageRating = reviewData ? reviewData.totalRating / reviewData.count : 0;
      
      // Calculate popularity score with enhanced formula
      // Formula: (clicks * 0.25) + (reviews * 0.35) + (average_rating * 0.25) + (engagement_bonus * 0.15)
      // Engagement bonus rewards recipes with both clicks AND reviews
      const engagementBonus = (totalClicks > 0 && totalReviews > 0) ? 
        Math.min(totalClicks, totalReviews) * 0.5 : 0;
      
      const popularityScore = (totalClicks * 0.25) + (totalReviews * 0.35) + (averageRating * 0.25) + engagementBonus;

      popularityData.push({
        recipe_id: recipeId,
        recipe_type: recipeType,
        total_clicks: totalClicks,
        total_reviews: totalReviews,
        average_rating: averageRating,
        popularity_score: popularityScore
      });
    });

    // Sort by popularity score and return top recipes
    return popularityData
      .sort((a, b) => b.popularity_score - a.popularity_score)
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