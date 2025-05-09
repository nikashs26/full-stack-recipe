
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
            .from('user_profiles')
            .select('*')
            .eq('id', user.id)
            .single();
            
          const enhancedUser: User = {
            id: user.id,
            email: user.email || '',
            displayName: profileData?.display_name || user.email?.split('@')[0] || '',
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
        if (event === 'SIGNED_IN' && session?.user) {
          const user = session.user;
          
          // Get user profile data if available
          const { data: profileData } = await supabase
            .from('user_profiles')
            .select('*')
            .eq('id', user.id)
            .single();
            
          const enhancedUser: User = {
            id: user.id,
            email: user.email || '',
            displayName: profileData?.display_name || user.email?.split('@')[0] || '',
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
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });
      
      if (error) throw new Error(error.message);
      
      // User data is handled by the auth state change listener
      return;
    } catch (error: any) {
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
      const { data, error } = await supabase.auth.signUp({
        email,
        password
      });
      
      if (error) throw new Error(error.message);
      
      if (data.user) {
        // Create a user profile record
        const { error: profileError } = await supabase
          .from('user_profiles')
          .insert({
            id: data.user.id,
            display_name: email.split('@')[0],
            email: email,
            created_at: new Date().toISOString()
          });
          
        if (profileError) {
          console.error("Error creating user profile:", profileError);
        }
      }
      
      // Rest is handled by auth state change listener
      return;
    } catch (error: any) {
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
    if (!state.user?.id) return;
    
    try {
      const { error } = await supabase
        .from('user_profiles')
        .update({ 
          preferences: preferences,
          updated_at: new Date().toISOString()
        })
        .eq('id', state.user.id);
        
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
