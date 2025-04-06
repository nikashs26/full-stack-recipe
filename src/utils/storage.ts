
import { Recipe } from '../types/recipe';
import { initialRecipes } from '../data/recipes';
import { 
  saveRecipeToDB, 
  getAllRecipesFromDB,
  deleteRecipeFromDB
} from '../lib/spoonacular';
import { checkMongoDBConnection } from './mongoStatus';

const RECIPES_STORAGE_KEY = 'dietary-delight-recipes';

export const loadRecipes = async (): Promise<Recipe[]> => {
  try {
    // First try to load from localStorage for immediate UI display
    const storedRecipes = localStorage.getItem(RECIPES_STORAGE_KEY);
    let recipes = storedRecipes ? JSON.parse(storedRecipes) : initialRecipes;
    
    // Try to check MongoDB connection and fetch the latest recipes
    const isConnected = await checkMongoDBConnection().catch(() => false);
    
    if (isConnected) {
      try {
        // If connected to MongoDB, try to fetch the latest recipes
        console.log("Connected to MongoDB - fetching latest recipes");
        const dbRecipes = await getAllRecipesFromDB();
        
        if (dbRecipes?.results && Array.isArray(dbRecipes.results) && dbRecipes.results.length > 0) {
          // Map the recipes from DB format to our app format if needed
          recipes = dbRecipes.results.map((dbRecipe: any) => ({
            id: dbRecipe.id || dbRecipe._id,
            name: dbRecipe.title || dbRecipe.name,
            cuisine: dbRecipe.cuisine || (dbRecipe.cuisines && dbRecipe.cuisines[0]) || "Unknown",
            dietaryRestrictions: dbRecipe.dietaryRestrictions || dbRecipe.diets || [],
            ingredients: dbRecipe.ingredients || [],
            instructions: dbRecipe.instructions || [],
            image: dbRecipe.image || '/placeholder.svg',
            ratings: dbRecipe.ratings || [],
            comments: dbRecipe.comments || []
          }));
          
          // Update local storage with the latest recipes from MongoDB
          localStorage.setItem(RECIPES_STORAGE_KEY, JSON.stringify(recipes));
          console.log(`Loaded ${recipes.length} recipes from MongoDB`);
        }
      } catch (dbError) {
        console.error("Error loading recipes from MongoDB:", dbError);
        // Continue with local recipes on error
      }
    } else {
      console.log("MongoDB not available, using local storage recipes");
    }
    
    return recipes;
  } catch (error) {
    console.error('Failed to load recipes:', error);
    return initialRecipes;
  }
};

// Sync local recipes with MongoDB in the background
const syncWithMongoDB = async (recipes: Recipe[]) => {
  try {
    // First check if MongoDB is available
    const isConnected = await checkMongoDBConnection().catch(() => false);
    
    if (!isConnected) {
      console.log('MongoDB not available, skipping sync');
      return false;
    }
    
    console.log(`Syncing ${recipes.length} recipes with MongoDB...`);
    
    // If MongoDB is available, sync local recipes to it
    for (const recipe of recipes) {
      await saveRecipeToDB(recipe).catch(err => 
        console.log(`Failed to sync recipe ${recipe.id} to MongoDB:`, err)
      );
    }
    
    console.log('Successfully synced local recipes with MongoDB');
    return true;
  } catch (error) {
    console.log('MongoDB sync failed:', error);
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
  const updatedRecipes = Array.isArray(recipes) 
    ? recipes.filter(recipe => recipe.id !== id)
    : [];
    
  saveRecipes(updatedRecipes);
  
  // Also try to delete from MongoDB directly
  deleteRecipeFromDB(id).catch(err => 
    console.error('Failed to delete recipe from MongoDB:', err)
  );
};
