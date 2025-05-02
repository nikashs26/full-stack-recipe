
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

  // Store registered users
  const getRegisteredUsers = () => {
    const users = localStorage.getItem('registeredUsers');
    return users ? JSON.parse(users) : [];
  };

  const saveRegisteredUser = (email: string, password: string) => {
    const users = getRegisteredUsers();
    users.push({ email, password });
    localStorage.setItem('registeredUsers', JSON.stringify(users));
  };

  const signIn = async (email: string, password: string) => {
    try {
      // Check if user exists
      const users = getRegisteredUsers();
      const user = users.find((u: any) => u.email === email && u.password === password);
      
      if (!user) {
        throw new Error('Invalid email or password');
      }
      
      // User exists, create session
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
      throw error; // Re-throw to handle in component
    }
  };

  const signUp = async (email: string, password: string) => {
    try {
      // Check if user already exists
      const users = getRegisteredUsers();
      if (users.some((u: any) => u.email === email)) {
        throw new Error('Email already in use');
      }
      
      // Register new user
      saveRegisteredUser(email, password);
      
      // Create session
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
      throw error; // Re-throw to handle in component
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
