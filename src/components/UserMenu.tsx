
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
  const { user, signOut } = useAuth(); // isAuthenticated and isLoading are now always true/false based on test mode
  const { toast } = useToast();
  const navigate = useNavigate();

  // In test mode, we always show the user menu

  const handleSignOut = async () => {
    try {
      console.log("Attempting to sign out (Test Mode)...");
      await signOut();
      
      // In test mode, we don't need a full page refresh for Supabase cleanup.
      // Just navigate to home.
      navigate('/');
      
      toast({
        title: "Signed out successfully (Test Mode)",
      });
    } catch (error) {
      console.error("Error signing out (Test Mode):", error);
      toast({
        title: "Signed out (Test Mode)",
        description: "You have been signed out",
      });
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-8 w-8 rounded-full">
          <User className="h-4 w-4" /> {/* Always show user icon in test mode */}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>
          {user?.email || "Test User"} {/* Display test user email or a generic name */}
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
