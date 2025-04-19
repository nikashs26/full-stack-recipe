export type DietaryRestriction = 'vegetarian' | 'vegan' | 'gluten-free' | 'carnivore';

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
}

export interface Comment {
  id: string;
  author: string;
  text: string;
  date: string;
}
