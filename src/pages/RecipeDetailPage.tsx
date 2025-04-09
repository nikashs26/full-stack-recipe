
import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Star, MessageSquare, Trash2 } from 'lucide-react';
import { useToast } from "@/hooks/use-toast";
import Header from '../components/Header';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { getRecipeById, updateRecipe } from '../utils/storage';
import { Recipe, Comment } from '../types/recipe';
import { getDietaryTags } from '../utils/recipeUtils';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';

const RecipeDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const [newComment, setNewComment] = useState('');
  const [newRating, setNewRating] = useState(0);
  const [commentAuthor, setCommentAuthor] = useState('');
  const [showCommentForm, setShowCommentForm] = useState(false);

  // Use React Query to fetch and cache the recipe
  const { data: recipe, isLoading, error } = useQuery({
    queryKey: ['recipe', id],
    queryFn: () => {
      if (!id) throw new Error("Recipe ID is required");
      const foundRecipe = getRecipeById(id);
      if (!foundRecipe) throw new Error("Recipe not found");
      return foundRecipe;
    },
    staleTime: 60 * 1000 // 1 minute
  });

  useEffect(() => {
    if (error) {
      console.error('Failed to load recipe:', error);
      toast({
        title: "Error",
        description: "Failed to load recipe details. Redirecting to recipes page.",
        variant: "destructive",
      });
      setTimeout(() => navigate('/'), 2000);
    }
  }, [error, navigate, toast]);

  const handleAddComment = () => {
    if (newComment.trim() === '') {
      toast({
        title: "Comment required",
        description: "Please enter your comment before submitting.",
        variant: "destructive",
      });
      return;
    }

    if (newRating === 0) {
      toast({
        title: "Rating required",
        description: "Please select a rating before submitting your review.",
        variant: "destructive",
      });
      return;
    }

    if (!recipe) return;

    const author = commentAuthor.trim() || 'Anonymous';
    const newCommentObj: Comment = {
      id: Date.now().toString(),
      author,
      text: newComment,
      date: new Date().toISOString()
    };

    const updatedRecipe: Recipe = {
      ...recipe,
      comments: [...(recipe.comments || []), newCommentObj],
      ratings: [...(recipe.ratings || []), newRating]
    };

    updateRecipe(updatedRecipe);
    queryClient.invalidateQueries({ queryKey: ['recipe', id] });
    
    setNewComment('');
    setCommentAuthor('');
    setNewRating(0);
    setShowCommentForm(false);

    toast({
      title: "Review submitted",
      description: "Your review has been successfully added.",
    });
  };

  const handleDeleteComment = (commentId: string) => {
    if (!recipe) return;

    const commentIndex = recipe.comments.findIndex(c => c.id === commentId);
    
    if (commentIndex > -1) {
      const updatedComments = [...recipe.comments];
      updatedComments.splice(commentIndex, 1);
      
      // Optional: Also remove the associated rating if it exists
      let updatedRatings = [...recipe.ratings];
      if (commentIndex < updatedRatings.length) {
        updatedRatings.splice(commentIndex, 1);
      }
      
      const updatedRecipe = {
        ...recipe,
        comments: updatedComments,
        ratings: updatedRatings
      };
      
      updateRecipe(updatedRecipe);
      queryClient.invalidateQueries({ queryKey: ['recipe', id] });
      
      toast({
        title: "Review deleted",
        description: "The review has been removed."
      });
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

  const getAverageRating = (ratings: number[]) => {
    if (!ratings || ratings.length === 0) return 0;
    const sum = ratings.reduce((total, rating) => total + rating, 0);
    return (sum / ratings.length).toFixed(1);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link to="/" className="inline-flex items-center text-recipe-primary hover:text-recipe-primary/80 mb-6">
            <ArrowLeft className="mr-2 h-5 w-5" /> Back to Recipes
          </Link>
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-64 bg-gray-200 rounded mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          </div>
        </main>
      </div>
    );
  }

  if (!recipe) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link to="/" className="inline-flex items-center text-recipe-primary hover:text-recipe-primary/80 mb-6">
            <ArrowLeft className="mr-2 h-5 w-5" /> Back to Recipes
          </Link>
          <div className="text-center py-12">
            <h2 className="text-2xl font-medium text-gray-600">Recipe Not Found</h2>
            <p className="text-gray-500 mt-2">The recipe you're looking for doesn't exist or couldn't be loaded.</p>
            <Link 
              to="/" 
              className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-recipe-primary hover:bg-recipe-primary/90"
            >
              Go back to all recipes
            </Link>
          </div>
        </main>
      </div>
    );
  }

  const dietaryTags = getDietaryTags(recipe.dietaryRestrictions);
  const avgRating = getAverageRating(recipe.ratings || []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link to="/" className="inline-flex items-center text-recipe-primary hover:text-recipe-primary/80 mb-6">
          <ArrowLeft className="mr-2 h-5 w-5" /> Back to Recipes
        </Link>
        
        <article className="bg-white shadow-lg rounded-lg overflow-hidden animate-fade-in">
          <div className="relative h-80 w-full">
            <img 
              src={recipe.image || '/placeholder.svg'} 
              alt={recipe.name} 
              className="absolute inset-0 h-full w-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/placeholder.svg';
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
            <div className="absolute bottom-0 left-0 p-6 w-full">
              <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">{recipe.name}</h1>
              <p className="text-white/90 text-lg">
                Cuisine: {recipe.cuisine || "Other"}
              </p>
            </div>
          </div>
          
          <div className="p-6">
            <div className="flex flex-wrap items-center justify-between mb-6">
              <div className="flex items-center">
                {dietaryTags.map((tag, index) => (
                  <span key={index} className={`recipe-tag ${tag.class}`}>
                    {tag.text}
                  </span>
                ))}
              </div>
              
              <div className="flex items-center bg-gray-100 rounded-full px-3 py-1 text-sm">
                <Star className="h-5 w-5 text-yellow-500 mr-1" />
                <span>{avgRating} ({recipe.ratings?.length || 0} {recipe.ratings?.length === 1 ? 'rating' : 'ratings'})</span>
              </div>
            </div>
            
            {/* Recipe summary if available */}
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-3">Description</h2>
              <p className="text-gray-700">
                A delicious {recipe.dietaryRestrictions.join(', ')} {recipe.cuisine} recipe with {recipe.ingredients.length} ingredients.
              </p>
            </div>
            
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-3">Ingredients</h2>
              <ul className="space-y-2 pl-5">
                {recipe.ingredients.map((ingredient, index) => (
                  <li key={index} className="text-gray-700 flex items-start">
                    <span className="inline-block h-2 w-2 rounded-full bg-recipe-primary mt-2 mr-2"></span>
                    {ingredient}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-3">Instructions</h2>
              <ol className="space-y-4 pl-5">
                {recipe.instructions.map((instruction, index) => (
                  <li key={index} className="text-gray-700">
                    <span className="font-medium text-recipe-primary mr-2">{index + 1}.</span> {instruction}
                  </li>
                ))}
              </ol>
            </div>
            
            {/* Additional recipe info */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-50 p-3 rounded-lg text-center">
                <p className="text-gray-500 text-sm">Difficulty</p>
                <p className="font-medium">Medium</p>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg text-center">
                <p className="text-gray-500 text-sm">Servings</p>
                <p className="font-medium">4</p>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg text-center">
                <p className="text-gray-500 text-sm">Type</p>
                <p className="font-medium">Main Dish</p>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg text-center">
                <p className="text-gray-500 text-sm">Time</p>
                <p className="font-medium">45 min</p>
              </div>
            </div>
            
            {/* Reviews Section */}
            <div className="mt-8 border-t pt-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-gray-800 flex items-center">
                  <MessageSquare className="mr-2 h-5 w-5" /> Reviews
                </h2>
                {!showCommentForm && (
                  <button 
                    onClick={() => setShowCommentForm(true)}
                    className="px-4 py-2 bg-recipe-primary text-white rounded-md hover:bg-recipe-primary/90 transition-colors"
                  >
                    Write a Review
                  </button>
                )}
              </div>
              
              {/* Review Form */}
              {showCommentForm && (
                <Card className="mb-6">
                  <CardContent className="pt-6">
                    <div className="mb-4">
                      <label htmlFor="author" className="block text-sm font-medium text-gray-700 mb-1">
                        Your Name (optional)
                      </label>
                      <input
                        type="text"
                        id="author"
                        value={commentAuthor}
                        onChange={(e) => setCommentAuthor(e.target.value)}
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
                            onClick={() => setNewRating(rating)}
                            className="focus:outline-none"
                          >
                            <Star
                              className={`h-6 w-6 ${
                                rating <= newRating ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'
                              }`}
                            />
                          </button>
                        ))}
                      </div>
                    </div>
                    
                    <div className="mb-4">
                      <label htmlFor="comment" className="block text-sm font-medium text-gray-700 mb-1">
                        Your Review
                      </label>
                      <Textarea
                        id="comment"
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        placeholder="Write your review here..."
                        rows={4}
                        className="w-full"
                      />
                    </div>
                    
                    <div className="flex justify-end space-x-2">
                      <button
                        onClick={() => setShowCommentForm(false)}
                        className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleAddComment}
                        className="px-4 py-2 bg-recipe-primary text-white rounded-md hover:bg-recipe-primary/90 transition-colors"
                      >
                        Submit Review
                      </button>
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {/* Reviews List */}
              {recipe.comments && recipe.comments.length > 0 ? (
                <div className="space-y-4">
                  {recipe.comments.map((comment, index) => (
                    <Card key={comment.id} className="bg-gray-50">
                      <CardContent className="pt-6">
                        <div className="flex justify-between">
                          <h3 className="font-medium">{comment.author}</h3>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-500">{formatDate(comment.date)}</span>
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-6 w-6 text-gray-500 hover:text-red-500">
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>Delete this review?</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    This action cannot be undone. This will permanently delete the review.
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                                  <AlertDialogAction onClick={() => handleDeleteComment(comment.id)}>
                                    Delete
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          </div>
                        </div>
                        <div className="flex items-center mt-1 mb-3">
                          {recipe.ratings && recipe.ratings[index] && (
                            <>
                              {[1, 2, 3, 4, 5].map((rating) => (
                                <Star
                                  key={rating}
                                  className={`h-4 w-4 ${
                                    rating <= recipe.ratings[index] ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'
                                  }`}
                                />
                              ))}
                            </>
                          )}
                        </div>
                        <p className="text-gray-700">{comment.text}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 italic">No reviews yet. Be the first to review this recipe!</p>
              )}
            </div>
          </div>
        </article>
      </main>
    </div>
  );
};

export default RecipeDetailPage;
