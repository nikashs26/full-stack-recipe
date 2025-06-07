
import React, { useEffect } from 'react';
import HomePage from './HomePage';
import { useAuth } from '../context/AuthContext';
import { useToast } from '@/hooks/use-toast';

const Index = () => {
  const { isAuthenticated, isLoading, error } = useAuth();
  const { toast } = useToast();
  
  // Display any auth errors
  useEffect(() => {
    if (error) {
      toast({
        title: "Authentication Error",
        description: error,
        variant: "destructive"
      });
    }
  }, [error, toast]);
  
  // Add a safety check for lengthy loading states
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    
    if (isLoading) {
      timer = setTimeout(() => {
        console.log('Auth loading safety timeout triggered');
        // We don't modify the state here as that would require changing AuthContext
        // Instead, we notify the user
        toast({
          title: "Still checking authentication",
          description: "This is taking longer than expected. You may need to refresh the page.",
        });
      }, 3000); // 3 seconds is reasonable for auth check
    }
    
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [isLoading, toast]);
  
  return <HomePage />;
};

export default Index;
