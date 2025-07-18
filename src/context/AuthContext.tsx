

import React, { createContext, useContext, useEffect, useState, useMemo, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';

interface User {
  user_id: string;
  email: string;
  full_name: string;
  created_at: string;
  is_verified: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<{ success: boolean; error?: any }>;
  signUp: (email: string, password: string, fullName?: string) => Promise<{ success: boolean; error?: any; verificationUrl?: string }>;
  signOut: () => Promise<void>;
  verifyEmail: (token: string) => Promise<{ success: boolean; error?: any }>;
  resendVerification: (email: string) => Promise<{ success: boolean; error?: any }>;
  checkAuth: () => Promise<boolean>;
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
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  const API_BASE_URL = 'http://localhost:5003/api';

  // Helper function to make authenticated API calls
  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return fetch(url, {
      ...options,
      headers,
    });
  };

  // Load token from localStorage on app start
  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token');
    if (savedToken) {
      setToken(savedToken);
      // Verify token and load user - pass the token directly
      verifyTokenAndLoadUser(savedToken).finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const verifyTokenAndLoadUser = async (tokenToCheck: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tokenToCheck}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
        return true;
      } else {
        // Token is invalid
        localStorage.removeItem('auth_token');
        setToken(null);
        setUser(null);
        return false;
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('auth_token');
      setToken(null);
      setUser(null);
      return false;
    }
  };

  const signUp = useCallback(async (email: string, password: string, fullName?: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName || '',
        }),
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: "Registration successful!",
          description: "Please check your email to verify your account.",
        });
        return { 
          success: true, 
          verificationUrl: data.verification_url  // For development
        };
      } else {
        return { success: false, error: { message: data.error } };
      }
    } catch (error) {
      console.error('Sign up error:', error);
      return { success: false, error: { message: 'Network error occurred' } };
    }
  }, [toast]);

  const signIn = useCallback(async (email: string, password: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        const { user: userData, token: userToken } = data;
        
        // Save token to localStorage
        localStorage.setItem('auth_token', userToken);
        setToken(userToken);
        setUser(userData);

        toast({
          title: "Welcome back!",
          description: `Good to see you again, ${userData.full_name || userData.email}!`,
        });

        return { success: true };
      } else {
        return { success: false, error: { message: data.error } };
      }
    } catch (error) {
      console.error('Sign in error:', error);
      return { success: false, error: { message: 'Network error occurred' } };
    }
  }, [toast]);

  const signOut = useCallback(async () => {
    try {
      // Call logout endpoint if needed
      if (token) {
        await apiCall('/auth/logout', { method: 'POST' });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local state regardless of API call success
      localStorage.removeItem('auth_token');
      setToken(null);
      setUser(null);
      
      toast({
        title: "Signed out",
        description: "You have been signed out successfully.",
      });
    }
  }, [token, toast]);

  const verifyEmail = useCallback(async (verificationToken: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/verify-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: verificationToken }),
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: "Email verified!",
          description: "Your account has been verified. You can now sign in.",
        });
        return { success: true };
      } else {
        return { success: false, error: { message: data.error } };
      }
    } catch (error) {
      console.error('Email verification error:', error);
      return { success: false, error: { message: 'Network error occurred' } };
    }
  }, [toast]);

  const resendVerification = useCallback(async (email: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/resend-verification`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: "Verification email sent",
          description: "Please check your email for the verification link.",
        });
        return { success: true };
      } else {
        return { success: false, error: { message: data.error } };
      }
    } catch (error) {
      console.error('Resend verification error:', error);
      return { success: false, error: { message: 'Network error occurred' } };
    }
  }, [toast]);

  const checkAuth = useCallback(async (): Promise<boolean> => {
    if (!token) {
      setUser(null);
      return false;
    }

    return verifyTokenAndLoadUser(token);
  }, [token]);

  const value = useMemo(() => ({
    user,
    token,
    isAuthenticated: !!user && !!token,
    isLoading,
    signIn,
    signUp,
    signOut,
    verifyEmail,
    resendVerification,
    checkAuth,
  }), [user, token, isLoading, signIn, signUp, signOut, verifyEmail, resendVerification, checkAuth]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
