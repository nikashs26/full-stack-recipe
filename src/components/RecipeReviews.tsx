
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { MessageSquare, Star } from 'lucide-react';
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
  onSubmitReview: (reviewData: { text: string, rating: number, author: string }) => void;
  recipeType: 'local' | 'external' | 'manual';
}

const RecipeReviews: React.FC<RecipeReviewsProps> = ({ reviews, onSubmitReview, recipeType }) => {
  const [newReview, setNewReview] = useState("");
  const [selectedRating, setSelectedRating] = useState(0);
  const [reviewAuthor, setReviewAuthor] = useState("");
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const { isAuthenticated } = useAuth();

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
        rating: selectedRating,
        author: reviewAuthor.trim() || "Anonymous"
      });
      
      // Reset form
      setNewReview("");
      setReviewAuthor("");
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
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-800 flex items-center">
          <MessageSquare className="mr-2 h-5 w-5" /> Reviews
        </h2>
        {isAuthenticated ? (
          !showReviewForm && (
            <button 
              onClick={() => setShowReviewForm(true)}
              className="px-4 py-2 bg-recipe-primary text-white rounded-md hover:bg-recipe-primary/90 transition-colors"
            >
              Write a Review
            </button>
          )
        ) : (
          <div className="flex space-x-2">
            <Link 
              to="/signin"
              className="px-4 py-2 bg-recipe-primary text-white rounded-md hover:bg-recipe-primary/90 transition-colors"
            >
              Sign In
            </Link>
            <Link 
              to="/signup"
              className="px-4 py-2 border border-recipe-primary text-recipe-primary rounded-md hover:bg-gray-50 transition-colors"
            >
              Sign Up
            </Link>
          </div>
        )}
      </div>

      {/* Review Form - Only show if authenticated */}
      {isAuthenticated && showReviewForm && (
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="mb-4">
              <label htmlFor="author" className="block text-sm font-medium text-gray-700 mb-1">
                Your Name (optional)
              </label>
              <input
                type="text"
                id="author"
                value={reviewAuthor}
                onChange={(e) => setReviewAuthor(e.target.value)}
                placeholder="Anonymous"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-recipe-primary"
              />
            </div>
            
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
                placeholder="Write your review here..."
                rows={4}
                className="w-full"
                disabled={isSubmitting}
              />
            </div>
            
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setShowReviewForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                onClick={handleReviewSubmit}
                className={`px-4 py-2 bg-recipe-primary text-white rounded-md hover:bg-recipe-primary/90 transition-colors ${
                  isSubmitting ? 'opacity-70 cursor-not-allowed' : ''
                }`}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Submitting...' : 'Submit Review'}
              </button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Auth message when user is not signed in */}
      {!isAuthenticated && reviews.length === 0 && (
        <div className="text-center p-6 bg-gray-50 rounded-lg mb-6">
          <p className="text-gray-600 mb-3">Sign in or create an account to be the first to review this recipe!</p>
          <div className="flex justify-center space-x-3">
            <Link 
              to="/signin"
              className="px-4 py-2 bg-recipe-primary text-white rounded-md hover:bg-recipe-primary/90 transition-colors"
            >
              Sign In
            </Link>
            <Link 
              to="/signup"
              className="px-4 py-2 border border-recipe-primary text-recipe-primary rounded-md hover:bg-gray-50 transition-colors"
            >
              Sign Up
            </Link>
          </div>
        </div>
      )}

      {/* Reviews List */}
      {reviews.length > 0 ? (
        <div className="space-y-4">
          {reviews.map((review) => (
            <Card key={review.id} className="bg-gray-50">
              <CardContent className="pt-6">
                <div className="flex justify-between">
                  <h3 className="font-medium">{review.author}</h3>
                  <span className="text-sm text-gray-500">{formatDate(review.date)}</span>
                </div>
                <div className="flex items-center mt-1 mb-3">
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
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        isAuthenticated && (
          <p className="text-gray-500 italic">No reviews yet. Be the first to review this recipe!</p>
        )
      )}
    </div>
  );
};

export default RecipeReviews;
