
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
    // Add null checks for all properties to avoid "toLowerCase of undefined" errors
    const recipeName = recipe.name || "";
    const searchTermLower = searchTerm ? searchTerm.toLowerCase() : "";
    const matchesSearchTerm = searchTerm ? recipeName.toLowerCase().includes(searchTermLower) : true;
    
    const dietaryRestrictions = recipe.dietaryRestrictions || [];
    const matchesDietary = dietaryFilter ? dietaryRestrictions.includes(dietaryFilter as DietaryRestriction) : true;
    
    const recipeCuisine = recipe.cuisine || "";
    const cuisineFilterLower = cuisineFilter ? cuisineFilter.toLowerCase() : "";
    const matchesCuisine = cuisineFilter ? recipeCuisine.toLowerCase() === cuisineFilterLower : true;
    
    const ingredients = recipe.ingredients || [];
    const ingredientTermLower = ingredientTerm ? ingredientTerm.toLowerCase() : "";
    const matchesIngredient = ingredientTerm
      ? ingredients.some(ingredient => {
          if (!ingredient) return false;
          return ingredient.toLowerCase().includes(ingredientTermLower);
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
