import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Heart, ShoppingCart, Star, ArrowLeft, Clock, Users } from 'lucide-react';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { updateRecipe } from '../utils/storage';
import { useToast } from '@/hooks/use-toast';
import { Folder as FolderType, ShoppingListItem as ShoppingListItemType, Recipe, DietaryRestriction } from '../types/recipe';
import { v4 as uuidv4 } from 'uuid';
import RecipeReviews, { Review } from '../components/RecipeReviews';
import { getReviewsByRecipeId, addReview } from '../utils/chromaReviewUtils';
import { useAuth } from '../context/AuthContext';

type Ingredient = string | { name: string; amount?: string };

interface FormattedInstruction {
  step: number;
  instruction: string;
}

interface RecipeWithFavorites extends Omit<Recipe, 'ingredients' | 'instructions'> {
  isFavorite: boolean;
  folderId?: string;
  readyInMinutes?: number;
  ingredients: Array<string | { name: string; amount?: string }>;
  instructions: string[];
  imageUrl?: string;
  title?: string;
  cookingTime?: string;
  difficulty?: string;
  dietaryRestrictions?: (DietaryRestriction | string)[];
  // Add other optional fields that might be present
  description?: string;
  servings?: number;
  name?: string;
}

const convertToFraction = (decimal: number): string => {
  if (decimal % 1 === 0) return decimal.toString();
  
  const tolerance = 1.0e-6;
  let h1 = 1, h2 = 0;
  let k1 = 0, k2 = 1;
  let b = decimal;
  
  do {
    const a = Math.floor(b);
    let aux = h1;
    h1 = a * h1 + h2;
    h2 = aux;
    aux = k1;
    k1 = a * k1 + k2;
    k2 = aux;
    b = 1 / (b - a);
  } while (Math.abs(decimal - h1 / k1) > decimal * tolerance);

  if (k1 === 1) return h1.toString();
  return `${h1}/${k1}`;
};

const RecipeDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [isFolderModalOpen, setIsFolderModalOpen] = useState(false);
  const [folders, setFolders] = useState<FolderType[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [servings, setServings] = useState(4);
  const [formattedInstructions, setFormattedInstructions] = useState<FormattedInstruction[]>([]);
  const [avgRating, setAvgRating] = useState(0);
  const [isFavorite, setIsFavorite] = useState(false);
  const [shoppingList, setShoppingList] = useState<ShoppingListItemType[]>([]);

  const { data: recipe, isLoading, error } = useQuery<RecipeWithFavorites>({
    queryKey: ['recipe', id],
    queryFn: async () => {
      if (!id) throw new Error('No recipe ID provided');
      const response = await fetch(`http://localhost:5003/get_recipe_by_id?id=${id}`);
      if (!response.ok) throw new Error('Failed to fetch recipe');
      const data = await response.json();
      return { 
        ...data, 
        isFavorite: false,
        ingredients: data.ingredients || [],
      };
    },
    enabled: !!id,
  });

  useEffect(() => {
    const fetchReviews = async () => {
      if (!id) return;
      try {
        const recipeReviews = await getReviewsByRecipeId(id);
        setReviews(recipeReviews);
        if (recipeReviews.length > 0) {
          const average = recipeReviews.reduce((sum, review) => sum + review.rating, 0) / recipeReviews.length;
          setAvgRating(parseFloat(average.toFixed(1)));
        }
      } catch (err) {
        console.error('Error fetching reviews:', err);
      }
    };

    fetchReviews();
  }, [id]);

  useEffect(() => {
    if (recipe?.instructions) {
      const instructions = Array.isArray(recipe.instructions) 
        ? recipe.instructions.join(' ')
        : String(recipe.instructions || '');

      const instructionsArray = instructions
        .split('.')
        .filter(step => step.trim() !== '')
        .map((step, index) => ({
          step: index + 1,
          instruction: step.trim() + (step.trim().endsWith('.') ? '' : '.')
        }));
      setFormattedInstructions(instructionsArray);
    } else {
      setFormattedInstructions([]);
    }
  }, [recipe]);

  const handleAddToShoppingList = useCallback((ingredients: Ingredient[]) => {
    if (!recipe) return;
    
    const newItems: ShoppingListItemType[] = ingredients.map(ing => {
      const ingredientName = typeof ing === 'string' ? ing : ing.name;
      return {
        id: uuidv4(),
        ingredient: ingredientName,
        recipeId: id || '',
        recipeName: recipe.title || recipe.name || 'Unknown Recipe',
        checked: false
      };
    });

    setShoppingList(prev => [...prev, ...newItems]);
    toast({
      title: 'Added to Shopping List',
      description: `${newItems.length} items added to your shopping list.`,
      variant: 'default',
    });
  }, [id, recipe?.title, toast]);

  const toggleFavorite = useCallback(async () => {
    if (!recipe) return;
    
    const updatedRecipe = { 
      ...recipe, 
      isFavorite: !isFavorite,
      title: recipe.title || recipe.name || ''
    };
    
    setIsFavorite(prev => !prev);
    
    try {
      await updateRecipe(updatedRecipe);
      queryClient.invalidateQueries({ queryKey: ['recipe', id] });
    } catch (error) {
      console.error('Error updating favorite status:', error);
      setIsFavorite(prev => !prev); // Revert on error
    }
  }, [recipe, isFavorite, queryClient, id]);

  const handleSubmitReview = useCallback(async (rating: number, comment: string) => {
    if (!user) {
      toast({
        title: 'Authentication Required',
        description: 'Please sign in to leave a review.',
        variant: 'destructive',
      });
      return;
    }

    const newReview: Review = {
      id: uuidv4(),
      author: user.email || 'Anonymous',
      text: comment,
      rating,
      date: new Date().toISOString(),
    };

    try {
      await addReview({
        recipeId: id || '',
        recipeType: 'external',
        author: user.email || 'Anonymous',
        text: comment,
        rating,
      });
      
      setReviews(prev => [...prev, newReview]);
      const newAvg = [...reviews, newReview].reduce((acc, curr) => acc + (curr.rating || 0), 0) / (reviews.length + 1);
      setAvgRating(parseFloat(newAvg.toFixed(1)));
      
      toast({
        title: 'Review Submitted',
        description: 'Thank you for your review!',
        variant: 'default',
      });
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to submit review. Please try again.',
        variant: 'destructive',
      });
    }
  }, [id, reviews, toast, user]);

  const adjustedIngredients = useMemo(() => {
    if (!recipe?.ingredients) return [];
    return recipe.ingredients.map(ing => ({
      ...ing,
      amount: (ing.amount / (recipe.servings || 1)) * servings,
      original: `${convertToFraction(ing.amount)} ${ing.unit} ${ing.name}`
    }));
  }, [recipe?.ingredients, recipe?.servings, servings]);

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  if (error) {
    return <div className="flex items-center justify-center min-h-screen">Error loading recipe: {error.message}</div>;
  }

  if (!recipe) {
    return <div className="flex items-center justify-center min-h-screen">Recipe not found</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="max-w-6xl mx-auto px-4 py-8">
        <Button 
          variant="ghost" 
          onClick={() => navigate(-1)}
          className="mb-6 flex items-center gap-2"
        >
          <ArrowLeft size={16} /> Back to Recipes
        </Button>

        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          {/* Recipe Header */}
          <div className="p-6 border-b">
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">{recipe.title}</h1>
                {recipe.description && <p className="text-gray-600 mt-2">{recipe.description}</p>}
                
                <div className="flex items-center mt-4 space-x-6">
                  {recipe.readyInMinutes && (
                    <div className="flex items-center text-sm text-gray-500">
                      <Clock className="mr-1.5 h-4 w-4" />
                      {recipe.readyInMinutes} min
                    </div>
                  )}
                  <div className="flex items-center text-sm text-gray-500">
                    <Users className="mr-1.5 h-4 w-4" />
                    {servings} servings
                  </div>
                  <div className="flex items-center text-sm text-gray-500">
                    <Star className="mr-1.5 h-4 w-4 text-yellow-400 fill-current" />
                    {avgRating > 0 ? avgRating.toFixed(1) : 'No ratings yet'}
                  </div>
                </div>
              </div>

              <div className="flex space-x-2">
                <Button
                  variant={isFavorite ? 'default' : 'outline'}
                  size="icon"
                  onClick={toggleFavorite}
                >
                  <Heart className={`h-5 w-5 ${isFavorite ? 'fill-current' : ''}`} />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setIsFolderModalOpen(true)}
                >
                  <Folder className="h-5 w-5" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => handleAddToShoppingList(recipe.ingredients || [])}
                >
                  <ShoppingCart className="h-5 w-5" />
                </Button>
              </div>
            </div>
          </div>

          <div className="md:flex">
            {/* Recipe Image */}
            {recipe.image && (
              <div className="md:w-1/2 p-6">
                <img
                  src={recipe.image}
                  alt={recipe.title}
                  className="w-full h-auto rounded-lg object-cover shadow-md"
                />
              </div>
            )}

            {/* Ingredients */}
            <div className={`${recipe.image ? 'md:w-1/2' : 'w-full'} p-6`}>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">Ingredients</h2>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setServings(s => Math.max(1, s - 1))}
                    disabled={servings <= 1}
                  >
                    <Minus className="h-4 w-4" />
                  </Button>
                  <span className="text-sm font-medium">{servings} servings</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setServings(s => s + 1)}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <ul className="space-y-2">
                {adjustedIngredients.map((ingredient, index) => (
                  <li key={index} className="flex items-start">
                    <span className="inline-block w-6 h-6 flex items-center justify-center bg-gray-100 rounded-full text-sm mr-2 mt-0.5">
                      {index + 1}
                    </span>
                    <span>
                      <span className="font-medium">
                        {ingredient.amount % 1 !== 0 
                          ? convertToFraction(ingredient.amount) 
                          : ingredient.amount}
                        {' '}{ingredient.unit}
                      </span>{' '}
                      {ingredient.name}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Instructions */}
          {formattedInstructions.length > 0 && (
            <div className="p-6 border-t">
              <h2 className="text-xl font-semibold mb-4">Instructions</h2>
              <div className="space-y-4">
                {formattedInstructions.map((step) => (
                  <div key={step.step} className="flex">
                    <span className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-800 font-medium mr-3">
                      {step.step}
                    </span>
                    <p className="text-gray-700">{step.instruction}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Reviews */}
          <div className="p-6 border-t">
            <RecipeReviews
              recipeId={id || ''}
              reviews={reviews}
              averageRating={avgRating}
              onReviewSubmit={handleSubmitReview}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecipeDetailPage;

// Interfaces
type Ingredient = {
  id?: string;
  name: string;
  amount?: number | string;
  unit?: string;
};

type FormattedInstruction = {
  step: number;
  text: string;
};

type RecipeWithFavorites = Recipe & {
  isFavorite?: boolean;
  folderId?: string;
};

// Helper function to convert decimal to fraction
const convertToFraction = (decimal: number): string => {
  if (decimal % 1 === 0) return decimal.toString();
  
  const tolerance = 0.01;
  const fractions: Array<[number, string]> = [
    [1/2, '½'],
    [1/3, '⅓'],
    [2/3, '⅔'],
    [1/4, '¼'],
    [3/4, '¾'],
    [1/8, '⅛'],
    [3/8, '⅜'],
    [5/8, '⅝'],
    [7/8, '⅞']
  ];

  for (const [value, fraction] of fractions) {
    if (Math.abs(decimal - value) < tolerance) return fraction;
    if (Math.abs(decimal - (1 - value)) < tolerance) return `1${fraction}`;
  }
  
  return decimal.toFixed(2).replace(/\.?0+$/, '');
};

// Interfaces
export interface Ingredient {
  id?: string;
  name: string;
  amount?: number | string;
  unit?: string;
}

export interface FormattedInstruction {
  step: number;
  text: string;
}

export interface RecipeWithFavorites extends Recipe {
  isFavorite?: boolean;
  folderId?: string;
}

// Helper function to convert decimal to fraction
const convertToFraction = (decimal: number): string => {
  if (decimal % 1 === 0) return decimal.toString();
  
  const tolerance = 0.01;
  const fractions = [
    [1/2, '½'],
    [1/3, '⅓'],
    [2/3, '⅔'],
    [1/4, '¼'],
    [3/4, '¾'],
    [1/8, '⅛'],
    [3/8, '⅜'],
    [5/8, '⅝'],
    [7/8, '⅞']
  ];

  for (const [value, fraction] of fractions) {
    if (Math.abs(decimal - value) < tolerance) return fraction;
    if (Math.abs(decimal - (1 - value)) < tolerance) return `1${fraction}`;
  }
  
  return decimal.toFixed(2).replace(/\.?0+$/, '');
};

interface Ingredient {
  id?: string;
  name: string;
  amount?: number | string;
  unit?: string;
}

interface FormattedInstruction {
  step: number;
  text: string;
}

interface RecipeWithFavorites extends Recipe {
  isFavorite?: boolean;
  folderId?: string;
}

const RecipeDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  // State management
  const [isFolderModalOpen, setIsFolderModalOpen] = useState(false);
  const [folders, setFolders] = useState<FolderType[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [servings, setServings] = useState(4);
  const [formattedInstructions, setFormattedInstructions] = useState<FormattedInstruction[]>([]);
  const [avgRating, setAvgRating] = useState(0);
  const [isFavorite, setIsFavorite] = useState(false);
  
  // Calculate average rating
  const calculateAverageRating = useCallback((reviewsList: Review[]): number => {
    if (!reviewsList || reviewsList.length === 0) {
      setAvgRating(0);
      return 0;
    }
    const sum = reviewsList.reduce((total, review) => total + (review.rating || 0), 0);
        step: index + 1,
        text: step.trim()
      }));
  } else {
    steps = (instructions as string)
      .split(/\n+|\d+\.\s*|•\s*|\*\s*|~\s*|\d+\)\s*/)
      .filter(step => step.trim() !== '')
      .map((step, index) => ({
        step: index + 1,
        text: step.trim().replace(/^[^a-zA-Z0-9]+/, '')
      const adjustedAmount = (amount / originalServings) * servings;
      amount = Math.round(adjustedAmount * 100) / 100; // Round to 2 decimal places
    }
    
    const unit: string = ingredient.unit ? ` ${ingredient.unit}` : '';
    const name: string = ingredient.name ? ` ${ingredient.name}` : '';
    
    // Format decimal numbers to fractions for better readability
    if (amount && Number.isInteger(amount)) {
      return `${amount}${unit}${name}`.trim();
    } else if (amount) {
      // Convert decimal to fraction for common measurements
      const fractionParts = convertToFraction(amount);
      return `${fractionParts}${unit}${name}`.trim();
    }
    
    return name.trim();
  }, [recipe?.servings, servings]);
  
  // Add missing state declarations
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { id } = useParams<{ id: string }>();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [isFolderModalOpen, setIsFolderModalOpen] = useState(false);
  const [currentFolder, setCurrentFolder] = useState<FolderType | null>(null);
  const [folders, setFolders] = useState<FolderType[]>([]);
  
  // Fetch recipe data
  const { data: recipe, isLoading, error } = useQuery<Recipe>({
    queryKey: ['recipe', id],
    queryFn: async () => {
      const response = await fetch(`/api/recipes/${id}`);
      if (!response.ok) {
        throw new Error('Failed to fetch recipe');
      }
      return response.json();
    },
    enabled: !!id,
  });
    
    // Format decimal numbers to fractions for better readability
    if (amount && Number.isInteger(amount)) {
      return `${amount}${unit}${name}`.trim();
    } else if (amount) {
      // Convert decimal to fraction for common measurements
      const fractionParts = convertToFraction(amount);
      return `${fractionParts}${unit}${name}`.trim();
    }
    
    return name.trim();
  };

  // Convert decimal to fraction for better readability
  const convertToFraction = (decimal: number): string => {
    const tolerance = 1.0E-6;
    const fractions = [
      [1.0, ''], [0.5, '½'], [0.25, '¼'], [0.75, '¾'],
      [0.33, '⅓'], [0.66, '⅔'], [0.2, '⅕'], [0.4, '⅖'],
      [0.6, '⅗'], [0.8, '⅘'], [0.125, '⅛'], [0.375, '⅜'],
      [0.625, '⅝'], [0.875, '⅞'], [0.166, '⅙'], [0.833, '⅚']
    ];

    // Check for whole numbers
    const whole = Math.floor(decimal);
    let remainder = decimal - whole;
    
    // Find the closest fraction
    let closestFraction = '';
    let minDiff = 1;
    
    for (const [value, fraction] of fractions) {
      const diff = Math.abs(remainder - value);
      if (diff < minDiff) {
        minDiff = diff;
        closestFraction = fraction as string;
      }
    }
    
    // Only use fraction if it's a good match
    if (minDiff < tolerance) {
      if (whole > 0) {
        return `${whole} ${closestFraction}`.trim();
      }
      return closestFraction;
    }
    
    // Otherwise round to 2 decimal places
    return decimal.toFixed(2);
  };

  // Toggle favorite status
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

  const currentFolder = recipe ? folders.find(folder => folder.id === (recipe as any).folderId) : null;

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
        
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          {/* Recipe header with image */}
          <div className="relative h-64 md:h-96">
            <img
              src={recipe.image || '/placeholder-recipe.jpg'}
              alt={recipe.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                if (target.src !== '/placeholder-recipe.jpg') {
                  target.src = '/placeholder-recipe.jpg';
                }
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex flex-col justify-end p-6">
              <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
                {recipe.title}
              </h1>
              <div className="flex items-center space-x-4 text-white/90">
                <div className="flex items-center">
                  <Clock className="h-5 w-5 mr-1" />
                  <span>{recipe.ready_in_minutes || 'N/A'} min</span>
                </div>
                <div className="flex items-center">
                  <Users className="h-5 w-5 mr-1" />
                  <span>{servings} {servings === 1 ? 'serving' : 'servings'}</span>
                </div>
                <div className="flex items-center">
                  <Star className="h-5 w-5 text-yellow-400 mr-1" />
                  <span>{isNaN(avgRating) ? 'N/A' : avgRating} ({reviews.length} {reviews.length === 1 ? 'review' : 'reviews'})</span>
                </div>
              </div>
            </div>
          </div>

          {/* Recipe content */}
          <div className="p-6">
            {/* Description */}
            {recipe.description && (
              <div className="mb-8 bg-blue-50 p-4 rounded-lg">
                <p className="text-gray-700">{recipe.description}</p>
              </div>
            )}

            <div className="grid md:grid-cols-3 gap-8">
              {/* Ingredients */}
              <div className="md:col-span-1">
                <div className="sticky top-4">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-2xl font-bold text-gray-800 flex items-center">
                      <Utensils className="h-5 w-5 mr-2 text-primary" />
                      Ingredients
                    </h2>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">Servings:</span>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => setServings(prev => Math.max(1, prev - 1))}
                        className="h-8 w-8 p-0"
                      >
                        <Minus className="h-4 w-4" />
                      </Button>
                      <span className="w-8 text-center">{servings}</span>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => setServings(prev => prev + 1)}
                        className="h-8 w-8 p-0"
                      >
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  
                  <ul className="space-y-3">
                    {Array.isArray(recipe.ingredients) 
                      ? recipe.ingredients.map((ingredient, index) => (
                          <li key={index} className="flex items-start">
                            <span className="inline-block w-2 h-2 rounded-full bg-primary mt-2 mr-2 flex-shrink-0"></span>
                            <span className="text-gray-700">
                              {formatIngredientAmount(ingredient)}
                            </span>
                          </li>
                        ))
                      : <li className="text-gray-500 italic">No ingredients listed</li>
                    }
                  </ul>

                  <div className="mt-6">
                    <Button 
                      variant="outline" 
                      className="w-full"
                      onClick={() => {
                        // Add to shopping list logic here
                        toast({
                          title: "Added to shopping list",
                          description: "All ingredients have been added to your shopping list.",
                        });
                      }}
                    >
                      <ShoppingCart className="h-4 w-4 mr-2" />
                      Add to Shopping List
                    </Button>
                  </div>
                </div>
              </div>

              {/* Instructions */}
              <div className="md:col-span-2">
                <div className="bg-white p-6 rounded-lg border border-gray-100">
                  <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                    <BookOpen className="h-5 w-5 mr-2 text-primary" />
                    Instructions
                  </h2>
                  
                  <div className="space-y-6">
                    {formattedInstructions.length > 0 ? (
                      formattedInstructions.map((step, index) => (
                        <div key={index} className="flex group">
                          <div className="flex-shrink-0">
                            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-white font-bold mr-4 mt-0.5">
                              {step.step}
                            </div>
                          </div>
                          <div className="pb-6 border-l-2 border-gray-100 pl-6 relative">
                            <div className="absolute left-0 top-2 w-2 h-2 rounded-full bg-primary -ml-1"></div>
                            <p className="text-gray-700 leading-relaxed">
                              {step.text}
                            </p>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-8">
                        <p className="text-gray-500 italic">No instructions available for this recipe.</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Recipe Notes */}
                {recipe.notes && (
                  <div className="mt-8 bg-yellow-50 p-4 rounded-lg border border-yellow-100">
                    <h3 className="font-semibold text-yellow-800 mb-2">Chef's Notes</h3>
                    <p className="text-yellow-700">{recipe.notes}</p>
                  </div>
                )}

                {/* Reviews Section */}
                <div className="mt-12">
                  <h2 className="text-2xl font-bold text-gray-800 mb-6">Reviews</h2>
                  <RecipeReviews
                    reviews={reviews}
                    onSubmitReview={handleReviewSubmit}
                    recipeType="local"
                  />
                </div>
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
