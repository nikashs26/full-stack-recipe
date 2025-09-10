
import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { User, Settings, ChefHat, ShoppingCart, LogOut, LogIn, UserPlus, Star, Folder } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const UserMenu: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const { user, isAuthenticated, signOut, isLoading } = useAuth();

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSignOut = async () => {
    setIsOpen(false);
    await signOut();
  };

  // If not authenticated, show sign in/sign up buttons
  if (!isLoading && !isAuthenticated) {
    return (
      <div className="flex items-center space-x-2">
        <Link to="/signin">
          <Button variant="ghost" size="sm" className="flex items-center gap-1">
            <LogIn className="h-4 w-4" />
            Sign In
          </Button>
        </Link>
        <Link to="/signup">
          <Button size="sm" className="flex items-center gap-1">
            <UserPlus className="h-4 w-4" />
            Sign Up
          </Button>
        </Link>
      </div>
    );
  }

  // If loading, show simple placeholder
  if (isLoading) {
    return (
      <Button variant="ghost" className="relative h-8 w-8 rounded-full animate-pulse">
        <User className="h-4 w-4" />
      </Button>
    );
  }

  // If authenticated, show user menu
  return (
    <div className="relative" ref={menuRef}>
      <Button 
        variant="ghost" 
        className="relative h-8 w-8 rounded-full"
        onClick={() => setIsOpen(!isOpen)}
      >
        <User className="h-4 w-4" />
      </Button>
      
      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          <div className="py-1">
            <div className="px-4 py-2 text-sm font-medium text-gray-900 border-b border-gray-100">
              {user?.full_name || user?.email || 'User'}
            </div>
            <Link
              to="/shopping-list"
              className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              onClick={() => setIsOpen(false)}
            >
              <ShoppingCart className="mr-3 h-4 w-4" />
              Shopping List
            </Link>
            <Link
              to="/folders"
              className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              onClick={() => setIsOpen(false)}
            >
              <Folder className="mr-3 h-4 w-4" />
              My Folders
            </Link>
            <Link
              to="/preferences"
              className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              onClick={() => setIsOpen(false)}
            >
              <Settings className="mr-3 h-4 w-4" />
              Preferences
            </Link>
            <Link
              to="/my-reviews"
              className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              onClick={() => setIsOpen(false)}
            >
              <Star className="mr-3 h-4 w-4" />
              My Reviews
            </Link>
            <button
              onClick={handleSignOut}
              className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 border-t border-gray-100 mt-1"
            >
              <LogOut className="mr-3 h-4 w-4" />
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserMenu;
