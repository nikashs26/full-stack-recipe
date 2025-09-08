

import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react';
import { useToast } from '@/hooks/use-toast';
import { apiCall } from '@/utils/apiUtils';
import { getApiUrl } from '../config/api';

interface User {
  user_id: string;
  email: string;
  full_name: string;
  created_at: string;
  is_verified: boolean;
  preferences?: {
    favoriteCuisines: string[];
    favoriteFoods: string[];
    foodsToAvoid: string[];
    dietaryRestrictions: string[];
    healthGoals: string[];
    allergens: string[];
    cookingSkillLevel: 'beginner' | 'intermediate' | 'advanced';
    maxCookingTime?: string;
    includeBreakfast?: boolean;
    includeLunch?: boolean;
    includeDinner?: boolean;
    includeSnacks?: boolean;
    targetCalories?: number;
    targetProtein?: number;
    targetCarbs?: number;
    targetFat?: number;
  };
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

  // Load token from localStorage on app start
  useEffect(() => {
    const loadAuthState = async () => {
      setIsLoading(true);
      const savedToken = localStorage.getItem('auth_token');
      console.log('🔑 AuthContext - Loading token from localStorage:', savedToken ? 'Present' : 'Missing');
      
      if (savedToken) {
        setToken(savedToken);
        try {
          const response = await apiCall('/api/auth/me', {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${savedToken}`,
              'Content-Type': 'application/json',
              'Accept': 'application/json'
            }
          });
          
          if (response.ok) {
            const data = await response.json();
            setUser(data.user);
            
            // Check if token needs refresh (if less than 1 hour remaining)
            try {
              const tokenData = JSON.parse(atob(savedToken.split('.')[1]));
              const expiresIn = tokenData.exp * 1000 - Date.now(); // Convert to milliseconds
              
              if (expiresIn < 60 * 60 * 1000) { // Less than 1 hour remaining
                // Refresh token using the current token
                try {
                  const refreshResponse = await apiCall('/api/auth/refresh', {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                      'Accept': 'application/json'
                    }
                  });

                  if (refreshResponse.ok) {
                    const refreshData = await refreshResponse.json();
                    if (refreshData.token) {
                      localStorage.setItem('auth_token', refreshData.token);
                      setToken(refreshData.token);
                      console.log('🔑 Token refreshed successfully');
                    }
                  }
                } catch (error) {
                  console.error('Error refreshing token:', error);
                }
              }
            } catch (error) {
              console.error('Error parsing token:', error);
            }
          } else {
            // If /me fails, clear auth state
            setUser(null);
            setToken(null);
            localStorage.removeItem('auth_token');
            localStorage.removeItem('refresh_token');
          }
        } catch (error) {
          console.error('Error verifying token:', error);
          setUser(null);
          setToken(null);
          localStorage.removeItem('auth_token');
          localStorage.removeItem('refresh_token');
        }
      }
      
      setIsLoading(false);
    };

    loadAuthState();
  }, []);

  // Set up periodic token refresh
  useEffect(() => {
    if (!token) return;

    const checkTokenExpiry = async () => {
      try {
        const tokenData = JSON.parse(atob(token.split('.')[1]));
        const expiresIn = tokenData.exp * 1000 - Date.now(); // Convert to milliseconds
        
        if (expiresIn < 24 * 60 * 60 * 1000) { // Less than 1 day remaining
          console.log('🔄 Periodic token refresh - token expires in less than 1 day');
          const response = await apiCall('/api/auth/refresh', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            }
          });
          
          if (response.ok) {
            const data = await response.json();
            localStorage.setItem('auth_token', data.token);
            setToken(data.token);
            console.log('🔑 Periodic token refresh successful');
          }
        }
      } catch (error) {
        console.error('Periodic token refresh failed:', error);
      }
    };

    // Check token expiry every hour
    const interval = setInterval(checkTokenExpiry, 60 * 60 * 1000);
    return () => clearInterval(interval);
  }, [token]);

  const verifyTokenAndLoadUser = async (tokenToCheck: string): Promise<boolean> => {
    try {
              const response = await apiCall('/api/auth/me', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${tokenToCheck}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
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
              const response = await apiCall('/api/auth/register', {
        method: 'POST',
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
              const response = await apiCall('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        const { user: userData, token: userToken } = data;
        
        // Save token to localStorage
        console.log('🔑 AuthContext - Setting token in localStorage:', userToken ? 'Present' : 'Missing');
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
        await apiCall('/api/auth/logout', { method: 'POST' });
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
              const response = await apiCall('/api/auth/verify-email', {
        method: 'POST',
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
              const response = await apiCall('/api/auth/resend-verification', {
        method: 'POST',
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
