
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { UtensilsCrossed, Menu, X, ChefHat, Settings, Star, User, LogOut, Users } from 'lucide-react';
import UserHoverTab from './UserHoverTab';
import { useAuth } from '../contexts/AuthContext';
import { AuthModal } from './Auth/AuthModal';
import { UserManagement } from './Admin/UserManagement';
import { Button } from './ui/button';

const Header: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [userManagementOpen, setUserManagementOpen] = useState(false);
  
  const { user, isAuthenticated, logout } = useAuth();

  
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);



  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  return (
    <header className={`fixed top-0 left-0 right-0 z-[60] transition-all duration-300 ${
      scrolled ? 'bg-white/95 shadow-md backdrop-blur-sm py-2' : 'bg-white py-4'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center">
        {/* Logo */}
        <Link to="/" className="flex items-center space-x-2 text-recipe-primary hover:text-recipe-primary/90 transition-colors">
          <UtensilsCrossed className="h-8 w-8" />
          <h1 className="text-2xl font-bold">Better Bulk</h1>
        </Link>
        
        {/* Mobile menu button */}
        <button 
          className="md:hidden p-2 text-gray-600" 
          onClick={toggleMobileMenu}
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
        
        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center space-x-6">
          {/* Primary Navigation */}
          <div className="flex items-center space-x-6">
            <Link 
              to="/" 
              className="text-gray-600 hover:text-recipe-primary transition-colors font-medium"
            >
              Home
            </Link>
            <Link 
              to="/recipes" 
              className="text-gray-600 hover:text-recipe-primary transition-colors font-medium"
            >
              Recipes
            </Link>
            
            {/* AI Meal Planner - Normal Text */}
            <Link 
              to="/meal-planner"
              className="text-gray-600 hover:text-recipe-primary transition-colors font-medium"
            >
              AI Meal Planner
            </Link>
          </div>

          {/* Right Side Actions */}
          <div className="flex items-center space-x-3">
            {isAuthenticated ? (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-700">Welcome, {user?.username}</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setUserManagementOpen(true)}
                  className="flex items-center gap-1"
                >
                  <Users className="h-4 w-4" />
                  Users
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={logout}
                  className="flex items-center gap-1"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </Button>
              </div>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAuthModalOpen(true)}
                className="flex items-center gap-1"
              >
                <User className="h-4 w-4" />
                Sign In
              </Button>
            )}
          </div>
        </nav>
      </div>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-t">
          <div className="px-4 py-3 space-y-1">
            {/* Primary Mobile Navigation */}
            <Link 
              to="/"
              className="block px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-md font-medium"
              onClick={() => setMobileMenuOpen(false)}
            >
              Home
            </Link>
            <Link 
              to="/recipes"
              className="block px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-md font-medium"
              onClick={() => setMobileMenuOpen(false)}
            >
              Recipes
            </Link>
            
            {/* AI Meal Planner - Mobile */}
            <Link 
              to="/meal-planner"
              className="block px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-md font-medium"
              onClick={() => setMobileMenuOpen(false)}
            >
              AI Meal Planner
            </Link>
            
            {/* Mobile Account Section */}
            <div className="border-t border-gray-100 pt-3 mt-3">
              <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Account
              </div>
              <Link 
                to="/preferences"
                className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-md"
                onClick={() => setMobileMenuOpen(false)}
              >
                <Settings className="mr-3 h-4 w-4" />
                Preferences
              </Link>
              <Link 
                to="/my-reviews"
                className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-md"
                onClick={() => setMobileMenuOpen(false)}
              >
                <Star className="mr-3 h-4 w-4" />
                My Reviews
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onSuccess={(user, token) => {
          // Auth context will handle the login
          setAuthModalOpen(false);
        }}
      />

      {/* User Management Modal */}
      {userManagementOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <UserManagement onClose={() => setUserManagementOpen(false)} />
          </div>
        </div>
      )}
    </header>
  );
};

export default Header;
