import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Star, MessageSquare } from 'lucide-react';
import Header from '../components/Header';
import { useToast } from "@/hooks/use-toast";
import { useQuery } from '@tanstack/react-query';
import { fetchRecipeById } from '../lib/spoonacular';
import { SpoonacularRecipe } from '../types/spoonacular';
import { getDietaryTags } from '../utils/recipeUtils';
import { formatDescriptionIntoParagraphs, formatInstructions } from '../utils/formatUtils';
import { DietaryRestriction } from '../types/recipe';
import { Card, CardContent } from "../components/ui/card";
import { Textarea } from "../components/ui/textarea";
import RecipeReviews from '../components/RecipeReviews';

// New types for external recipe reviews
interface ExternalReview {
  id: string;
  author: string;
  text: string;
  date: string;
  rating: number;
}

const ExternalRecipeDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const numericId = id ? parseInt(id) : 0;
  const navigate = useNavigate();
  const { toast } = useToast();
  const [recipe, setRecipe] = useState<SpoonacularRecipe | null>(null);
  const [reviews, setReviews] = useState<ExternalReview[]>([]);
  const [newReview, setNewReview] = useState("");
  const [selectedRating, setSelectedRating] = useState(0);
  const [reviewAuthor, setReviewAuthor] = useState("");
  const [showReviewForm, setShowReviewForm] = useState(false);
  
  // Fetch the external recipe data by ID
  const { data, isLoading, error } = useQuery({
    queryKey: ['externalRecipe', numericId],
    queryFn: () => fetchRecipeById(numericId),
    enabled: !!numericId,
    staleTime: 60 * 1000, // 1 minute
    retry: 2,
  });

  // Load saved reviews from localStorage
  useEffect(() => {
    if (id) {
      const savedReviews = localStorage.getItem(`external-reviews-${id}`);
      if (savedReviews) {
        setReviews(JSON.parse(savedReviews));
      }
    }
  }, [id]);

  // Save reviews to localStorage when they change
  useEffect(() => {
    if (id && reviews.length > 0) {
      localStorage.setItem(`external-reviews-${id}`, JSON.stringify(reviews));
    }
  }, [id, reviews]);

  useEffect(() => {
    if (data) {
      console.log("Loaded recipe details:", data);
      setRecipe(data);
    }
  }, [data]);

  useEffect(() => {
    if (error) {
      console.error("Error loading recipe:", error);
      toast({
        title: "Error loading recipe",
        description: "Could not load the recipe details. Please try again later.",
        variant: "destructive",
      });
    }
  }, [error, toast]);

  const handleReviewSubmit = (reviewData: { text: string, rating: number, author: string }) => {
    const { text, rating, author } = reviewData;
    
    const newReviewObj: ExternalReview = {
      id: Date.now().toString(),
      author: author || "Anonymous",
      text,
      date: new Date().toISOString(),
      rating
    };

    setReviews([...reviews, newReviewObj]);
    setNewReview("");
    setReviewAuthor("");
    setSelectedRating(0);
    setShowReviewForm(false);
    
    toast({
      title: "Review submitted",
      description: "Your review has been successfully added.",
    });
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const getAverageRating = () => {
    if (reviews.length === 0) return 0;
    const sum = reviews.reduce((total, review) => total + review.rating, 0);
    return (sum / reviews.length).toFixed(1);
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

  // Extract ingredients from the recipe
  const ingredients = recipe.extendedIngredients?.map(ing => 
    ing.originalString || ing.original || `${ing.amount} ${ing.unit} ${ing.name}`
  ) || [];
  
  // Extract and format instructions from the recipe
  let instructions: string[] = [];
  if (recipe.instructions) {
    // Use our new formatInstructions utility
    instructions = formatInstructions(recipe.instructions);
  } else if (recipe.analyzedInstructions && recipe.analyzedInstructions.length > 0) {
    // Or use analyzed instructions
    instructions = recipe.analyzedInstructions[0].steps.map(s => s.step);
  }

  // Make dietary info match the format of regular recipes
  const dietaryRestrictions = (recipe.diets || []).map(diet => {
    if (diet.includes('vegetarian')) return 'vegetarian';
    if (diet.includes('vegan')) return 'vegan'; 
    if (diet.includes('gluten-free')) return 'gluten-free';
    return diet;
  }) as DietaryRestriction[];
  
  const dietaryTags = getDietaryTags(dietaryRestrictions);
  const avgRating = getAverageRating();
  
  // Format the description into paragraphs
  const formattedSummary = recipe.summary ? formatDescriptionIntoParagraphs(recipe.summary) : '';

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
              alt={recipe.title || "Recipe"} 
              className="absolute inset-0 h-full w-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/placeholder.svg';
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
            <div className="absolute bottom-0 left-0 p-6 w-full">
              <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">{recipe.title || "Untitled Recipe"}</h1>
              <p className="text-white/90 text-lg">
                Cuisine: {recipe.cuisines && recipe.cuisines.length > 0 
                  ? recipe.cuisines[0] 
                  : "Other"}
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
                <span>{avgRating} ({reviews.length} {reviews.length === 1 ? 'rating' : 'ratings'})</span>
              </div>
            </div>

            {/* Recipe summary with formatted paragraphs */}
            {formattedSummary && (
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-800 mb-3">Summary</h2>
                <div className="text-gray-700 space-y-4" dangerouslySetInnerHTML={{ __html: formattedSummary }} />
              </div>
            )}
            
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-3">Ingredients</h2>
              <ul className="space-y-2 pl-5">
                {ingredients.length > 0 ? (
                  ingredients.map((ingredient, index) => (
                    <li key={index} className="text-gray-700 flex items-start">
                      <span className="inline-block h-2 w-2 rounded-full bg-recipe-primary mt-2 mr-2"></span>
                      {ingredient}
                    </li>
                  ))
                ) : (
                  <li className="text-gray-500">No ingredients information available</li>
                )}
              </ul>
            </div>
            
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-3">Instructions</h2>
              <ol className="space-y-4 pl-5">
                {instructions.length > 0 ? (
                  instructions.map((instruction, index) => (
                    <li key={index} className="text-gray-700">
                      <span className="font-medium text-recipe-primary mr-2">{index + 1}.</span> {instruction}
                    </li>
                  ))
                ) : (
                  <li className="text-gray-500">No instructions available</li>
                )}
              </ol>
            </div>

            {/* Additional recipe info */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              {recipe.readyInMinutes && (
                <div className="bg-gray-50 p-3 rounded-lg text-center">
                  <p className="text-gray-500 text-sm">Prep Time</p>
                  <p className="font-medium">{recipe.readyInMinutes} min</p>
                </div>
              )}
              {recipe.servings && (
                <div className="bg-gray-50 p-3 rounded-lg text-center">
                  <p className="text-gray-500 text-sm">Servings</p>
                  <p className="font-medium">{recipe.servings}</p>
                </div>
              )}
              {recipe.dishTypes && recipe.dishTypes.length > 0 && (
                <div className="bg-gray-50 p-3 rounded-lg text-center">
                  <p className="text-gray-500 text-sm">Type</p>
                  <p className="font-medium">{recipe.dishTypes[0]}</p>
                </div>
              )}
              {recipe.sourceUrl && (
                <div className="bg-gray-50 p-3 rounded-lg text-center">
                  <p className="text-gray-500 text-sm">Source</p>
                  <a 
                    href={recipe.sourceUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="font-medium text-recipe-primary hover:underline"
                  >
                    View Original
                  </a>
                </div>
              )}
            </div>

            {/* Reviews Section - Using the shared component */}
            <RecipeReviews
              reviews={reviews}
              onSubmitReview={handleReviewSubmit}
              recipeType="external"
            />
          </div>
        </article>
      </main>
    </div>
  );
};

export default ExternalRecipeDetailPage;
