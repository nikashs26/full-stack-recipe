export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'dessert' | 'any';

export interface Folder {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export enum DietaryRestriction {
  VEGETARIAN = 'vegetarian',
  VEGAN = 'vegan',
  GLUTEN_FREE = 'glutenFree',
  DAIRY_FREE = 'dairyFree',
  NUT_FREE = 'nutFree',
  KETO = 'keto',
  PALEO = 'paleo',
  LOW_CARB = 'lowCarb',
  LOW_CALORIE = 'lowCalorie',
  LOW_SODIUM = 'lowSodium',
  HIGH_PROTEIN = 'highProtein',
  PESCETARIAN = 'pescetarian'
}

export enum DifficultyLevel {
  EASY = 'easy',
  MEDIUM = 'medium',
  HARD = 'hard'
}

export interface NutritionInfo {
  calories?: number;
  protein?: number;
  carbs?: number;
  fat?: number;
  fiber?: number;
  sugar?: number;
  sodium?: number;
  cholesterol?: number;
  servingSize?: string;
}

export interface BaseRecipe {
  // Core fields
  id: string | number;
  name?: string;
  title?: string;
  description?: string;
  image?: string;
  imageUrl?: string;
  
  // Cuisine and categories
  cuisine?: string;
  cuisines?: string[];
  
  // Dietary information
  dietaryRestrictions?: DietaryRestriction[];
  diets?: (DietaryRestriction | string)[];
  
  // Ingredients and instructions
  ingredients?: Array<{
    id?: number | string;
    name: string;
    original?: string;
    amount?: string | number;
    unit?: string;
  }>;
  
  instructions?: string | string[];
  analyzedInstructions?: any[];
  
  // Timing and servings
  prepTime?: number;
  cookTime?: number;
  totalTime?: number;
  readyInMinutes?: number;
  ready_in_minutes?: number;
  cookingTime?: string;
  servings?: number;
  
  // Difficulty and ratings
  difficulty?: DifficultyLevel;
  ratings?: number | number[] | Array<{ score: number; count: number }>;
  averageRating?: number;
  
  // Source and metadata
  source?: string;
  sourceUrl?: string;
  summary?: string;
  
  // Nutrition
  nutrition?: NutritionInfo;
  
  // Internal fields
  type?: 'manual' | 'spoonacular' | 'saved' | string;
  isFavorite?: boolean;
  folderId?: string;
  createdAt?: string;
  updatedAt?: string;
  comments?: any[];
}

export interface Recipe extends BaseRecipe {
  // Required fields for the application
  id: string | number;
  name: string;
  image: string;
  ingredients: Array<{
    name: string;
    amount?: string | number;
    unit?: string;
  }>;
  instructions: string[];
  dietaryRestrictions: DietaryRestriction[];
  cuisine: string;
  type: 'manual' | 'spoonacular' | 'saved';
}

export interface Comment {
  id: string;
  author: string;
  text: string;
  date: string;
}

export interface ShoppingListItem {
  id: string;
  ingredient: string;
  recipeId: string;
  recipeName: string;
  checked: boolean;
}
