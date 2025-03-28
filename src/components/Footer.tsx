
import React from 'react';
import { Heart } from 'lucide-react';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="md:flex md:items-center md:justify-between">
          <div className="flex justify-center md:justify-start">
            <p className="text-gray-500 text-sm">
              &copy; {currentYear} Better Bulk, Inc. All rights reserved.
            </p>
          </div>
          <div className="mt-4 md:mt-0 flex items-center justify-center md:justify-end text-sm">
            <div className="flex items-center text-gray-500">
              Made with <Heart className="h-4 w-4 mx-1 text-recipe-secondary" /> for healthy eating
            </div>
          </div>
        </div>
        <div className="mt-4 text-center text-xs text-gray-400">
          <p>The content on this site is for informational purposes only and is not intended to be a substitute for professional nutritional advice.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
