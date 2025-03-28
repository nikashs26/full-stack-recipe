
import { Recipe, DietaryRestriction } from '../types/recipe';

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
  cuisineFilter: string
): Recipe[] => {
  return recipes.filter(recipe => 
    recipe.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
    (dietaryFilter ? recipe.dietaryRestrictions.includes(dietaryFilter as DietaryRestriction) : true) &&
    (cuisineFilter ? recipe.cuisine === cuisineFilter : true)
  );
};

export const getUniqueCuisines = (recipes: Recipe[]): string[] => {
  const cuisines = recipes.map(recipe => recipe.cuisine);
  return [...new Set(cuisines)].sort();
};
