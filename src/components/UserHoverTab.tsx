import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { User, Settings, ChefHat, ShoppingCart, LogOut, LogIn, UserPlus, Star, Folder, Heart, Clock, BookOpen, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const UserHoverTab: React.FC = () => {
  const [isHovered, setIsHovered] = useState(false);
  const [isClicked, setIsClicked] = useState(false);
  const { user, isAuthenticated, signOut, isLoading } = useAuth();
  const sidebarRef = useRef<HTMLDivElement>(null);

  const handleSignOut = async () => {
    await signOut();
  };

  // Handle ESC key press
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsHovered(false);
        setIsClicked(false);
      }
    };

    if (isHovered || isClicked) {
      document.addEventListener('keydown', handleEscKey);
    }

    return () => {
      document.removeEventListener('keydown', handleEscKey);
    };
  }, [isHovered, isClicked]);

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (sidebarRef.current && !sidebarRef.current.contains(event.target as Node)) {
        // Only close if it was opened by click, not by hover
        if (isClicked) {
          setIsClicked(false);
          setIsHovered(false);
        }
      }
    };

    if (isClicked) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isClicked]);

  // Determine if sidebar should be visible
  const isSidebarVisible = isHovered || isClicked;

  // Handle profile icon click
  const handleProfileClick = () => {
    setIsClicked(!isClicked);
    setIsHovered(false); // Reset hover state when clicking
  };

  // Handle hover on right side
  const handleRightSideHover = () => {
    if (!isClicked) { // Only allow hover to open if not clicked
      setIsHovered(true);
    }
  };

  const handleRightSideLeave = () => {
    if (!isClicked) { // Only allow hover to close if not clicked
      setIsHovered(false);
    }
  };

  // If not authenticated, show sign in/sign up buttons
  if (!isLoading && !isAuthenticated) {
    return (
      <div className="flex items-center space-x-2">
        <Link to="/signin">
          <button className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-recipe-primary hover:bg-gray-50 rounded-md transition-all duration-200">
            <LogIn className="h-4 w-4" />
            Sign In
          </button>
        </Link>
        <Link to="/signup">
          <button className="flex items-center gap-2 px-3 py-2 text-sm bg-recipe-primary text-white hover:bg-recipe-primary/90 rounded-md transition-colors duration-200">
            <UserPlus className="h-4 w-4" />
            Sign Up
          </button>
        </Link>
      </div>
    );
  }

  // If loading, show simple placeholder
  if (isLoading) {
    return (
      <div className="relative h-8 w-8 rounded-full bg-gray-200 animate-pulse flex items-center justify-center">
        <User className="h-4 w-4 text-gray-400" />
      </div>
    );
  }

  // If authenticated, show hover tab
  return (
    <>
      {/* Hover Trigger Area - Right side of screen */}
      <div 
        className="fixed top-0 right-0 h-full w-4 z-[55]"
        onMouseEnter={handleRightSideHover}
        onMouseLeave={handleRightSideLeave}
      />
      
      {/* User Icon Trigger - Clickable to open manually */}
      <div className="relative">
        <button 
          className="relative h-8 w-8 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors duration-200 flex items-center justify-center cursor-pointer"
          onClick={handleProfileClick}
        >
          <User className="h-4 w-4 text-gray-600" />
        </button>
      </div>
      
      {/* Full Height Aside Tab */}
      <div 
        ref={sidebarRef}
        className={`fixed top-0 right-0 h-full w-80 shadow-2xl border-l border-gray-200 z-[55] transform transition-transform duration-300 ease-out ${
          isSidebarVisible ? 'translate-x-0' : 'translate-x-full'
        }`}
        onMouseEnter={() => {
          if (!isClicked) { // Only allow hover to keep open if not clicked
            setIsHovered(true);
          }
        }}
        onMouseLeave={() => {
          if (!isClicked) { // Only allow hover to close if not clicked
            setIsHovered(false);
          }
        }}
        style={{ 
          backgroundColor: '#ffffff',
          backdropFilter: 'none',
          isolation: 'isolate'
        }}
      >
        {/* Background Layer */}
        <div 
          className="absolute inset-0 bg-white"
          style={{ zIndex: -1 }}
        />
        {/* Close Button */}
        <button
          onClick={() => {
            setIsHovered(false);
            setIsClicked(false);
          }}
          className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors duration-200"
        >
          <X className="h-5 w-5" />
        </button>

        {/* User Header */}
        <div className="px-6 py-8 bg-gradient-to-b from-recipe-primary/5 to-transparent border-b border-gray-100">
          <div className="flex items-center space-x-4">
            <div className="h-16 w-16 rounded-full bg-recipe-primary/20 flex items-center justify-center">
              <User className="h-8 w-8 text-recipe-primary" />
            </div>
            <div>
              <div className="font-bold text-xl text-gray-900">
                {user?.full_name || 'User'}
              </div>
              <div className="text-sm text-gray-500">
                {user?.email || 'user@example.com'}
              </div>
            </div>
          </div>
        </div>
        
        {/* Quick Actions */}
        <div className="p-6 border-b border-gray-100">
          <div className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">
            Quick Actions
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Link
              to="/meal-planner"
              className="flex flex-col items-center p-4 text-sm text-gray-600 hover:text-recipe-primary hover:bg-gray-50 rounded-lg transition-all duration-200 border border-gray-100 hover:border-recipe-primary/20"
            >
              <ChefHat className="h-6 w-6 mb-2" />
              Meal Planner
            </Link>
            <Link
              to="/shopping-list"
              className="flex flex-col items-center p-4 text-sm text-gray-600 hover:text-recipe-primary hover:bg-gray-50 rounded-lg transition-all duration-200 border border-gray-100 hover:border-recipe-primary/20"
            >
              <ShoppingCart className="h-6 w-6 mb-2" />
              Shopping List
            </Link>
          </div>
        </div>
        
        {/* Navigation Links */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-6 space-y-2">
            <div className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">
              My Account
            </div>
            <Link
              to="/folders"
              className="flex items-center px-4 py-3 text-gray-700 hover:text-recipe-primary hover:bg-gray-50 rounded-lg transition-all duration-200 group"
            >
              <Folder className="mr-4 h-5 w-5 group-hover:text-recipe-primary" />
              <span className="font-medium">My Folders</span>
            </Link>
            <Link
              to="/preferences"
              className="flex items-center px-4 py-3 text-gray-700 hover:text-recipe-primary hover:bg-gray-50 rounded-lg transition-all duration-200 group"
            >
              <Settings className="mr-4 h-5 w-5 group-hover:text-recipe-primary" />
              <span className="font-medium">Preferences</span>
            </Link>
            <Link
              to="/my-reviews"
              className="flex items-center px-4 py-3 text-gray-700 hover:text-recipe-primary hover:bg-gray-50 rounded-lg transition-all duration-200 group"
            >
              <Star className="mr-4 h-5 w-5 group-hover:text-recipe-primary" />
              <span className="font-medium">My Reviews</span>
            </Link>
            <Link
              to="/favorites"
              className="flex items-center px-4 py-3 text-gray-700 hover:text-recipe-primary hover:bg-gray-50 rounded-lg transition-all duration-200 group"
            >
              <Heart className="mr-4 h-5 w-5 group-hover:text-recipe-primary" />
              <span className="font-medium">Favorites</span>
            </Link>
            <Link
              to="/meal-history"
              className="flex items-center px-4 py-3 text-gray-700 hover:text-recipe-primary hover:bg-gray-50 rounded-lg transition-all duration-200 group"
            >
              <Clock className="mr-4 h-5 w-5 group-hover:text-recipe-primary" />
              <span className="font-medium">Meal History</span>
            </Link>
            <Link
              to="/cookbook"
              className="flex items-center px-4 py-3 text-gray-700 hover:text-recipe-primary hover:bg-gray-50 rounded-lg transition-all duration-200 group"
            >
              <BookOpen className="mr-4 h-5 w-5 group-hover:text-recipe-primary" />
              <span className="font-medium">My Cookbook</span>
            </Link>
          </div>
        </div>
        
        {/* Sign Out */}
        <div className="border-t border-gray-100 p-6">
          <button
            onClick={handleSignOut}
            className="flex items-center w-full px-4 py-3 text-gray-700 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all duration-200 group"
          >
            <LogOut className="mr-4 h-5 w-5 group-hover:text-red-600" />
            <span className="font-medium">Sign Out</span>
          </button>
        </div>
      </div>
    </>
  );
};

export default UserHoverTab;
