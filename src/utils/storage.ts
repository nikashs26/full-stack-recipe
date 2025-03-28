
import { Recipe } from '../types/recipe';
import { initialRecipes } from '../data/recipes';

const RECIPES_STORAGE_KEY = 'dietary-delight-recipes';

export const loadRecipes = (): Recipe[] => {
  try {
    const storedRecipes = localStorage.getItem(RECIPES_STORAGE_KEY);
    return storedRecipes ? JSON.parse(storedRecipes) : initialRecipes;
  } catch (error) {
    console.error('Failed to load recipes from localStorage:', error);
    return initialRecipes;
  }
};

export const saveRecipes = (recipes: Recipe[]): void => {
  try {
    localStorage.setItem(RECIPES_STORAGE_KEY, JSON.stringify(recipes));
  } catch (error) {
    console.error('Failed to save recipes to localStorage:', error);
  }
};

export const getRecipeById = (id: string): Recipe | undefined => {
  const recipes = loadRecipes();
  return recipes.find(recipe => recipe.id === id);
};

export const addRecipe = (recipe: Omit<Recipe, 'id'>): Recipe => {
  const recipes = loadRecipes();
  const newRecipe = {
    ...recipe,
    id: Date.now().toString(),
  };
  
  const updatedRecipes = [...recipes, newRecipe];
  saveRecipes(updatedRecipes);
  return newRecipe;
};

export const updateRecipe = (updatedRecipe: Recipe): void => {
  const recipes = loadRecipes();
  const updatedRecipes = recipes.map(recipe => 
    recipe.id === updatedRecipe.id ? updatedRecipe : recipe
  );
  saveRecipes(updatedRecipes);
};

export const deleteRecipe = (id: string): void => {
  const recipes = loadRecipes();
  const updatedRecipes = recipes.filter(recipe => recipe.id !== id);
  saveRecipes(updatedRecipes);
};
