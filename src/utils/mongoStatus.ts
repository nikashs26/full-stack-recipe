
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

// Get database status with more information
export const getDatabaseStatus = async (): Promise<{
  connected: boolean;
  message: string;
  timestamp: Date;
}> => {
  try {
    await getAllRecipesFromDB();
    return {
      connected: true,
      message: "Successfully connected to MongoDB Atlas",
      timestamp: new Date()
    };
  } catch (error) {
    console.error("MongoDB connection error:", error);
    return {
      connected: false,
      message: error instanceof Error ? error.message : "Unknown connection error",
      timestamp: new Date()
    };
  }
};
