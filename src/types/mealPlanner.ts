export interface MealPlan {
  [day: string]: {
    breakfast: MealPlanItem | null;
    lunch: MealPlanItem | null;
    dinner: MealPlanItem | null;
  };
}

export interface MealPlanItem {
  id: string;
  name: string;
  description: string;
  cuisine: string;
  cookingTime: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  ingredients: string[];
  instructions: string;
}

export interface MealPlanResponse {
  success: boolean;
  plan: MealPlan;
  preferences_used: any;
  llm_used?: string;
  error?: string;
}

export type MealType = 'breakfast' | 'lunch' | 'dinner';

export type WeekDay = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday'; 