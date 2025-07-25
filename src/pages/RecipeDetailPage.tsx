import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Heart, Folder, ShoppingCart, Star, ArrowLeft } from 'lucide-react';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { updateRecipe, loadRecipes } from '../utils/storage';
import { useToast } from '@/hooks/use-toast';
import FolderAssignmentModal from '../components/FolderAssignmentModal';
import { Folder as FolderType, ShoppingListItem } from '../types/recipe';
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
  const [isFolderModalOpen, setIsFolderModalOpen] = useState(false);
  const [folders, setFolders] = useState<FolderType[]>([]);
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
  
  // Load folders from localStorage
  React.useEffect(() => {
    const loadFolders = () => {
      try {
        const storedFolders = localStorage.getItem('recipe-folders');
        return storedFolders ? JSON.parse(storedFolders) : [];
      } catch (error) {
        console.error('Failed to load folders:', error);
        return [];
      }
    };
    
    setFolders(loadFolders());
  }, []);

  // Handle loading and error states
  if (isLoading) {
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
            <h1 className="text-2xl font-bold mb-4">Loading recipe...</h1>
          </div>
        </main>
      </div>
    );
  }

  // Handle if recipe is not found
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

  const handleAssignFolder = (recipeId: string, folderId: string | undefined) => {
    const updatedRecipe = {
      ...recipe,
      folderId
    };
    
    updateRecipe(updatedRecipe);
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

  const currentFolder = folders.find(folder => folder.id === recipe.folderId);

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
              
              <Button 
                variant="outline"
                onClick={() => setIsFolderModalOpen(true)}
                className="flex items-center gap-2"
              >
                <Folder className="h-4 w-4" />
                {currentFolder ? `In: ${currentFolder.name}` : "Add to Folder"}
              </Button>
              
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
              <h2 className="text-2xl font-semibold mb-4">Ingredients</h2>
              <ul className="list-disc list-inside mb-6 space-y-1">
                {Array.isArray(recipe.ingredients) 
                  ? recipe.ingredients.map((ingredient, index) => {
                      // Handle both string and object formats
                      const ingredientText = typeof ingredient === 'string' 
                        ? ingredient 
                        : ingredient.name 
                          ? `${ingredient.amount || ''} ${ingredient.unit || ''} ${ingredient.name}`.trim()
                          : JSON.stringify(ingredient);
                      
                      return (
                        <li key={index} className="text-gray-700">
                          {ingredientText}
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
                  let instructions = [];
                  
                  if (Array.isArray(recipe.instructions)) {
                    instructions = recipe.instructions;
                  } else if (typeof recipe.instructions === 'string') {
                    // First try splitting by double newlines (common format)
                    instructions = recipe.instructions.split('\n\n');
                    
                    // If that doesn't give us multiple steps, try splitting by periods
                    if (instructions.length <= 1) {
                      instructions = recipe.instructions
                        .split(/(?<=\.)\s+(?=[A-Z])/) // Split on period followed by space and capital letter
                        .filter(step => step.trim().length > 0);
                    }
                    
                    // If we still don't have multiple steps, try splitting by numbered steps
                    if (instructions.length <= 1) {
                      instructions = recipe.instructions
                        .split(/(?<=\d+\.)\s+/)
                        .filter(step => step.trim().length > 0);
                    }
                  }
                  
                  if (instructions.length > 0) {
                    return (
                      <ol className="list-decimal pl-6 space-y-3">
                        {instructions.map((step, index) => (
                          <li key={index} className="text-gray-700 leading-relaxed pl-2">
                            {step.trim().replace(/^\.\s*/, '')}
                          </li>
                        ))}
                      </ol>
                    );
                  }
                  
                  return <p className="text-gray-500 italic">No instructions available</p>;
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
      
      <FolderAssignmentModal
        isOpen={isFolderModalOpen}
        onClose={() => setIsFolderModalOpen(false)}
        recipe={recipe}
        folders={folders}
        onAssignFolder={handleAssignFolder}
      />
    </div>
  );
};

export default RecipeDetailPage;
