
import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, AuthState, UserPreferences } from '../types/auth';
import { supabase } from '../integrations/supabase/client';
import { Json } from '../integrations/supabase/types';

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null
};

interface AuthContextType extends AuthState {
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<{ error?: string }>;
  signOut: () => Promise<void>;
  updateUserPreferences: (preferences: UserPreferences) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>(initialState);

  // Check user session on initial load
  useEffect(() => {
    const checkSession = async () => {
      try {
        console.log("Checking current session...");
        const { data, error } = await supabase.auth.getSession();
        
        if (error) {
          console.error("Error fetching session:", error);
          setState({ ...initialState, isLoading: false, error: error.message });
          return;
        }
        
        if (data?.session) {
          console.log("Session found:", data.session);
          const { user } = data.session;
          
          // Get user profile data if available
          const { data: profileData, error: profileError } = await supabase
            .from('sign_ups')
            .select('*')
            .eq('email', user.email)
            .single();
            
          if (profileError) {
            console.log("No sign-up record found, user may have been created through direct auth");
          } else {
            console.log("Found sign-up record:", profileData);
          }
          
          // Parse preferences from profileData as UserPreferences or undefined
          let userPreferences: UserPreferences | undefined;
          if (profileData?.preferences && typeof profileData.preferences === 'object') {
            userPreferences = validateUserPreferences(profileData.preferences as unknown as Record<string, any>);
          }
            
          const enhancedUser: User = {
            id: user.id,
            email: user.email || '',
            displayName: user.email?.split('@')[0] || '',
            preferences: userPreferences,
            createdAt: user.created_at || new Date().toISOString()
          };
          
          setState({
            user: enhancedUser,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
        } else {
          console.log("No active session found");
          setState({ ...initialState, isLoading: false });
        }
      } catch (error) {
        console.error("Unexpected error during session check:", error);
        setState({ ...initialState, isLoading: false, error: "Session check failed" });
      }
    };
    
    checkSession();
    
    // Set up auth state change listener
    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log("Auth state changed:", event, session);
        
        if (event === 'SIGNED_IN' && session?.user) {
          const user = session.user;
          console.log("User signed in:", user);
          
          // Get user sign-up record if available
          const { data: profileData, error: profileError } = await supabase
            .from('sign_ups')
            .select('*')
            .eq('email', user.email)
            .single();
            
          if (profileError) {
            console.log("No sign-up record found:", profileError.message);
          } else {
            console.log("Found sign-up record:", profileData);
          }
          
          // Parse preferences from profileData as UserPreferences or undefined
          let userPreferences: UserPreferences | undefined;
          if (profileData?.preferences && typeof profileData.preferences === 'object') {
            userPreferences = validateUserPreferences(profileData.preferences as unknown as Record<string, any>);
          }
            
          const enhancedUser: User = {
            id: user.id,
            email: user.email || '',
            displayName: user.email?.split('@')[0] || '',
            preferences: userPreferences,
            createdAt: user.created_at || new Date().toISOString()
          };
          
          setState({
            user: enhancedUser,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
        } else if (event === 'SIGNED_OUT') {
          console.log("User signed out");
          setState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null
          });
        }
      }
    );
    
    // Cleanup subscription on unmount
    return () => {
      if (authListener && authListener.subscription) {
        authListener.subscription.unsubscribe();
      }
    };
  }, []);

  // Helper function to validate and convert preferences data to UserPreferences type
  const validateUserPreferences = (data: Record<string, any>): UserPreferences => {
    const defaultPreferences: UserPreferences = {
      dietaryRestrictions: [],
      favoriteCuisines: [],
      allergens: [],
      cookingSkillLevel: 'beginner'
    };
    
    const validatedPrefs: UserPreferences = {
      dietaryRestrictions: Array.isArray(data.dietaryRestrictions) ? data.dietaryRestrictions : defaultPreferences.dietaryRestrictions,
      favoriteCuisines: Array.isArray(data.favoriteCuisines) ? data.favoriteCuisines : defaultPreferences.favoriteCuisines,
      allergens: Array.isArray(data.allergens) ? data.allergens : defaultPreferences.allergens,
      cookingSkillLevel: ['beginner', 'intermediate', 'advanced'].includes(data.cookingSkillLevel) 
        ? data.cookingSkillLevel as 'beginner' | 'intermediate' | 'advanced'
        : defaultPreferences.cookingSkillLevel
    };
    
    return validatedPrefs;
  };

  const signIn = async (email: string, password: string) => {
    try {
      console.log('Attempting to sign in user:', email);
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });
      
      if (error) {
        console.error('Sign in error:', error);
        setState(prev => ({ ...prev, isLoading: false, error: error.message }));
        throw new Error(error.message);
      }
      
      console.log('Sign in successful:', data);
      // Auth state listener will handle updating the state
    } catch (error: any) {
      console.error('Sign in error:', error);
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to sign in',
        isLoading: false
      }));
      throw error;
    }
  };

  const signUp = async (email: string, password: string): Promise<{ error?: string }> => {
    try {
      console.log('Attempting to sign up user:', email);
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const { data, error } = await supabase.auth.signUp({
        email,
        password
      });
      
      if (error) {
        console.error('Sign up error:', error);
        setState(prev => ({ ...prev, isLoading: false, error: error.message }));
        
        // Check if it's a user already registered error
        if (error.message.includes('already registered') || error.message.includes('already exists')) {
          return { error: 'An account with this email already exists. Please sign in instead.' };
        }
        
        return { error: error.message };
      }
      
      console.log('Sign up successful:', data);
      
      if (data.user) {
        // If user is immediately confirmed (no email verification required)
        if (data.user.email_confirmed_at) {
          console.log('User email is confirmed, creating sign-up record');
          
          try {
            const signUpRecord = { email: email };
            const { error: signUpError } = await supabase
              .from('sign_ups')
              .insert([signUpRecord]);
              
            if (signUpError) {
              console.error("Error creating sign-up record:", signUpError);
            }
          } catch (profileError: any) {
            console.error("Error creating profile:", profileError);
          }
          
          // User is automatically signed in, auth listener will handle state
          setState(prev => ({ ...prev, isLoading: false }));
        } else {
          // Email verification required
          console.log('Email verification required');
          setState(prev => ({ ...prev, isLoading: false }));
          return { error: 'Please check your email for a verification link before signing in.' };
        }
      }
      
      return {};
    } catch (error: any) {
      console.error('Sign up error:', error);
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to sign up',
        isLoading: false
      }));
      
      return { error: error.message || 'Failed to sign up' };
    }
  };

  const signOut = async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));
      const { error } = await supabase.auth.signOut();
      if (error) {
        console.error("Error signing out:", error.message);
        setState(prev => ({ ...prev, error: error.message, isLoading: false }));
        throw error;
      }
    } catch (error: any) {
      console.error("Error signing out:", error.message);
      setState(prev => ({ ...prev, isLoading: false }));
    }
  };

  const updateUserPreferences = async (preferences: UserPreferences) => {
    if (!state.user?.email) return;
    
    try {
      const jsonPreferences = preferences as unknown as Json;
      
      const { error } = await supabase
        .from('sign_ups')
        .update({ 
          preferences: jsonPreferences
        })
        .eq('email', state.user.email);
        
      if (error) throw error;
      
      setState({
        ...state,
        user: {
          ...state.user,
          preferences
        }
      });
    } catch (error: any) {
      console.error("Error updating preferences:", error.message);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        ...state,
        signIn,
        signUp,
        signOut,
        updateUserPreferences
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
