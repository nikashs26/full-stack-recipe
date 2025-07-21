
import { Recipe } from '../types/recipe';
import { initialRecipes } from '../data/recipes';
// Local storage based recipe management
// This file handles recipe storage using browser's localStorage as a fallback

const RECIPES_STORAGE_KEY = 'dietary-delight-recipes';

// Helper function to get recipes synchronously from localStorage
export const getLocalRecipes = (): Recipe[] => {
  try {
    const storedRecipes = localStorage.getItem(RECIPES_STORAGE_KEY);
    return storedRecipes ? JSON.parse(storedRecipes) : initialRecipes;
  } catch (error) {
    console.error('Failed to load recipes from localStorage:', error);
    return initialRecipes;
  }
};

export const loadRecipes = async (): Promise<Recipe[]> => {
  // First try to load from localStorage for immediate UI display
  const localRecipes = getLocalRecipes();
  
  // First try to load from localStorage
  if (localRecipes.length > 0) {
    return localRecipes;
  }
  
  // If we get here, both ChromaDB and database failed - use local storage
  console.log("Using recipes from local storage");
  return localRecipes;
};

export const saveRecipes = (recipes: Recipe[]): void => {
  try {
    localStorage.setItem(RECIPES_STORAGE_KEY, JSON.stringify(recipes));
  } catch (error) {
    console.error('Failed to save recipes to localStorage:', error);
  }
};

export const getRecipeById = (id: string): Recipe | undefined => {
  const recipes = getLocalRecipes();
  return recipes.find(recipe => recipe.id === id);
};

export const addRecipe = (recipe: Omit<Recipe, 'id'>): Recipe => {
  const recipes = getLocalRecipes();
  const newRecipe = {
    ...recipe,
    id: Date.now().toString(),
  };
  
  const updatedRecipes = [...recipes, newRecipe];
  saveRecipes(updatedRecipes);
  
  return newRecipe;
};

export const updateRecipe = (updatedRecipe: Recipe): void => {
  const recipes = getLocalRecipes();
  const updatedRecipes = recipes.map(recipe => 
    recipe.id === updatedRecipe.id ? updatedRecipe : recipe
  );
  saveRecipes(updatedRecipes);
};

export const deleteRecipe = (id: string): void => {
  const recipes = getLocalRecipes();
  const updatedRecipes = recipes.filter(recipe => recipe.id !== id);
  saveRecipes(updatedRecipes);
};
