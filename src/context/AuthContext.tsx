
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
    let mounted = true;

    const initializeAuth = async () => {
      try {
        console.log("Initializing auth...");
        
        // Set up auth state change listener first
        const { data: authListener } = supabase.auth.onAuthStateChange(
          async (event, session) => {
            console.log("Auth state changed:", event, session?.user?.id);
            
            if (!mounted) return;
            
            if (event === 'SIGNED_IN' && session?.user) {
              console.log("User signed in successfully");
              const enhancedUser: User = {
                id: session.user.id,
                email: session.user.email || '',
                displayName: session.user.email?.split('@')[0] || '',
                createdAt: session.user.created_at || new Date().toISOString()
              };
              
              setState({
                user: enhancedUser,
                isAuthenticated: true,
                isLoading: false,
                error: null
              });
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
              
            } else if (event === 'TOKEN_REFRESHED' && session?.user) {
              console.log("Token refreshed");
              const enhancedUser: User = {
                id: session.user.id,
                email: session.user.email || '',
                displayName: session.user.email?.split('@')[0] || '',
                createdAt: session.user.created_at || new Date().toISOString()
              };
              
              setState(prev => ({
                ...prev,
                user: enhancedUser,
                isAuthenticated: true,
                error: null
              }));
            } else if (!session) {
              console.log("No session available");
              setState(prev => ({
                ...prev,
                user: null,
                isAuthenticated: false,
                isLoading: false
              }));
            }
          }
        );

        // Then check for existing session
        const { data: { session }, error } = await supabase.auth.getSession();
        
        if (error) {
          console.error("Error getting session:", error);
          if (mounted) {
            setState(prev => ({ ...prev, isLoading: false, error: error.message }));
          }
          return;
        }
        
        if (session?.user) {
          console.log("Found existing session");
          const enhancedUser: User = {
            id: session.user.id,
            email: session.user.email || '',
            displayName: session.user.email?.split('@')[0] || '',
            createdAt: session.user.created_at || new Date().toISOString()
          };
          
          if (mounted) {
            setState({
              user: enhancedUser,
              isAuthenticated: true,
              isLoading: false,
              error: null
            });
          }
        } else {
          console.log("No existing session");
          if (mounted) {
            setState(prev => ({ ...prev, isLoading: false }));
          }
        }

        return () => {
          if (authListener?.subscription) {
            authListener.subscription.unsubscribe();
          }
        };
        
      } catch (error) {
        console.error("Auth initialization error:", error);
        if (mounted) {
          setState(prev => ({ ...prev, isLoading: false, error: "Authentication initialization failed" }));
        }
      }
    };

    const cleanup = initializeAuth();
    
    return () => {
      mounted = false;
      cleanup?.then(cleanupFn => cleanupFn?.());
    };
  }, []);

  const signIn = async (email: string, password: string) => {
    try {
      console.log('Attempting to sign in user:', email);
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      setIsVerificationRequired(false);
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });
      
      if (error) {
        console.error('Sign in error:', error.message);
        
        if (error.message.includes('Email not confirmed') || error.message.includes('email_not_confirmed')) {
          setIsVerificationRequired(true);
          setState(prev => ({ 
            ...prev, 
            isLoading: false, 
            error: "Please verify your email address before signing in. Check your inbox for a verification link." 
          }));
          return;
        }
        
        setState(prev => ({ ...prev, isLoading: false, error: error.message }));
        throw new Error(error.message);
      }
      
      if (data.session && data.user) {
        console.log('Sign in successful, session created');
        // Auth state listener will handle the rest
      } else {
        console.log('Sign in returned no session');
        setState(prev => ({ ...prev, isLoading: false, error: "Sign in failed - no session created" }));
      }
      
    } catch (error: any) {
      console.error('Sign in catch block:', error);
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
      setIsVerificationRequired(false);
      
      const { data, error } = await supabase.auth.signUp({
        email,
        password
      });
      
      if (error) {
        console.error('Sign up error:', error.message);
        setState(prev => ({ ...prev, isLoading: false, error: error.message }));
        return { error: error.message };
      }
      
      console.log('Sign up response:', data);
      
      // Check if email confirmation is required
      if (data.user && !data.session) {
        console.log('Email verification required for signup');
        setIsVerificationRequired(true);
        setState(prev => ({ 
          ...prev, 
          isLoading: false,
          error: null
        }));
        return { error: "Please check your email to verify your account before signing in." };
      }
      
      // If we have a session, the user is automatically signed in
      if (data.session && data.user) {
        console.log('User automatically signed in after signup');
        setState(prev => ({ ...prev, isLoading: false }));
        // Auth state listener will handle the user state update
        return {};
      }
      
      setState(prev => ({ ...prev, isLoading: false }));
      return {};
      
    } catch (error: any) {
      console.error('Sign up catch block:', error);
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
      console.log("Sign out successful");
      // Auth state listener will handle the state update
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
