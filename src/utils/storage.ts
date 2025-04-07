
import { Recipe } from '../types/recipe';
import { initialRecipes } from '../data/recipes';
import { 
  saveRecipeToDB, 
  getAllRecipesFromDB,
  deleteRecipeFromDB
} from '../lib/spoonacular';
import { checkMongoDBConnection } from './mongoStatus';

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
  try {
    // First try to load from localStorage for immediate UI display
    const localRecipes = getLocalRecipes();
    
    // Try to check MongoDB connection and fetch the latest recipes
    try {
      console.log("Attempting to connect to MongoDB...");
      const isConnected = await checkMongoDBConnection(1); // Try with 1 retry
      
      if (isConnected) {
        console.log("Connected to MongoDB - fetching latest recipes");
        try {
          const dbRecipes = await getAllRecipesFromDB();
          
          if (dbRecipes?.results && Array.isArray(dbRecipes.results) && dbRecipes.results.length > 0) {
            // Map the recipes from DB format to our app format
            const mappedRecipes = dbRecipes.results.map((dbRecipe: any) => ({
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
            localStorage.setItem(RECIPES_STORAGE_KEY, JSON.stringify(mappedRecipes));
            console.log(`Loaded ${mappedRecipes.length} recipes from MongoDB`);
            return mappedRecipes;
          } else {
            console.log("No recipes found in MongoDB - initializing with default recipes");
            
            // If MongoDB is empty, push our initial recipes to it
            console.log("Seeding MongoDB with initial recipes...");
            for (const recipe of localRecipes) {
              try {
                await saveRecipeToDB({
                  // Convert to MongoDB format
                  id: recipe.id,
                  title: recipe.name,
                  cuisine: recipe.cuisine,
                  cuisines: [recipe.cuisine],
                  diets: recipe.dietaryRestrictions,
                  ingredients: recipe.ingredients,
                  instructions: recipe.instructions,
                  image: recipe.image,
                  ratings: recipe.ratings || []
                });
                console.log(`Seeded recipe: ${recipe.name}`);
              } catch (err) {
                console.error(`Failed to seed recipe ${recipe.name}:`, err);
              }
            }
            console.log(`Initialized MongoDB with ${localRecipes.length} default recipes`);
            return localRecipes;
          }
        } catch (dbError) {
          console.error("Error loading recipes from MongoDB:", dbError);
        }
      } else {
        console.log("MongoDB not available, using local storage recipes");
      }
    } catch (connectionError) {
      console.error("MongoDB connection failed:", connectionError);
      console.log("MongoDB not available, using local storage recipes");
    }
    
    return localRecipes;
  } catch (error) {
    console.error('Failed to load recipes:', error);
    return initialRecipes;
  }
};

// Sync local recipes with MongoDB in the background
const syncWithMongoDB = async (recipes: Recipe[]): Promise<boolean> => {
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
      try {
        await saveRecipeToDB({
          // Convert to MongoDB format
          id: recipe.id,
          title: recipe.name,
          cuisine: recipe.cuisine,
          cuisines: [recipe.cuisine],
          diets: recipe.dietaryRestrictions,
          ingredients: recipe.ingredients,
          instructions: recipe.instructions,
          image: recipe.image,
          ratings: recipe.ratings || [],
          comments: recipe.comments || []
        });
        console.log(`Synced recipe: ${recipe.name}`);
      } catch (err) {
        console.error(`Failed to sync recipe ${recipe.id} to MongoDB:`, err);
      }
    }
    
    console.log('Successfully synced local recipes with MongoDB');
    return true;
  } catch (error) {
    console.error('MongoDB sync failed:', error);
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
  
  // Also save to MongoDB directly
  saveRecipeToDB(newRecipe).catch(err => 
    console.error('Failed to save new recipe to MongoDB:', err)
  );
  
  return newRecipe;
};

export const updateRecipe = (updatedRecipe: Recipe): void => {
  const recipes = getLocalRecipes();
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
  const recipes = getLocalRecipes();
  const updatedRecipes = recipes.filter(recipe => recipe.id !== id);
  saveRecipes(updatedRecipes);
  
  // Also try to delete from MongoDB directly
  deleteRecipeFromDB(id).catch(err => 
    console.error('Failed to delete recipe from MongoDB:', err)
  );
};
