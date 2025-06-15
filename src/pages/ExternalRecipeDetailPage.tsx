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

  // Function to generate fallback ingredients based on recipe title
  const generateFallbackIngredients = (title: string): string[] => {
    const titleLower = title.toLowerCase();
    
    // Common cooking ingredients
    const baseIngredients = ['salt', 'black pepper', 'olive oil'];
    
    // Recipe-specific ingredients based on title keywords
    if (titleLower.includes('chicken')) {
      return [
        '1 lb chicken breast, boneless and skinless',
        '2 tablespoons olive oil',
        '1 teaspoon garlic powder',
        '1 teaspoon paprika',
        'Salt and pepper to taste',
        '1 onion, diced',
        '2 cloves garlic, minced'
      ];
    }
    
    if (titleLower.includes('pasta')) {
      return [
        '12 oz pasta (your choice of shape)',
        '2 tablespoons olive oil',
        '3 cloves garlic, minced',
        '1 onion, diced',
        '1 can (14 oz) diced tomatoes',
        'Salt and pepper to taste',
        'Fresh basil leaves',
        'Parmesan cheese, grated'
      ];
    }
    
    if (titleLower.includes('salad')) {
      return [
        '4 cups mixed greens',
        '1 cucumber, sliced',
        '2 tomatoes, chopped',
        '1/4 red onion, thinly sliced',
        '2 tablespoons olive oil',
        '1 tablespoon balsamic vinegar',
        'Salt and pepper to taste'
      ];
    }
    
    if (titleLower.includes('soup')) {
      return [
        '2 tablespoons olive oil',
        '1 onion, diced',
        '2 carrots, chopped',
        '2 celery stalks, chopped',
        '4 cups broth (chicken or vegetable)',
        '2 cloves garlic, minced',
        'Salt and pepper to taste',
        'Fresh herbs (thyme, parsley)'
      ];
    }
    
    if (titleLower.includes('salmon') || titleLower.includes('fish')) {
      return [
        '4 salmon fillets (6 oz each)',
        '2 tablespoons olive oil',
        '2 tablespoons lemon juice',
        '2 cloves garlic, minced',
        '1 teaspoon dried dill',
        'Salt and pepper to taste',
        'Lemon wedges for serving'
      ];
    }
    
    // Default fallback
    return [
      'Main ingredient (as specified in recipe title)',
      '2 tablespoons olive oil',
      '1 onion, diced',
      '2 cloves garlic, minced',
      'Salt and pepper to taste',
      'Additional seasonings as needed'
    ];
  };

  // Function to generate fallback instructions based on recipe title
  const generateFallbackInstructions = (title: string): string[] => {
    const titleLower = title.toLowerCase();
    
    if (titleLower.includes('chicken')) {
      return [
        'Preheat your oven to 375°F (190°C).',
        'Season the chicken breast with salt, pepper, garlic powder, and paprika.',
        'Heat olive oil in a large oven-safe skillet over medium-high heat.',
        'Sear the chicken for 3-4 minutes on each side until golden brown.',
        'Add diced onion and minced garlic to the skillet and cook for 2 minutes.',
        'Transfer the skillet to the preheated oven and bake for 15-20 minutes.',
        'Check that internal temperature reaches 165°F (74°C).',
        'Let rest for 5 minutes before serving.'
      ];
    }
    
    if (titleLower.includes('pasta')) {
      return [
        'Bring a large pot of salted water to boil.',
        'Cook pasta according to package directions until al dente.',
        'While pasta cooks, heat olive oil in a large skillet over medium heat.',
        'Add diced onion and cook until softened, about 5 minutes.',
        'Add minced garlic and cook for another minute.',
        'Add diced tomatoes and seasonings, simmer for 10 minutes.',
        'Drain pasta and add to the sauce.',
        'Toss well and serve with fresh basil and Parmesan cheese.'
      ];
    }
    
    if (titleLower.includes('salad')) {
      return [
        'Wash and dry all vegetables thoroughly.',
        'Chop tomatoes and slice cucumber and red onion.',
        'In a large bowl, combine mixed greens with prepared vegetables.',
        'In a small bowl, whisk together olive oil and balsamic vinegar.',
        'Season dressing with salt and pepper.',
        'Drizzle dressing over salad just before serving.',
        'Toss gently and serve immediately.'
      ];
    }
    
    if (titleLower.includes('soup')) {
      return [
        'Heat olive oil in a large pot over medium heat.',
        'Add diced onion, carrots, and celery. Cook until softened, about 8 minutes.',
        'Add minced garlic and cook for another minute.',
        'Pour in broth and bring to a boil.',
        'Reduce heat and simmer for 20-25 minutes.',
        'Season with salt, pepper, and fresh herbs.',
        'Taste and adjust seasonings as needed.',
        'Serve hot with crusty bread.'
      ];
    }
    
    if (titleLower.includes('salmon') || titleLower.includes('fish')) {
      return [
        'Preheat oven to 400°F (200°C).',
        'Pat salmon fillets dry and place on a baking sheet.',
        'In a small bowl, mix olive oil, lemon juice, garlic, and dill.',
        'Brush the mixture over salmon fillets.',
        'Season with salt and pepper.',
        'Bake for 12-15 minutes until fish flakes easily.',
        'Serve immediately with lemon wedges.'
      ];
    }
    
    if (titleLower.includes('stir fry') || titleLower.includes('stirfry')) {
      return [
        'Heat oil in a large wok or skillet over high heat.',
        'Add protein first and cook until nearly done, then remove.',
        'Add harder vegetables (like carrots, broccoli) and stir-fry for 2-3 minutes.',
        'Add softer vegetables (like bell peppers, snap peas) and cook 1-2 minutes.',
        'Return protein to the pan.',
        'Add sauce and toss everything together.',
        'Cook for another minute until heated through.',
        'Serve immediately over rice or noodles.'
      ];
    }
    
    if (titleLower.includes('burger')) {
      return [
        'Preheat grill or skillet to medium-high heat.',
        'Form ground meat into patties, slightly larger than buns.',
        'Season patties with salt and pepper.',
        'Cook patties for 3-4 minutes per side for medium doneness.',
        'Add cheese in the last minute if desired.',
        'Toast buns lightly on the grill or in a toaster.',
        'Assemble burgers with desired toppings.',
        'Serve immediately while hot.'
      ];
    }
    
    if (titleLower.includes('pizza')) {
      return [
        'Preheat oven to 475°F (245°C).',
        'Roll out pizza dough on a floured surface.',
        'Transfer dough to a pizza stone or baking sheet.',
        'Spread sauce evenly, leaving a border for the crust.',
        'Add cheese and desired toppings.',
        'Bake for 12-15 minutes until crust is golden and cheese is bubbly.',
        'Let cool for 2-3 minutes before slicing.',
        'Serve hot.'
      ];
    }
    
    if (titleLower.includes('curry')) {
      return [
        'Heat oil in a large pot over medium heat.',
        'Add onions and cook until softened and lightly golden.',
        'Add garlic, ginger, and spices, cook for 1 minute until fragrant.',
        'Add curry paste or powder and cook for another minute.',
        'Add main protein or vegetables and cook until coated.',
        'Pour in coconut milk or broth and bring to a simmer.',
        'Reduce heat and simmer for 20-30 minutes until tender.',
        'Taste and adjust seasoning, serve over rice.'
      ];
    }
    
    if (titleLower.includes('bread') || titleLower.includes('baking')) {
      return [
        'Preheat oven according to recipe temperature.',
        'Mix dry ingredients in a large bowl.',
        'In a separate bowl, combine wet ingredients.',
        'Add wet ingredients to dry ingredients and mix until just combined.',
        'Pour into prepared baking pan.',
        'Bake for specified time until golden brown and a toothpick comes out clean.',
        'Cool in pan for 10 minutes before removing.',
        'Cool completely before slicing.'
      ];
    }
    
    if (titleLower.includes('smoothie') || titleLower.includes('drink')) {
      return [
        'Add all ingredients to a high-speed blender.',
        'Start blending on low speed, gradually increasing to high.',
        'Blend until smooth and creamy, about 1-2 minutes.',
        'Add more liquid if needed for desired consistency.',
        'Taste and adjust sweetness if needed.',
        'Pour into glasses and serve immediately.',
        'Garnish as desired.'
      ];
    }
    
    // Default fallback - still generic but better than before
    return [
      `This ${titleLower} recipe requires careful preparation and attention to cooking times.`,
      'Start by gathering and preparing all ingredients as listed.',
      'Follow traditional cooking methods appropriate for this type of dish.',
      'Monitor cooking progress and adjust heat as needed.',
      'Season thoughtfully and taste as you go.',
      'Serve according to traditional presentation for this cuisine.'
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
    
    // Fallback to generated instructions
    console.log('Using fallback instructions for:', recipe.title);
    return generateFallbackInstructions(recipe.title || '');
  })();

  // Better image handling with high-quality fallback
  const getRecipeImage = () => {
    // Try the original image first
    if (recipe?.image && recipe.image.includes('http')) {
      return recipe.image;
    }
    
    // Use a food-related placeholder that's more specific
    const foodImages = [
      'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445',
      'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b',
      'https://images.unsplash.com/photo-1540189549336-e6e99c3679fe',
      'https://images.unsplash.com/photo-1565958011703-44f9829ba187',
      'https://images.unsplash.com/photo-1559181567-c3190ca9959b'
    ];
    
    // Use recipe ID to consistently pick the same image
    const imageIndex = (recipe?.id || 0) % foodImages.length;
    return `${foodImages[imageIndex]}?auto=format&fit=crop&w=800&q=80`;
  };
      
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
                src={getRecipeImage()}
                alt={recipe.title}
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=800&q=80';
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
