
import { supabase } from '../lib/supabase';
import { toast } from '@/hooks/use-toast';
import { Review } from '../components/RecipeReviews';

// Function to ensure the reviews table exists
export async function ensureReviewsTableExists() {
  try {
    console.log('Checking if reviews table exists...');
    
    // Check if the table exists by attempting a simple query
    const { error } = await supabase
      .from('reviews')
      .select('count()', { count: 'exact', head: true });
    
    if (error && error.code === '42P01') { // Table doesn't exist error code
      console.log('Reviews table does not exist, creating it...');
      
      // Create the reviews table using SQL
      const { error: createError } = await supabase.rpc('create_reviews_table');
      
      if (createError) {
        console.error('Error creating reviews table:', createError);
        return false;
      }
      
      console.log('Reviews table created successfully');
      return true;
    }
    
    console.log('Reviews table exists');
    return true;
  } catch (error) {
    console.error('Error checking/creating reviews table:', error);
    return false;
  }
}

// Function to add a new review to the database
export async function addReview(
  review: Omit<Review, 'id'> & { recipeId: string, recipeType: 'local' | 'external' }
) {
  try {
    console.log('Adding review to Supabase:', review);
    
    // First ensure the table exists
    await ensureReviewsTableExists();
    
    // Add review to the reviews table
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
      
      // More descriptive error message
      let errorMessage = 'Database error occurred';
      if (error.code === '42P01') {
        errorMessage = 'Reviews table does not exist - please try again after table creation';
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast({
        title: 'Error',
        description: `Failed to save your review: ${errorMessage}`,
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
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('Exception adding review:', error);
    toast({
      title: 'Error',
      description: `Failed to save your review: ${errorMessage}`,
      variant: 'destructive',
    });
    return null;
  }
}

// Function to get reviews for a recipe
export async function getReviewsByRecipeId(recipeId: string, recipeType: 'local' | 'external') {
  try {
    console.log(`Fetching reviews for ${recipeType} recipe:`, recipeId);
    
    // First ensure the table exists
    const tableExists = await ensureReviewsTableExists();
    if (!tableExists) {
      console.log('Reviews table does not exist yet, returning empty array');
      return [];
    }
    
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
