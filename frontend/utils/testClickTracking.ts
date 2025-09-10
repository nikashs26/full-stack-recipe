import { trackRecipeClick } from './clickTracking';
import { supabase } from '../integrations/supabase/client';

/**
 * Test function to add sample clicks for testing the popularity system
 * This can be called from the browser console for testing
 */
export async function addSampleClicks() {
  console.log('Adding sample clicks for testing...');
  
  const sampleClicks = [
    { recipeId: '52772', recipeType: 'external' as const }, // Teriyaki Chicken Casserole
    { recipeId: '52772', recipeType: 'external' as const }, // Multiple clicks
    { recipeId: '52772', recipeType: 'external' as const },
    { recipeId: '52959', recipeType: 'external' as const }, // Baked salmon with fennel
    { recipeId: '52959', recipeType: 'external' as const },
    { recipeId: '53013', recipeType: 'external' as const }, // Beef Dumpling Stew
    { recipeId: '53013', recipeType: 'external' as const },
    { recipeId: '53013', recipeType: 'external' as const },
    { recipeId: '53016', recipeType: 'external' as const }, // Chicken Ham and Leek Pie
    { recipeId: '53016', recipeType: 'external' as const },
    { recipeId: '53022', recipeType: 'external' as const }, // Broccoli & Stilton soup
    { recipeId: '53022', recipeType: 'external' as const },
    { recipeId: '53022', recipeType: 'external' as const },
    { recipeId: '53025', recipeType: 'external' as const }, // English Breakfast
    { recipeId: '53025', recipeType: 'external' as const },
    { recipeId: '53026', recipeType: 'external' as const }, // Roast fennel and aubergine paella
    { recipeId: '53026', recipeType: 'external' as const },
    { recipeId: '53027', recipeType: 'external' as const }, // Smoky Black Bean and Quinoa Stew
    { recipeId: '53027', recipeType: 'external' as const },
    { recipeId: '53027', recipeType: 'external' as const },
    { recipeId: '53028', recipeType: 'external' as const }, // Spinach & Ricotta Cannelloni
    { recipeId: '53028', recipeType: 'external' as const },
    { recipeId: '53029', recipeType: 'external' as const }, // Italian Seafood Stew
    { recipeId: '53029', recipeType: 'external' as const },
    { recipeId: '53029', recipeType: 'external' as const },
  ];

  for (const click of sampleClicks) {
    try {
      await trackRecipeClick(click.recipeId, click.recipeType);
      console.log(`✅ Tracked click for recipe ${click.recipeId}`);
    } catch (error) {
      console.error(`❌ Failed to track click for recipe ${click.recipeId}:`, error);
    }
  }

  console.log('Sample clicks added successfully!');
}

/**
 * Debug function to show current user's clicks and reviews
 */
export async function debugUserData() {
  try {
    // Get current user ID from localStorage or auth context
    const token = localStorage.getItem('auth_token');
    if (!token) {
      console.log('❌ No auth token found. Please sign in first.');
      return;
    }

    // Get user clicks
    const { data: clicksData, error: clicksError } = await supabase
      .from('recipe_clicks')
      .select('recipe_id, recipe_type, clicked_at')
      .not('user_id', 'is', null);

    if (clicksError) {
      console.error('Error getting clicks:', clicksError);
    } else {
      console.log('👆 User clicks:', clicksData);
    }

    // Get user reviews
    const { data: reviewsData, error: reviewsError } = await supabase
      .from('reviews')
      .select('recipe_id, recipe_type, rating, text, date')
      .not('author', 'is', null);

    if (reviewsError) {
      console.error('Error getting reviews:', reviewsError);
    } else {
      console.log('⭐ User reviews:', reviewsData);
    }

    // Show summary
    const uniqueClickedRecipes = new Set(clicksData?.map(c => `${c.recipe_id}-${c.recipe_type}`) || []);
    const uniqueReviewedRecipes = new Set(reviewsData?.map(r => `${r.recipe_id}-${r.recipe_type}`) || []);

    console.log('📊 Summary:', {
      totalClicks: clicksData?.length || 0,
      totalReviews: reviewsData?.length || 0,
      uniqueClickedRecipes: uniqueClickedRecipes.size,
      uniqueReviewedRecipes: uniqueReviewedRecipes.size,
      clickedRecipes: Array.from(uniqueClickedRecipes),
      reviewedRecipes: Array.from(uniqueReviewedRecipes)
    });

  } catch (error) {
    console.error('Error debugging user data:', error);
  }
}

// Make it available globally for testing
if (typeof window !== 'undefined') {
  (window as any).addSampleClicks = addSampleClicks;
  (window as any).debugUserData = debugUserData;
} 