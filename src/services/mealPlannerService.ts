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

export interface NutritionValue {
  amount: number | string;
  unit?: string;
  name?: string;
}

export type NutritionField = number | string | NutritionValue;

export interface NutritionInfo {
  calories: NutritionField;
  protein: NutritionField;
  carbs: NutritionField;
  fat: NutritionField;
  [key: string]: NutritionField;
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
    calories: NutritionField;
    protein: NutritionField;
    carbs: NutritionField;
    fat: NutritionField;
    [key: string]: NutritionField;
  };
  weekly_totals: {
    calories: NutritionField;
    protein: NutritionField;
    carbs: NutritionField;
    fat: NutritionField;
    [key: string]: NutritionField;
  };
  targets?: {
    calories: NutritionField;
    protein: NutritionField;
    carbs: NutritionField;
    fat: NutritionField;
    [key: string]: NutritionField;
  };
  dietary_considerations?: string[];
  meal_inclusions?: {
    breakfast: boolean;
    lunch: boolean;
    dinner: boolean;
    snacks: boolean;
    [key: string]: boolean;
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
    console.log('🚀 Generating meal plan...');
    
    // Use the simple meal planner endpoint (no complex macro/nutrition logic)
    const response = await apiCall('/ai/simple_meal_plan', {
      method: 'POST',
      body: JSON.stringify({}) // No complex options needed
    });

    if (!response.ok) {
      const errorData = await response.json();
      if (response.status === 400 && errorData.redirect_to) {
        throw new Error(errorData.error || 'Preferences required');
      }
      throw new Error(errorData.error || 'Failed to generate meal plan');
    }

    const data = await response.json();
    console.log('📦 Received response:', data);
    
    // Handle the response format from the simple LLM meal planner
    if (data.success && data.plan) {
      console.log('✅ Converting plan data:', data.plan);
      // Convert the simple plan format to our expected format
      return convertSimplePlanToMealPlanData(data.plan);
    } else if (data.error) {
      throw new Error(data.error);
    }
    
    console.error('❌ Invalid response format:', data);
    throw new Error('Invalid response format from server');
  } catch (error) {
    console.error('❌ Error generating meal plan:', error);
    throw error;
  }
};

/**
 * Convert the simple LLM meal plan format to our expected MealPlanData format
 */
function convertSimplePlanToMealPlanData(simplePlan: any): MealPlanData {
  const days: MealDay[] = [];
  const today = new Date();
  
  // Handle different response formats from free LLM agent
  let planData = simplePlan;
  
  // If the response has a 'plan' property, use that
  if (simplePlan.plan) {
    planData = simplePlan.plan;
  }
  
  // If the response has a 'days' property, use that
  if (simplePlan.days) {
    planData = simplePlan.days;
  }
  
  // If the response has a 'meal_plan' property, use that
  if (simplePlan.meal_plan) {
    planData = simplePlan.meal_plan;
  }
  
  console.log('Converting plan data:', planData);
  
  // Convert the simple plan format to our expected format
  const dayNames = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
  
  dayNames.forEach((dayName, index) => {
    const date = new Date(today);
    date.setDate(today.getDate() + index);
    
    const dayData = planData[dayName] || {};
    const meals: Meal[] = [];
    
    console.log(`Processing ${dayName}:`, dayData);
    
    // Convert breakfast, lunch, dinner to our format
    ['breakfast', 'lunch', 'dinner'].forEach(mealType => {
      const mealData = dayData[mealType];
      if (mealData) {
        console.log(`Processing ${mealType}:`, mealData);
        
        meals.push({
          name: mealData.name || mealData.title || `Unknown ${mealType}`,
          meal_type: mealType,
          cuisine: mealData.cuisine || 'Unknown',
          is_vegetarian: mealData.is_vegetarian || false,
          is_vegan: mealData.is_vegan || false,
          ingredients: Array.isArray(mealData.ingredients) ? mealData.ingredients : [],
          instructions: Array.isArray(mealData.instructions) 
            ? mealData.instructions 
            : [mealData.instructions || 'No instructions provided'],
          nutrition: {
            calories: mealData.calories || mealData.nutrition?.calories || 0,
            protein: mealData.protein || mealData.nutrition?.protein || '0g',
            carbs: mealData.carbs || mealData.nutrition?.carbs || '0g',
            fat: mealData.fat || mealData.nutrition?.fat || '0g'
          },
          prep_time: mealData.prep_time || mealData.cookingTime || '30 minutes',
          cook_time: mealData.cook_time || mealData.cookingTime || '30 minutes',
          servings: mealData.servings || 2,
          difficulty: mealData.difficulty || 'beginner'
        });
      }
    });
    
    days.push({
      day: dayName.charAt(0).toUpperCase() + dayName.slice(1),
      date: date.toISOString().split('T')[0],
      meals
    });
  });
  
  console.log('Converted days:', days);
  
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
    dietary_considerations: [],
    meal_inclusions: {
      breakfast: true,
      lunch: true,
      dinner: true,
      snacks: false
    }
  };
  
  return {
    days,
    shopping_list,
    nutrition_summary,
    generated_at: new Date().toISOString(),
    preferences_used: {},
    plan_type: 'weekly'
  };
}

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