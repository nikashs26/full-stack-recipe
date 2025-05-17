
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
  
  return <HomePage />;
};

export default Index;
