<<<<<<< HEAD

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase } from '../integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
=======
import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, AuthState, UserProfile } from '../types/auth';
import { supabase } from '../lib/supabase';
>>>>>>> a0fa3e0 (test agent)

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
  updatePreferences: (preferences: UserPreferences) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

<<<<<<< HEAD
=======
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>(initialState);

  // Helper function to fetch user profile and set state
  const fetchAndSetUserProfile = async (user: any) => {
    try {
      console.log("fetchAndSetUserProfile: Fetching profile for", user.email);
      const { data: profileData, error: profileError } = await supabase
        .from('sign-ups')
        .select('*')
        .eq('email', user.email)
        .single();

      if (profileError && profileError.code !== 'PGRST116') { // PGRST116 is 'No rows found'
        console.warn("fetchAndSetUserProfile: No sign-up record found or other error:", profileError.message);
        // We can proceed even if no explicit sign-up record is found, user might be from another auth method
      }

      const enhancedUser: User = {
        id: user.id,
        email: user.email || '',
        displayName: user.email?.split('@')[0] || '',
        preferences: profileData?.preferences,
        createdAt: user.created_at || new Date().toISOString()
      };

      setState(prevState => ({
        ...prevState,
        user: enhancedUser,
        isAuthenticated: true,
        isLoading: false, // Explicitly set isLoading to false after profile fetch
        error: null
      }));
      console.log("fetchAndSetUserProfile: State Updated (Success)");
    } catch (profileFetchError) {
      console.error("fetchAndSetUserProfile: Unexpected error during profile fetch:", profileFetchError);
      setState(prevState => ({
        ...prevState,
        isLoading: false, // Ensure loading is off even on profile fetch error
        error: `Failed to load user profile: ${(profileFetchError as Error).message}`
      }));
      console.log("fetchAndSetUserProfile: State Updated (Error)");
    }
  };

  // Diagnostic log for isLoading state changes
  useEffect(() => {
    console.log("AuthContext State Changed: isLoading=", state.isLoading, "isAuthenticated=", state.isAuthenticated, "user=", state.user?.email || 'none');
  }, [state.isLoading, state.isAuthenticated, state.user?.email]);

  // Check user session on initial load and set up auth state change listener
  useEffect(() => {
    const checkSession = async () => {
      console.log("checkSession: Starting...");
      setState(prevState => ({ ...prevState, isLoading: true, error: null })); // Ensure loading true when session check begins
      try {
        const { data, error } = await supabase.auth.getSession();

        if (error) {
          console.error("checkSession: Error fetching session:", error);
          setState({ ...initialState, isLoading: false, error: error.message });
          console.log("checkSession: State Updated (Error Path)");
          return;
        }

        if (data?.session) {
          console.log("checkSession: Session found, fetching profile for", data.session.user.email);
          await fetchAndSetUserProfile(data.session.user); // Use the new helper
        } else {
          console.log("checkSession: No session found.");
          setState(prevState => ({ ...initialState, isLoading: false })); // Explicitly set isLoading to false
          console.log("checkSession: State Updated (No Session Found)");
        }
      } catch (error) {
        console.error("checkSession: Unexpected error during session check:", error);
        setState(prevState => ({ ...initialState, isLoading: false, error: (error as Error).message })); // Explicitly set isLoading to false on error
        console.log("checkSession: State Updated (Unexpected Error)");
      }
    };

    checkSession();

    // Set up auth state change listener
    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log("onAuthStateChange: Event=", event, "Session=", session ? "present" : "null");

        if (event === 'SIGNED_IN' && session?.user) {
          console.log("onAuthStateChange: User signed in:", session.user.email);
          await fetchAndSetUserProfile(session.user); // Use the new helper
        } else if (event === 'SIGNED_OUT') {
          console.log("onAuthStateChange: User signed out.");
          setState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null
          });
          console.log("onAuthStateChange: State Updated (SIGNED_OUT)");
        } else if (event === 'INITIAL_SESSION') {
          console.log("onAuthStateChange: Initial session event.");
          // If session is null, it implies no user logged in.
          if (!session) {
            setState(prevState => ({
              ...prevState,
              user: null,
              isAuthenticated: false,
              isLoading: false, // Ensure loading is off after initial check
              error: null
            }));
            console.log("onAuthStateChange: State Updated (INITIAL_SESSION - No User)");
          } else {
            // If session is present on INITIAL_SESSION, ensure loading is off too
            // The fetchAndSetUserProfile from checkSession() will already handle this if a session is present initially
            setState(prevState => ({
                ...prevState,
                isLoading: false, // Ensure loading is off if a session is found during initial check
                error: null
            }));
            console.log("onAuthStateChange: State Updated (INITIAL_SESSION - User Found)");
          }
        } else {
          console.log(`onAuthStateChange: Unhandled event type: ${event}`);
          setState(prevState => ({
              ...prevState,
              isLoading: false
          }));
          console.log(`onAuthStateChange: State Updated (Unhandled Event ${event})`);
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

  const signIn = async (email: string, password: string) => {
    setState(prevState => ({ ...prevState, isLoading: true, error: null })); // Start loading immediately
    console.log('signIn: Attempting to sign in user:', email);

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if (error) {
        console.error('signIn: Supabase Auth Error:', error);
        setState(prevState => ({
            ...prevState,
            error: error.message || 'Failed to sign in',
            isLoading: false // Always turn off loading on error
        }));
        console.log("signIn: State Updated (Error Path)");
        throw new Error(error.message);
      }

      console.log('signIn: Sign in successful, auth data:', data);
      // State update for success is now handled by onAuthStateChange listener
      // No explicit setState for user/isAuthenticated/isLoading:false here on success

    } catch (error: any) {
      console.error('signIn: Catch block - Sign in error:', error);
      setState(prevState => ({
        ...prevState,
        error: error.message || 'Failed to sign in',
        isLoading: false
      }));
      console.log("signIn: State Updated (Catch Error Path)");
      throw error;
    }
  };

  const signUp = async (email: string, password: string) => {
    setState(prevState => ({ ...prevState, isLoading: true, error: null }));
    console.log('signUp: Attempting to sign up user:', email);
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password
      });

      if (error) {
        console.error('signUp: Supabase Auth Error:', error);
        setState(prevState => ({
            ...prevState,
            error: error.message || 'Failed to sign up',
            isLoading: false
        }));
        console.log("signUp: State Updated (Error Path)");
        throw new Error(error.message);
      }

      console.log('signUp: Sign up successful, auth data:', data);

      if (data.user) {
        // State update for success is now handled by onAuthStateChange listener
        // The SIGNED_IN event will be fired after sign up, which will call fetchAndSetUserProfile

        const signUpRecord = {
          email: email,
          password: "********" // Store a placeholder or hash, not raw password
        };

        // Attempt to save sign-up record to 'sign-ups' table
        const { error: signUpRecordError } = await supabase
          .from('sign-ups')
          .insert([signUpRecord]);

        if (signUpRecordError) {
          console.error("signUp: Error saving sign-up record:", signUpRecordError);
          // This error shouldn't prevent the user from being logged in, but we log it
        }
      }

    } catch (error: any) {
      console.error('signUp: Catch block - Sign up error:', error);
      setState(prevState => ({
        ...prevState,
        error: error.message || 'Failed to sign up',
        isLoading: false
      }));
      console.log("signUp: State Updated (Catch Error Path)");
      throw error;
    }
  };

  const signOut = async () => {
    setState(prevState => ({ ...prevState, isLoading: true, error: null }));
    console.log("signOut: Attempting to sign out user.");
    try {
      const { error } = await supabase.auth.signOut();
      if (error) {
        console.error('signOut: Supabase Auth Error:', error);
        setState(prevState => ({
            ...prevState,
            error: error.message || 'Failed to sign out',
            isLoading: false
        }));
        console.log("signOut: State Updated (Error Path)");
        throw new Error(error.message);
      }
      console.log('signOut: Sign out successful.');
      // State is reset by onAuthStateChange listener for 'SIGNED_OUT' event
    } catch (error: any) {
      console.error('signOut: Catch block - Sign out error:', error);
      setState(prevState => ({
        ...prevState,
        error: error.message || 'Failed to sign out',
        isLoading: false
      }));
      console.log("signOut: State Updated (Catch Error Path)");
      throw error;
    }
  };

  const updateUserPreferences = async (preferences: any) => {
    console.log("updateUserPreferences: Attempting to update preferences:", preferences);
    if (!state.user) {
      console.warn("updateUserPreferences: No authenticated user to update preferences for.");
      return; 
    }

    try {
      // 1. Update preferences in Supabase auth's user_metadata (if applicable/desired)
      // Supabase user_metadata updates are not directly supported for arbitrary fields without admin API
      // For simplicity, we are storing user-specific preferences in a dedicated 'sign-ups' table

      // 2. Update preferences in the 'sign-ups' table
      const { data, error } = await supabase
        .from('sign-ups')
        .update({ preferences: preferences })
        .eq('email', state.user.email);

      if (error) {
        console.error("updateUserPreferences: Error updating preferences in Supabase:", error);
        throw new Error(error.message || "Failed to update preferences");
      }
      console.log("updateUserPreferences: Supabase update successful:", data);

      // 3. Sync preferences to ChromaDB via Flask backend
      const response = await fetch('/api/preferences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${await supabase.auth.getSession().then(s => s.data.session?.access_token)}`
        },
        body: JSON.stringify({ userId: state.user.id, preferences: preferences })
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("updateUserPreferences: Error syncing to backend/ChromaDB:", errorData);
        throw new Error(errorData.message || "Failed to sync preferences to backend");
      }
      console.log("updateUserPreferences: Synced preferences to backend/ChromaDB successfully.");

      // Update local state after successful updates
      setState(prevState => {
        if (prevState.user) {
          return {
            ...prevState,
            user: { ...prevState.user, preferences: preferences }
          };
        }
        return prevState;
      });
      console.log("updateUserPreferences: Local state updated.");

    } catch (error: any) {
      console.error("updateUserPreferences: Error:", error);
      throw error; // Re-throw to be caught by UI components
    }
  };

  return (
    <AuthContext.Provider value={{ ...state, signIn, signUp, signOut, updateUserPreferences }}>
      {children}
    </AuthContext.Provider>
  );
}

