import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Star, Trash2, MessageSquare, ArrowLeft } from 'lucide-react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from '../context/AuthContext';
import { getMyReviews, deleteReview } from '../utils/chromaReviewUtils';
import { Review } from '../components/RecipeReviews';
import Header from '../components/Header';

const MyReviewsPage: React.FC = () => {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/signin');
      return;
    }

    loadReviews();
  }, [isAuthenticated, navigate]);

  const loadReviews = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const userReviews = await getMyReviews();
      setReviews(userReviews);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load reviews';
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteReview = async (reviewId: string) => {
    if (window.confirm("Are you sure you want to delete this review?")) {
      try {
        await deleteReview(reviewId);
        // Remove the deleted review from the local state
        setReviews(prevReviews => prevReviews.filter(review => review.id !== reviewId));
        toast({
          title: "Review deleted",
          description: "Your review has been deleted successfully.",
        });
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to delete review';
        toast({
          title: "Error",
          description: errorMessage,
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
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!isAuthenticated) {
    return null; // Will redirect in useEffect
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="pt-24 md:pt-28 flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-recipe-primary"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="pt-24 md:pt-28 px-4 py-8 max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate(-1)}
            className="mb-4 p-0 h-auto font-normal text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          
          <div className="flex items-center gap-3 mb-2">
            <MessageSquare className="h-8 w-8 text-recipe-primary" />
            <h1 className="text-3xl font-bold text-gray-900">My Reviews</h1>
          </div>
          
          <p className="text-gray-600">
            {user?.full_name ? `Reviews by ${user.full_name}` : 'Your recipe reviews'}
          </p>
        </div>

        {/* Reviews */}
        {error ? (
          <Card className="p-6">
            <CardContent className="text-center">
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={loadReviews} variant="outline">
                Try Again
              </Button>
            </CardContent>
          </Card>
        ) : reviews.length === 0 ? (
          <Card className="p-12">
            <CardContent className="text-center">
              <MessageSquare className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No Reviews Yet</h3>
              <p className="text-gray-600 mb-6">
                You haven't written any reviews yet. Start reviewing recipes to see them here!
              </p>
              <Button onClick={() => navigate('/')} className="bg-recipe-primary hover:bg-recipe-primary/90">
                Browse Recipes
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {reviews.map((review) => (
              <Card key={review.id} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="font-medium text-gray-900">{review.author}</span>
                        <span className="text-sm text-gray-500">•</span>
                        <span className="text-sm text-gray-500">{formatDate(review.date)}</span>
                      </div>
                      
                      <div className="flex items-center gap-1 mb-3">
                        {[1, 2, 3, 4, 5].map((rating) => (
                          <Star
                            key={rating}
                            className={`h-5 w-5 ${
                              rating <= review.rating ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'
                            }`}
                          />
                        ))}
                        <span className="ml-2 text-sm text-gray-600">
                          {review.rating}/5
                        </span>
                      </div>
                      
                      <p className="text-gray-700 text-lg leading-relaxed">{review.text}</p>
                    </div>
                    
                    <Button
                      onClick={() => handleDeleteReview(review.id)}
                      variant="ghost"
                      size="sm"
                      className="ml-4 p-2 text-red-500 hover:text-red-700 hover:bg-red-50"
                      title="Delete review"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Summary */}
        {reviews.length > 0 && (
          <div className="mt-8 p-4 bg-white rounded-lg border">
            <div className="text-center">
              <p className="text-gray-600">
                You have written <span className="font-semibold text-recipe-primary">{reviews.length}</span> review{reviews.length !== 1 ? 's' : ''}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Keep sharing your thoughts about recipes!
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MyReviewsPage;
