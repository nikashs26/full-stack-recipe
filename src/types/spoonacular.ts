
export interface SpoonacularRecipe {
  id: number;
  title: string;
  image: string;
  imageType: string;
  readyInMinutes?: number;
  servings?: number;
  sourceUrl?: string;
  summary?: string;
  cuisines?: string[];
  dishTypes?: string[];
  diets?: string[];
  instructions?: string;
  isExternal?: boolean;
  analyzedInstructions?: {
    name: string;
    steps: {
      number: number;
      step: string;
      ingredients?: { id: number; name: string; localizedName: string; image: string }[];
    }[];
  }[];
  extendedIngredients?: {
    id: number;
    aisle: string;
    image: string;
    name: string;
    amount: number;
    unit: string;
    originalString: string;
    original?: string;
  }[];
}

export interface SpoonacularSearchResponse {
  results: SpoonacularRecipe[];
  offset: number;
  number: number;
  totalResults: number;
}
