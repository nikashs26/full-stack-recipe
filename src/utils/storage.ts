
import { Recipe } from '../types/recipe';
import { initialRecipes } from '../data/recipes';
import { 
  saveRecipeToDB, 
  getAllRecipesFromDB,
  deleteRecipeFromDB
} from '../lib/spoonacular';

const RECIPES_STORAGE_KEY = 'dietary-delight-recipes';

export const loadRecipes = (): Recipe[] => {
  try {
    const storedRecipes = localStorage.getItem(RECIPES_STORAGE_KEY);
    const recipes = storedRecipes ? JSON.parse(storedRecipes) : initialRecipes;
    
    // Attempt to sync with MongoDB in the background
    syncWithMongoDB(recipes).catch(err => {
      console.log('MongoDB sync skipped:', err);
    });
    
    return recipes;
  } catch (error) {
    console.error('Failed to load recipes from localStorage:', error);
    return initialRecipes;
  }
};

// Sync local recipes with MongoDB in the background
const syncWithMongoDB = async (recipes: Recipe[]) => {
  try {
    // First check if MongoDB is available by making a request
    console.log("Checking MongoDB connection through Flask API...");
    await getAllRecipesFromDB();
    
    // If MongoDB is available, sync local recipes to it
    for (const recipe of recipes) {
      await saveRecipeToDB(recipe).catch(err => 
        console.log(`Failed to sync recipe ${recipe.id} to MongoDB:`, err)
      );
    }
    
    console.log('Successfully synced local recipes with MongoDB');
    return true;
  } catch (error) {
    console.log('MongoDB sync skipped:', error);
    return false;
  }
};

export const saveRecipes = (recipes: Recipe[]): void => {
  try {
    localStorage.setItem(RECIPES_STORAGE_KEY, JSON.stringify(recipes));
    
    // Try to sync with MongoDB in the background
    syncWithMongoDB(recipes).catch(err => 
      console.error('Failed to sync recipes with MongoDB:', err)
    );
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
  
  // Also save to MongoDB directly
  saveRecipeToDB(newRecipe).catch(err => 
    console.error('Failed to save new recipe to MongoDB:', err)
  );
  
  return newRecipe;
};

export const updateRecipe = (updatedRecipe: Recipe): void => {
  const recipes = loadRecipes();
  const updatedRecipes = recipes.map(recipe => 
    recipe.id === updatedRecipe.id ? updatedRecipe : recipe
  );
  saveRecipes(updatedRecipes);
  
  // Also update in MongoDB
  saveRecipeToDB(updatedRecipe).catch(err => 
    console.error('Failed to update recipe in MongoDB:', err)
  );
};

export const deleteRecipe = (id: string): void => {
  const recipes = loadRecipes();
  const updatedRecipes = recipes.filter(recipe => recipe.id !== id);
  saveRecipes(updatedRecipes);
  
  // Also try to delete from MongoDB directly
  deleteRecipeFromDB(id).catch(err => 
    console.error('Failed to delete recipe from MongoDB:', err)
  );
};
