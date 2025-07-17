

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

  const verifyTokenAndLoadUser = async (tokenToCheck: string): Promise<boolean> => {
    try {
      console.log('🔐 Verifying token:', tokenToCheck ? 'token present' : 'no token');
      
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tokenToCheck}`
        }
      });
      
      console.log('🔐 Auth verification response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('🔐 Auth verification successful:', data.user?.email);
        setUser(data.user);
        return true;
      } else {
        // Log the specific error for debugging
        const errorText = await response.text();
        console.log('🔐 Auth verification failed:', response.status, errorText);
        
        // Token is invalid - clear it
        localStorage.removeItem('auth_token');
        setToken(null);
        setUser(null);
        
        // Only show error toast for 401 (other errors might be expected during startup)
        if (response.status === 401) {
          console.log('🔐 Session expired - user needs to log in again');
        }
        
        return false;
      }
    } catch (error) {
      console.error('🔐 Auth check failed with error:', error);
      
      // On network error, don't clear token immediately - might be temporary
      // Only clear if it's a parsing error or similar
      if (error instanceof TypeError || error instanceof SyntaxError) {
        localStorage.removeItem('auth_token');
        setToken(null);
        setUser(null);
      }
      
      return false;
    }
  };

  // Load token from localStorage on app start
  useEffect(() => {
    const loadAuthState = async () => {
      const savedToken = localStorage.getItem('auth_token');
      console.log('🔐 Loading auth state - token found:', !!savedToken);
      
      if (savedToken) {
        setToken(savedToken);
        
        // Verify token and load user with retry logic
        let attempts = 0;
        const maxAttempts = 3;
        let success = false;
        
        while (attempts < maxAttempts && !success) {
          attempts++;
          console.log(`🔐 Verification attempt ${attempts}/${maxAttempts}`);
          
          try {
            success = await verifyTokenAndLoadUser(savedToken);
            if (success) {
              console.log('🔐 Token verification successful');
              break;
            }
          } catch (error) {
            console.log(`🔐 Verification attempt ${attempts} failed:`, error);
          }
          
          // Wait before retry (except on last attempt)
          if (attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
        }
        
        if (!success) {
          console.log('🔐 All verification attempts failed - clearing token');
          localStorage.removeItem('auth_token');
          setToken(null);
          setUser(null);
        }
      } else {
        console.log('🔐 No saved token found');
      }
      
      setIsLoading(false);
    };

    loadAuthState();
  }, []);

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
    const currentToken = token || localStorage.getItem('auth_token');
    
    if (!currentToken) {
      setUser(null);
      setToken(null);
      return false;
    }

    try {
      const isValid = await verifyTokenAndLoadUser(currentToken);
      
      // If verification failed but we had a token, it might be expired
      if (!isValid && currentToken) {
        console.log('🔐 Token validation failed - clearing auth state');
        localStorage.removeItem('auth_token');
        setToken(null);
        setUser(null);
      }
      
      return isValid;
    } catch (error) {
      console.error('🔐 Auth check failed:', error);
      return false;
    }
  }, [token]);

  // Add automatic auth check on visibility change (when user comes back to tab)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && user && token) {
        checkAuth();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [user, token, checkAuth]);

  // Add periodic auth check (every 5 minutes)
  useEffect(() => {
    if (!user || !token) return;

    const interval = setInterval(() => {
      checkAuth();
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(interval);
  }, [user, token, checkAuth]);

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
