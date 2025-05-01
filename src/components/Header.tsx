
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { UtensilsCrossed, Search, FolderPlus, Heart, ShoppingCart } from 'lucide-react';

const Header: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);
  
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      scrolled ? 'bg-white/95 shadow-md backdrop-blur-sm py-2' : 'bg-white py-4'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center">
        <Link to="/" className="flex items-center space-x-2 text-recipe-primary hover:text-recipe-primary/90 transition-colors">
          <UtensilsCrossed className="h-8 w-8" />
          <h1 className="text-2xl font-bold">Better Bulk</h1>
        </Link>
        <nav>
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
                <Search className="h-4 w-4 inline mr-1" />
                Recipes
              </Link>
            </li>
            <li>
              <Link 
                to="/folders" 
                className="text-gray-600 hover:text-recipe-primary transition-colors"
              >
                <FolderPlus className="h-4 w-4 inline mr-1" />
                Folders
              </Link>
            </li>
            <li>
              <Link 
                to="/favorites" 
                className="text-gray-600 hover:text-recipe-primary transition-colors"
              >
                <Heart className="h-4 w-4 inline mr-1" />
                Favorites
              </Link>
            </li>
            <li>
              <Link 
                to="/shopping-list" 
                className="text-gray-600 hover:text-recipe-primary transition-colors"
              >
                <ShoppingCart className="h-4 w-4 inline mr-1" />
                Shopping List
              </Link>
            </li>
            <li>
              <Link 
                to="/add-recipe" 
                className="text-gray-600 hover:text-recipe-primary transition-colors"
              >
                Add Recipe
              </Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
};

export default Header;
