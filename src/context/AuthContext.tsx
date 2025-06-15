
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
  updatePreferences: (preferences: UserPreferences) => Promise<boolean>;
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
