import { apiCall } from '../utils/apiUtils';

export interface UserPreferences {
  dietaryRestrictions: string[];
  favoriteCuisines: string[];
  favoriteFoods: string[];
  allergens: string[];
  cookingSkillLevel: 'beginner' | 'intermediate' | 'advanced';
  healthGoals?: string[];
  maxCookingTime?: string;
  includeBreakfast?: boolean;
  includeLunch?: boolean;
  includeDinner?: boolean;
  includeSnacks?: boolean;
  targetCalories?: number;
  targetProtein?: number;
  targetCarbs?: number;
  targetFat?: number;
}

export const loadUserPreferences = async (): Promise<UserPreferences> => {
  const response = await apiCall('/api/preferences', {
    method: 'GET'
  });

  if (!response.ok) {
    throw new Error('Failed to load preferences');
  }

  const data = await response.json();
  return data.preferences || {
    dietaryRestrictions: [],
    favoriteCuisines: [],
    favoriteFoods: [],
    allergens: [],
    cookingSkillLevel: 'beginner',
    healthGoals: [],
    maxCookingTime: '30 minutes'
  };
};

export const saveUserPreferences = async (preferences: UserPreferences): Promise<void> => {
  const response = await apiCall('/api/preferences', {
    method: 'POST',
    body: JSON.stringify({ preferences })
  });

  if (!response.ok) {
    throw new Error('Failed to save preferences');
  }
}; 