
import { Recipe, DietaryRestriction } from '../types/recipe';
import { SpoonacularRecipe } from '../types/spoonacular';

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
      recipeCuisines.some(cuisine => 
        (typeof cuisine === 'string' && cuisine.toLowerCase() === cuisineFilterLower)
      ) : true;
    
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
