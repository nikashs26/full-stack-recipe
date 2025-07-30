import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Heart, Folder, ShoppingCart, Star, ArrowLeft, Loader2, FolderPlus } from 'lucide-react';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { updateRecipe, loadRecipes } from '../utils/storage';
import { useToast } from '@/hooks/use-toast';
import { RecipeFolderActions } from '../components/RecipeFolderActions';
import { ShoppingListItem } from '../types/recipe';
import { v4 as uuidv4 } from 'uuid';
import RecipeReviews, { Review } from '../components/RecipeReviews';
import { getReviewsByRecipeId, addReview } from '../utils/chromaReviewUtils';
import { useAuth } from '../context/AuthContext';

const RecipeDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  // Removed unused folder modal state
  const [reviews, setReviews] = useState<Review[]>([]);
  
  // Fetch the recipe from the backend
  const { data: recipe, isLoading, error } = useQuery({
    queryKey: ['recipe', id],
    queryFn: async () => {
      if (!id) return null;
      try {
        const response = await fetch(`http://localhost:5003/get_recipe_by_id?id=${id}`);
        if (!response.ok) {
          throw new Error('Recipe not found');
        }
        const data = await response.json();
        
        // Normalize the recipe data
        return {
          ...data,
          // Ensure instructions is an array
          instructions: Array.isArray(data.instructions) 
            ? data.instructions 
            : data.instructions 
              ? [data.instructions] 
              : ['No instructions available'],
          // Ensure ingredients is an array
          ingredients: Array.isArray(data.ingredients) 
            ? data.ingredients 
            : data.ingredients 
              ? [data.ingredients] 
              : []
        };
      } catch (err) {
        console.error('Error fetching recipe:', err);
        throw err;
      }
    },
    enabled: !!id,
  });

  // Load reviews from ChromaDB
  useEffect(() => {
    const loadReviews = async () => {
      if (id) {
        try {
          const fetchedReviews = await getReviewsByRecipeId(id, 'local');
          console.log('Loaded reviews for recipe:', id, fetchedReviews);
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
  
  // Handle loading and error states
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p>Loading recipe...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !recipe) {
    return (
      <div className="flex flex-col min-h-screen">
        <Header />
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="text-center max-w-md">
            <h2 className="text-2xl font-bold mb-2">Recipe Not Found</h2>
            <p className="text-muted-foreground mb-6">
              The recipe you're looking for isn't available in your local collection.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button onClick={() => navigate(-1)} variant="outline" className="w-full sm:w-auto">
                <ArrowLeft className="mr-2 h-4 w-4" /> Back to recipes
              </Button>
              <Button onClick={() => navigate('/recipes')} variant="default" className="w-full sm:w-auto">
                Browse All Recipes
              </Button>
            </div>
          </div>
        </div>
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

  const toggleFavorite = () => {
    const updatedRecipe = {
      ...recipe,
      isFavorite: !recipe.isFavorite
    };
    
    updateRecipe(updatedRecipe);
    
    toast({
      title: updatedRecipe.isFavorite ? "Added to favorites" : "Removed from favorites",
      description: `"${recipe.name}" has been ${updatedRecipe.isFavorite ? 'added to' : 'removed from'} your favorites.`,
    });
    
    queryClient.invalidateQueries({ queryKey: ['recipes'] });
  };

  // Handler for submitting reviews
  const handleReviewSubmit = async (reviewData: { text: string, rating: number, author: string }) => {
    if (!id) return;
    
    const { text, rating, author } = reviewData;
    
    try {
      console.log('Submitting review:', { text, rating, author, recipeId: id });
      
      const savedReview = await addReview({
        recipeId: id,
        recipeType: 'local',
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

  // Add to shopping list functionality
  const addToShoppingList = () => {
    try {
      const existingItems = JSON.parse(localStorage.getItem('shopping-list') || '[]');
      
      const newItems: ShoppingListItem[] = recipe.ingredients.map(ingredient => ({
        id: uuidv4(),
        name: ingredient,
        completed: false,
        recipeId: recipe.id,
        recipeName: recipe.name
      }));
      
      const updatedItems = [...existingItems, ...newItems];
      localStorage.setItem('shopping-list', JSON.stringify(updatedItems));
      
      toast({
        title: "Added to shopping list",
        description: `${recipe.ingredients.length} ingredients from "${recipe.name}" have been added to your shopping list.`,
      });
    } catch (error) {
      console.error('Error adding to shopping list:', error);
      toast({
        title: 'Error',
        description: 'Failed to add ingredients to shopping list.',
        variant: 'destructive'
      });
    }
  };

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
                alt={recipe.name}
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = '/placeholder.svg';
                }}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex flex-col justify-end p-6">
                <h1 className="text-white text-3xl md:text-4xl font-bold">{recipe.name}</h1>
                <div className="flex items-center text-white mt-2">
                  <span className="text-sm">{recipe.cuisine}</span>
                  {avgRating > 0 && (
                    <div className="ml-4 flex items-center">
                      <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                      <span className="ml-1">{avgRating} ({reviews.length} {reviews.length === 1 ? 'review' : 'reviews'})</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div className="p-6 flex flex-wrap gap-3">
              <Button 
                onClick={toggleFavorite}
                variant={recipe.isFavorite ? "default" : "outline"}
                className="flex items-center gap-2"
              >
                <Heart 
                  className={recipe.isFavorite ? "text-white" : "text-red-500"} 
                  fill={recipe.isFavorite ? "currentColor" : "none"} 
                />
                {recipe.isFavorite ? "Remove from Favorites" : "Add to Favorites"}
              </Button>
              
              <RecipeFolderActions 
                recipeId={recipe.id}
                recipeType="local"
                recipeData={recipe}
              />
              
              <Button
                variant="outline"
                onClick={addToShoppingList}
                className="flex items-center gap-2"
              >
                <ShoppingCart className="h-4 w-4" />
                Add to Shopping List
              </Button>
            </div>

            {/* Recipe content */}
            <div className="p-6">
              {recipe.description && (
                <div className="mb-8 bg-blue-50 p-4 rounded-lg">
                  <h2 className="text-xl font-semibold mb-2">About This Recipe</h2>
                  <p className="text-gray-700">{recipe.description}</p>
                </div>
              )}
              
              <h2 className="text-2xl font-semibold mb-4">Ingredients</h2>
              <ul className="list-disc list-inside mb-6 space-y-2">
                {Array.isArray(recipe.ingredients) 
                  ? recipe.ingredients.map((ingredient, index) => {
                      // Handle different ingredient formats
                      let displayText = '';
                      
                      if (typeof ingredient === 'string') {
                        // If it's already a string, use it as is
                        displayText = ingredient;
                      } else if (ingredient.original) {
                        // Prefer the original format if available
                        displayText = ingredient.original;
                      } else if (ingredient.name) {
                        // Build from parts if no original is available
                        const parts = [
                          ingredient.amount,
                          ingredient.unit,
                          ingredient.name
                        ].filter(Boolean);
                        displayText = parts.join(' ');
                      } else {
                        // Fallback to JSON stringify if format is unknown
                        displayText = JSON.stringify(ingredient);
                      }
                      
                      // Clean up common formatting issues
                      displayText = displayText
                        .replace(/\.$/, '')  // Remove trailing period
                        .replace(/\s+/g, ' ')  // Collapse multiple spaces
                        .trim();
                      
                      return (
                        <li key={index} className="text-gray-700 pl-2 -indent-4 ml-4">
                          {displayText}
                        </li>
                      );
                    })
                  : <li className="text-gray-500 italic">No ingredients listed</li>
                }
              </ul>

              <h2 className="text-2xl font-semibold mb-4">Instructions</h2>
              <div className="mb-6">
                {(() => {
                  // Handle different instruction formats
                  let instructions: string[] = [];
                  
                  // Get instructions from recipe, handling both string and array formats
                  const instructionsSource = Array.isArray(recipe.instructions) 
                    ? recipe.instructions 
                    : recipe.instructions || '';
                  
                  // If it's a string, process it
                  if (typeof instructionsSource === 'string') {
                    // First, normalize line endings and clean up the string
                    let text = instructionsSource
                      .replace(/\r\n/g, '\n')  // Normalize line endings
                      .trim();
                    
                    // Try splitting by numbered steps (1., 2. etc.)
                    const numberedSteps = text.split(/(?<=\d+[\.\)])\s+/);
                    
                    // If we have multiple steps from numbering, use those
                    if (numberedSteps.length > 1) {
                      instructions = numberedSteps
                        .map(step => step.replace(/^\d+[\.\)]\s*/, '').trim())
                        .filter(step => step.length > 0);
                    } 
                    // Otherwise try splitting by double newlines
                    else {
                      const paragraphs = text.split(/\n\s*\n+/);
                      if (paragraphs.length > 1) {
                        instructions = paragraphs.map(p => p.trim()).filter(p => p.length > 0);
                      }
                      // As a last resort, split by periods or newlines
                      else {
                        instructions = text
                          .split(/(?<=\S[.!?])\s+(?=[A-Z])|\n/)
                          .map(step => step.trim())
                          .filter(step => step.length > 0);
                      }
                    }
                  } 
                  // If it's already an array, use it directly
                  else if (Array.isArray(instructionsSource)) {
                    instructions = instructionsSource;
                  }
                  
                  // Clean up each instruction
                  instructions = instructions
                    .map(step => {
                      // Remove any leading numbers or bullets
                      step = step.replace(/^\s*[\d•-]+\.?\s*/, '').trim();
                      // Capitalize first letter if it's a letter
                      if (step.length > 0 && /[a-z]/.test(step[0])) {
                        step = step.charAt(0).toUpperCase() + step.slice(1);
                      }
                      return step;
                    })
                    .filter(step => step.trim().length > 0);
                  
                  // If we have instructions, render them
                  if (instructions.length > 0) {
                    return (
                      <div className="space-y-6">
                        {instructions.map((step, index) => {
                          // Clean up the step text
                          let stepText = step.trim();
                          
                          // Remove trailing period if there's already punctuation
                          if (/[.!?]$/.test(stepText) && stepText.endsWith('..')) {
                            stepText = stepText.slice(0, -1);
                          }
                          
                          // Add a period if the step doesn't end with punctuation
                          if (!/[.!?]$/.test(stepText)) {
                            stepText += '.';
                          }
                          
                          return (
                            <div key={index} className="mb-6 last:mb-0">
                              <div className="flex group">
                                <div className="flex-shrink-0">
                                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-700 text-sm font-semibold mr-4 mt-0.5 group-hover:bg-blue-200 transition-colors">
                                    {index + 1}
                                  </div>
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-gray-700 leading-relaxed">
                                    {stepText}
                                  </p>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    );
                  }
                  
                  // Fallback if no instructions are found
                  return (
                    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                      <div className="flex">
                        <div className="flex-shrink-0">
                          <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <div className="ml-3">
                          <p className="text-sm text-yellow-700">
                            No detailed instructions available for this recipe.
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>
              
              {/* Reviews section */}
              <div className="mt-8 pt-6 border-t border-gray-200">
                <RecipeReviews
                  reviews={reviews}
                  onSubmitReview={handleReviewSubmit}
                  recipeType="local"
                />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default RecipeDetailPage;
