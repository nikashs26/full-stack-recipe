
import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, AuthState, UserProfile } from '../types/auth';
import { supabase } from '../lib/supabase';

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null
};

interface AuthContextType extends AuthState {
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  updateUserPreferences: (preferences: any) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>(initialState);

  // Check user session on initial load
  useEffect(() => {
    const checkSession = async () => {
      try {
        const { data, error } = await supabase.auth.getSession();
        
        if (error) {
          console.error("Error fetching session:", error);
          setState({ ...initialState, isLoading: false });
          return;
        }
        
        if (data?.session) {
          const { user } = data.session;
          
          // Get user profile data if available
          const { data: profileData } = await supabase
            .from('sign-ups')
            .select('*')
            .eq('email', user.email)
            .single();
            
          console.log("Found sign-up record:", profileData);
            
          const enhancedUser: User = {
            id: user.id,
            email: user.email || '',
            displayName: user.email?.split('@')[0] || '',
            preferences: undefined,
            createdAt: user.created_at || new Date().toISOString()
          };
          
          setState({
            user: enhancedUser,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
        } else {
          setState({ ...initialState, isLoading: false });
        }
      } catch (error) {
        console.error("Unexpected error during session check:", error);
        setState({ ...initialState, isLoading: false });
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
            .from('sign-ups')
            .select('*')
            .eq('email', user.email)
            .single();
            
          if (profileError) {
            console.error("Error fetching sign-up record:", profileError);
          } else {
            console.log("Found sign-up record:", profileData);
          }
            
          const enhancedUser: User = {
            id: user.id,
            email: user.email || '',
            displayName: user.email?.split('@')[0] || '',
            preferences: undefined,
            createdAt: user.created_at || new Date().toISOString()
          };
          
          setState({
            user: enhancedUser,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
        } else if (event === 'SIGNED_OUT') {
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

  const signIn = async (email: string, password: string) => {
    try {
      // Log the sign-in attempt to help with debugging
      console.log('Attempting to sign in user:', email);
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });
      
      if (error) {
        console.error('Supabase Auth Error:', error);
        throw new Error(error.message);
      }
      
      console.log('Sign in successful, auth data:', data);
      
      // Check if the user exists in our sign-ups table
      const { data: signUpData, error: signUpError } = await supabase
        .from('sign-ups')
        .select('*')
        .eq('email', email)
        .single();
        
      if (signUpError) {
        console.log('No sign-up record found, will be created if needed');
      } else {
        console.log('Found existing sign-up record:', signUpData);
      }
      
      if (data.user) {
        // User data is handled by the auth state change listener
        return;
      }
    } catch (error: any) {
      console.error('Sign in error:', error);
      setState({
        ...state,
        error: error.message || 'Failed to sign in',
        isLoading: false
      });
      throw error;
    }
  };

  const signUp = async (email: string, password: string) => {
    try {
      // Log the sign-up attempt to help with debugging
      console.log('Attempting to sign up user:', email);
      
      const { data, error } = await supabase.auth.signUp({
        email,
        password
      });
      
      if (error) {
        console.error('Supabase Auth Error:', error);
        throw new Error(error.message);
      }
      
      console.log('Sign up successful, auth data:', data);
      
      if (data.user) {
        // Create a record in the sign-ups table
        const signUpRecord = {
          email: email,
          password: "********" // We don't actually store the real password here
        };
        
        console.log('Creating sign-up record:', signUpRecord);
        
        const { error: signUpError, data: signUpData } = await supabase
          .from('sign-ups')
          .insert([signUpRecord]) // Make sure to wrap in array brackets
          .select();
          
        if (signUpError) {
          console.error("Error creating sign-up record:", signUpError);
          // Don't throw here to allow the auth process to complete even if table insert fails
          console.log("Continuing despite table insert error");
        } else {
          console.log('Sign-up record created successfully:', signUpData);
        }

        // After sign-up, return without waiting for auth state change
        return;
      } else {
        console.error("User object not found in sign-up response");
        throw new Error("Failed to create user account");
      }
    } catch (error: any) {
      console.error('Sign up error:', error);
      setState({
        ...state,
        error: error.message || 'Failed to sign up',
        isLoading: false
      });
      throw error;
    }
  };

  const signOut = async () => {
    try {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
      
      // State update handled by auth listener
    } catch (error: any) {
      console.error("Error signing out:", error.message);
    }
  };

  const updateUserPreferences = async (preferences: any) => {
    if (!state.user?.email) return;
    
    try {
      const { error } = await supabase
        .from('sign-ups')
        .update({ 
          preferences: preferences
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
