// Temporary file to fix build error
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
  diets?: string[];
  ratings?: number[];
}