
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
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
  const { user, isAuthenticated, isLoading, signOut } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  // Show loading only briefly during initial auth check
  if (isLoading) {
    return (
      <div className="flex items-center">
        <Button variant="ghost" size="sm" disabled>
          <span className="h-4 w-4 mr-2 animate-spin">⌛</span>
          Loading...
        </Button>
      </div>
    );
  }

  // If not authenticated, show sign in buttons
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
      console.log("Attempting to sign out...");
      await signOut();
      
      // Force a page refresh and navigate to home
      setTimeout(() => {
        window.location.href = '/';
      }, 100);
      
      toast({
        title: "Signed out successfully",
      });
    } catch (error) {
      console.error("Error signing out:", error);
      
      // Even if there's an error, try to clear local state and redirect
      localStorage.clear();
      setTimeout(() => {
        window.location.href = '/';
      }, 100);
      
      toast({
        title: "Signed out",
        description: "You have been signed out",
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
        <DropdownMenuItem asChild>
          <Link to="/preferences" className="cursor-pointer">
            <User className="mr-2 h-4 w-4" />
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
