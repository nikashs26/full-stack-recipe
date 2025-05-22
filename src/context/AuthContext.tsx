
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
  resetAuthError: () => void;
  isVerificationRequired: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>(initialState);
  const [isVerificationRequired, setIsVerificationRequired] = useState(false);

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
            // Add a validation function to ensure the data conforms to UserPreferences
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
        console.log("Auth state changed:", event);
        
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
            // Add a validation function to ensure the data conforms to UserPreferences
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
          
          // Reset verification flag when user is successfully signed in
          setIsVerificationRequired(false);
        } else if (event === 'SIGNED_OUT') {
          console.log("User signed out");
          setState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null
          });
          setIsVerificationRequired(false);
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
    
    // Check if the data has the required fields and proper types
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
      // Log the sign-in attempt to help with debugging
      console.log('Attempting to sign in user:', email);
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });
      
      if (error) {
        console.error('Supabase Auth Error:', error);
        
        // Check if this could be due to unverified email
        if (error.message === 'Invalid login credentials') {
          // Check if user exists but might need email verification
          const { data: userData } = await supabase.auth.admin.listUsers();
          const userExists = userData?.users?.some(u => u.email === email);
          
          if (userExists) {
            setIsVerificationRequired(true);
            setState(prev => ({ 
              ...prev, 
              isLoading: false, 
              error: "Your email may not be verified. Please check your inbox for a verification link or try resetting your password." 
            }));
            return;
          }
        }
        
        setState(prev => ({ ...prev, isLoading: false, error: error.message }));
        throw new Error(error.message);
      }
      
      console.log('Sign in successful, auth data:', data);
      
      // We'll let the auth state listener handle updating the state
      // Just make sure we're not stuck in a loading state
      if (!data.user) {
        setState(prev => ({ ...prev, isLoading: false }));
      }
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
      // Reset verification flag when attempting a new sign-up
      setIsVerificationRequired(false);
      
      // Log the sign-up attempt to help with debugging
      console.log('Attempting to sign up user:', email);
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const { data, error } = await supabase.auth.signUp({
        email,
        password
      });
      
      if (error) {
        console.error('Supabase Auth Error:', error);
        setState(prev => ({ ...prev, isLoading: false, error: error.message }));
        return { error: error.message };
      }
      
      console.log('Sign up successful, auth data:', data);
      
      // Check if email verification is required
      if (data.user && !data.session) {
        console.log('Email verification required');
        setIsVerificationRequired(true);
        setState(prev => ({ 
          ...prev, 
          isLoading: false,
          error: null
        }));
        
        return { error: "Please check your email to verify your account before signing in." };
      }
      
      if (data.user) {
        try {
          console.log('Creating sign-up record for email:', email);
          
          // Insert into the sign_ups table
          const signUpRecord = {
            email: email
          };
          
          const { error: signUpError } = await supabase
            .from('sign_ups')
            .insert([signUpRecord]);
            
          if (signUpError) {
            console.error("Error creating sign-up record:", signUpError);
            console.log("Will proceed with authentication despite profile creation error");
          }
          
          // Update the state directly since authentication was successful
          const enhancedUser: User = {
            id: data.user.id,
            email: data.user.email || '',
            displayName: data.user.email?.split('@')[0] || '',
            createdAt: data.user.created_at || new Date().toISOString()
          };
          
          setState({
            user: enhancedUser,
            isAuthenticated: !!data.session, // Only set to true if we have a session
            isLoading: false,
            error: null
          });
          
          if (!data.session) {
            return { error: "Please check your email to verify your account before signing in." };
          }
          
          return {};
        } catch (profileError: any) {
          console.error("Unexpected error creating profile:", profileError);
          
          // Still authenticate the user even if profile creation failed
          const enhancedUser: User = {
            id: data.user.id,
            email: data.user.email || '',
            displayName: data.user.email?.split('@')[0] || '',
            createdAt: data.user.created_at || new Date().toISOString()
          };
          
          setState({
            user: enhancedUser,
            isAuthenticated: !!data.session,
            isLoading: false,
            error: null
          });
          
          if (!data.session) {
            return { error: "Please check your email to verify your account before signing in." };
          }
          
          return { error: profileError.message || "Failed to create profile" };
        }
      } else {
        console.error("User object not found in sign-up response");
        setState(prev => ({ 
          ...prev, 
          isLoading: false,
          error: "Failed to create user account" 
        }));
        
        return { error: "Failed to create user account" };
      }
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
      
      // State update should be handled by auth listener, but
      // let's make sure we don't get stuck in a loading state
      setTimeout(() => {
        setState(prev => {
          // Only update if we're still in loading state
          if (prev.isLoading) {
            return {
              user: null,
              isAuthenticated: false,
              isLoading: false,
              error: null
            };
          }
          return prev;
        });
      }, 1000);
    } catch (error: any) {
      console.error("Error signing out:", error.message);
      setState(prev => ({ ...prev, isLoading: false }));
    }
  };

  const updateUserPreferences = async (preferences: UserPreferences) => {
    if (!state.user?.email) return;
    
    try {
      // Convert UserPreferences to Json type for Supabase
      const jsonPreferences = preferences as unknown as Json;
      
      const { error } = await supabase
        .from('sign_ups')
        .update({ 
          preferences: jsonPreferences
        })
        .eq('email', state.user.email);
        
      if (error) throw error;
      
      // Update local state
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
  
  const resetAuthError = () => {
    setState(prev => ({ ...prev, error: null }));
  };

  return (
    <AuthContext.Provider
      value={{
        ...state,
        signIn,
        signUp,
        signOut,
        updateUserPreferences,
        resetAuthError,
        isVerificationRequired
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

