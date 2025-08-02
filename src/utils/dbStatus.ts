import { getAllRecipes } from '../lib/spoonacular';

// Check ChromaDB connection status with retries
export const checkChromaDBConnection = async (retryCount = 2): Promise<boolean> => {
  let attempts = 0;
  
  while (attempts <= retryCount) {
    try {
      console.log(`Checking ChromaDB connection status (attempt ${attempts + 1})...`);
      
      // Try to fetch recipes as a simple connection test
      const response = await getAllRecipes();
      console.log("ChromaDB connection test response:", response);
      
      // If we got here, the connection was successful
      console.log("ChromaDB connection successful");
      return true;
      
    } catch (error) {
      console.error(`ChromaDB connection failed (attempt ${attempts + 1}):`, error);
      attempts++;
      
      if (attempts <= retryCount) {
        console.log(`Retrying ChromaDB connection in 2 seconds...`);
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
  }
  
  console.error(`ChromaDB connection failed after ${retryCount + 1} attempts`);
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
    // First try direct API endpoint for testing ChromaDB
    try {
      const testResponse = await fetch('http://localhost:5004/api/health');
      if (testResponse.ok) {
        const testData = await testResponse.json();
        console.log("ChromaDB health check:", testData);
        
        // Check if ChromaDB is connected
        if (testData.status === 'up') {
          // Try to get recipe count
          const recipes = await getAllRecipes();
          const recipeCount = Array.isArray(recipes) ? recipes.length : 0;
          
          return {
            connected: true,
            message: `Connected to ChromaDB with ${recipeCount} recipes`,
            timestamp: new Date(),
            recipeCount,
            details: testData
          };
        }
      }
    } catch (e) {
      console.log("Direct ChromaDB health check failed, trying alternative check...");
    }
    
    // If direct test failed, try a simple query
    try {
      const recipes = await getAllRecipes();
      const recipeCount = Array.isArray(recipes) ? recipes.length : 0;
      
      return {
        connected: true,
        message: `Connected to ChromaDB with ${recipeCount} recipes`,
        timestamp: new Date(),
        recipeCount,
        details: {}
      };
    } catch (error) {
      console.error("ChromaDB query failed:", error);
      
      // Handle specific error cases
      let errorType = "Connection Error";
      let errorDetails = error instanceof Error ? error.message : "Unknown error";
      
      if (error instanceof Error) {
        if (error.message.includes("ECONNREFUSED")) {
          errorType = "Connection Refused";
          errorDetails = "ChromaDB server is not running or not accepting connections";
        } else if (error.message.includes("timed out")) {
          errorType = "Connection Timeout";
          errorDetails = "Connection attempt to ChromaDB timed out";
        } else if (error.message.includes("ENOTFOUND")) {
          errorType = "Host Not Found";
          errorDetails = "Could not find the ChromaDB server";
        } else if (error.message.includes("401")) {
          errorType = "Authentication Error";
          errorDetails = "Invalid or missing authentication token";
        }
      }
      
      return {
        connected: false,
        message: `Failed to connect to ChromaDB: ${errorType}`,
        timestamp: new Date(),
        details: errorDetails
      };
    }
  } catch (error) {
    console.error("Database connection failed:", error);
    
    // Handle specific error cases
    let errorType = "Connection Error";
    let errorDetails = error instanceof Error ? error.message : "Unknown error";
    
    if (error instanceof Error) {
      if (error.message.includes("401") || error.message.includes("unauthorized")) {
        errorType = "Authentication Error";
        errorDetails = "Invalid or missing authentication token";
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
