import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Clock, ChefHat, Star, Utensils, Globe } from 'lucide-react';
import Header from '../components/Header';
import { fetchRecipeById } from '../lib/spoonacular';
import { Button } from '@/components/ui/button';
import RecipeReviews, { Review } from '../components/RecipeReviews';
import { getReviewsByRecipeId, addReview } from '../utils/chromaReviewUtils';
import { useToast } from '@/hooks/use-toast';
import { cleanRecipeDescription } from '../utils/recipeDescriptionCleaner';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Recipe } from '../types/recipe';

type RecipeSource = 'spoonacular' | 'themealdb';

interface ExternalRecipeDetailLocationState {
  source?: RecipeSource;
}

const ExternalRecipeDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();
  const [reviews, setReviews] = useState<Review[]>([]);
  
  // Determine the source from location state or default to spoonacular
  const source = (location.state as ExternalRecipeDetailLocationState)?.source || 'spoonacular';
  
  const { data: recipe, isLoading, error } = useQuery({
    queryKey: ['external-recipe', source, id],
    queryFn: async () => {
      if (source === 'themealdb') {
        const response = await fetch(`http://localhost:5003/api/mealdb/recipe/${id}`);
        if (!response.ok) throw new Error('Failed to fetch recipe from TheMealDB');
        return await response.json();
      } else {
        return await fetchRecipeById(parseInt(id!));
      }
    },
    enabled: !!id,
  });

  // Load reviews from ChromaDB
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
      
      const savedReview = await addReview({
        recipeId: id,
        recipeType: 'external',
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

  // Get the cuisine for display
  const cuisine = (() => {
    if (source === 'themealdb') {
      return recipe.strArea || 'International';
    }
    if (recipe.cuisines && recipe.cuisines.length > 0) {
      return Array.isArray(recipe.cuisines) ? recipe.cuisines[0] : recipe.cuisines;
    }
    return 'International';
  })();

  // Get the recipe name
  const recipeName = (() => {
    if (source === 'themealdb') return recipe.strMeal || 'Unnamed Recipe';
    return recipe.title || recipe.name || 'Unnamed Recipe';
  })();

  // Get the recipe source URL
  const getSourceUrl = () => {
    if (source === 'themealdb') return recipe.strSource || `https://www.themealdb.com/meal/${id}`;
    if (recipe.sourceUrl) return recipe.sourceUrl;
    if (recipe.spoonacularSourceUrl) return recipe.spoonacularSourceUrl;
    return '#';
  };

  // Get the recipe image
  const getRecipeImage = () => {
    if (source === 'themealdb') {
      return recipe.strMealThumb || '/placeholder.svg';
    }
    if (recipe.image && recipe.image.trim()) {
      return recipe.image;
    }
    return 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=800&q=80';
  };

  // Extract ingredients and measurements from TheMealDB recipe
  const extractMealDBIngredients = (meal: any): {name: string, measure: string}[] => {
    const ingredients = [];
    for (let i = 1; i <= 20; i++) {
      const ingredient = meal[`strIngredient${i}`];
      const measure = meal[`strMeasure${i}`];
      if (ingredient && ingredient.trim() !== '') {
        ingredients.push({
          name: ingredient,
          measure: measure || ''
        });
      }
    }
    return ingredients;
  };

  // Get the recipe ingredients
  const getIngredients = () => {
    if (source === 'themealdb') {
      return extractMealDBIngredients(recipe);
    }
    if (recipe.extendedIngredients) {
      return recipe.extendedIngredients.map((ing: any) => ({
        name: ing.name,
        amount: ing.amount,
        unit: ing.unit
      }));
    }
    return [];
  };

  // Helper function to generate fallback ingredients based on recipe title
  const generateFallbackIngredients = (title: string): string[] => {
    console.log('Generating fallback ingredients for:', title);
    const baseIngredients = [
      "Check the original recipe source for detailed ingredients",
      "This recipe includes ingredients typically used for " + title.toLowerCase(),
      "Seasonings and spices as per traditional preparation"
    ];
    
    // Add some smart guesses based on the title
    const titleLower = title.toLowerCase();
    const additionalIngredients = [];
    
    if (titleLower.includes('chicken')) additionalIngredients.push("Chicken (main protein)");
    if (titleLower.includes('beef')) additionalIngredients.push("Beef (main protein)");
    if (titleLower.includes('pasta')) additionalIngredients.push("Pasta", "Parmesan cheese");
    if (titleLower.includes('salad')) additionalIngredients.push("Fresh vegetables", "Salad dressing");
    if (titleLower.includes('soup')) additionalIngredients.push("Broth or stock", "Vegetables");
    if (titleLower.includes('pizza')) additionalIngredients.push("Pizza dough", "Tomato sauce", "Mozzarella cheese");
    
    return [...baseIngredients, ...additionalIngredients];
  };

  // Get the recipe instructions
  const getInstructions = () => {
    if (source === 'themealdb') {
      return recipe.strInstructions || 'No instructions available.';
    }
    if (recipe.instructions) {
      return recipe.instructions;
    }
    if (recipe.analyzedInstructions && recipe.analyzedInstructions.length > 0) {
      return recipe.analyzedInstructions[0].steps
        .map((step: any) => step.step)
        .join('\n\n');
    }
    return 'No instructions available. Please check the original source for preparation steps.';
  };

  // Helper function to generate fallback instructions
  const generateFallbackInstructions = (title: string): string[] => {
    console.log('Generating fallback instructions for:', title);
    return [
      "This is a popular recipe from our collection.",
      "For detailed cooking instructions, please refer to traditional preparation methods for " + title.toLowerCase() + ".",
      "Adjust cooking time and seasonings based on your preferences.",
      "We're working on adding complete step-by-step instructions soon!"
    ];
  };

  // Better ingredient parsing with fallback
  const ingredients = (() => {
    console.log('Full recipe data for ingredients:', recipe);
    
    // Try extendedIngredients first
    if (recipe?.extendedIngredients && Array.isArray(recipe.extendedIngredients) && recipe.extendedIngredients.length > 0) {
      console.log('Found extendedIngredients:', recipe.extendedIngredients);
      const parsedIngredients = recipe.extendedIngredients.map(ing => {
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
      
      if (parsedIngredients.length > 0) {
        return parsedIngredients;
      }
    }
    
    // Fallback to generated ingredients
    console.log('Using fallback ingredients for:', recipe.title);
    return generateFallbackIngredients(recipe.title || '');
  })();

  // Better instruction parsing with fallback
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
        // More intelligent splitting that looks for actual step numbers, not just any number
        // Look for numbers at the beginning of lines or after periods, but not in the middle of sentences
        const stepPattern = /(?:\b(?:Step\s*)?\d+[.)]|\n\s*\d+[.)]|^\s*\d+[.)])/;
        const numberedSteps = cleanInstructions.split(stepPattern).filter(step => step.trim().length > 15);
        if (numberedSteps.length > 1) {
          return numberedSteps.slice(1);
        } else {
          // More intelligent sentence splitting that doesn't break on measurements
          // Look for periods followed by space and capital letter, but avoid breaking on measurements
          const sentences = cleanInstructions.split(/\.\s+(?=[A-Z][a-z])/).filter(step => step.trim().length > 20);
          if (sentences.length > 1) {
            return sentences.map(sentence => sentence.endsWith('.') ? sentence : sentence + '.');
          } else {
            return [cleanInstructions];
          }
        }
      }
    }
    
    // Fallback to generated instructions
    console.log('Using fallback instructions for:', recipe.title);
    return generateFallbackInstructions(recipe.title || '');
  })();

  // Get the prep time
  const getPrepTime = () => {
    if (source === 'themealdb') return recipe.strPrepTime || 'N/A';
    if (recipe.readyInMinutes) return `${recipe.readyInMinutes} minutes`;
    return 'N/A';
  };

  // Get the servings
  const getServings = () => {
    if (source === 'themealdb') return recipe.servings || 1;
    if (recipe.servings) return recipe.servings;
    return 1;
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
                src={getRecipeImage()}
                alt={recipeName}
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=800&q=80';
                }}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex flex-col justify-end p-6">
                <h1 className="text-white text-3xl md:text-4xl font-bold">{recipeName}</h1>
                <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600 mb-2">
                  <div className="flex items-center">
                    <Clock className="mr-1 h-4 w-4" />
                    <span>{getPrepTime()}</span>
                  </div>
                  <span>•</span>
                  <div className="flex items-center">
                    <ChefHat className="mr-1 h-4 w-4" />
                    <span>{getServings()} {getServings() === 1 ? 'serving' : 'servings'}</span>
                  </div>
                  <span>•</span>
                  <div className="flex items-center">
                    <Globe className="mr-1 h-4 w-4" />
                    <span>{cuisine}</span>
                  </div>
                  {source === 'themealdb' && (
                    <>
                      <span>•</span>
                      <div className="flex items-center">
                        <Utensils className="mr-1 h-4 w-4" />
                        <span>Source: TheMealDB</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Recipe content */}
            <div className="p-6">
              {recipe.summary && (
                <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                  <h2 className="text-xl font-semibold mb-2">About This Recipe</h2>
                  <p className="text-gray-700">
                    {cleanRecipeDescription(recipe.summary)}
                  </p>
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
