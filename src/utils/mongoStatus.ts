
import { getAllRecipesFromDB } from '../lib/spoonacular';

// Check MongoDB connection status
export const checkMongoDBConnection = async (): Promise<boolean> => {
  try {
    console.log("Checking MongoDB connection status...");
    // Try to fetch recipes as a simple connection test
    const response = await getAllRecipesFromDB();
    console.log("MongoDB connection test response:", response);
    
    if (response?.results) {
      console.log(`MongoDB connection successful with ${response.results.length} recipes found`);
      return true;
    } else {
      console.log("MongoDB connected but no recipes found");
      return true; // Still return true as the connection works
    }
  } catch (error) {
    console.error("MongoDB connection failed:", error);
    return false;
  }
};

// Get database status with more information
export const getDatabaseStatus = async (): Promise<{
  connected: boolean;
  message: string;
  timestamp: Date;
  recipeCount?: number;
}> => {
  try {
    const response = await getAllRecipesFromDB();
    const recipeCount = response?.results?.length || 0;
    
    console.log(`Database status check: Found ${recipeCount} recipes in MongoDB`);
    
    return {
      connected: true,
      message: `Successfully connected to MongoDB Atlas (${recipeCount} recipes found)`,
      timestamp: new Date(),
      recipeCount
    };
  } catch (error) {
    console.error("MongoDB status check error:", error);
    return {
      connected: false,
      message: error instanceof Error ? error.message : "Unknown connection error",
      timestamp: new Date()
    };
  }
};