>>>>>>> a0fa3e0 (test agent)
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

  const loadUserPreferences = async (userEmail: string): Promise<UserPreferences | undefined> => {
    try {
      const { data, error } = await supabase
        .from('sign_ups')
        .select('preferences')
        .eq('email', userEmail)
        .maybeSingle();

      if (error) {
        return undefined;
      }
      if (!data?.preferences) {
        return undefined;
      }
      const rawPrefs = data.preferences;
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
    } catch {
      return undefined;
    }
  };

  useEffect(() => {
    let mounted = true;

    const initializeAuth = async () => {
      try {
        const { data: { session: initialSession } } = await supabase.auth.getSession();

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
            } catch {
              if (mounted) {
                setUser(initialSession.user);
              }
            }
          } else {
            setUser(null);
          }
        }

        const { data: { subscription } } = supabase.auth.onAuthStateChange(
          async (event, session) => {
            if (!mounted) return;

            setSession(session);

            if (session?.user) {
              try {
                const preferences = await loadUserPreferences(session.user.email!);
                if (mounted) {
                  setUser({
                    ...session.user,
                    preferences
                  });
                }
              } catch {
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

        if (mounted) {
          setIsLoading(false);
        }

        return () => {
          mounted = false;
          subscription.unsubscribe();
        };
      } catch {
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
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        return { error };
      }

      return { error: null };
    } catch (error) {
      return { error };
    }
  };

  const signUp = async (email: string, password: string) => {
    try {
      const redirectUrl = `${window.location.origin}/`;

      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: redirectUrl
        }
      });

      if (error) {
        return { error };
      }

      return { error: null };
    } catch (error) {
      return { error };
    }
  };

  const signOut = async () => {
    try {
      setUser(null);
      setSession(null);

      const keysToRemove = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && (key.startsWith('sb-') || key.includes('supabase') || key.includes('auth'))) {
          keysToRemove.push(key);
        }
      }
      keysToRemove.forEach(key => localStorage.removeItem(key));

      const { error } = await supabase.auth.signOut();

      if (error) {
        // Handle error silently
      }

      window.location.href = '/';

    } catch {
      setUser(null);
      setSession(null);
      localStorage.clear();
      window.location.href = '/';
    }
  };

  // --- FIXED: This now always returns true/false, and always updates user in state after save
  const updatePreferences = async (preferences: UserPreferences) => {
    if (!user?.email) {
      toast({
        title: 'Error',
        description: 'You must be signed in to update preferences.',
        variant: 'destructive',
      });
      return false;
    }

    try {
      const preferencesJson = {
        favoriteCuisines: preferences.favoriteCuisines,
        dietaryRestrictions: preferences.dietaryRestrictions,
        cookingSkillLevel: preferences.cookingSkillLevel,
        allergens: preferences.allergens
      };

      // Upsert (insert if new, update if exists)
      const { error } = await supabase
        .from('sign_ups')
        .upsert(
          {
            email: user.email,
            preferences: preferencesJson,
          },
          { onConflict: 'email' }
        );

      if (error) {
        toast({
          title: 'Error',
          description: `Failed to update preferences: ${error.message}`,
          variant: 'destructive',
        });
        return false;
      } else {
        // Also update in local state!
        setUser(prev => prev ? { ...prev, preferences: preferencesJson } : null);
        toast({
          title: 'Preferences Updated',
          description: 'Your preferences have been saved successfully.',
        });
        return true;
      }
    } catch {
      toast({
        title: 'Error',
        description: 'An unexpected error occurred while saving preferences.',
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
