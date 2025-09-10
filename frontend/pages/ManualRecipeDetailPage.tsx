import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Clock, ChefHat, Star, Info } from 'lucide-react';
import Header from '../components/Header';
import { fetchManualRecipeById } from '../lib/manualRecipes';
import { Button } from '@/components/ui/button';
import RecipeReviews, { Review } from '../components/RecipeReviews';
import { getReviewsByRecipeId, addReview, deleteReview } from '../utils/chromaReviewUtils';
import { useToast } from '@/hooks/use-toast';

const ManualRecipeDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [reviews, setReviews] = useState<Review[]>([]);
  
  const { data: recipe, isLoading, error } = useQuery({
    queryKey: ['manual-recipe', id],
    queryFn: () => fetchManualRecipeById(parseInt(id!)),
    enabled: !!id,
  });

  // Load reviews from ChromaDB
  useEffect(() => {
    const loadReviews = async () => {
      if (id) {
        try {
          const fetchedReviews = await getReviewsByRecipeId(id, 'manual');
          console.log('Loaded reviews for manual recipe:', id, fetchedReviews);
          setReviews(fetchedReviews);
        } catch (error) {
          console.error('Error loading reviews:', error);
          toast({
            title: 'Error',
            description: 'Failed to load reviews. Please try again later.',
            variant: 'destructive'
          });
        }
      }
    };
    
    loadReviews();
  }, [id, toast]);

  // Handler for submitting reviews
  const handleReviewSubmit = async (reviewData: { text: string, rating: number }) => {
    if (!id) return;
    
    const { text, rating } = reviewData;
    
    try {
      console.log('Submitting review:', { text, rating, recipeId: id });
      
      const savedReview = await addReview({
        recipeId: id,
        recipeType: 'manual',
        text,
        rating
      });
      
      if (savedReview) {
        console.log('Review saved successfully:', savedReview);
        setReviews(prevReviews => [savedReview, ...prevReviews]);
        toast({
          title: 'Review submitted',
          description: 'Your review has been added successfully.',
        });
      } else {
        console.error('Failed to save review - no data returned');
      }
    } catch (error) {
      console.error('Error in handleReviewSubmit:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'An unexpected error occurred while saving your review.',
        variant: 'destructive'
      });
    }
  };

  // Handler for deleting reviews
  const handleDeleteReview = async (reviewId: string) => {
    try {
      await deleteReview(reviewId);
      // Remove the deleted review from the local state
      setReviews(prevReviews => prevReviews.filter(review => review.id !== reviewId));
    } catch (error) {
      console.error('Error in handleDeleteReview:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to delete review.',
        variant: 'destructive'
      });
    }
  };

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

  if (error || !recipe) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="pt-24 md:pt-28 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-6">
            <Button 
              variant="outline" 
              onClick={() => navigate('/recipes')}
              className="mb-4"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Recipes
            </Button>
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Recipe not found</h1>
            <Button onClick={() => navigate('/recipes')}>Back to Recipes</Button>
          </div>
        </main>
      </div>
    );
  }

  // Calculate average rating
  const getAverageRating = () => {
    if (reviews.length === 0) return 0;
    const sum = reviews.reduce((total, review) => total + review.rating, 0);
    return (sum / reviews.length).toFixed(1);
  };

  const avgRating = Number(getAverageRating());
  // Enhanced cuisine display with proper fallback
  const cuisine = (() => {
    // Try the cuisine field (which is string[] in ManualRecipe)
    if (recipe.cuisine && Array.isArray(recipe.cuisine) && recipe.cuisine.length > 0) {
      return recipe.cuisine[0];
    }
    
    // If no cuisine found, return empty string instead of "International"
    return '';
  })();

  // Use actual ingredients from recipe or provide realistic defaults
  const ingredients = (() => {
    if (recipe.ingredients && Array.isArray(recipe.ingredients) && recipe.ingredients.length > 0) {
      return recipe.ingredients.map(ing => {
        if (typeof ing === 'string') {
          return ing;
        }
        // Handle ingredient objects
        if (ing.name) {
          const parts = [];
          if (ing.amount) parts.push(ing.amount);
          if (ing.unit) parts.push(ing.unit);
          if (ing.name) parts.push(ing.name);
          return parts.join(' ');
        }
        return 'Ingredient';
      });
    }
    return [];
  })();

  // Use actual cooking instructions if available, otherwise provide helpful guidance
  const instructions = (() => {
    if (recipe.instructions && Array.isArray(recipe.instructions) && recipe.instructions.length > 0) {
      return recipe.instructions;
    }
    if (recipe.instructions && typeof recipe.instructions === 'string') {
      return [recipe.instructions];
    }
    return [];
  })();

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="pt-24 md:pt-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-6">
            <Button 
              variant="outline" 
              onClick={() => navigate('/recipes')}
              className="mb-4"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Recipes
            </Button>
          </div>

          {/* Recipe header */}
          <div className="bg-white shadow-sm rounded-lg overflow-hidden">
            <div className="relative h-64 md:h-96 w-full">
              <img
                src={recipe.image || '/placeholder.svg'}
                alt={recipe.title}
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = '/placeholder.svg';
                }}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex flex-col justify-end p-6">
                <h1 className="text-white text-3xl md:text-4xl font-bold">{recipe.title}</h1>
                <div className="flex items-center text-white mt-2">
                  {cuisine && <span className="text-sm">{cuisine}</span>}
                  {recipe.ready_in_minutes && (
                    <div className="ml-4 flex items-center">
                      <Clock className="h-4 w-4" />
                      <span className="ml-1">{recipe.ready_in_minutes} minutes</span>
                    </div>
                  )}
                  {avgRating > 0 && (
                    <div className="ml-4 flex items-center">
                      <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                      <span className="ml-1">{avgRating} ({reviews.length} {reviews.length === 1 ? 'review' : 'reviews'})</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Recipe content */}
            <div className="p-6">
              {recipe.description && (
                <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                  <h2 className="text-xl font-semibold mb-2">About This Recipe</h2>
                  <p className="text-gray-700">{recipe.description}</p>
                </div>
              )}

              <h2 className="text-2xl font-semibold mb-4">Ingredients</h2>
              {ingredients.length > 0 ? (
                <ul className="list-disc list-inside mb-6 space-y-1">
                  {ingredients.map((ingredient, index) => (
                    <li key={index} className="text-gray-700">{ingredient}</li>
                  ))}
                </ul>
              ) : (
                <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-yellow-800">
                    <Info className="inline mr-2 h-4 w-4" />
                    Ingredients information is not available for this recipe. Please check the original source for complete ingredient details.
                  </p>
                </div>
              )}

              <h2 className="text-2xl font-semibold mb-4">Instructions</h2>
              {instructions.length > 0 ? (
                <ol className="list-decimal list-inside space-y-3 mb-6">
                  {instructions.map((instruction, index) => (
                    <li key={index} className="text-gray-700 leading-relaxed">{instruction}</li>
                  ))}
                </ol>
              ) : (
                <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-yellow-800">
                    <Info className="inline mr-2 h-4 w-4" />
                    Cooking instructions are not available for this recipe. Please check the original source for complete preparation steps.
                  </p>
                </div>
              )}

              {/* Dietary information */}
              {recipe.diets && recipe.diets.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold mb-3">Dietary Information</h3>
                  <div className="flex flex-wrap gap-2">
                    {recipe.diets.map((diet, index) => (
                      <span 
                        key={index}
                        className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                      >
                        {diet}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Reviews section */}
              <div className="mt-8 pt-6 border-t border-gray-200">
                <RecipeReviews
                  reviews={reviews}
                  onSubmitReview={handleReviewSubmit}
                  onDeleteReview={handleDeleteReview}
                  recipeType="manual"
                />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ManualRecipeDetailPage;
