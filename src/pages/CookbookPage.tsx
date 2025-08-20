import React from 'react';
import { BookOpen, ArrowLeft, Plus, Search } from 'lucide-react';
import { Link } from 'react-router-dom';

const CookbookPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link 
            to="/" 
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Home
          </Link>
          <div className="flex items-center space-x-3">
            <div className="h-12 w-12 rounded-full bg-recipe-primary/20 flex items-center justify-center">
              <BookOpen className="h-6 w-6 text-recipe-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">My Cookbook</h1>
              <p className="text-gray-600">Your personal collection of favorite recipes and cooking notes</p>
            </div>
          </div>
        </div>

        {/* Search and Add */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search your cookbook..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-recipe-primary focus:border-transparent"
              />
            </div>
            <button className="inline-flex items-center px-4 py-2 bg-recipe-primary text-white rounded-md hover:bg-recipe-primary/90 transition-colors duration-200">
              <Plus className="h-4 w-4 mr-2" />
              Add Recipe
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="text-center">
            <div className="h-16 w-16 rounded-full bg-gray-100 mx-auto mb-4 flex items-center justify-center">
              <BookOpen className="h-8 w-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Coming Soon</h3>
            <p className="text-gray-600 mb-6">
              Your personal cookbook is currently under development. This feature will allow you to:
            </p>
            <ul className="text-left text-gray-600 space-y-2 max-w-md mx-auto">
              <li className="flex items-center">
                <span className="h-2 w-2 bg-recipe-primary rounded-full mr-3"></span>
                Save and organize your favorite recipes
              </li>
              <li className="flex items-center">
                <span className="h-2 w-2 bg-recipe-primary rounded-full mr-3"></span>
                Add personal cooking notes and modifications
              </li>
              <li className="flex items-center">
                <span className="h-2 w-2 bg-recipe-primary rounded-full mr-3"></span>
                Create custom recipe categories and tags
              </li>
              <li className="flex items-center">
                <span className="h-2 w-2 bg-recipe-primary rounded-full mr-3"></span>
                Share recipes with family and friends
              </li>
              <li className="flex items-center">
                <span className="h-2 w-2 bg-recipe-primary rounded-full mr-3"></span>
                Track recipe ratings and cooking success
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CookbookPage;
