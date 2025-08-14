import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Clock, ChefHat, Star } from 'lucide-react';
import Header from '../components/Header';
import { fetchManualRecipeById } from '../lib/manualRecipes';
import { Button } from '@/components/ui/button';
import RecipeReviews, { Review } from '../components/RecipeReviews';
import { getReviewsByRecipeId, addReview } from '../utils/chromaReviewUtils';
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
  const handleReviewSubmit = async (reviewData: { text: string, rating: number, author: string }) => {
    if (!id) return;
    
    const { text, rating, author } = reviewData;
    
    try {
      console.log('Submitting review:', { text, rating, author, recipeId: id });
      
      const savedReview = await addReview({
        recipeId: id,
        recipeType: 'manual',
        author: author || "Anonymous",
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
  const cuisine = recipe.cuisine?.[0] || 'International';

  // Use actual ingredients from recipe or provide realistic defaults
  const ingredients = [
    'Check the original recipe source for detailed ingredients',
    'This curated recipe includes traditional ingredients for ' + recipe.title,
    'Seasonings and spices as per traditional preparation'
  ];

  // Use actual cooking instructions if available, otherwise provide helpful guidance
 
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
                  <span className="text-sm">{cuisine}</span>
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
              <ul className="list-disc list-inside mb-6 space-y-1">
                {ingredients.map((ingredient, index) => (
                  <li key={index} className="text-gray-700">{ingredient}</li>
                ))}
              </ul>

              <h2 className="text-2xl font-semibold mb-4">Instructions</h2>
              <ol className="list-decimal list-inside space-y-3 mb-6">
                {instructions.map((instruction, index) => (
                  <li key={index} className="text-gray-700 leading-relaxed">{instruction}</li>
                ))}
              </ol>

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
