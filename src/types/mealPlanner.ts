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
  // Add any other properties of a recipe that are used in the meal plan item
}

export type MealType = 'breakfast' | 'lunch' | 'dinner'; 