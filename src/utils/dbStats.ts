
// This file is now deprecated. All functionality has been moved to storage.ts
// Keeping as an import stub for backwards compatibility
import {
  loadRecipes,
  saveRecipes,
  getRecipeById,
  addRecipe,
  updateRecipe,
  deleteRecipe
} from './storage';

// Also export the MongoDB status checking functions
import { checkMongoDBConnection, getDatabaseStatus } from './mongoStatus';

export {
  loadRecipes,
  saveRecipes,
  getRecipeById,
  addRecipe,
  updateRecipe,
  deleteRecipe,
  checkMongoDBConnection,
  getDatabaseStatus
};
