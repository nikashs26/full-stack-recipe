
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
            .from('sign-ups')
            .select('*')
            .eq('email', user.email)
            .single();
            
          if (profileError) {
            console.log("No sign-up record found, user may have been created through direct auth");
          } else {
            console.log("Found sign-up record:", profileData);
          }
            
          const enhancedUser: User = {
            id: user.id,
            email: user.email || '',
            displayName: user.email?.split('@')[0] || '',
            preferences: profileData?.preferences || undefined,
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
            .from('sign-ups')
            .select('*')
            .eq('email', user.email)
            .single();
            
          if (profileError) {
            console.log("No sign-up record found:", profileError.message);
          } else {
            console.log("Found sign-up record:", profileData);
          }
            
          const enhancedUser: User = {
            id: user.id,
            email: user.email || '',
            displayName: user.email?.split('@')[0] || '',
            preferences: profileData?.preferences || undefined,
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

  const signUp = async (email: string, password: string) => {
    try {
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
        throw new Error(error.message);
      }
      
      console.log('Sign up successful, auth data:', data);
      
      if (data.user) {
        // We don't need the password in the sign-ups table
        // Just create a simple record with email to track the user
        try {
          console.log('Creating sign-up record for email:', email);
          
          // First check if the sign-ups table exists
          const { error: tableCheckError } = await supabase
            .from('sign-ups')
            .select('email')
            .limit(1);
            
          if (tableCheckError) {
            console.error('Error checking sign-ups table:', tableCheckError);
            
            if (tableCheckError.message.includes('does not exist')) {
              console.log('The sign-ups table does not exist in Supabase, proceeding without creating record');
              
              // Create a user object anyway and proceed
              const enhancedUser: User = {
                id: data.user.id,
                email: data.user.email || '',
                displayName: data.user.email?.split('@')[0] || '',
                createdAt: data.user.created_at || new Date().toISOString()
              };
              
              setState({
                user: enhancedUser,
                isAuthenticated: true,
                isLoading: false,
                error: null
              });
              return;
            }
          }
          
          // If we get here, the table exists, so insert the record
          const signUpRecord = {
            email: email
          };
          
          const { error: signUpError } = await supabase
            .from('sign-ups')
            .insert([signUpRecord]);
            
          if (signUpError) {
            console.error("Error creating sign-up record:", signUpError);
            // Don't throw here, just log it but continue with auth
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
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
        } catch (profileError) {
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
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
        }
      } else {
        console.error("User object not found in sign-up response");
        setState(prev => ({ 
          ...prev, 
          isLoading: false,
          error: "Failed to create user account" 
        }));
        throw new Error("Failed to create user account");
      }
    } catch (error: any) {
      console.error('Sign up error:', error);
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to sign up',
        isLoading: false
      }));
      throw error;
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
