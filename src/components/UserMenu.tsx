
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
import { LogIn, LogOut, User } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const UserMenu: React.FC = () => {
  const { user, isAuthenticated, isLoading: authLoading, signOut } = useAuth();
  const [showLoading, setShowLoading] = useState(false);
  const { toast } = useToast();

  // Only show loading for a very short time and only if we're actually loading
  useEffect(() => {
    if (authLoading && !isAuthenticated) {
      setShowLoading(true);
      
      // Don't show loading for more than 1 second
      const timer = setTimeout(() => {
        console.log('UserMenu loading timeout reached, hiding loading state');
        setShowLoading(false);
      }, 1000);
      
      return () => clearTimeout(timer);
    } else {
      setShowLoading(false);
    }
  }, [authLoading, isAuthenticated]);

  // If we're clearly not authenticated and not loading, show sign in buttons
  if (!isAuthenticated && !showLoading) {
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

  // Show brief loading state only when actually loading
  if (showLoading) {
    return (
      <div className="flex items-center">
        <Button variant="ghost" size="sm" disabled>
          <span className="h-4 w-4 mr-2 animate-spin">⌛</span>
          Loading...
        </Button>
      </div>
    );
  }

  const handleSignOut = async () => {
    try {
      console.log("Attempting to sign out...");
      await signOut();
      toast({
        title: "Signed out successfully",
      });
    } catch (error) {
      console.error("Error signing out:", error);
      toast({
        title: "Error signing out",
        description: "Please try again or refresh the page",
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
          {user?.email}
        </DropdownMenuLabel>
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
