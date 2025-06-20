
export type DietaryRestriction = 'vegetarian' | 'vegan' | 'gluten-free' | 'carnivore' | 'non-vegetarian';
export type DifficultyLevel = 'easy' | 'medium' | 'hard';

export interface Folder {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Recipe {
  id: string;
  name: string;
  cuisine: string;
  dietaryRestrictions: DietaryRestriction[];
  ingredients: string[];
  instructions: string[];
  image: string;
  ratings: number[];
  comments: Comment[];
  folderId?: string; // Reference to the folder this recipe belongs to
  createdAt?: string; // Added this property
  updatedAt?: string; // Added this property for consistency
  isFavorite?: boolean; // New property to mark recipes as favorites
  difficulty?: DifficultyLevel; // Added difficulty property
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
