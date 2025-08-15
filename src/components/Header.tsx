
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { UtensilsCrossed, Menu, X, Plus, Folder } from 'lucide-react';
import UserMenu from './UserMenu';

const Header: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
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
                AI Meal Planner
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
            <li>
              <Link 
                to="/preferences" 
                className="text-gray-600 hover:text-recipe-primary transition-colors"
              >
                Preferences
              </Link>
            </li>
            <li>
              <Link 
                to="/folders" 
                className="flex items-center text-gray-600 hover:text-recipe-primary transition-colors"
              >
                <Folder className="mr-1 h-4 w-4" />
                My Folders
              </Link>
            </li>
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
              AI Meal Planner
            </Link>
            <Link 
              to="/shopping-list"
              className="block text-gray-600 hover:text-recipe-primary"
              onClick={() => setMobileMenuOpen(false)}
            >
              Shopping List
            </Link>
            <Link 
              to="/preferences" 
              className="block px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
              onClick={() => setMobileMenuOpen(false)}
            >
              Preferences
            </Link>
            <Link 
              to="/folders" 
              className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
              onClick={() => setMobileMenuOpen(false)}
            >
              <Folder className="mr-2 h-4 w-4" />
              My Folders
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};

export default Header;
