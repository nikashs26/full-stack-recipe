
export type DietaryRestriction = 'vegetarian' | 'vegan' | 'gluten-free' | 'carnivore';

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
}

export interface Comment {
  id: string;
  author: string;
  text: string;
  date: string;
}
