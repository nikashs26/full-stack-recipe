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
    console.log('Generating fallback ingredients for:', titleLower);
    
    // More specific ingredient mapping based on common recipe patterns
    if (titleLower.includes('chicken') && titleLower.includes('breast')) {
      return [
        '4 boneless skinless chicken breasts (6 oz each)',
        '2 tablespoons olive oil',
        '1 teaspoon garlic powder',
        '1 teaspoon paprika',
        '1/2 teaspoon dried thyme',
        'Salt and black pepper to taste',
        '1 medium onion, diced',
        '3 cloves garlic, minced'
      ];
    }
    
    if (titleLower.includes('chicken') && (titleLower.includes('thigh') || titleLower.includes('leg'))) {
      return [
        '8 chicken thighs (bone-in, skin-on)',
        '2 tablespoons olive oil',
        '1 teaspoon smoked paprika',
        '1 teaspoon dried rosemary',
        '1 teaspoon garlic powder',
        'Salt and black pepper to taste',
        '1 lemon, sliced',
        '4 cloves garlic, whole'
      ];
    }
    
    if (titleLower.includes('pasta') && titleLower.includes('marinara')) {
      return [
        '1 lb spaghetti or penne pasta',
        '2 tablespoons olive oil',
        '1 large onion, diced',
        '4 cloves garlic, minced',
        '1 can (28 oz) crushed tomatoes',
        '2 tablespoons tomato paste',
        '1 teaspoon dried basil',
        '1/2 teaspoon dried oregano',
        'Salt and pepper to taste',
        'Fresh basil leaves',
        'Parmesan cheese, grated'
      ];
    }
    
    if (titleLower.includes('pasta') && titleLower.includes('alfredo')) {
      return [
        '1 lb fettuccine pasta',
        '1/2 cup butter',
        '1 cup heavy cream',
        '1 1/2 cups freshly grated Parmesan cheese',
        '3 cloves garlic, minced',
        '1/4 teaspoon nutmeg',
        'Salt and white pepper to taste',
        'Fresh parsley for garnish'
      ];
    }
    
    if (titleLower.includes('beef') && titleLower.includes('stir fry')) {
      return [
        '1 lb beef sirloin, sliced thin',
        '2 tablespoons vegetable oil',
        '1 red bell pepper, sliced',
        '1 green bell pepper, sliced',
        '1 medium onion, sliced',
        '2 cloves garlic, minced',
        '1 tablespoon fresh ginger, minced',
        '3 tablespoons soy sauce',
        '1 tablespoon oyster sauce',
        '1 teaspoon cornstarch',
        'Green onions for garnish'
      ];
    }
    
    if (titleLower.includes('salmon')) {
      return [
        '4 salmon fillets (6 oz each), skin removed',
        '2 tablespoons olive oil',
        '2 tablespoons fresh lemon juice',
        '2 cloves garlic, minced',
        '1 tablespoon fresh dill, chopped',
        '1 teaspoon lemon zest',
        'Salt and black pepper to taste',
        'Lemon wedges for serving'
      ];
    }
    
    if (titleLower.includes('caesar') && titleLower.includes('salad')) {
      return [
        '1 large head romaine lettuce, chopped',
        '1/2 cup mayonnaise',
        '2 tablespoons fresh lemon juice',
        '2 cloves garlic, minced',
        '1 teaspoon Worcestershire sauce',
        '1/2 cup grated Parmesan cheese',
        '2 tablespoons olive oil',
        '1 cup croutons',
        'Salt and black pepper to taste'
      ];
    }
    
    if (titleLower.includes('chocolate') && titleLower.includes('chip') && titleLower.includes('cookie')) {
      return [
        '2 1/4 cups all-purpose flour',
        '1 teaspoon baking soda',
        '1 teaspoon salt',
        '1 cup butter, softened',
        '3/4 cup granulated sugar',
        '3/4 cup brown sugar, packed',
        '2 large eggs',
        '2 teaspoons vanilla extract',
        '2 cups chocolate chips'
      ];
    }
    
    if (titleLower.includes('pancake')) {
      return [
        '2 cups all-purpose flour',
        '2 tablespoons sugar',
        '2 teaspoons baking powder',
        '1 teaspoon salt',
        '2 large eggs',
        '1 3/4 cups milk',
        '1/4 cup melted butter',
        '1 teaspoon vanilla extract',
        'Butter for cooking',
        'Maple syrup for serving'
      ];
    }
    
    // Generic fallback based on main ingredient
    if (titleLower.includes('chicken')) {
      return [
        '2 lbs chicken (cuts as needed)',
        '2 tablespoons cooking oil',
        '1 onion, diced',
        '3 cloves garlic, minced',
        'Salt and pepper to taste',
        'Herbs and spices as desired'
      ];
    }
    
    if (titleLower.includes('beef')) {
      return [
        '1.5 lbs beef (cut as needed)',
        '2 tablespoons oil',
        '1 onion, diced',
        '2 cloves garlic, minced',
        'Salt and black pepper',
        'Beef broth or wine as needed'
      ];
    }
    
    if (titleLower.includes('pasta')) {
      return [
        '1 lb pasta (shape as preferred)',
        '2 tablespoons olive oil',
        '3 cloves garlic, minced',
        '1 onion, diced',
        'Salt and pepper to taste',
        'Parmesan cheese for serving'
      ];
    }
    
    // Default fallback
    return [
      'Main ingredients as specified in recipe title',
      '2 tablespoons cooking oil or butter',
      '1 onion, diced (if savory dish)',
      '2-3 cloves garlic, minced (if savory dish)',
      'Salt and pepper to taste',
      'Additional seasonings as appropriate'
    ];
  };

  // Function to generate fallback instructions based on recipe title
  const generateFallbackInstructions = (title: string): string[] => {
    const titleLower = title.toLowerCase();
    console.log('Generating fallback instructions for:', titleLower);
    
    // More specific instruction mapping
    if (titleLower.includes('chicken') && titleLower.includes('breast')) {
      return [
        'Preheat oven to 375°F (190°C).',
        'Pat chicken breasts dry and season both sides with salt, pepper, garlic powder, paprika, and thyme.',
        'Heat olive oil in a large oven-safe skillet over medium-high heat.',
        'Sear chicken breasts for 3-4 minutes on each side until golden brown.',
        'Add diced onion around the chicken and cook for 2-3 minutes.',
        'Add minced garlic and cook for another minute until fragrant.',
        'Transfer skillet to preheated oven and bake for 15-20 minutes.',
        'Check that internal temperature reaches 165°F (74°C) with a meat thermometer.',
        'Let rest for 5 minutes before slicing and serving.'
      ];
    }
    
    if (titleLower.includes('pasta') && titleLower.includes('marinara')) {
      return [
        'Bring a large pot of salted water to boil for the pasta.',
        'Heat olive oil in a large skillet over medium heat.',
        'Add diced onion and cook until softened and translucent, about 5-7 minutes.',
        'Add minced garlic and cook for another minute until fragrant.',
        'Stir in tomato paste and cook for 1 minute.',
        'Add crushed tomatoes, basil, oregano, salt, and pepper.',
        'Simmer sauce for 15-20 minutes, stirring occasionally.',
        'Meanwhile, cook pasta according to package directions until al dente.',
        'Drain pasta and toss with the marinara sauce.',
        'Serve immediately topped with fresh basil and Parmesan cheese.'
      ];
    }
    
    if (titleLower.includes('salmon')) {
      return [
        'Preheat oven to 400°F (200°C) and line a baking sheet with parchment paper.',
        'Pat salmon fillets dry with paper towels.',
        'In a small bowl, whisk together olive oil, lemon juice, minced garlic, and dill.',
        'Place salmon on the prepared baking sheet.',
        'Brush the oil mixture evenly over each fillet.',
        'Season with salt, pepper, and lemon zest.',
        'Bake for 12-15 minutes until fish flakes easily with a fork.',
        'Internal temperature should reach 145°F (63°C).',
        'Serve immediately with lemon wedges.'
      ];
    }
    
    if (titleLower.includes('stir fry')) {
      return [
        'Slice beef thinly against the grain and set aside.',
        'Heat 1 tablespoon oil in a large wok or skillet over high heat.',
        'Add beef and stir-fry for 2-3 minutes until browned. Remove and set aside.',
        'Add remaining oil to the pan.',
        'Add bell peppers and onion, stir-fry for 2-3 minutes until crisp-tender.',
        'Add garlic and ginger, stir-fry for 30 seconds until fragrant.',
        'Return beef to the pan.',
        'Add soy sauce and oyster sauce, toss everything together.',
        'Cook for another 1-2 minutes until heated through.',
        'Garnish with green onions and serve over rice.'
      ];
    }
    
    if (titleLower.includes('cookie')) {
      return [
        'Preheat oven to 375°F (190°C).',
        'In a medium bowl, whisk together flour, baking soda, and salt.',
        'In a large bowl, cream together softened butter and both sugars until light and fluffy.',
        'Beat in eggs one at a time, then add vanilla extract.',
        'Gradually mix in the flour mixture until just combined.',
        'Fold in chocolate chips.',
        'Drop rounded tablespoons of dough onto ungreased baking sheets.',
        'Bake for 9-11 minutes until edges are golden brown.',
        'Cool on baking sheets for 5 minutes before transferring to a wire rack.'
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
    
    // Default fallback with more specific guidance
    return [
      `Prepare this ${titleLower.split(' ')[0]} recipe with attention to timing and technique.`,
      'Gather and prepare all ingredients before starting to cook.',
      'Follow proper cooking techniques for the main ingredients involved.',
      'Monitor cooking progress and adjust heat levels as needed.',
      'Season and taste throughout the cooking process.',
      'Serve according to the traditional style for this type of dish.'
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
