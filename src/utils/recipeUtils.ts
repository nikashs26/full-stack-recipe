
import { Recipe, DietaryRestriction, NutritionInfo } from '../types/recipe';
import { SpoonacularRecipe } from '../types/spoonacular';

/**
 * Normalizes recipe data to ensure consistent structure
 */
export const normalizeRecipe = (recipeData: any): Recipe => {
  if (!recipeData) return null;

  // Handle both name and title fields
  const name = recipeData.name || recipeData.title || 'Untitled Recipe';
  
  // Handle both single cuisine and cuisines array
  let cuisine = '';
  if (recipeData.cuisine) {
    cuisine = recipeData.cuisine;
  } else if (Array.isArray(recipeData.cuisines) && recipeData.cuisines.length > 0) {
    cuisine = recipeData.cuisines[0];
  }

  // Handle both dietaryRestrictions and diets arrays
  let dietaryRestrictions: DietaryRestriction[] = [];
  if (Array.isArray(recipeData.dietaryRestrictions)) {
    dietaryRestrictions = recipeData.dietaryRestrictions;
  } else if (Array.isArray(recipeData.diets)) {
    dietaryRestrictions = recipeData.diets;
  }

  // Handle ingredients in different formats
  let ingredients: {name: string, amount?: string | number, unit?: string}[] = [];
  if (Array.isArray(recipeData.ingredients)) {
    ingredients = recipeData.ingredients.map(ing => {
      if (typeof ing === 'string') {
        // Try to parse string format like "2 cups flour"
        const match = ing.match(/^(\d+\s*\/?\d*\s*\w*)?\s*(.+)$/);
        return {
          name: match ? match[2].trim() : ing,
          amount: match && match[1] ? match[1].trim() : undefined
        };
      }
      // Already in object format
      let amount: string | number | undefined;
      let unit: string | undefined;
      
      // Handle new Spoonacular format with nested amount structure
      if (ing.amount && typeof ing.amount === 'object') {
        // Prefer US measurements, fallback to metric
        if (ing.amount.us && ing.amount.us.value !== undefined) {
          amount = ing.amount.us.value;
          unit = ing.amount.us.unit || ing.unit;
        } else if (ing.amount.metric && ing.amount.metric.value !== undefined) {
          amount = ing.amount.metric.value;
          unit = ing.amount.metric.unit || ing.unit;
        }
      } else {
        // Handle simple amount/unit format
        amount = ing.amount;
        unit = ing.unit;
      }
      
      // Format amount and unit together if both exist
      let formattedAmount: string | number | undefined = amount;
      if (amount !== undefined && unit && unit !== '') {
        formattedAmount = `${amount} ${unit}`.trim();
      } else if (amount !== undefined) {
        formattedAmount = amount;
      }
      
      return {
        name: ing.name || ing.ingredient || 'Unknown',
        amount: formattedAmount,
        unit: unit
      };
    });
  }

  // Handle instructions in different formats
  let instructions: string[] = [];
  if (Array.isArray(recipeData.instructions)) {
    instructions = recipeData.instructions;
  } else if (typeof recipeData.instructions === 'string') {
    // Split by newlines and filter out empty lines
    instructions = recipeData.instructions
      .split('\n')
      .map((s: string) => s.trim())
      .filter(Boolean);
  }

  // Extract nutrition info if available
  let nutrition: NutritionInfo | undefined;
  if (recipeData.nutrition) {
    nutrition = {
      calories: recipeData.nutrition.calories,
      protein: recipeData.nutrition.protein,
      carbohydrates: recipeData.nutrition.carbohydrates,
      fat: recipeData.nutrition.fat,
      fiber: recipeData.nutrition.fiber,
      sugar: recipeData.nutrition.sugar,
      sodium: recipeData.nutrition.sodium,
      servingSize: recipeData.nutrition.servingSize
    };
  } else if (recipeData.nutritionalInfo) {
    // Alternative nutrition field
    nutrition = {
      calories: recipeData.nutritionalInfo.calories,
      protein: recipeData.nutritionalInfo.protein,
      carbohydrates: recipeData.nutritionalInfo.carbs,
      fat: recipeData.nutritionalInfo.fat,
      fiber: recipeData.nutritionalInfo.fiber,
      sugar: recipeData.nutritionalInfo.sugar,
      sodium: recipeData.nutritionalInfo.sodium,
      servingSize: recipeData.nutritionalInfo.servingSize
    };
  }

  // Handle time fields
  const prepTime = recipeData.prepTime || recipeData.prepTimeMinutes || 0;
  const cookTime = recipeData.cookTime || recipeData.cookTimeMinutes || 0;
  const totalTime = recipeData.totalTime || (prepTime + cookTime) || undefined;

  return {
    id: recipeData.id || `recipe-${Date.now()}`,
    name,
    cuisine,
    dietaryRestrictions,
    image: recipeData.image || recipeData.imageUrl || '/placeholder-recipe.jpg',
    ingredients,
    instructions,
    nutrition,
    description: recipeData.description,
    prepTime,
    cookTime,
    totalTime,
    servings: recipeData.servings,
    difficulty: recipeData.difficulty,
    source: recipeData.source,
    sourceUrl: recipeData.sourceUrl || recipeData.source_url,
    ratings: recipeData.ratings || [],
    averageRating: recipeData.averageRating || getAverageRating(recipeData.ratings || []),
    reviewCount: recipeData.reviewCount || 0,
    isFavorite: !!recipeData.isFavorite,
    folderId: recipeData.folderId,
    createdAt: recipeData.createdAt || new Date().toISOString(),
    updatedAt: recipeData.updatedAt || new Date().toISOString()
  };
};

