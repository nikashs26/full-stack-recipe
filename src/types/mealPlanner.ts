// Updated types for LLM-powered meal planning

export interface MealPlanItem {
  name: string;
  cuisine: string;
  prep_time: string;
  cook_time: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  servings: number;
  ingredients: string[];
  instructions: string[];
  nutritional_highlights: string[];
  tags: string[];
}

export interface DayMealPlan {
  day: string;
  date: string;
  meals: {
    breakfast: MealPlanItem;
    lunch: MealPlanItem;
    dinner: MealPlanItem;
  };
  daily_notes?: string;
}

export interface WeekSummary {
  theme: string;
  total_recipes: number;
  prep_tips: string[];
  shopping_highlights: string[];
}

export interface WeeklyShoppingList {
  proteins: string[];
  vegetables: string[];
  grains: string[];
  dairy: string[];
  pantry: string[];
  estimated_cost: string;
}

export interface NutritionalSummary {
  weekly_highlights: string[];
  variety_score: string;
  health_rating: string;
}

export interface LLMMealPlan {
  week_summary: WeekSummary;
  days: DayMealPlan[];
  weekly_shopping_list: WeeklyShoppingList;
  nutritional_summary: NutritionalSummary;
  generated_at: string;
  preferences_used: any;
  plan_type: 'llm_generated' | 'rule_based_fallback';
  user_id?: string;
  source?: string;
  note?: string;
}

export interface MealPlanResponse {
  success: boolean;
  meal_plan: LLMMealPlan;
  llm_used: string;
  preferences_used: any;
  generated_at: string;
  total_recipes: number;
  error?: string;
}

export type MealType = 'breakfast' | 'lunch' | 'dinner';

export type WeekDay = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday';

// Legacy types for backward compatibility
export interface MealPlan {
  [day: string]: {
    breakfast: MealPlanItem | null;
    lunch: MealPlanItem | null;
    dinner: MealPlanItem | null;
  };
} 