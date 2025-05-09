
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
  allergens: string[];
  cookingSkillLevel: 'beginner' | 'intermediate' | 'advanced';
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
