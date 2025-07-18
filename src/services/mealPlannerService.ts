import { apiCall } from '../utils/apiUtils';

export interface MealPlan {
  days: Array<{
    day: string;
    meals: {
      [key: string]: {
        name: string;
        description: string;
        cuisine: string;
        cookingTime?: string;
        cook_time?: string;
        prep_time?: string;
        difficulty: string;
        ingredients: string[];
      };
    };
  }>;
  plan_type: 'llm_generated' | 'rule_based';
}

export const generateMealPlan = async (): Promise<MealPlan> => {
  const response = await apiCall('/meal-plan/generate', {
    method: 'POST'
  });

  if (!response.ok) {
    const data = await response.json();
    if (response.status === 400 && data.redirect_to) {
      throw new Error(data.error || 'Preferences required');
    }
    throw new Error(data.error || 'Failed to generate meal plan');
  }

  const data = await response.json();
  return data;
};

export const regenerateMeal = async (day: string, mealType: string): Promise<void> => {
  const response = await apiCall('/meal-plan/regenerate', {
    method: 'POST',
    body: JSON.stringify({ day, mealType })
  });

  if (!response.ok) {
    throw new Error('Failed to regenerate meal');
  }
}; 