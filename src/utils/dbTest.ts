
import { Recipe } from '../types/recipe';

const API_DB_RECIPES = "http://localhost:5000/recipes";

// Function to directly add a test recipe to MongoDB
export const addTestRecipeToDB = async (): Promise<{success: boolean; message: string}> => {
  try {
    console.log("Adding test recipe directly to MongoDB...");
    
    // Create a test recipe
    const testRecipe: Recipe = {
      id: `test-${Date.now()}`,  // Unique ID using timestamp
      name: "Test MongoDB Recipe",
      cuisine: "Test Cuisine",
      dietaryRestrictions: ["vegetarian"],
      ingredients: ["Test Ingredient 1", "Test Ingredient 2", "Test Ingredient 3"],
      instructions: ["Step 1: Test instruction", "Step 2: Another test instruction"],
      image: "https://via.placeholder.com/400x300",
      ratings: [5, 4],
      comments: [
        {
          id: "comment1",
          author: "Test User",
          text: "This is a test comment",
          date: new Date().toISOString()
        }
      ]
    };

    // Convert to format MongoDB expects
    const mongoRecipe = {
      id: testRecipe.id,
      title: testRecipe.name,
      name: testRecipe.name,
      cuisine: testRecipe.cuisine,
      cuisines: [testRecipe.cuisine],
      dietaryRestrictions: testRecipe.dietaryRestrictions,
      diets: testRecipe.dietaryRestrictions,
      ingredients: testRecipe.ingredients,
      instructions: testRecipe.instructions,
      image: testRecipe.image,
      ratings: testRecipe.ratings,
      comments: testRecipe.comments
    };

    // Call the API endpoint to add recipe to MongoDB
    const response = await fetch(API_DB_RECIPES, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(mongoRecipe),
    });

    if (!response.ok) {
      throw new Error(`Failed to add test recipe (Status: ${response.status})`);
    }

    const result = await response.json();
    console.log("MongoDB test result:", result);
    
    return { 
      success: true, 
      message: `Successfully added test recipe with ID: ${testRecipe.id}`
    };
  } catch (error) {
    console.error("Error adding test recipe to MongoDB:", error);
    return { 
      success: false, 
      message: error instanceof Error ? error.message : "Unknown error occurred"
    };
  }
};

// Function to check if recipes exist in MongoDB
export const checkRecipesInDB = async (): Promise<{
  success: boolean;
  message: string;
  count?: number;
  recipes?: any[];
}> => {
  try {
    console.log("Checking for recipes in MongoDB...");
    
    const response = await fetch(API_DB_RECIPES);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch recipes (Status: ${response.status})`);
    }
    
    const data = await response.json();
    
    if (!data.results || !Array.isArray(data.results)) {
      return {
        success: false,
        message: "No recipes found or invalid response format"
      };
    }
    
    return {
      success: true,
      message: `Found ${data.results.length} recipes in MongoDB`,
      count: data.results.length,
      recipes: data.results
    };
  } catch (error) {
    console.error("Error checking recipes in MongoDB:", error);
    return {
      success: false,
      message: error instanceof Error ? error.message : "Unknown error occurred"
    };
  }
};

// Helper function to display a sample MongoDB query for command line
export const getMongoCLICommands = (): string => {
  return `
# MongoDB CLI Commands to manually add a recipe:

# 1. Connect to your MongoDB cluster using mongosh:
mongosh "${process.env.MONGO_URI || 'mongodb+srv://username:password@betterbulkrecipes.mongodb.net/nikash'}"

# 2. Switch to the nikash database:
use nikash

# 3. Insert a test recipe:
db.Recipes.insertOne({
  id: "manual-test-recipe",
  title: "Manual Test Recipe",
  name: "Manual Test Recipe",
  cuisine: "Test",
  cuisines: ["Test"],
  dietaryRestrictions: ["vegetarian"],
  diets: ["vegetarian"],
  ingredients: ["Test Ingredient 1", "Test Ingredient 2"],
  instructions: ["Step 1", "Step 2"],
  image: "https://via.placeholder.com/400x300",
  ratings: [5]
})

# 4. Verify the recipe was added:
db.Recipes.find({ id: "manual-test-recipe" })
`;
};
