
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { MessageSquare, Star, Trash2 } from 'lucide-react';
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from '../context/AuthContext';

// Generic review interface that can work with both local and external recipes
export interface Review {
  id: string;
  author: string;
  text: string;
  date: string;
  rating: number;
}

interface RecipeReviewsProps {
  reviews: Review[];
  onSubmitReview: (review: { text: string; rating: number }) => Promise<void>;
  onDeleteReview?: (reviewId: string) => Promise<void>;
  recipeType: 'local' | 'external' | 'manual';
}

const RecipeReviews: React.FC<RecipeReviewsProps> = ({ reviews, onSubmitReview, onDeleteReview, recipeType }) => {
  const [newReview, setNewReview] = useState("");
  const [selectedRating, setSelectedRating] = useState(0);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const { isAuthenticated, user } = useAuth();

  const handleReviewSubmit = async () => {
    if (newReview.trim() === "") {
      toast({
        title: "Review text required",
        description: "Please enter your review text before submitting.",
        variant: "destructive",
      });
      return;
    }

    if (selectedRating === 0) {
      toast({
        title: "Rating required",
        description: "Please select a rating before submitting your review.",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    
    try {
      await onSubmitReview({
        text: newReview,
        rating: selectedRating
      });
      
      // Reset form
      setNewReview("");
      setSelectedRating(0);
      setShowReviewForm(false);
    } catch (error) {
      console.error("Error submitting review:", error);
      toast({
        title: "Error",
        description: "Failed to submit your review. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteReview = async (reviewId: string) => {
    if (!onDeleteReview) return;
    
    if (window.confirm("Are you sure you want to delete this review?")) {
      try {
        await onDeleteReview(reviewId);
        toast({
          title: "Review deleted",
          description: "Your review has been deleted successfully.",
        });
      } catch (error) {
        console.error("Error deleting review:", error);
        toast({
          title: "Error",
          description: "Failed to delete your review. Please try again.",
          variant: "destructive",
        });
      }
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <div className="mt-8 border-t pt-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Reviews ({reviews.length})
          </h3>
        </div>
        
        {isAuthenticated && (
          <button
            onClick={() => setShowReviewForm(!showReviewForm)}
            className="px-4 py-2 bg-recipe-primary text-white rounded-md hover:bg-recipe-primary/90 transition-colors"
          >
            {showReviewForm ? 'Cancel' : 'Write a Review'}
          </button>
        )}
      </div>

      {/* Review Form - Only show if authenticated */}
      {isAuthenticated && showReviewForm && (
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Your Rating
              </label>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((rating) => (
                  <button
                    key={rating}
                    type="button"
                    onClick={() => setSelectedRating(rating)}
                    className="focus:outline-none"
                    disabled={isSubmitting}
                  >
                    <Star
                      className={`h-6 w-6 ${
                        rating <= selectedRating ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'
                      }`}
                    />
                  </button>
                ))}
              </div>
            </div>
            
            <div className="mb-4">
              <label htmlFor="review" className="block text-sm font-medium text-gray-700 mb-1">
                Your Review
              </label>
              <Textarea
                id="review"
                value={newReview}
                onChange={(e) => setNewReview(e.target.value)}
                placeholder="Share your thoughts about this recipe..."
                className="min-h-[100px]"
                disabled={isSubmitting}
              />
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={handleReviewSubmit}
                disabled={isSubmitting}
                className="px-4 py-2 bg-recipe-primary text-white rounded-md hover:bg-recipe-primary/90 transition-colors disabled:opacity-50"
              >
                {isSubmitting ? 'Submitting...' : 'Submit Review'}
              </button>
              <button
                onClick={() => setShowReviewForm(false)}
                disabled={isSubmitting}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Reviews List */}
      {reviews.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <MessageSquare className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No reviews yet. Be the first to share your thoughts!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map((review) => (
            <Card key={review.id}>
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-medium text-gray-900">{review.author}</span>
                      <span className="text-sm text-gray-500">•</span>
                      <span className="text-sm text-gray-500">{formatDate(review.date)}</span>
                    </div>
                    
                    <div className="flex items-center gap-1 mb-3">
                      {[1, 2, 3, 4, 5].map((rating) => (
                        <Star
                          key={rating}
                          className={`h-4 w-4 ${
                            rating <= review.rating ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'
                          }`}
                        />
                      ))}
                    </div>
                    
                    <p className="text-gray-700">{review.text}</p>
                  </div>
                  
                  {/* Delete button - only show for the current user's reviews */}
                  {isAuthenticated && onDeleteReview && user && review.author === user.full_name && (
                    <button
                      onClick={() => handleDeleteReview(review.id)}
                      className="ml-4 p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors"
                      title="Delete review"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default RecipeReviews;