export const getAverageRating = (ratings: number[]): number => {
  if (ratings.length === 0) return 0;
  const sum = ratings.reduce((acc, rating) => acc + rating, 0);
  return parseFloat((sum / ratings.length).toFixed(1));
};

export const getDietaryTags = (dietaryRestrictions: DietaryRestriction[]): { text: string, class: string }[] => {
  if (!dietaryRestrictions || !Array.isArray(dietaryRestrictions)) return [];
  
  return dietaryRestrictions.map(restriction => {
    switch (restriction) {
      case 'vegetarian':
        return { text: 'Vegetarian', class: 'vegetarian-tag' };
      case 'vegan':
        return { text: 'Vegan', class: 'vegan-tag' };
      case 'gluten-free':
        return { text: 'Gluten-Free', class: 'gluten-free-tag' };
      case 'dairy-free':
        return { text: 'Dairy-Free', class: 'dairy-free-tag' };
      case 'keto':
        return { text: 'Keto', class: 'keto-tag' };
      case 'paleo':
        return { text: 'Paleo', class: 'paleo-tag' };
      case 'carnivore':
        return { text: 'Carnivore', class: 'carnivore-tag' };
      default:
        return { text: restriction, class: '' };
    }
  });
};

export const filterRecipes = (
  recipes: Recipe[], 
  searchTerm: string, 
  dietaryFilter: string,
  cuisineFilter: string,
  ingredientTerm: string
): Recipe[] => {
  if (!Array.isArray(recipes)) {
    console.error("Expected recipes to be an array, got:", typeof recipes);
    return [];
  }
  
  return recipes.filter(recipe => {
    // Handle both name and title fields for different recipe sources
    const recipeName = (recipe?.name || recipe?.title || "").toLowerCase();
    const searchTermLower = searchTerm ? searchTerm.toLowerCase() : "";
    
    // Match search term against name/title
    const matchesSearchTerm = searchTerm ? recipeName.includes(searchTermLower) : true;
    
    // Handle dietary restrictions from both formats
    const dietaryRestrictions = recipe?.dietaryRestrictions || recipe?.diets || [];
    const matchesDietary = dietaryFilter ? 
      dietaryRestrictions.some(diet => 
        (typeof diet === 'string' && diet.toLowerCase() === dietaryFilter.toLowerCase())
      ) : true;
    
    // Handle cuisine from both formats
    const recipeCuisines = Array.isArray(recipe?.cuisines) ? recipe.cuisines : [recipe?.cuisine].filter(Boolean);
    const cuisineFilterLower = cuisineFilter ? cuisineFilter.toLowerCase() : "";
    
    const matchesCuisine = cuisineFilter ? 
      recipeCuisines.some(cuisine => {
        const cuisineLower = typeof cuisine === 'string' ? cuisine.toLowerCase() : '';
        // If American is selected, also match Southern and Creole cuisines
        if (cuisineFilterLower === 'american') {
          const americanRegionalCuisines = [
            'american', 'southern', 'creole', 'cajun', 'soul food', 'southwestern', 
            'louisiana', 'tex-mex', 'new orleans', 'deep south', 'gulf coast',
            'southern american', 'southern us', 'southern united states', 'southern cuisine',
            'creole cuisine', 'cajun cuisine', 'soul food cuisine', 'southwestern cuisine',
            'louisiana cuisine', 'tex-mex cuisine', 'new orleans cuisine', 'deep south cuisine',
            'gulf coast cuisine', 'southern cooking', 'southern style', 'southern food',
            'creole cooking', 'cajun cooking', 'soul food cooking', 'southwestern cooking',
            'louisiana cooking', 'tex-mex cooking', 'new orleans cooking', 'deep south cooking',
            'gulf coast cooking', 'southern dishes', 'southern recipes', 'southern meals'
          ];
          return americanRegionalCuisines.includes(cuisineLower);
        }
        // Normal cuisine matching for other cases
        return cuisineLower === cuisineFilterLower;
      }) : true;
    
    // Handle ingredients from both formats
    const ingredients = recipe?.ingredients || [];
    const ingredientTermLower = ingredientTerm ? ingredientTerm.toLowerCase() : "";
    const matchesIngredient = ingredientTerm
      ? ingredients.some(ingredient => {
          if (!ingredient) return false;
          // Handle both string and object formats
          const ingredientName = typeof ingredient === 'string' ? ingredient : ingredient.name;
          return ingredientName.toLowerCase().includes(ingredientTermLower);
        })
      : true;

    return matchesSearchTerm && matchesDietary && matchesCuisine && matchesIngredient;
  });
};

