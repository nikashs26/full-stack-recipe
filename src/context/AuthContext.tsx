
import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase } from '../integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

interface UserPreferences {
  favoriteCuisines: string[];
  dietaryRestrictions: string[];
  cookingSkillLevel: 'beginner' | 'intermediate' | 'advanced';
  allergens: string[];
}

interface ExtendedUser extends User {
  preferences?: UserPreferences;
}

interface AuthContextType {
  user: ExtendedUser | null;
  session: Session | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<{ error: any }>;
  signUp: (email: string, password: string) => Promise<{ error: any }>;
  signOut: () => Promise<void>;
  updatePreferences: (preferences: UserPreferences) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<ExtendedUser | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  // Load user preferences from Supabase
  const loadUserPreferences = async (userEmail: string): Promise<UserPreferences | undefined> => {
    try {
      console.log('Loading preferences for user:', userEmail);
      const { data, error } = await supabase
        .from('sign_ups')
        .select('preferences')
        .eq('email', userEmail)
        .maybeSingle();

      if (error && error.code !== 'PGRST116') { // PGRST116 is "not found"
        console.error('Error loading user preferences:', error);
        return undefined;
      }

      if (!data?.preferences) {
        console.log('No preferences found for user');
        return undefined;
      }

      // Safely validate the preferences data
      const preferences = data.preferences;
      if (preferences && typeof preferences === 'object' && !Array.isArray(preferences)) {
        const prefObj = preferences as Record<string, any>;
        
        // Create a validated preferences object
        const validatedPreferences: UserPreferences = {
          favoriteCuisines: Array.isArray(prefObj.favoriteCuisines) ? prefObj.favoriteCuisines : [],
          dietaryRestrictions: Array.isArray(prefObj.dietaryRestrictions) ? prefObj.dietaryRestrictions : [],
          allergens: Array.isArray(prefObj.allergens) ? prefObj.allergens : [],
          cookingSkillLevel: ['beginner', 'intermediate', 'advanced'].includes(prefObj.cookingSkillLevel) 
            ? prefObj.cookingSkillLevel 
            : 'beginner'
        };
        
        console.log('Loaded preferences:', validatedPreferences);
        return validatedPreferences;
      }

      return undefined;
    } catch (error) {
      console.error('Unexpected error loading preferences:', error);
      return undefined;
    }
  };

  useEffect(() => {
    let mounted = true;

    const initializeAuth = async () => {
      try {
        console.log('Initializing auth...');
        
        // Get current session first
        const { data: { session: initialSession } } = await supabase.auth.getSession();
        console.log('Initial session:', initialSession?.user?.email || 'none');
        
        if (mounted) {
          setSession(initialSession);
          
          if (initialSession?.user) {
            try {
              const preferences = await loadUserPreferences(initialSession.user.email!);
              if (mounted) {
                setUser({
                  ...initialSession.user,
                  preferences
                });
              }
            } catch (error) {
              console.error('Error loading initial user data:', error);
              if (mounted) {
                setUser(initialSession.user);
              }
            }
          } else {
            setUser(null);
          }
          
          setIsLoading(false);
        }

        // Set up auth state listener
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
          async (event, session) => {
            console.log('Auth state changed:', event, session?.user?.email);
            
            if (!mounted) return;
            
            setSession(session);
            
            if (session?.user) {
              try {
                // Load preferences for the user
                const preferences = await loadUserPreferences(session.user.email!);
                if (mounted) {
                  setUser({
                    ...session.user,
                    preferences
                  });
                }
              } catch (error) {
                console.error('Error loading user data:', error);
                if (mounted) {
                  setUser(session.user);
                }
              }
            } else {
              if (mounted) {
                setUser(null);
              }
            }
          }
        );

        return () => {
          mounted = false;
          subscription.unsubscribe();
        };
      } catch (error) {
        console.error('Auth initialization error:', error);
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    const cleanup = initializeAuth();
    
    return () => {
      mounted = false;
      cleanup?.then(fn => fn?.());
    };
  }, []);

  const signIn = async (email: string, password: string) => {
    try {
      console.log('Attempting sign in for:', email);
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        console.error('Sign in error:', error);
        return { error };
      }

      if (data.user) {
        console.log('Sign in successful for:', data.user.email);
      }

      return { error: null };
    } catch (error) {
      console.error('Unexpected sign in error:', error);
      return { error };
    }
  };

  const signUp = async (email: string, password: string) => {
    try {
      console.log('Attempting sign up for:', email);
      const redirectUrl = `${window.location.origin}/`;
      
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: redirectUrl
        }
      });

      if (error) {
        console.error('Sign up error:', error);
        return { error };
      }

      console.log('Sign up result:', data);
      return { error: null };
    } catch (error) {
      console.error('Unexpected sign up error:', error);
      return { error };
    }
  };

  const signOut = async () => {
    try {
      console.log('Attempting sign out');
      const { error } = await supabase.auth.signOut();
      if (error) {
        console.error('Sign out error:', error);
      } else {
        console.log('Sign out successful');
      }
    } catch (error) {
      console.error('Unexpected sign out error:', error);
    }
  };

  const updatePreferences = async (preferences: UserPreferences) => {
    if (!user) {
      console.error('No user found when updating preferences');
      return;
    }

    try {
      console.log('Updating preferences for user:', user.email, preferences);
      
      // Convert UserPreferences to a plain object that matches Json type
      const preferencesJson = {
        favoriteCuisines: preferences.favoriteCuisines,
        dietaryRestrictions: preferences.dietaryRestrictions,
        cookingSkillLevel: preferences.cookingSkillLevel,
        allergens: preferences.allergens
      };
      
      // Add user to our sign_ups table with preferences
      const { error } = await supabase
        .from('sign_ups')
        .upsert({
          email: user.email!,
          preferences: preferencesJson,
        }, {
          onConflict: 'email'
        });

      if (error) {
        console.error('Error updating preferences:', error);
        toast({
          title: 'Error',
          description: 'Failed to update preferences. Please try again.',
          variant: 'destructive',
        });
      } else {
        console.log('Preferences updated successfully');
        // Update local user state
        setUser(prev => prev ? { ...prev, preferences } : null);
        toast({
          title: 'Preferences Updated',
          description: 'Your preferences have been saved successfully.',
        });
      }
    } catch (error) {
      console.error('Unexpected error updating preferences:', error);
      toast({
        title: 'Error',
        description: 'An unexpected error occurred.',
        variant: 'destructive',
      });
    }
  };

  const value = {
    user,
    session,
    isAuthenticated: !!user,
    isLoading,
    signIn,
    signUp,
    signOut,
    updatePreferences,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
