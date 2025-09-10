
// This file is now deprecated. All functionality has been moved to storage.ts
// Keeping as an import stub for backwards compatibility
import {
  loadRecipes,
  saveRecipes,
  getRecipeById,
  addRecipe,
  updateRecipe,
  deleteRecipe,
  getLocalRecipes // Add the new sync function
} from './storage';

// Also export the MongoDB status checking functions
import { checkChromaDBConnection as checkMongoDBConnection, getDatabaseStatus } from './dbStatus';

export {
  loadRecipes,
  saveRecipes,
  getRecipeById,
  addRecipe,
  updateRecipe,
  deleteRecipe,
  getLocalRecipes, // Export the new sync function
  checkMongoDBConnection,
  getDatabaseStatus
};
