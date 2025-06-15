
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Clock, ChefHat, Star } from 'lucide-react';
import Header from '../components/Header';
import { fetchRecipeById } from '../lib/spoonacular';
import { Button } from '@/components/ui/button';
import RecipeReviews, { Review } from '../components/RecipeReviews';
import { getReviewsByRecipeId, addReview } from '../utils/reviewUtils';
import { useToast } from '@/hooks/use-toast';

const ExternalRecipeDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [reviews, setReviews] = useState<Review[]>([]);
  
  const { data: recipe, isLoading, error } = useQuery({
    queryKey: ['external-recipe', id],
    queryFn: () => fetchRecipeById(parseInt(id!)),
    enabled: !!id,
  });

  // Load reviews from Supabase
  useEffect(() => {
    const loadReviews = async () => {
      if (id) {
        try {
          const fetchedReviews = await getReviewsByRecipeId(id, 'external');
          console.log('Loaded reviews for external recipe:', id, fetchedReviews);
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
      
      const newReviewData = {
        author: author || "Anonymous",
        text,
        date: new Date().toISOString(),
        rating,
        recipeId: id,
        recipeType: 'external' as const
      };

      const savedReview = await addReview(newReviewData);
      
      if (savedReview) {
        console.log('Review saved successfully:', savedReview);
        setReviews(prevReviews => [savedReview, ...prevReviews]);
      } else {
        console.error('Failed to save review - no data returned');
      }
    } catch (error) {
      console.error('Error in handleReviewSubmit:', error);
      toast({
        title: 'Error',
        description: 'An unexpected error occurred while saving your review.',
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

  // Better ingredient parsing - only show actual data if available
  const ingredients = (() => {
    console.log('Full recipe data for ingredients:', recipe);
    
    // Try extendedIngredients first
    if (recipe?.extendedIngredients && Array.isArray(recipe.extendedIngredients) && recipe.extendedIngredients.length > 0) {
      console.log('Found extendedIngredients:', recipe.extendedIngredients);
      return recipe.extendedIngredients.map(ing => {
        if (ing.original && ing.original.trim()) return ing.original.trim();
        if (ing.originalString && ing.originalString.trim()) return ing.originalString.trim();
        
        // Only construct if we have meaningful data
        const parts = [];
        if (ing.amount && ing.amount > 0) {
          const amount = ing.amount % 1 === 0 ? ing.amount.toString() : ing.amount.toFixed(2).replace(/\.?0+$/, '');
          parts.push(amount);
        }
        if (ing.unit && ing.unit.trim()) parts.push(ing.unit.trim());
        if (ing.name && ing.name.trim()) parts.push(ing.name.trim());
        
        return parts.length > 1 ? parts.join(' ') : ing.name || 'Ingredient';
      }).filter(ingredient => ingredient && ingredient.trim().length > 0);
    }
    
    return [];
  })();

  // Better instruction parsing - only show actual data if available
  const instructions = (() => {
    console.log('Full recipe data for instructions:', recipe);
    
    // Try analyzedInstructions first
    if (recipe?.analyzedInstructions && Array.isArray(recipe.analyzedInstructions) && recipe.analyzedInstructions.length > 0) {
      console.log('Found analyzedInstructions:', recipe.analyzedInstructions);
      const allSteps = [];
      
      recipe.analyzedInstructions.forEach(instructionSet => {
        if (instructionSet.steps && Array.isArray(instructionSet.steps)) {
          instructionSet.steps.forEach(step => {
            if (step.step && step.step.trim().length > 10) { // Only meaningful steps
              allSteps.push(step.step.trim());
            }
          });
        }
      });
      
      if (allSteps.length > 0) {
        return allSteps;
      }
    }
    
    // Try the instructions field
    if (recipe?.instructions && typeof recipe.instructions === 'string' && recipe.instructions.trim().length > 20) {
      console.log('Found instructions field:', recipe.instructions);
      
      let cleanInstructions = recipe.instructions
        .replace(/<[^>]*>/g, '')
        .replace(/&nbsp;/g, ' ')
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/\s+/g, ' ')
        .trim();
      
      if (cleanInstructions.length > 20) {
        const numberedSteps = cleanInstructions.split(/\d+\.\s+/).filter(step => step.trim().length > 15);
        if (numberedSteps.length > 1) {
          return numberedSteps.slice(1);
        } else {
          const sentences = cleanInstructions.split(/\.\s+(?=[A-Z])/).filter(step => step.trim().length > 20);
          if (sentences.length > 1) {
            return sentences.map(sentence => sentence.endsWith('.') ? sentence : sentence + '.');
          } else {
            return [cleanInstructions];
          }
        }
      }
    }
    
    return [];
  })();
      
  const cuisine = recipe?.cuisines?.[0] || 'International';

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
                  {recipe.readyInMinutes && (
                    <div className="ml-4 flex items-center">
                      <Clock className="h-4 w-4" />
                      <span className="ml-1">{recipe.readyInMinutes} minutes</span>
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
              {recipe.summary && (
                <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                  <h2 className="text-xl font-semibold mb-2">About This Recipe</h2>
                  <div 
                    className="text-gray-700" 
                    dangerouslySetInnerHTML={{ __html: recipe.summary }}
                  />
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
                  <p className="text-gray-700">
                    Ingredients are not available from the API for this recipe. 
                    {recipe.sourceUrl && (
                      <span> Please check the <a href={recipe.sourceUrl} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">original source</a> for the complete ingredient list.</span>
                    )}
                  </p>
                </div>
              )}

              <h2 className="text-2xl font-semibold mb-4">Instructions</h2>
              {instructions.length > 0 ? (
                <ol className="list-decimal list-inside space-y-3">
                  {instructions.map((instruction, index) => (
                    <li key={index} className="text-gray-700 leading-relaxed">{instruction}</li>
                  ))}
                </ol>
              ) : (
                <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-gray-700">
                    Cooking instructions are not available from the API for this recipe. 
                    {recipe.sourceUrl && (
                      <span> Please check the <a href={recipe.sourceUrl} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">original source</a> for the complete instructions.</span>
                    )}
                  </p>
                </div>
              )}
              
              {/* Source URL if available */}
              {recipe.sourceUrl && (
                <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                  <h3 className="text-lg font-semibold mb-2">Original Recipe</h3>
                  <a 
                    href={recipe.sourceUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 underline"
                  >
                    View full recipe at original source
                  </a>
                </div>
              )}
              
              {/* Reviews section */}
              <div className="mt-8 pt-6 border-t border-gray-200">
                <RecipeReviews
                  reviews={reviews}
                  onSubmitReview={handleReviewSubmit}
                  recipeType="external"
                />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ExternalRecipeDetailPage;
