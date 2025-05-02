
import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, AuthState } from '../types/auth';

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null
};

interface AuthContextType extends AuthState {
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => void;
  updateUserPreferences: (preferences: any) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>(initialState);

  useEffect(() => {
    // Check if user is already logged in via localStorage
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser);
        setState({
          user,
          isAuthenticated: true,
          isLoading: false,
          error: null
        });
      } catch (error) {
        localStorage.removeItem('user');
        setState({ ...initialState, isLoading: false });
      }
    } else {
      setState({ ...initialState, isLoading: false });
    }
  }, []);

  const signIn = async (email: string, password: string) => {
    try {
      // This is a mock authentication - in real app, you'd use Supabase
      // For demo, we'll create a fake user
      const mockUser: User = {
        id: 'user-' + Math.random().toString(36).substring(2, 9),
        email,
        displayName: email.split('@')[0],
        createdAt: new Date().toISOString()
      };

      localStorage.setItem('user', JSON.stringify(mockUser));
      
      setState({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        error: null
      });
      
    } catch (error) {
      setState({
        ...state,
        error: 'Failed to sign in',
        isLoading: false
      });
    }
  };

  const signUp = async (email: string, password: string) => {
    try {
      // Mock sign-up logic
      const mockUser: User = {
        id: 'user-' + Math.random().toString(36).substring(2, 9),
        email,
        displayName: email.split('@')[0],
        createdAt: new Date().toISOString()
      };

      localStorage.setItem('user', JSON.stringify(mockUser));
      
      setState({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        error: null
      });
    } catch (error) {
      setState({
        ...state,
        error: 'Failed to sign up',
        isLoading: false
      });
    }
  };

  const signOut = () => {
    localStorage.removeItem('user');
    setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null
    });
  };

  const updateUserPreferences = (preferences: any) => {
    if (state.user) {
      const updatedUser = {
        ...state.user,
        preferences
      };
      
      localStorage.setItem('user', JSON.stringify(updatedUser));
      
      setState({
        ...state,
        user: updatedUser
      });
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
