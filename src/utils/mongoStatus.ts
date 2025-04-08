
import { getAllRecipesFromDB } from '../lib/spoonacular';

// Check MongoDB connection status with retries
export const checkMongoDBConnection = async (retryCount = 2): Promise<boolean> => {
  let attempts = 0;
  
  while (attempts <= retryCount) {
    try {
      console.log(`Checking MongoDB connection status (attempt ${attempts + 1})...`);
      
      // Try to fetch MongoDB test status directly
      const testEndpoint = "http://localhost:5000/test-mongodb";
      const response = await fetch(testEndpoint, { 
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        // Longer timeout for potential slow connections
        signal: AbortSignal.timeout(10000)
      });
      
      if (!response.ok) {
        throw new Error(`MongoDB test endpoint returned status: ${response.status}`);
      }
      
      const result = await response.json();
      console.log("MongoDB connection test result:", result);
      
      if (result.connected) {
        console.log(`MongoDB connection successful with ${result.recipeCount || 0} recipes found`);
        return true;
      } else {
        console.log(`MongoDB connection failed: ${result.message || "Unknown error"}`);
        throw new Error(result.message || "MongoDB connection failed");
      }
    } catch (error) {
      console.error(`MongoDB connection failed (attempt ${attempts + 1}):`, error);
      attempts++;
      
      if (attempts <= retryCount) {
        console.log(`Retrying MongoDB connection in 2 seconds...`);
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
  }
  
  console.error(`MongoDB connection failed after ${retryCount + 1} attempts`);
  return false;
};

// Get database status with more information
export const getDatabaseStatus = async (): Promise<{
  connected: boolean;
  message: string;
  timestamp: Date;
  recipeCount?: number;
  uri?: string;
  error?: string;
}> => {
  try {
    // First try the dedicated test endpoint
    try {
      const response = await fetch("http://localhost:5000/test-mongodb", { 
        signal: AbortSignal.timeout(10000) 
      });
      
      if (response.ok) {
        const result = await response.json();
        return {
          connected: result.connected || false,
          message: result.message || "MongoDB status check completed",
          timestamp: new Date(),
          recipeCount: result.recipeCount || 0,
          uri: result.uri ? `${result.uri.substring(0, 20)}...` : undefined,
          error: result.error || undefined
        };
      } else {
        const errorText = await response.text();
        return {
          connected: false,
          message: `MongoDB test endpoint returned error status: ${response.status}`,
          timestamp: new Date(),
          error: errorText
        };
      }
    } catch (error) {
      console.error("Error using test-mongodb endpoint:", error);
    }
    
    // Fall back to checking via getAllRecipesFromDB
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
      timestamp: new Date(),
      error: error instanceof Error ? error.stack : undefined
    };
  }
};
