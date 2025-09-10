import React from 'react';
import { Link } from 'react-router-dom';

const Navigation: React.FC = () => {
  return (
    <nav className="bg-background border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link to="/" className="text-xl font-bold">
              Dietary Delight
            </Link>
            <div className="hidden md:flex space-x-4">
              <Link
                to="/recipes"
                className="text-foreground/60 hover:text-foreground"
              >
                Recipes
              </Link>
              <Link
                to="/folders"
                className="text-foreground/60 hover:text-foreground"
              >
                My Folders
              </Link>
              <Link
                to="/create"
                className="text-foreground/60 hover:text-foreground"
              >
                Create Recipe
              </Link>
            </div>
          </div>
          {/* ... rest of the navigation ... */}
        </div>
      </div>
    </nav>
  );
};

export default Navigation; 