

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase'; // Using '../lib/supabase' for consistency
import { useToast } from '@/hooks/use-toast';
import { UserProfile } from '../types/auth'; // Ensure UserProfile is imported if used for preferences

interface UserPreferences {
  favoriteCuisines: string[];
  dietaryRestrictions: string[];
  cookingSkillLevel: 'beginner' | 'intermediate' | 'advanced';
  allergens: string[];
}

// Extend Supabase's User type to include our custom preferences
interface ExtendedUser extends User {
  preferences?: UserPreferences;
  displayName?: string;
  createdAt?: string;
}

interface AuthContextType {
  user: ExtendedUser | null;
  session: Session | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<{ error: any }>;
  signUp: (email: string, password: string) => Promise<{ error: any }>;
  signOut: () => Promise<void>;
  updatePreferences: (preferences: UserPreferences) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<ExtendedUser | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  // Helper to load user preferences from 'sign_ups' table
  const loadUserPreferences = async (userEmail: string): Promise<UserPreferences | undefined> => {
    try {
      const { data, error } = await supabase
        .from('sign_ups')
        .select('preferences')
        .eq('email', userEmail)
        .maybeSingle();

      if (error) {
        console.error("Error loading user preferences:", error);
        return undefined;
      }
      if (!data?.preferences) {
        return undefined;
      }
      const rawPrefs = data.preferences;
      // Basic runtime check for expected preference structure
      if (
        rawPrefs &&
        typeof rawPrefs === 'object' &&
        !Array.isArray(rawPrefs) &&
        'favoriteCuisines' in rawPrefs &&
        'dietaryRestrictions' in rawPrefs &&
        'cookingSkillLevel' in rawPrefs &&
        'allergens' in rawPrefs
      ) {
        return rawPrefs as unknown as UserPreferences;
      }
      return undefined;
    } catch (e) {
      console.error("Unexpected error in loadUserPreferences:", e);
      return undefined;
    }
  };

  // Helper to set the user state including preferences
  const updateUserState = async (session: Session | null) => {
    if (!session?.user) {
      setUser(null);
      setIsLoading(false); // No user, turn off loading
      return;
    }

    try {
      const preferences = await loadUserPreferences(session.user.email!);
      const enhancedUser: ExtendedUser = {
        ...session.user,
        preferences,
        displayName: session.user.email?.split('@')[0] || '',
        createdAt: session.user.created_at || new Date().toISOString()
      };
      setUser(enhancedUser);
      setIsLoading(false); // User loaded, turn off loading
      console.log("AuthContext: User state updated:", enhancedUser.email, "Loading:", false);
    } catch (e) {
      console.error("AuthContext: Error updating user state with preferences:", e);
      // Even if preferences fail, set user and turn off loading
      setUser(session.user);
      setIsLoading(false);
      console.log("AuthContext: User state updated (partial) due to preference error. Loading:", false);
    }
  };

