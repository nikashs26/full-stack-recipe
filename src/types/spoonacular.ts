
export interface SpoonacularRecipe {
  id: number;
  title: string;
  image: string;
  imageType: string;
}

export interface SpoonacularSearchResponse {
  results: SpoonacularRecipe[];
  offset: number;
  number: number;
  totalResults: number;
}
