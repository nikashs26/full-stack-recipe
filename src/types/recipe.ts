
export type DietaryRestriction = 'vegetarian' | 'vegan' | 'gluten-free' | 'dairy-free' | 'keto' | 'paleo';
export type DifficultyLevel = 'easy' | 'medium' | 'hard';
export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'dessert' | 'any'; // New MealType definition

export interface Folder {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Recipe {
  id: string;
  // Support both name and title
  name?: string;
  title?: string;
  // Support both cuisine and cuisines array
  cuisine?: string;
  cuisines?: string[];
  // Support both dietaryRestrictions and diets
  dietaryRestrictions?: DietaryRestriction[];
  diets?: string[];
  // Support both image formats
  image?: string;
  imageUrl?: string;
  // Support both ingredient formats
  ingredients: Array<string | { name: string; amount?: string }>;
  instructions: string[];
  // Optional fields
  description?: string;
  cookingTime?: string;
  servings?: number;
  difficulty?: string;
  ratings?: number[];
  comments?: string[];
  // Support relevance score from search
  relevance_score?: number;
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
