
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
        
        if (data?.session?.user) {
          console.log("Session found:", data.session);
          const user = data.session.user;
          
          const enhancedUser: User = {
            id: user.id,
            email: user.email || '',
            displayName: user.email?.split('@')[0] || '',
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
      (event, session) => {
        console.log("Auth state changed:", event, session);
        
        if (event === 'SIGNED_IN' && session?.user) {
          const user = session.user;
          console.log("User signed in:", user);
          
          const enhancedUser: User = {
            id: user.id,
            email: user.email || '',
            displayName: user.email?.split('@')[0] || '',
            createdAt: user.created_at || new Date().toISOString()
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
        } else if (event === 'TOKEN_REFRESHED') {
          console.log("Token refreshed");
          if (session?.user) {
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
          }
        }
      }
    );
    
    return () => {
      if (authListener?.subscription) {
        authListener.subscription.unsubscribe();
      }
    };
  }, []);

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
      
      console.log('Sign in successful:', data);
      // Auth state listener will handle the state update
      
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
      setIsVerificationRequired(false);
      console.log('Attempting to sign up user:', email);
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const { data, error } = await supabase.auth.signUp({
        email,
        password
      });
      
      if (error) {
        console.error('Sign up error:', error);
        setState(prev => ({ ...prev, isLoading: false, error: error.message }));
        return { error: error.message };
      }
      
      console.log('Sign up successful:', data);
      
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
      
      if (data.session) {
        console.log('User automatically signed in after signup');
        // Auth state listener will handle the state update
        setState(prev => ({ ...prev, isLoading: false }));
        return {};
      }
      
      setState(prev => ({ ...prev, isLoading: false }));
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