export const getUniqueCuisines = (recipes: Recipe[]): string[] => {
  if (!Array.isArray(recipes)) {
    console.error("Expected recipes to be an array, got:", typeof recipes);
    return [];
  }
  
  const cuisines = recipes
    .filter(recipe => recipe && recipe.cuisine) // Filter out recipes without cuisine
    .map(recipe => recipe.cuisine);
  return [...new Set(cuisines)].sort();
};

export const formatExternalRecipeCuisine = (recipe: SpoonacularRecipe): string => {
  // Handle cuisine data for external recipes
  if (recipe && recipe.cuisines && Array.isArray(recipe.cuisines) && recipe.cuisines.length > 0) {
    return recipe.cuisines[0];
  }
  return "Other";
};

export const formatRecipeForDisplay = (recipe: Recipe | SpoonacularRecipe, isExternal: boolean): any => {
  if (!recipe) return null;
  
  if (isExternal) {
    const spoonacularRecipe = recipe as SpoonacularRecipe;
    return {
      ...spoonacularRecipe,
      cuisine: formatExternalRecipeCuisine(spoonacularRecipe),
      // Add any other formatting needed for external recipes
    };
  }
  return recipe;
};

/**
 * Get a reliable image URL with fallback
 * @param imageUrl - The original image URL
 * @param size - The desired image size (small, medium, large)
 * @returns A reliable image URL
 */
export const getReliableImageUrl = (imageUrl?: string, size: 'small' | 'medium' | 'large' = 'medium'): string => {
  // Check if the image URL is valid and accessible
  const isValidImageUrl = (url: string): boolean => {
    if (!url || typeof url !== 'string') return false;
    
    // Only filter out the most problematic URL patterns that cause actual errors
    // These are the specific patterns that cause ERR_TUNNEL_CONNECTION_FAILED
    const problematicPatterns = [
      /^[a-z]{6}\d{10}\.(jpg|png)$/i, // Pattern like urzj1d1587670726.jpg
      /^\d{10}\.(jpg|png)$/i, // Pattern like 1529443236.jpg
    ];
    
    // Only reject URLs that match the problematic patterns
    if (problematicPatterns.some(pattern => pattern.test(url))) {
      console.log(`Filtering out problematic image URL: ${url}`);
      return false;
    }
    
    // Allow ALL other URLs, including:
    // - HTTP/HTTPS URLs
    // - Data URLs
    // - Relative URLs
    // - External URLs like Unsplash, etc.
    // - Any other valid image URL
    return true;
  };
  
  // If the original URL is valid, try direct access first, then proxy as fallback
  if (imageUrl && isValidImageUrl(imageUrl)) {
    // For production (Netlify), try direct access first to avoid proxy issues
    if (import.meta.env.PROD) {
      // Check if it's already a full URL
      if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
        return imageUrl;
      }
      // If it's a relative URL, make it absolute
      if (imageUrl.startsWith('/')) {
        const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://dietary-delight.onrender.com';
        return `${backendUrl}${imageUrl}`;
      }
    }
    
    // Fallback to proxy for development or problematic URLs
    const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://dietary-delight.onrender.com';
    const encodedUrl = encodeURIComponent(imageUrl);
    return `${backendUrl}/api/proxy-image?url=${encodedUrl}`;
  }
  
  // Return appropriate fallback based on size
  const fallbackImages = {
    small: 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=300&h=200&q=80',
    medium: 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=400&h=300&q=80',
    large: 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=800&h=600&q=80'
  };
  
  return fallbackImages[size];
};
