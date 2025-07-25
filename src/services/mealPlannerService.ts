import { apiCall } from '../utils/apiUtils';

export interface MealPlanOptions {
  budget?: number;
  dietaryGoals?: string[];
  currency?: string;
}

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
        cost?: {
          perServing: number;
          total: number;
          currency: string;
        };
      };
    };
  }>;
  plan_type: 'llm_generated' | 'rule_based';
  totalCost?: number;
  budget?: number;
  currency?: string;
}

export const generateMealPlan = async (options?: MealPlanOptions): Promise<MealPlan> => {
  const response = await apiCall('/ai/meal_plan', {
    method: 'POST',
    body: JSON.stringify({
      budget: options?.budget,
      dietary_goals: options?.dietaryGoals,
      currency: options?.currency
    })
  });

  if (!response.ok) {
    const data = await response.json();
    if (response.status === 400 && data.redirect_to) {
      throw new Error(data.error || 'Preferences required');
    }
    throw new Error(data.error || 'Failed to generate meal plan');
  }

  const data = await response.json();
  
  // If we already have a structured response, return it directly
  if (data.days) {
    return {
      ...data,
      days: data.days.map((day: any) => ({
        ...day,
        meals: Object.entries(day.meals || {}).reduce((acc, [mealType, meal]: [string, any]) => ({
          ...acc,
          [mealType]: {
            name: meal.name,
            description: meal.description || `A delicious ${mealType} option`,
            cuisine: '',
            difficulty: 'medium',
            ingredients: meal.ingredients || [],
            cost: meal.cost ? {
              perServing: meal.cost.per_serving || 0,
              total: meal.cost.total || 0,
              currency: data.currency || '$'
            } : undefined,
            nutrition: meal.nutrition || {
              calories: 0,
              protein: 0,
              carbs: 0,
              fat: 0
            },
            prep_time: meal.prep_time || 15,
            cook_time: meal.cook_time || 30
          }
        }), {})
      })),
      plan_type: data.plan_type || 'llm_generated',
      totalCost: data.totalCost || 0,
      budget: data.budget,
      currency: data.currency || 'USD'
    } as MealPlan;
  }
  
  // Fallback to markdown parsing if needed
  if (data.meal_plan) {
    return parseMealPlanResponse(data.meal_plan, {
      budget: options?.budget,
      currency: options?.currency,
      dietaryGoals: options?.dietaryGoals
    });
  }
  
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

interface ParseMealPlanOptions {
  budget?: number;
  currency?: string;
  dietaryGoals?: string[];
}

const parseMealPlanResponse = (markdown: string, options: ParseMealPlanOptions): MealPlan => {
  const lines = markdown.split('\n').filter(line => line.trim());
  let currentDay = '';
  let currentMeal = '';
  
  const days: Array<{day: string; meals: {[key: string]: any}}> = [];
  let currentDayMeals: {[key: string]: any} = {};
  
  // Helper function to parse a meal line
  const parseMealLine = (line: string) => {
    // Extract meal name, description, etc. from the line
    // This is a simplified parser - you may need to adjust based on the actual format
    const match = line.match(/^\s*-\s*(\w+):\s*(.+)$/i);
    if (match) {
      const mealType = match[1].toLowerCase();
      const mealDetails = match[2];
      
      // Extract name, cuisine, etc. from mealDetails
      // This is a simplified example - adjust based on your actual format
      const nameMatch = mealDetails.match(/([^,]+),/);
      const name = nameMatch ? nameMatch[1].trim() : mealDetails.trim();
      
      currentMeal = mealType;
      currentDayMeals[mealType] = {
        name,
        description: mealDetails,
        cuisine: '',
        difficulty: '',
        ingredients: [],
        cost: options.budget ? {
          perServing: options.budget / 21, // Simple average per meal
          total: options.budget / 3, // Simple average per day
          currency: options.currency || '$'
        } : undefined
      };
    }
  };
  
  // Process each line of the markdown
  for (const line of lines) {
    // Check for day headers
    const dayMatch = line.match(/^#+\s*(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)/i);
    if (dayMatch) {
      // Save previous day's meals if they exist
      if (currentDay && Object.keys(currentDayMeals).length > 0) {
        days.push({
          day: currentDay,
          meals: {...currentDayMeals}
        });
        currentDayMeals = {};
      }
      currentDay = dayMatch[1];
      continue;
    }
    
    // Check for meal lines
    if (line.match(/^\s*-\s*(Breakfast|Lunch|Dinner|Snack):/i)) {
      parseMealLine(line);
    }
    
    // Additional parsing for meal details could go here
  }
  
  // Add the last day's meals
  if (currentDay && Object.keys(currentDayMeals).length > 0) {
    days.push({
      day: currentDay,
      meals: {...currentDayMeals}
    });
  }
  
  // Calculate total cost
  const totalCost = options.budget ? 
    days.reduce((sum, day) => {
      return sum + Object.values(day.meals).reduce((daySum, meal) => {
        return daySum + (meal.cost?.total || 0);
      }, 0);
    }, 0) : undefined;
  
  return {
    days,
    plan_type: 'llm_generated',
    totalCost,
    budget: options.budget,
    currency: options.currency
  };
};