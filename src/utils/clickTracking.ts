import { supabase } from '../integrations/supabase/client';
import { useAuth } from '../context/AuthContext';

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
 * Track when a user clicks on a recipe
 */
export async function trackRecipeClick(
  recipeId: string, 
  recipeType: 'local' | 'external' | 'manual' | 'spoonacular',
  userId?: string | null
): Promise<void> {
  try {
    // Get user agent and IP (if available)
    const userAgent = navigator.userAgent;
    
    // Create the click record
    const clickData = {
      recipe_id: recipeId,
      recipe_type: recipeType,
      user_id: userId || null,
      clicked_at: new Date().toISOString(),
      ip_address: null, // We'll get this from the backend if needed
      user_agent: userAgent
    };

    console.log('Tracking recipe click:', clickData);

    const { error } = await supabase
      .from('recipe_clicks')
      .insert([clickData]);

    if (error) {
      console.error('Error tracking recipe click:', error);
      // Don't throw error to avoid breaking the user experience
    } else {
      console.log('Recipe click tracked successfully');
    }
  } catch (error) {
    console.error('Exception tracking recipe click:', error);
    // Don't throw error to avoid breaking the user experience
  }
}

/**
 * Get recipe popularity data including clicks and reviews
 */
export async function getRecipePopularity(
  recipeId: string,
  recipeType: string
): Promise<RecipePopularity | null> {
  try {
    // Get total clicks for this recipe
    const { data: clicksData, error: clicksError } = await supabase
      .from('recipe_clicks')
      .select('id')
      .eq('recipe_id', recipeId)
      .eq('recipe_type', recipeType);

    if (clicksError) {
      console.error('Error getting recipe clicks:', clicksError);
      return null;
    }

    // Get reviews for this recipe
    const { data: reviewsData, error: reviewsError } = await supabase
      .from('reviews')
      .select('rating')
      .eq('recipe_id', recipeId)
      .eq('recipe_type', recipeType);

    if (reviewsError) {
      console.error('Error getting recipe reviews:', reviewsError);
      return null;
    }

    const totalClicks = clicksData?.length || 0;
    const totalReviews = reviewsData?.length || 0;
    
    // Calculate average rating
    let averageRating = 0;
    if (totalReviews > 0) {
      const totalRating = reviewsData.reduce((sum, review) => sum + review.rating, 0);
      averageRating = totalRating / totalReviews;
    }

    // Calculate popularity score (weighted combination of clicks and reviews)
    // Formula: (clicks * 0.3) + (reviews * 0.4) + (average_rating * 0.3)
    const popularityScore = (totalClicks * 0.3) + (totalReviews * 0.4) + (averageRating * 0.3);

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
    // Get all unique recipes with their popularity data
    const { data: clicksData, error: clicksError } = await supabase
      .from('recipe_clicks')
      .select('recipe_id, recipe_type');

    if (clicksError) {
      console.error('Error getting recipe clicks:', clicksError);
      return [];
    }

    // Get all reviews
    const { data: reviewsData, error: reviewsError } = await supabase
      .from('reviews')
      .select('recipe_id, recipe_type, rating');

    if (reviewsError) {
      console.error('Error getting recipe reviews:', reviewsError);
      return [];
    }

    console.log('📊 Popularity data:', {
      totalClicks: clicksData?.length || 0,
      totalReviews: reviewsData?.length || 0,
      uniqueRecipesWithClicks: new Set(clicksData?.map(c => `${c.recipe_id}-${c.recipe_type}`)).size,
      uniqueRecipesWithReviews: new Set(reviewsData?.map(r => `${r.recipe_id}-${r.recipe_type}`)).size
    });

    // Group clicks by recipe
    const clicksByRecipe = new Map<string, number>();
    clicksData?.forEach(click => {
      const key = `${click.recipe_id}-${click.recipe_type}`;
      clicksByRecipe.set(key, (clicksByRecipe.get(key) || 0) + 1);
    });

    // Group reviews by recipe
    const reviewsByRecipe = new Map<string, { count: number; totalRating: number }>();
    reviewsData?.forEach(review => {
      const key = `${review.recipe_id}-${review.recipe_type}`;
      const existing = reviewsByRecipe.get(key) || { count: 0, totalRating: 0 };
      existing.count += 1;
      existing.totalRating += review.rating;
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
      
      // Calculate popularity score
      const popularityScore = (totalClicks * 0.3) + (totalReviews * 0.4) + (averageRating * 0.3);

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
      score: r.popularity_score.toFixed(2)
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
    // Get clicks by this user
    const { data: clicksData, error: clicksError } = await supabase
      .from('recipe_clicks')
      .select('recipe_id, recipe_type')
      .eq('user_id', userId);

    if (clicksError) {
      console.error('Error getting user clicks:', clicksError);
      return [];
    }

    // Get reviews by this user
    const { data: reviewsData, error: reviewsError } = await supabase
      .from('reviews')
      .select('recipe_id, recipe_type, rating')
      .eq('author', userId);

    if (reviewsError) {
      console.error('Error getting user reviews:', reviewsError);
      return [];
    }

    console.log('👤 Personal popularity data:', {
      userClicks: clicksData?.length || 0,
      userReviews: reviewsData?.length || 0,
      userId
    });

    // Group clicks by recipe
    const clicksByRecipe = new Map<string, number>();
    clicksData?.forEach(click => {
      const key = `${click.recipe_id}-${click.recipe_type}`;
      clicksByRecipe.set(key, (clicksByRecipe.get(key) || 0) + 1);
    });

    // Group reviews by recipe
    const reviewsByRecipe = new Map<string, { count: number; totalRating: number }>();
    reviewsData?.forEach(review => {
      const key = `${review.recipe_id}-${review.recipe_type}`;
      const existing = reviewsByRecipe.get(key) || { count: 0, totalRating: 0 };
      existing.count += 1;
      existing.totalRating += review.rating;
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
      
      // Calculate popularity score
      const popularityScore = (totalClicks * 0.3) + (totalReviews * 0.4) + (averageRating * 0.3);

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
  const { user } = useAuth();

  const trackClick = async (recipeId: string, recipeType: 'local' | 'external' | 'manual' | 'spoonacular') => {
    await trackRecipeClick(recipeId, recipeType, user?.id);
  };

  return { trackClick };
} 