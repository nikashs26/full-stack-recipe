
import { Recipe, DietaryRestriction } from '../types/recipe';
import { SpoonacularRecipe } from '../types/spoonacular';

export const getAverageRating = (ratings: number[]): number => {
  if (ratings.length === 0) return 0;
  const sum = ratings.reduce((acc, rating) => acc + rating, 0);
  return parseFloat((sum / ratings.length).toFixed(1));
};

export const getDietaryTags = (dietaryRestrictions: DietaryRestriction[]): { text: string, class: string }[] => {
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
    const matchesSearchTerm = recipe.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDietary = dietaryFilter ? recipe.dietaryRestrictions.includes(dietaryFilter as DietaryRestriction) : true;
    const matchesCuisine = cuisineFilter ? recipe.cuisine === cuisineFilter : true;
    const matchesIngredient = ingredientTerm
      ? recipe.ingredients.some(ingredient => ingredient.toLowerCase().includes(ingredientTerm.toLowerCase()))
      : true;

    return matchesSearchTerm && matchesDietary && matchesCuisine && matchesIngredient;
  });
};

export const getUniqueCuisines = (recipes: Recipe[]): string[] => {
  if (!Array.isArray(recipes)) {
    console.error("Expected recipes to be an array, got:", typeof recipes);
    return [];
  }
  
  const cuisines = recipes.map(recipe => recipe.cuisine);
  return [...new Set(cuisines)].sort();
};

export const formatExternalRecipeCuisine = (recipe: SpoonacularRecipe): string => {
  // Handle cuisine data for external recipes
  if (recipe.cuisines && Array.isArray(recipe.cuisines) && recipe.cuisines.length > 0) {
    return recipe.cuisines[0];
  }
  return "Other";
};

export const formatRecipeForDisplay = (recipe: Recipe | SpoonacularRecipe, isExternal: boolean): any => {
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
