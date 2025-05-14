
import { supabase } from '../lib/supabase';
import { toast } from '@/hooks/use-toast';
import { Review } from '../components/RecipeReviews';

// Function to add a new review to the database
export async function addReview(
  review: Omit<Review, 'id'> & { recipeId: string, recipeType: 'local' | 'external' }
) {
  try {
    console.log('Adding review to Supabase:', review);
    
    const { data, error } = await supabase
      .from('reviews')
      .insert([{
        author: review.author,
        text: review.text,
        rating: review.rating,
        date: review.date,
        recipe_id: review.recipeId,
        recipe_type: review.recipeType
      }])
      .select('id')
      .single();
    
    if (error) {
      console.error('Error adding review:', error);
      toast({
        title: 'Error',
        description: 'Failed to save your review. Please try again.',
        variant: 'destructive',
      });
      return null;
    }
    
    console.log('Review added successfully:', data);
    toast({
      title: 'Review submitted',
      description: 'Your review has been added successfully.',
    });
    
    return {
      ...review,
      id: data.id
    };
  } catch (error) {
    console.error('Exception adding review:', error);
    toast({
      title: 'Error',
      description: 'Failed to save your review. Please try again.',
      variant: 'destructive',
    });
    return null;
  }
}

// Function to get reviews for a recipe
export async function getReviewsByRecipeId(recipeId: string, recipeType: 'local' | 'external') {
  try {
    console.log(`Fetching reviews for ${recipeType} recipe:`, recipeId);
    
    const { data, error } = await supabase
      .from('reviews')
      .select('*')
      .eq('recipe_id', recipeId)
      .eq('recipe_type', recipeType)
      .order('date', { ascending: false });
    
    if (error) {
      console.error('Error fetching reviews:', error);
      return [];
    }
    
    // Map the database fields to our Review interface
    const reviews: Review[] = data.map(item => ({
      id: item.id,
      author: item.author,
      text: item.text,
      rating: item.rating,
      date: item.date
    }));
    
    console.log('Fetched reviews:', reviews);
    return reviews;
  } catch (error) {
    console.error('Exception fetching reviews:', error);
    return [];
  }
}
