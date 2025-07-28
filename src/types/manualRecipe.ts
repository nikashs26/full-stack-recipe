export interface ManualRecipe {
  id: string;
  title: string;
  description?: string;
  ingredients: string[];
  instructions: string[];
  image?: string;
  cookingTime?: string;
  servings?: number;
  difficulty?: string;
  cuisine?: string[];
  cuisines?: string[];
  diets?: string[];
  dietaryRestrictions?: string[];
  ratings?: number[];
  ready_in_minutes?: number;
  cooking_instructions?: string[];
}