
import { getAllRecipesFromDB } from '../lib/spoonacular';

// Check MongoDB connection status
export const checkMongoDBConnection = async (): Promise<boolean> => {
  try {
    // Try to fetch recipes as a simple connection test
    await getAllRecipesFromDB();
    console.log("MongoDB connection successful");
    return true;
  } catch (error) {
    console.error("MongoDB connection failed:", error);
    return false;
  }
};
