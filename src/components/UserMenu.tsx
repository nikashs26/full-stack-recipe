
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from '@/components/ui/button';
import { LogIn, LogOut, User, Settings, Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const UserMenu: React.FC = () => {
  const { user, isAuthenticated, isLoading: authLoading, signOut, error } = useAuth();
  const [isLoading, setIsLoading] = useState(authLoading);
  const { toast } = useToast();

  // Safety timeout: if auth loading takes too long, we'll stop showing the loading state
  useEffect(() => {
    setIsLoading(authLoading);
    
    // Local loading state timeout (5 seconds max)
    if (authLoading) {
      const timer = setTimeout(() => {
        console.log('Auth loading timeout reached, forcing UI update');
        setIsLoading(false);
        
        // Show a toast if we had to force the loading state to end
        toast({
          title: "Authentication status unclear",
          description: "Please refresh the page if you're experiencing issues",
          variant: "destructive"
        });
      }, 5000);
      
      return () => clearTimeout(timer);
    }
  }, [authLoading, toast]);

  // If there's an auth error, show it
  useEffect(() => {
    if (error) {
      console.error("Auth error:", error);
      toast({
        title: "Authentication Error",
        description: error,
        variant: "destructive"
      });
    }
  }, [error, toast]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex items-center">
        <Button variant="ghost" size="sm" disabled>
          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          Loading...
        </Button>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex items-center gap-2">
        <Link to="/signin">
          <Button variant="outline" size="sm">
            <LogIn className="h-4 w-4 mr-2" />
            Sign In
          </Button>
        </Link>
        <Link to="/signup">
          <Button size="sm">
            Sign Up
          </Button>
        </Link>
      </div>
    );
  }

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error("Error signing out:", error);
      toast({
        title: "Error signing out",
        description: "Please try again",
        variant: "destructive"
      });
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-8 w-8 rounded-full">
          <User className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>
          {user?.displayName || user?.email}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link to="/preferences" className="cursor-pointer flex w-full items-center">
            <Settings className="mr-2 h-4 w-4" />
            <span>Preferences</span>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem 
          onClick={handleSignOut}
          className="cursor-pointer text-red-600 focus:text-red-600"
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>Sign out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default UserMenu;
