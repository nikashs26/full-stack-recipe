
export interface User {
  id: string;
  email: string;
  displayName?: string;
  preferences?: UserPreferences;
  createdAt: string;
}

export interface UserPreferences {
  dietaryRestrictions: string[];
  favoriteCuisines: string[];
  favoriteFoods: string[];
  foodsToAvoid: string[];
  healthGoals: string[];
  allergens: string[];
  cookingSkillLevel: 'beginner' | 'intermediate' | 'advanced';
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

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Supabase Database Types
export interface UserProfile {
  id: string;
  email: string;
  display_name: string;
  preferences?: UserPreferences;
  created_at: string;
  updated_at?: string;
}
