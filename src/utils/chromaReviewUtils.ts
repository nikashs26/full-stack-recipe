import { Review } from '../components/RecipeReviews';

const API_BASE_URL = "http://localhost:5003/api";

// Function to add a new review using ChromaDB backend
export async function addReview(
  review: {
    recipeId: string;
    recipeType: 'local' | 'external' | 'manual';
    author: string;
    text: string;
    rating: number;
  }
): Promise<Review | null> {
  try {
    console.log('Adding review to ChromaDB backend:', review);
    
    // Get the auth token from localStorage
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('No authentication token found. Please sign in to add a review.');
    }
    
    const response = await fetch(`${API_BASE_URL}/reviews`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        recipe_id: review.recipeId,
        recipe_type: review.recipeType,
        author: review.author,
        text: review.text,
        rating: review.rating
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      if (response.status === 401) {
        throw new Error('Authentication required. Please sign in to add a review.');
      } else if (response.status === 400) {
        throw new Error(errorData.error || 'Invalid review data provided.');
      } else {
        throw new Error(errorData.error || `Failed to add review: ${response.status}`);
      }
    }
    
    const data = await response.json();
    console.log('Review added successfully:', data);
    
    return data.review;
  } catch (error) {
    console.error('Error in addReview:', error);
    throw error;
  }
}

// Function to get reviews for a recipe using ChromaDB backend
export async function getReviewsByRecipeId(
  recipeId: string, 
  recipeType: 'local' | 'external' | 'manual'
): Promise<Review[]> {
  try {
    console.log(`Fetching reviews for ${recipeType} recipe:`, recipeId);
    
    const response = await fetch(`${API_BASE_URL}/reviews/${recipeType}/${recipeId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      console.error(`Failed to fetch reviews: ${response.status}`);
      return [];
    }
    
    const data = await response.json();
    console.log('Fetched reviews:', data.reviews);
    
    return data.reviews || [];
  } catch (error) {
    console.error('Error fetching reviews:', error);
    return [];
  }
}

// Function to get all reviews by the current user
export async function getMyReviews(): Promise<Review[]> {
  try {
    console.log('Fetching user reviews from ChromaDB backend');
    
    // Get the auth token from localStorage
    const token = localStorage.getItem('auth_token');
    if (!token) {
      console.log('No authentication token found');
      return [];
    }
    
    const response = await fetch(`${API_BASE_URL}/reviews/my-reviews`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        console.log('Authentication required for fetching user reviews');
        return [];
      }
      console.error(`Failed to fetch user reviews: ${response.status}`);
      return [];
    }
    
    const data = await response.json();
    console.log('Fetched user reviews:', data.reviews);
    
    return data.reviews || [];
  } catch (error) {
    console.error('Error fetching user reviews:', error);
    return [];
  }
}

// Function to delete a review
export async function deleteReview(reviewId: string): Promise<boolean> {
  try {
    console.log('Deleting review:', reviewId);
    
    // Get the auth token from localStorage
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('No authentication token found. Please sign in to delete a review.');
    }
    
    const response = await fetch(`${API_BASE_URL}/reviews/${reviewId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      if (response.status === 401) {
        throw new Error('Authentication required. Please sign in to delete a review.');
      } else if (response.status === 404) {
        throw new Error('Review not found or you don\'t have permission to delete it.');
      } else {
        throw new Error(errorData.error || `Failed to delete review: ${response.status}`);
      }
    }
    
    console.log('Review deleted successfully');
    return true;
  } catch (error) {
    console.error('Error deleting review:', error);
    throw error;
  }
}

// Function to get review statistics for a recipe
export async function getRecipeStats(
  recipeId: string, 
  recipeType: 'local' | 'external' | 'manual'
): Promise<{
  total_reviews: number;
  average_rating: number;
  rating_distribution: Record<number, number>;
}> {
  try {
    console.log(`Fetching review stats for ${recipeType} recipe:`, recipeId);
    
    const response = await fetch(`${API_BASE_URL}/reviews/stats/${recipeType}/${recipeId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      console.error(`Failed to fetch review stats: ${response.status}`);
      return {
        total_reviews: 0,
        average_rating: 0,
        rating_distribution: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
      };
    }
    
    const data = await response.json();
    console.log('Fetched review stats:', data.stats);
    
    return data.stats;
  } catch (error) {
    console.error('Error fetching review stats:', error);
    return {
      total_reviews: 0,
      average_rating: 0,
      rating_distribution: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    };
  }
} 