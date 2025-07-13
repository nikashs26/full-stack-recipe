
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { UtensilsCrossed, Menu, X, Plus } from 'lucide-react';
import UserMenu from './UserMenu';
import { useAuth } from '../context/AuthContext';

const Header: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { isAuthenticated } = useAuth();
  
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
    <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      scrolled ? 'bg-white/95 shadow-md backdrop-blur-sm py-2' : 'bg-white py-4'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center">
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
        <nav className="hidden md:block">
          <ul className="flex space-x-6 items-center">
            <li>
              <Link 
                to="/" 
                className="text-gray-600 hover:text-recipe-primary transition-colors"
              >
                Home
              </Link>
            </li>
            <li>
              <Link 
                to="/recipes" 
                className="text-gray-600 hover:text-recipe-primary transition-colors"
              >
                Recipes
              </Link>
            </li>
            <li>
              <Link 
                to="/meal-planner" 
                className="text-gray-600 hover:text-recipe-primary transition-colors font-medium"
              >
                🤖 AI Meal Planner
              </Link>
            </li>
            <li>
              <Link 
                to="/shopping-list" 
                className="text-gray-600 hover:text-recipe-primary transition-colors"
              >
                Shopping List
              </Link>
            </li>
            {isAuthenticated && (
              <>
                <li>
                  <Link 
                    to="/favorites" 
                    className="text-gray-600 hover:text-recipe-primary transition-colors"
                  >
                    Favorites
                  </Link>
                </li>
                <li>
                  <Link 
                    to="/add-recipe" 
                    className="bg-recipe-primary hover:bg-recipe-primary/90 text-white px-3 py-1 rounded-md flex items-center"
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    My Recipe
                  </Link>
                </li>
              </>
            )}
            <li>
              <UserMenu />
            </li>
          </ul>
        </nav>
      </div>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-t">
          <div className="px-4 py-3 space-y-3">
            <Link 
              to="/"
              className="block text-gray-600 hover:text-recipe-primary"
              onClick={() => setMobileMenuOpen(false)}
            >
              Home
            </Link>
            <Link 
              to="/recipes"
              className="block text-gray-600 hover:text-recipe-primary"
              onClick={() => setMobileMenuOpen(false)}
            >
              Recipes
            </Link>
            <Link 
              to="/meal-planner"
              className="block text-gray-600 hover:text-recipe-primary font-medium"
              onClick={() => setMobileMenuOpen(false)}
            >
              🤖 AI Meal Planner
            </Link>
            <Link 
              to="/shopping-list"
              className="block text-gray-600 hover:text-recipe-primary"
              onClick={() => setMobileMenuOpen(false)}
            >
              Shopping List
            </Link>
            {isAuthenticated && (
              <>
                <Link 
                  to="/favorites"
                  className="block text-gray-600 hover:text-recipe-primary" 
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Favorites
                </Link>
                <Link 
                  to="/add-recipe"
                  className="block text-recipe-primary font-medium hover:text-recipe-primary/90"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Plus className="h-4 w-4 inline mr-1" />
                  My Recipe
                </Link>
                <Link 
                  to="/folders"
                  className="block text-gray-600 hover:text-recipe-primary"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Folders
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
};

export default Header;
