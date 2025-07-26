import { apiCall } from '../utils/apiUtils';

export interface MealPlanOptions {
  budget?: number;
  dietaryGoals?: string[];
  currency?: string;
  mealPreferences?: {
    includeBreakfast: boolean;
    includeLunch: boolean;
    includeDinner: boolean;
    includeSnacks: boolean;
  };
  nutritionTargets?: {
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
  };
}

export interface NutritionInfo {
  calories: number;
  protein: string | number;
  carbs: string | number;
  fat: string | number;
  [key: string]: string | number;
}

export interface Meal {
  name: string;
  meal_type: string;
  cuisine: string;
  is_vegetarian: boolean;
  is_vegan: boolean;
  ingredients: string[];
  instructions: string[] | string;
  nutrition: NutritionInfo;
  prep_time?: string;
  cook_time?: string;
  servings?: number;
  difficulty?: string;
  nutritional_highlights?: string[];
  tags?: string[];
}

export interface MealDay {
  day: string;
  date: string;
  meals: Meal[];
  daily_notes?: string;
}

export interface ShoppingListItem {
  item: string;
  category: string;
  estimated_cost: number;
  quantity?: string;
}

export interface ShoppingList {
  ingredients: ShoppingListItem[];
  estimated_cost: number;
}

export interface NutritionSummary {
  daily_average: {
    calories: number;
    protein: string;
    carbs: string;
    fat: string;
  };
  weekly_totals: {
    calories: number;
    protein: string;
    carbs: string;
    fat: string;
  };
  targets: {
    calories: number;
    protein: string;
    carbs: string;
    fat: string;
  };
  dietary_considerations: string[];
  meal_inclusions: {
    breakfast: boolean;
    lunch: boolean;
    dinner: boolean;
    snacks: boolean;
  };
}

export interface MealPlanData {
  days: MealDay[];
  shopping_list: ShoppingList;
  nutrition_summary: NutritionSummary;
  generated_at: string;
  preferences_used: Record<string, any>;
  plan_type: string;
}

export interface MealPlanResponse {
  success: boolean;
  data: MealPlanData;
  message: string;
}

export const generateMealPlan = async (options?: MealPlanOptions): Promise<MealPlanData> => {
  try {
    // Call the actual backend endpoint
    const requestBody: any = {
      budget: options?.budget,
      dietary_goals: options?.dietaryGoals,
      currency: options?.currency || '$',
      meal_preferences: options?.mealPreferences,
      nutrition_targets: options?.nutritionTargets
    };

    // Remove undefined values
    Object.keys(requestBody).forEach(key => requestBody[key] === undefined && delete requestBody[key]);

    const response = await apiCall('/api/ai/meal_plan', {
      method: 'POST',
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const errorData = await response.json();
      if (response.status === 400 && errorData.redirect_to) {
        throw new Error(errorData.error || 'Preferences required');
      }
      throw new Error(errorData.error || 'Failed to generate meal plan');
    }

    const data = await response.json();
    
    // Handle the response format from the backend
    if (data.success && data.data) {
      return data.data;  // The plan is in the data field
    } else if (data.error) {
      throw new Error(data.error);
    } else if (data.plan) {
      // Fallback to the old format
      return data.plan;
    }
    
    console.error('Invalid response format:', data);
    throw new Error('Invalid response format from server');
  } catch (error) {
    console.error('Error generating meal plan:', error);
    throw error;
  }
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

interface ParseMealPlanOptions {
  budget?: number;
  currency?: string;
  dietaryGoals?: string[];
}

export const parseMealPlanResponse = (markdown: string, options: ParseMealPlanOptions): MealPlanData => {
  // Create empty days for the week
  const days: MealDay[] = [];
  const today = new Date();
  
  // Generate a week's worth of empty days
  for (let i = 0; i < 7; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() + i);
    
    const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const dayName = dayNames[date.getDay()];
    
    days.push({
      day: dayName,
      date: date.toISOString().split('T')[0],
      meals: []
    });
  }
  
  // Create a default shopping list
  const shopping_list: ShoppingList = {
    ingredients: [],
    estimated_cost: 0
  };
  
  // Create a default nutrition summary
  const nutrition_summary: NutritionSummary = {
    daily_average: {
      calories: 0,
      protein: '0g',
      carbs: '0g',
      fat: '0g'
    },
    weekly_totals: {
      calories: 0,
      protein: '0g',
      carbs: '0g',
      fat: '0g'
    },
    targets: {
      calories: 0,
      protein: '0g',
      carbs: '0g',
      fat: '0g'
    },
    dietary_considerations: [],
    meal_inclusions: {
      breakfast: true,
      lunch: true,
      dinner: true,
      snacks: false
    }
  };
  
  // Parse the markdown to extract meal information
  const lines = markdown.split('\n').filter(line => line.trim());
  let currentDay: MealDay | null = null;
  
  // Process each line of the markdown
  for (const line of lines) {
    // Check for day headers
    const dayMatch = line.match(/^#+\s*(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)/i);
    if (dayMatch) {
      currentDay = days.find(d => d.day.toLowerCase() === dayMatch[1].toLowerCase()) || null;
      continue;
    }
    
    // Check for meal lines
    if (currentDay) {
      const mealMatch = line.match(/^\s*-\s*(\w+):\s*(.+)$/i);
      if (mealMatch) {
        const mealType = mealMatch[1].toLowerCase();
        const mealDetails = mealMatch[2];
        
        // Create a new meal with default values
        const meal: Meal = {
          name: mealDetails.split(',')[0]?.trim() || `Meal ${currentDay.meals.length + 1}`,
          meal_type: mealType,
          cuisine: '',
          is_vegetarian: false,
          is_vegan: false,
          ingredients: [],
          instructions: '',
          nutrition: {
            calories: 0,
            protein: '0g',
            carbs: '0g',
            fat: '0g'
          }
        };
        
        currentDay.meals.push(meal);
      }
    }
  }
  
  // Return the basic structure matching our new format
  return {
    days,
    shopping_list,
    nutrition_summary,
    generated_at: new Date().toISOString(),
    preferences_used: {
      budget: options.budget,
      currency: options.currency || '$',
      dietary_goals: options.dietaryGoals || []
    },
    plan_type: 'weekly'
  };
};