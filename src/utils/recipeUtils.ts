
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
      return {
        name: ing.name || ing.ingredient || 'Unknown',
        amount: ing.amount,
        unit: ing.unit
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
          return ['american', 'southern', 'creole', 'cajun'].includes(cuisineLower);
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
