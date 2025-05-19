
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
      
      // Try to create the table using a direct SQL approach
      const { error: createError } = await supabase.rpc('exec_sql', {
        sql: `
        CREATE TABLE IF NOT EXISTS public.reviews (
          id UUID DEFAULT extensions.uuid_generate_v4() PRIMARY KEY,
          author TEXT NOT NULL,
          text TEXT NOT NULL,
          rating INTEGER NOT NULL,
          date TIMESTAMP WITH TIME ZONE NOT NULL,
          recipe_id TEXT NOT NULL,
          recipe_type TEXT NOT NULL,
          created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Grant access to anonymous users (adjust as needed)
        GRANT ALL ON public.reviews TO anon;
        GRANT ALL ON public.reviews TO authenticated;
        GRANT ALL ON public.reviews TO service_role;
        `
      });
      
      if (createError) {
        console.error('Error creating reviews table with SQL:', createError);
        return false;
      }
      
      console.log('Reviews table created successfully with exec_sql');
      return true;
    }
    
    console.log('Reviews table exists or was checked');
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
    const tableExists = await ensureReviewsTableExists();
    
    if (!tableExists) {
      console.error('Could not ensure reviews table exists');
      toast({
        title: 'Error',
        description: 'Could not save your review: Reviews table setup failed',
        variant: 'destructive',
      });
      return null;
    }
    
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
