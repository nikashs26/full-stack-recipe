
import { getAllRecipesFromDB } from '../lib/spoonacular';

// Check MongoDB connection status with retries
export const checkMongoDBConnection = async (retryCount = 2): Promise<boolean> => {
  let attempts = 0;
  
  while (attempts <= retryCount) {
    try {
      console.log(`Checking MongoDB connection status (attempt ${attempts + 1})...`);
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
  details?: any;
}> => {
  try {
    // First try direct API endpoint for testing MongoDB
    try {
      const testResponse = await fetch('http://localhost:5003/test-mongodb');
      if (testResponse.ok) {
        const testData = await testResponse.json();
        console.log("Direct MongoDB test results:", testData);
        
        if (testData.connected) {
          return {
            connected: true,
            message: `Successfully connected to MongoDB: ${testData.message}`,
            timestamp: new Date(),
            recipeCount: testData.recipeCount,
            details: testData
          };
        } else {
          throw new Error(testData.message || "Direct test shows MongoDB is not available");
        }
      }
    } catch (testError) {
      console.log("Direct MongoDB test failed, falling back to recipe fetch:", testError);
    }
    
    // Fall back to recipe fetch if direct test fails
    const response = await getAllRecipesFromDB();
    const recipeCount = response?.results?.length || 0;
    
    console.log(`Database status check: Found ${recipeCount} recipes in MongoDB`);
    
    return {
      connected: true,
      message: `Successfully connected to MongoDB (${recipeCount} recipes found)`,
      timestamp: new Date(),
      recipeCount
    };
  } catch (error) {
    console.error("MongoDB status check error:", error);
    
    // Try to get more detailed error information
    let errorDetails = "Unknown connection error";
    let errorType = "Connection Error";
    
    if (error instanceof Error) {
      errorDetails = error.message;
      
      // Try to identify common MongoDB connection issues
      if (error.message.includes("ECONNREFUSED")) {
        errorType = "Connection Refused";
        errorDetails = "MongoDB server is not running or not accepting connections at the specified address";
      } else if (error.message.includes("timed out")) {
        errorType = "Connection Timeout";
        errorDetails = "Connection attempt to MongoDB timed out. Server might be slow or unreachable";
      } else if (error.message.includes("DNS")) {
        errorType = "DNS Resolution Error";
        errorDetails = "Could not resolve MongoDB hostname. Check your connection string and internet connectivity";
      } else if (error.message.includes("authentication")) {
        errorType = "Authentication Error";
        errorDetails = "Invalid username or password in MongoDB connection string";
      }
    }
    
    return {
      connected: false,
      message: `MongoDB connection failed: ${errorType} - ${errorDetails}`,
      timestamp: new Date(),
      details: { error: errorDetails, type: errorType }
    };
  }
};

// Test direct connection to database with native driver
export const testDirectConnection = async (): Promise<{
  success: boolean;
  message: string;
  details?: any;
}> => {
  try {
    const response = await fetch('http://localhost:5003/test-mongodb');
    if (!response.ok) {
      throw new Error(`Failed to test MongoDB connection: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    return {
      success: data.connected === true,
      message: data.message || "Connection test completed",
      details: data
    };
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : "Unknown error testing MongoDB connection",
      details: { error }
    };
  }
};