  // Main effect for auth state changes and initial session check
  useEffect(() => {
    let mounted = true;

    const initializeAuth = async () => {
      console.log("AuthContext: Initializing authentication...");
      setIsLoading(true); // Ensure loading is true at start of initialization

      try {
        const { data: { session: initialSession }, error: sessionError } = await supabase.auth.getSession();

        if (!mounted) return;

        if (sessionError) {
          console.error("AuthContext: Error fetching initial session:", sessionError);
          setSession(null);
          setUser(null);
          setIsLoading(false); // Turn off loading on session fetch error
          return;
        }

        setSession(initialSession);
        await updateUserState(initialSession); // Update user state based on initial session
        setIsLoading(false); // Ensure loading is false after initial session check

      } catch (e) {
        console.error("AuthContext: Unexpected error during initial session check:", e);
        if (mounted) {
          setSession(null);
          setUser(null);
          setIsLoading(false); // Ensure loading is false on unexpected error
        }
      }
    };

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (!mounted) return;
        console.log("AuthContext: Auth state changed event:", event, "Session present:", !!session);

        setSession(session);
        // For SIGNED_IN and INITIAL_SESSION (with a session), update user state
        // For SIGNED_OUT, updateUserState will set user to null
        await updateUserState(session);

        if (event === 'SIGNED_OUT') {
          // Additional cleanup specific to sign out if needed
          console.log("AuthContext: User signed out. Clearing local storage related to auth.");
          const keysToRemove = [];
          for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && (key.startsWith('sb-') || key.includes('supabase') || key.includes('auth'))) {
              keysToRemove.push(key);
            }
          }
          keysToRemove.forEach(key => localStorage.removeItem(key));
          // Optionally redirect to home or sign-in page after full cleanup
          // window.location.href = '/'; 
        }
        setIsLoading(false); // Ensure loading is false after any auth state change
      }
    );

    // Run initial setup
    initializeAuth();

    // Cleanup subscription on unmount
    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []); // Empty dependency array means this runs once on mount

  // Diagnostic log for state changes (can be commented out in production)
  useEffect(() => {
    console.log("AuthContext State (Diagnostic):", {
      user: user?.email,
      isAuthenticated: !!user,
      isLoading,
      session: !!session
    });
  }, [user, session, isLoading]);


  const signIn = async (email: string, password: string) => {
    setIsLoading(true); // Start loading on sign in attempt
    console.log('AuthContext: Attempting to sign in user:', email);
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        console.error('AuthContext: Supabase Auth Error during sign-in:', error);
        setIsLoading(false); // Turn off loading on error
        return { error };
      }

      console.log('AuthContext: Sign in successful. Auth state change listener will update state.');
      return { error: null }; // State update handled by onAuthStateChange
    } catch (error: any) {
      console.error('AuthContext: Unexpected error during sign-in:', error);
      setIsLoading(false); // Turn off loading on unexpected error
      return { error: error.message || "An unexpected error occurred during sign-in." };
    }
  };

  const signUp = async (email: string, password: string) => {
    setIsLoading(true); // Start loading on sign up attempt
    console.log('AuthContext: Attempting to sign up user:', email);
    try {
      const redirectUrl = `${window.location.origin}/`; // Ensure this is correct

      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: redirectUrl,
          data: { // You can add initial user metadata here if needed
            preferences: {} as any // Initialize empty preferences for new users
          }
        }
      });

      if (error) {
        console.error('AuthContext: Supabase Auth Error during sign-up:', error);
        setIsLoading(false); // Turn off loading on error
        return { error };
      }

      console.log('AuthContext: Sign up successful. Auth state change listener will update state.');

      // After successful sign-up, attempt to save a record in 'sign_ups' table if user is created
      // Supabase's signUp often triggers a SIGNED_IN event, so the user might already be set by then.
      // This is a redundant check if your auth listener fully handles it.
      // If you are relying on an explicit 'sign_ups' table for profiles:
      if (!user) { // Only if user is not already set by auth listener (e.g., email confirmation flow)
        try {
          const { error: signUpRecordError } = await supabase
            .from('sign_ups')
            .insert([{ email: email, preferences: {} as any }]); // Ensure preferences is cast to any for Supabase
          if (signUpRecordError) {
            console.error("AuthContext: Error saving initial sign-up record:", signUpRecordError);
          } else {
            console.log("AuthContext: Initial sign-up record saved for new user.");
          }
        } catch (e) {
          console.error("AuthContext: Unexpected error saving sign-up record:", e);
        }
      }

      return { error: null };
    } catch (error: any) {
      console.error('AuthContext: Unexpected error during sign-up:', error);
      setIsLoading(false); // Turn off loading on unexpected error
      return { error: error.message || "An unexpected error occurred during sign-up." };
    }
  };

  const signOut = async () => {
    setIsLoading(true); // Indicate loading for sign out
    console.log("AuthContext: Attempting to sign out user.");
    try {
      const { error } = await supabase.auth.signOut();
      if (error) {
        console.error('AuthContext: Supabase Auth Error during sign-out:', error);
        toast({
          title: 'Sign out failed',
          description: error.message,
          variant: 'destructive',
        });
        setIsLoading(false); // Turn off loading on error
        throw new Error(error.message);
      }
      console.log('AuthContext: Sign out successful. Auth state change listener will clear state.');
      // State reset handled by onAuthStateChange listener
      // No explicit setIsLoading(false) here, as onAuthStateChange will do it when user becomes null
    } catch (error: any) {
      console.error('AuthContext: Unexpected error during sign-out:', error);
      setIsLoading(false); // Turn off loading on unexpected error
      throw error;
    }
  };

  const updatePreferences = async (preferences: UserPreferences) => {
    console.log("AuthContext: Attempting to update preferences:", preferences);
    if (!user?.email) {
      toast({
        title: 'Error',
        description: 'You must be signed in to update preferences.',
        variant: 'destructive',
      });
      return false;
    }

    try {
      // 1. Update preferences in the 'sign_ups' table
      const { error: supabaseError } = await supabase
        .from('sign_ups')
        .update({ preferences: preferences as any }) // Cast to any to satisfy Supabase's Json type
        .eq('email', user.email);

      if (supabaseError) {
        console.error("AuthContext: Error updating preferences in Supabase:", supabaseError);
        toast({
          title: 'Error',
          description: `Failed to update preferences: ${supabaseError.message}`,
          variant: 'destructive',
        });
        return false;
      }
      console.log("AuthContext: Supabase preferences updated successfully.");

      // 2. Sync preferences to ChromaDB via Flask backend (using access token)
      const sessionData = await supabase.auth.getSession();
      const accessToken = sessionData.data.session?.access_token;

      if (!accessToken) {
        console.error("AuthContext: No access token found for backend sync.");
        toast({
          title: 'Error',
          description: 'Authentication token missing. Please sign in again.',
          variant: 'destructive',
        });
        return false;
      }

      const response = await fetch('/api/preferences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({ userId: user.id, preferences: preferences })
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("AuthContext: Error syncing preferences to backend/ChromaDB:", errorData);
        toast({
          title: 'Error',
          description: errorData.message || 'Failed to sync preferences to backend.',
          variant: 'destructive',
        });
        return false;
      }
      console.log("AuthContext: Synced preferences to backend/ChromaDB successfully.");

      // Update local state after successful updates
      setUser(prev => {
        if (prev) {
          return { ...prev, preferences: preferences };
        }
        return null;
      });
      console.log("AuthContext: Local user state updated with new preferences.");
      toast({
        title: 'Preferences Updated',
        description: 'Your preferences have been saved successfully.',
      });
      return true;

    } catch (error: any) {
      console.error("AuthContext: Unexpected error during preference update:", error);
      toast({
        title: 'Error',
        description: error.message || 'An unexpected error occurred while saving preferences.',
        variant: 'destructive',
      });
      return false;
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

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
